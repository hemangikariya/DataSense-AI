"use client"

import React, { useEffect } from "react"
import { useAuth } from "@/app/providers"
import { useRouter } from "next/navigation"
import Sidebar from "./sidebar"
import Navbar from "./navbar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/login")
    }
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400 animate-pulse uppercase tracking-wider font-semibold">
            Loading DataSense Workspace Session...
          </p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Navigation Sidebar */}
      <Sidebar />

      {/* Main content body area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        
        {/* Dynamic children viewport content container */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
