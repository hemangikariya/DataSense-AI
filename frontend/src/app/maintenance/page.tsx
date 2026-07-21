"use client"

import React from "react"
import { RefreshCw } from "lucide-react"

export default function MaintenancePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="text-center space-y-4 max-w-md">
        <RefreshCw className="w-12 h-12 text-blue-500 mx-auto animate-spin" />
        <h1 className="text-3xl font-extrabold tracking-tight">System Maintenance</h1>
        <p className="text-slate-400 text-xs leading-relaxed">
          The analytics query engines are temporarily offline for updates. Normal service is resuming shortly.
        </p>
      </div>
    </div>
  )
}
