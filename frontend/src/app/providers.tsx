"use client"

import React, { createContext, useContext, useState, useEffect } from "react"
import { QueryClientProvider } from "@tanstack/react-query"
import { queryClient } from "@/lib/query-client"

interface AuthContextType {
  isAuthenticated: boolean
  user: any | null
  login: (token: string, user: any) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [user, setUser] = useState<any | null>(null)

  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (token) {
      setIsAuthenticated(true)
      // Retrieve user configuration values
      const cachedUser = localStorage.getItem("user")
      if (cachedUser) {
        setUser(JSON.parse(cachedUser))
      }
    }
  }, [])

  const login = (token: string, userData: any) => {
    localStorage.setItem("access_token", token)
    localStorage.setItem("user", JSON.stringify(userData))
    setIsAuthenticated(true)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    setIsAuthenticated(false)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
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

import { ThemeProvider } from "@/providers/theme-provider"
import { NotificationProvider } from "@/providers/notification-provider"
import { ModalProvider } from "@/providers/modal-provider"
import { SidebarProvider } from "@/providers/sidebar-provider"

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
