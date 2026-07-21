"use client"

import React from "react"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { MetricCard } from "@/components/common/components"
import { ChartCard } from "@/components/common/charts"

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="p-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Analytical BI Dashboard</h1>
          <p className="text-slate-400 text-xs mt-1">
            Visual workspace canvas showing operational KPI stats.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard title="Sales Transactions" value="1,240" change="+12% from last week" />
          <MetricCard title="Data Quality score" value="98.4%" change="-0.2% variance drift" changeType="negative" />
          <MetricCard title="AI Query requests" value="384" change="+24% concurrency" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard title="Monthly Sales Metrics" chartType="Bar" />
          <ChartCard title="Total Conversions Trends" chartType="Line" />
        </div>
      </div>
    </DashboardLayout>
  )
}
