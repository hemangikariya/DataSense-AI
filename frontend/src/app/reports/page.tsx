"use client"

import React from "react"
import DashboardLayout from "@/components/layout/dashboard-layout"

export default function ReportsPage() {
  return (
    <DashboardLayout>
      <div className="p-8 space-y-4">
        <h1 className="text-xl font-bold tracking-tight">Structured Reports Catalog</h1>
        <p className="text-slate-400 text-xs">
          Build text chapters, attach visual cards captures, and automate cron schedules deliveries.
        </p>
        <div className="border border-slate-800 rounded-lg p-10 text-center bg-slate-900">
          <p className="text-xs text-slate-500">Reports compilation parameters will initialize here on next phases.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}
