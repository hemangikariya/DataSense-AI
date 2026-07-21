"use client"

import React from "react"
import DashboardLayout from "@/components/layout/dashboard-layout"

export default function ProfilePage() {
  return (
    <DashboardLayout>
      <div className="p-8 space-y-4">
        <h1 className="text-xl font-bold tracking-tight">User Profile Settings</h1>
        <p className="text-slate-400 text-xs">
          Edit user info, change credentials passwords, or upload MinIO avatar pictures.
        </p>
        <div className="border border-slate-800 rounded-lg p-10 text-center bg-slate-900">
          <p className="text-xs text-slate-500">Avatar configuration forms will initialize here on next phases.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}
