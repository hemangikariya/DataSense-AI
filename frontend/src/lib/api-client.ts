import axios from "axios"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const axiosClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Crucial for HTTP-only cookies refresh session
})

// Request Interceptor: Inject JWT token into headers dynamically
axiosClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token")
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      // Inject Workspace/Organization context claims if present
      const orgId = localStorage.getItem("org_id")
      const workspaceId = localStorage.getItem("workspace_id")
      if (orgId && config.headers) {
        config.headers["X-Organization-ID"] = orgId
      }
      if (workspaceId && config.headers) {
        config.headers["X-Workspace-ID"] = workspaceId
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

let isRefreshing = false
let failedQueue: any[] = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Response Interceptor: Auto refresh on 401
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Avoid infinite loop if refresh token itself returns 401
      if (originalRequest.url?.includes("/auth/refresh")) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token")
          localStorage.removeItem("user")
          window.location.href = "/login?session=expired"
        }
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return axiosClient(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const res = await axios.post(`${API_URL}/api/v1/auth/refresh`, {}, { withCredentials: true })
        const { access_token } = res.data
        localStorage.setItem("access_token", access_token)
        
        axiosClient.defaults.headers.common["Authorization"] = `Bearer ${access_token}`
        processQueue(null, access_token)
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return axiosClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token")
          localStorage.removeItem("user")
          window.location.href = "/login?session=expired"
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)
