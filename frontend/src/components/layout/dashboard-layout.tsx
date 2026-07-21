"use client"

import React from "react"
import Sidebar from "./sidebar"
import Navbar from "./navbar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
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
