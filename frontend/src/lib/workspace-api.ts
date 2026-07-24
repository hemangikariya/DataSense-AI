import { axiosClient } from "./api-client"

export const workspaceApi = {
  createWorkspace: async (payload: any) => {
    const res = await axiosClient.post("/api/v1/workspaces", payload)
    return res.data
  },

  getWorkspaceDetails: async (id: string) => {
    const res = await axiosClient.get(`/api/v1/workspaces/${id}`)
    return res.data
  },

  updateWorkspace: async (id: string, payload: any) => {
    const res = await axiosClient.put(`/api/v1/workspaces/${id}`, payload)
    return res.data
  },

  deleteWorkspace: async (id: string) => {
    const res = await axiosClient.delete(`/api/v1/workspaces/${id}`)
    return res.data
  },

  listWorkspaces: async () => {
    const res = await axiosClient.get("/api/v1/workspaces")
    return res.data
  },

  inviteMember: async (workspaceId: string, email: string, role: string) => {
    const res = await axiosClient.post(`/api/v1/workspaces/${workspaceId}/members`, { email, role })
    return res.data
  },

  removeMember: async (workspaceId: string, userId: string) => {
    const res = await axiosClient.delete(`/api/v1/workspaces/${workspaceId}/members/${userId}`)
    return res.data
  },

  listMembers: async (workspaceId: string) => {
    const res = await axiosClient.get(`/api/v1/workspaces/${workspaceId}/members`)
    return res.data
  }
}
