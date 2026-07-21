"use client"

import React, { createContext, useContext, useState } from "react"

interface SidebarContextType {
  isCollapsed: boolean
  toggleSidebar: () => void
  isMobileOpen: boolean
  toggleMobileSidebar: () => void
  closeMobileSidebar: () => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  const toggleSidebar = () => setIsCollapsed((prev) => !prev)
  const toggleMobileSidebar = () => setIsMobileOpen((prev) => !prev)
  const closeMobileSidebar = () => setIsMobileOpen(false)

  return (
    <SidebarContext.Provider
      value={{
        isCollapsed,
        toggleSidebar,
        isMobileOpen,
        toggleMobileSidebar,
        closeMobileSidebar
      }}
    >
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  const context = useContext(SidebarContext)
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider wrapper.")
  }
  return context
}
