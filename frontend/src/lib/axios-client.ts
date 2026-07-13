import axios from "axios"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const axiosClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request Interceptor: Inject JWT token into headers dynamically
axiosClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token")
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      // Inject Workspace context claims if present
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

// Response Interceptor: Redirect to login or refresh token on 401 Unauthenticated
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        console.warn("Session expired. Redirecting to auth portal...")
        localStorage.removeItem("access_token")
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  }
)
