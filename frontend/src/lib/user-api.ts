import { axiosClient } from "./api-client"

export const userApi = {
  getProfile: async () => {
    const res = await axiosClient.get("/api/v1/auth/profile")
    return res.data
  },

  updateProfile: async (payload: any) => {
    const res = await axiosClient.put("/api/v1/auth/profile", payload)
    return res.data
  },

  changePassword: async (payload: any) => {
    const res = await axiosClient.post("/api/v1/auth/profile/change-password", payload)
    return res.data
  },

  changeEmail: async (newEmail: string) => {
    const res = await axiosClient.post("/api/v1/auth/profile/change-email", { new_email: newEmail })
    return res.data
  },

  uploadAvatar: async (file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    const res = await axiosClient.post("/api/v1/auth/profile/avatar", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    })
    return res.data
  }
}
