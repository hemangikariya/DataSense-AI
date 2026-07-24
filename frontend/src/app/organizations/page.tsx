"use client"

import React, { useEffect, useState, useCallback } from "react"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { useAuth } from "@/app/providers"
import { organizationApi } from "@/lib/organization-api"
import { workspaceApi } from "@/lib/workspace-api"
import { Button, Input, Card, Tabs, Badge } from "@/components/common/components"
import { DataTable } from "@/components/common/table"
import { ShieldAlert, CheckCircle2, UserPlus, Trash2, Building, Layers } from "lucide-react"

export default function OrganizationsPage() {
  const { activeOrgId, activeWorkspaceId, user, workspaces } = useAuth()
  
  const [orgDetails, setOrgDetails] = useState<any>(null)
  const [members, setMembers] = useState<any[]>([])
  
  const [loading, setLoading] = useState(true)

  // Forms states
  const [orgName, setOrgName] = useState("")
  const [orgSlug, setOrgSlug] = useState("")
  const [orgMsg, setOrgMsg] = useState("")
  const [orgError, setOrgError] = useState("")

  const [wsName, setWsName] = useState("")
  const [wsSlug, setWsSlug] = useState("")
  const [wsMsg, setWsMsg] = useState("")
  const [wsError, setWsError] = useState("")

  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole] = useState("WS_ANALYST")
  const [inviteMsg, setInviteMsg] = useState("")
  const [inviteError, setInviteError] = useState("")

  const isAdmin = user?.org_role === "ORG_OWNER" || user?.org_role === "ORG_ADMIN"

  const loadOrgData = useCallback(async () => {
    if (!activeOrgId) return
    setLoading(true)
    try {
      const details = await organizationApi.getOrgDetails(activeOrgId)
      setOrgDetails(details)
      setOrgName(details.name)
      setOrgSlug(details.slug)

      if (activeWorkspaceId) {
        const memList = await workspaceApi.listMembers(activeWorkspaceId)
        setMembers(memList)
      }
    } catch (err) {
      console.error("Failed to load organization active parameters details.")
    } finally {
      setLoading(false)
    }
  }, [activeOrgId, activeWorkspaceId])

  useEffect(() => {
    loadOrgData()
  }, [loadOrgData])

  const handleUpdateOrg = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeOrgId) return
    setOrgMsg("")
    setOrgError("")
    try {
      const updated = await organizationApi.updateOrg(activeOrgId, { name: orgName })
      setOrgDetails(updated)
      setOrgMsg("Organization updated successfully!")
    } catch (err: any) {
      setOrgError(err.response?.data?.detail || "Failed to update organization.")
    }
  }

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault()
    setWsMsg("")
    setWsError("")
    try {
      await workspaceApi.createWorkspace({
        name: wsName,
        slug: wsSlug
      })
      setWsMsg("Workspace created successfully! Refresh to switch contexts.")
      setWsName("")
      setWsSlug("")
    } catch (err: any) {
      setWsError(err.response?.data?.detail || "Failed to create workspace.")
    }
  }

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeWorkspaceId) return
    setInviteMsg("")
    setInviteError("")
    try {
      await workspaceApi.inviteMember(activeWorkspaceId, inviteEmail, inviteRole)
      setInviteMsg("Invitation sent successfully!")
      setInviteEmail("")
      const memList = await workspaceApi.listMembers(activeWorkspaceId)
      setMembers(memList)
    } catch (err: any) {
      setInviteError(err.response?.data?.detail || "Failed to invite user.")
    }
  }

  const handleRemoveMember = async (userId: string) => {
    if (!activeWorkspaceId) return
    try {
      await workspaceApi.removeMember(activeWorkspaceId, userId)
      const memList = await workspaceApi.listMembers(activeWorkspaceId)
      setMembers(memList)
    } catch (err) {
      console.error("Failed to revoke member access.")
    }
  }

  const orgSettingsTabContent = (
    <Card className="space-y-6">
      <div className="flex items-center gap-3 pb-4 border-b border-slate-850">
        <Building className="w-5 h-5 text-blue-500" />
        <h2 className="text-xs font-bold uppercase text-slate-200">Organization Settings</h2>
      </div>

      {orgMsg && (
        <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-400 text-xs rounded">
          {orgMsg}
        </div>
      )}

      {orgError && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded">
          {orgError}
        </div>
      )}

      <form onSubmit={handleUpdateOrg} className="space-y-4">
        <Input
          label="Organization Name"
          value={orgName}
          onChange={(e) => setOrgName(e.target.value)}
          disabled={!isAdmin}
          required
        />
        <Input
          label="Slug (Unique URL identifier)"
          value={orgSlug}
          disabled
          required
        />
        {isAdmin && (
          <div className="flex justify-end pt-2">
            <Button type="submit">Save settings</Button>
          </div>
        )}
      </form>
    </Card>
  )

  const workspacesTabContent = (
    <div className="space-y-6">
      {isAdmin && (
        <Card className="space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-850">
            <Layers className="w-5 h-5 text-blue-500" />
            <h2 className="text-xs font-bold uppercase text-slate-200">Create Workspace</h2>
          </div>

          {wsMsg && (
            <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-400 text-xs rounded">
              {wsMsg}
            </div>
          )}

          {wsError && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded">
              {wsError}
            </div>
          )}

          <form onSubmit={handleCreateWorkspace} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Workspace Name"
                value={wsName}
                onChange={(e) => setWsName(e.target.value)}
                placeholder="Finance analytics"
                required
              />
              <Input
                label="Slug identifier"
                value={wsSlug}
                onChange={(e) => setWsSlug(e.target.value)}
                placeholder="finance-analytics"
                required
              />
            </div>
            <div className="flex justify-end pt-2">
              <Button type="submit">Create Workspace</Button>
            </div>
          </form>
        </Card>
      )}

      <Card className="space-y-4">
        <h3 className="text-xs font-bold uppercase text-slate-200">Workspace Directory</h3>
        <div className="space-y-2">
          {workspaces.map((ws) => (
            <div key={ws.id} className="flex justify-between items-center p-3 bg-slate-950 border border-slate-850 rounded">
              <div>
                <span className="block text-xs font-semibold text-slate-200">{ws.name}</span>
                <span className="text-[10px] text-slate-500 font-mono">slug: {ws.slug}</span>
              </div>
              {ws.id === activeWorkspaceId && <Badge variant="success">Active</Badge>}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )

  const membersColumns = [
    { id: "user_id", header: "User ID", accessorKey: "user_id" },
    { id: "role", header: "Workspace Role", accessorKey: "workspace_role" },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }: any) => {
        const mem = row.original
        if (!isAdmin || mem.user_id === user?.id) return null
        return (
          <button
            onClick={() => handleRemoveMember(mem.user_id)}
            className="p-1 text-red-400 hover:bg-red-500/10 rounded transition"
            title="Remove Member"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )
      }
    }
  ]

  const membersTabContent = (
    <div className="space-y-6">
      {isAdmin && (
        <Card className="space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-850">
            <UserPlus className="w-5 h-5 text-blue-500" />
            <h2 className="text-xs font-bold uppercase text-slate-200">Invite Workspace Member</h2>
          </div>

          {inviteMsg && (
            <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-400 text-xs rounded">
              {inviteMsg}
            </div>
          )}

          {inviteError && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded">
              {inviteError}
            </div>
          )}

          <form onSubmit={handleInviteMember} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Member Email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="analyst@company.com"
                required
              />
              <div className="space-y-1.5 w-full">
                <label className="block text-[10px] text-slate-400 font-semibold uppercase">Role Scope</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
                >
                  <option value="WS_ADMIN">WS_ADMIN</option>
                  <option value="WS_ANALYST">WS_ANALYST</option>
                  <option value="WS_VIEWER">WS_VIEWER</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button type="submit">Invite Member</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="space-y-2">
        <h3 className="text-xs font-bold uppercase text-slate-200">Workspace Members Catalog</h3>
        <DataTable columns={membersColumns as any} data={members} />
      </div>
    </div>
  )

  const tabsConfig = [
    { value: "settings", label: "Settings", content: orgSettingsTabContent },
    { value: "workspaces", label: "Workspaces", content: workspacesTabContent },
    { value: "members", label: "Members & Invites", content: membersTabContent }
  ]

  return (
    <DashboardLayout>
      <div className="p-8 space-y-6 max-w-4xl">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Organization Profile</h1>
          <p className="text-slate-400 text-xs mt-1">
            Manage organization members, workspaces, invitations, and active tenant settings.
          </p>
        </div>

        <Tabs tabs={tabsConfig} />
      </div>
    </DashboardLayout>
  )
}
