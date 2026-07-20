"use client"

import React, { useEffect, useState } from "react"
import { ArrowLeft, Plus, Settings, Save, Download, FileJson } from "lucide-react"
import axios from "axios"
import Link from "next/link"
import { useParams } from "next/navigation"
import ChartRenderer from "../ChartRenderer"
import WidgetEditor from "../WidgetEditor"

export default function DashboardDetailsPage() {
  const params = useParams()
  const id = params?.id as string

  const [dashboard, setDashboard] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [editingWidget, setEditingWidget] = useState<any>(null)
  const [theme, setTheme] = useState<"dark" | "light">("dark")

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const fetchDashboardDetails = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem("token")
      const res = await axios.get(`/api/v1/dashboards/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      setDashboard(res.data)
      setError(null)
    } catch (err: any) {
      setError("Failed to load dashboard parameters. Please verify authorization.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchDashboardDetails()
    }
  }, [id])

  // Widget addition/update save hook
  const handleSaveWidget = async (widgetData: any) => {
    try {
      const token = localStorage.getItem("token")
      const headers = {
        Authorization: `Bearer ${token}`,
        "X-Workspace-ID": workspaceId
      }
      if (editingWidget) {
        await axios.put(`/api/v1/widgets/${editingWidget.id}`, widgetData, { headers })
      } else {
        await axios.post(`/api/v1/dashboards/${id}/widgets`, widgetData, { headers })
      }
      setIsEditorOpen(false)
      setEditingWidget(null)
      fetchDashboardDetails()
    } catch (err) {
      console.error(err)
    }
  }

  // Configuration JSON download handler
  const handleExportJSON = async () => {
    try {
      const token = localStorage.getItem("token")
      const res = await axios.get(`/api/v1/dashboards/${id}/export`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" })
      const link = document.createElement("a")
      link.href = URL.createObjectURL(blob)
      link.download = `${dashboard.name.replace(/\s+/g, "_")}_config.json`
      link.click()
    } catch (err) {
      console.error("Export config failed")
    }
  }

  return (
    <div className={`min-h-screen p-8 transition-colors duration-200 ${
      theme === "dark" ? "bg-slate-950 text-slate-100" : "bg-slate-50 text-slate-900"
    }`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-6 mb-8 gap-4">
          <div className="flex items-center gap-4">
            <Link 
              href="/dashboard"
              className="p-2 hover:bg-slate-900/50 rounded-full border border-slate-800 transition"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight">{dashboard?.name || "Interactive Canvas"}</h1>
                <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  v{dashboard?.version || 1}
                </span>
              </div>
              <p className="text-slate-400 text-xs mt-1">{dashboard?.description || "No description loaded."}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end md:self-auto">
            {/* Toggle light/dark */}
            <button 
              onClick={() => setTheme(prev => prev === "dark" ? "light" : "dark")}
              className="px-3 py-2 bg-slate-900 border border-slate-800 rounded text-xs font-semibold text-slate-300 hover:text-white transition"
            >
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </button>

            <button 
              onClick={handleExportJSON}
              className="flex items-center gap-2 px-3 py-2 bg-slate-900 border border-slate-800 rounded text-xs font-semibold text-slate-300 hover:text-white transition"
              title="Export Config JSON"
            >
              <FileJson className="w-4 h-4" /> Export Configuration
            </button>

            <button 
              onClick={() => {
                setEditingWidget(null)
                setIsEditorOpen(true)
              }}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-xs transition shadow-lg"
            >
              <Plus className="w-4 h-4" /> Add Widget
            </button>
          </div>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <span className="text-sm text-slate-400">Loading widgets grid canvas...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-950/30 border border-red-900/50 rounded text-red-400 text-sm">
            {error}
          </div>
        ) : dashboard?.widgets?.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/40 border border-slate-850 border-dashed rounded-lg">
            <Plus className="w-10 h-10 text-slate-600 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-300 text-sm">Empty Dashboard Layout</h3>
            <p className="text-slate-500 text-xs mt-1 mb-6">Create widgets templates to load charts.</p>
            <button 
              onClick={() => setIsEditorOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition"
            >
              Add First Widget
            </button>
          </div>
        ) : (
          // Grid layout widgets mapping
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {dashboard.widgets.map((w: any) => (
              <div key={w.id} className="min-h-[300px]">
                <ChartRenderer 
                  widget={w}
                  theme={theme}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <WidgetEditor 
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        onSave={handleSaveWidget}
        widget={editingWidget}
        workspaceId={workspaceId}
      />
    </div>
  )
}
