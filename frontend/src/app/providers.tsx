"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"
import { QueryClientProvider } from "@tanstack/react-query"
import { queryClient } from "@/lib/query-client"
import { ThemeProvider } from "@/providers/theme-provider"
import { NotificationProvider } from "@/providers/notification-provider"
import { ModalProvider } from "@/providers/modal-provider"
import { SidebarProvider } from "@/providers/sidebar-provider"
import { axiosClient } from "@/lib/api-client"
import axios from "axios"

interface AuthContextType {
  isAuthenticated: boolean
  user: any | null
  activeOrgId: string | null
  activeWorkspaceId: string | null
  permissions: string[]
  workspaces: any[]
  loading: boolean
  login: (token: string, user: any) => void
  logout: () => void
  switchWorkspace: (workspaceId: string) => void
  switchOrganization: (orgId: string) => Promise<void>
  refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [user, setUser] = useState<any | null>(null)
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null)
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null)
  const [permissions, setPermissions] = useState<string[]>([])
  const [workspaces, setWorkspaces] = useState<any[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  // Fetch workspaces matching org context
  const loadWorkspaces = useCallback(async () => {
    try {
      const res = await axiosClient.get("/api/v1/workspaces")
      setWorkspaces(res.data)
      if (res.data.length > 0 && !localStorage.getItem("workspace_id")) {
        const defaultWs = res.data[0].id
        localStorage.setItem("workspace_id", defaultWs)
        setActiveWorkspaceId(defaultWs)
      }
    } catch (err) {
      console.error("Failed to load active workspaces list context")
    }
  }, [])

  // Rotate JWT token
  const refreshSession = useCallback(async () => {
    try {
      const res = await axiosClient.post("/api/v1/auth/refresh", {})
      const { access_token } = res.data
      localStorage.setItem("access_token", access_token)
      setIsAuthenticated(true)
      
      const cachedUser = localStorage.getItem("user")
      if (cachedUser) {
        const u = JSON.parse(cachedUser)
        setUser(u)
        setActiveOrgId(u.organization_id || localStorage.getItem("org_id"))
      }
      
      setActiveWorkspaceId(localStorage.getItem("workspace_id"))
      await loadWorkspaces()
    } catch (err) {
      logout()
    } finally {
      setLoading(false)
    }
  }, [loadWorkspaces])

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (token) {
      setIsAuthenticated(true)
      const cachedUser = localStorage.getItem("user")
      if (cachedUser) {
        const u = JSON.parse(cachedUser)
        setUser(u)
        setActiveOrgId(u.organization_id || localStorage.getItem("org_id"))
      }
      setActiveWorkspaceId(localStorage.getItem("workspace_id"))
      loadWorkspaces().finally(() => setLoading(false))
    } else {
      // Try refresh session on start
      refreshSession()
    }

    // Auto rotate token every 10 minutes
    const interval = setInterval(() => {
      if (localStorage.getItem("access_token")) {
        refreshSession()
      }
    }, 10 * 60 * 1000)

    return () => clearInterval(interval)
  }, [loadWorkspaces, refreshSession])

  const login = (token: string, userData: any) => {
    localStorage.setItem("access_token", token)
    localStorage.setItem("user", JSON.stringify(userData))
    if (userData.organization_id) {
      localStorage.setItem("org_id", userData.organization_id)
      setActiveOrgId(userData.organization_id)
    }
    setIsAuthenticated(true)
    setUser(userData)
    loadWorkspaces()
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    localStorage.removeItem("org_id")
    localStorage.removeItem("workspace_id")
    setIsAuthenticated(false)
    setUser(null)
    setActiveOrgId(null)
    setActiveWorkspaceId(null)
    setWorkspaces([])
    setPermissions([])
  }

  const switchWorkspace = (wsId: string) => {
    localStorage.setItem("workspace_id", wsId)
    setActiveWorkspaceId(wsId)
    // Reload permissions or dispatch updates
  }

  const switchOrganization = async (orgId: string) => {
    try {
      await axiosClient.post("/api/v1/organizations/switch", {}, {
        headers: { "X-Organization-ID": orgId }
      })
      localStorage.setItem("org_id", orgId)
      setActiveOrgId(orgId)
      
      // Clear previous workspace choice to select default
      localStorage.removeItem("workspace_id")
      setActiveWorkspaceId(null)
      await loadWorkspaces()
    } catch (err) {
      console.error("Switch organization context failed", err)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        activeOrgId,
        activeWorkspaceId,
        permissions,
        workspaces,
        loading,
        login,
        logout,
        switchWorkspace,
        switchOrganization,
        refreshSession
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be executed within an AuthProvider element.")
  }
  return context
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <NotificationProvider>
          <ModalProvider>
            <SidebarProvider>
              <AuthProvider>{children}</AuthProvider>
            </SidebarProvider>
          </ModalProvider>
        </NotificationProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
