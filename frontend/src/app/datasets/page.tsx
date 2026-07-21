"use client"

import React from "react"
import DashboardLayout from "@/components/layout/dashboard-layout"
import { DataTable } from "@/components/common/table"

const SAMPLE_COLS = [
  { accessorKey: "name", header: "Dataset Name" },
  { accessorKey: "format", header: "File Format" },
  { accessorKey: "size", header: "Size (KB)" },
  { accessorKey: "status", header: "Ingestion Status" }
]

const SAMPLE_DATA = [
  { name: "sales_q3_raw.csv", format: "CSV", size: "1,048", status: "Ready" },
  { name: "customers_churn_predictions.xlsx", format: "XLSX", size: "4,210", status: "Ready" },
  { name: "marketing_funnel_clicks.json", format: "JSON", size: "512", status: "Ready" }
]

export default function DatasetsPage() {
  return (
    <DashboardLayout>
      <div className="p-8 space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Dataset Ingestion Manager</h1>
          <p className="text-slate-400 text-xs mt-1">
            Browse profile analytics schemas, null rates, and drift configurations.
          </p>
        </div>

        <DataTable columns={SAMPLE_COLS as any} data={SAMPLE_DATA} searchKey="name" />
      </div>
    </DashboardLayout>
  )
}
