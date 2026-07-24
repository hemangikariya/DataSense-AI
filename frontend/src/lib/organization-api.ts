import { axiosClient } from "./api-client"

export const organizationApi = {
  createOrg: async (payload: any) => {
    const res = await axiosClient.post("/api/v1/organizations", payload)
    return res.data
  },

  getOrgDetails: async (id: string) => {
    const res = await axiosClient.get(`/api/v1/organizations/${id}`)
    return res.data
  },

  updateOrg: async (id: string, payload: any) => {
    const res = await axiosClient.put(`/api/v1/organizations/${id}`, payload)
    return res.data
  },

  deleteOrg: async (id: string) => {
    const res = await axiosClient.delete(`/api/v1/organizations/${id}`)
    return res.data
  },

  switchOrg: async (targetOrgId: string) => {
    const res = await axiosClient.post(
      "/api/v1/organizations/switch",
      {},
      {
        headers: {
          "X-Organization-ID": targetOrgId,
        },
      }
    )
    return res.data
  }
}
