import { axiosClient } from "./api-client"

export const authApi = {
  login: async (payload: any) => {
    const res = await axiosClient.post("/api/v1/auth/login", payload)
    return res.data
  },

  signup: async (payload: any) => {
    const res = await axiosClient.post("/api/v1/auth/signup", payload)
    return res.data
  },

  logout: async () => {
    const res = await axiosClient.post("/api/v1/auth/logout")
    return res.data
  },

  forgotPassword: async (email: string) => {
    const res = await axiosClient.post("/api/v1/auth/forgot-password", { email })
    return res.data
  },

  resetPassword: async (payload: any) => {
    const res = await axiosClient.post("/api/v1/auth/reset-password", payload)
    return res.data
  },

  verifyEmail: async (token: string) => {
    const res = await axiosClient.get(`/api/v1/auth/verify-email?token=${token}`)
    return res.data
  },

  resendVerification: async () => {
    const res = await axiosClient.post("/api/v1/auth/profile/resend-verification")
    return res.data
  },

  getRoles: async () => {
    const res = await axiosClient.get("/api/v1/auth/roles")
    return res.data
  },

  getPermissions: async () => {
    const res = await axiosClient.get("/api/v1/auth/permissions")
    return res.data
  }
}
