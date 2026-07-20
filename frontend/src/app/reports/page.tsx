"use client"

import React, { useEffect, useState } from "react"
import { Plus, FileText, Calendar, Download, Trash2, ArrowRight } from "lucide-react"
import axios from "axios"
import Link from "next/link"

export default function ReportsListPage() {
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const fetchReports = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem("token")
      const res = await axios.get(`/api/v1/reports`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      setReports(res.data)
      setError(null)
    } catch (err: any) {
      setError("Failed to load reporting profiles list.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReports()
  }, [])

  const deleteReport = async (id: string) => {
    try {
      const token = localStorage.getItem("token")
      await axios.delete(`/api/v1/reports/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      fetchReports()
    } catch (err) {
      console.error(err)
    }
  }

  const triggerExport = async (id: string) => {
    try {
      const token = localStorage.getItem("token")
      await axios.post(`/api/v1/reports/${id}/export?format=PDF`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      alert("PDF compilation job enqueued. Check downloads tab in a few moments!")
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between border-b border-slate-800 pb-6 mb-8">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Structured Reports</h1>
            <p className="text-slate-400 text-sm mt-1">Compile executive document summaries and schedule cron mail deliveries.</p>
          </div>
          <Link 
            href="/reports/new"
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm transition"
          >
            <Plus className="w-4 h-4" /> New Report Layout
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-44 bg-slate-900 border border-slate-800 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="p-4 bg-red-950/20 border border-red-900/50 rounded text-red-400 text-xs">
            {error}
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-16 bg-slate-900 border border-slate-800 border-dashed rounded-lg">
            <FileText className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-200">No reports generated yet</h3>
            <p className="text-slate-400 text-xs mt-1 mb-6">Create text chapters, tables, and widget captures.</p>
            <Link 
              href="/reports/new"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-xs text-white border border-slate-700 transition"
            >
              Configure Report
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {reports.map(r => (
              <div key={r.id} className="group flex flex-col justify-between p-6 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition">
                <div>
                  <h3 className="font-bold text-slate-200 group-hover:text-blue-500 transition text-base mb-1">{r.name}</h3>
                  <p className="text-slate-400 text-xs line-clamp-2">{r.description || "No description provided."}</p>
                </div>

                <div className="flex items-center justify-between border-t border-slate-800/80 pt-4 mt-6">
                  <span className="text-[10px] text-slate-500 font-medium">Sections: {r.sections?.length || 0}</span>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => triggerExport(r.id)}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition"
                      title="Trigger PDF Export"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => deleteReport(r.id)}
                      className="p-1.5 hover:bg-red-500/10 text-slate-400 hover:text-red-500 rounded transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <Link 
                      href={`/reports/${r.id}`}
                      className="p-1.5 hover:bg-blue-600/10 text-slate-400 hover:text-blue-500 rounded transition"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
