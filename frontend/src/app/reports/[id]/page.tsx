"use client"

import React, { useEffect, useState } from "react"
import { ArrowLeft, Download, Calendar } from "lucide-react"
import axios from "axios"
import Link from "next/link"
import { useParams } from "next/navigation"

export default function ReportDetailsPage() {
  const params = useParams()
  const id = params?.id as string

  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  useEffect(() => {
    if (!id) return
    const fetchReportDetails = async () => {
      try {
        const token = localStorage.getItem("token")
        const res = await axios.get(`/api/v1/reports/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-ID": workspaceId
          }
        })
        setReport(res.data)
      } catch (err) {
        setError("Failed to load report layout.")
      } finally {
        setLoading(false)
      }
    }
    fetchReportDetails()
  }, [id])

  const triggerPDFExport = async () => {
    try {
      const token = localStorage.getItem("token")
      await axios.post(`/api/v1/reports/${id}/export?format=PDF`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      alert("PDF compilation enqueued. Check downloads tab in a few moments!")
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between border-b border-slate-800 pb-6 mb-8">
          <div className="flex items-center gap-4">
            <Link 
              href="/reports"
              className="p-2 hover:bg-slate-900 rounded-full border border-slate-800 transition"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">{report?.name || "Report Preview"}</h1>
              <p className="text-slate-400 text-xs mt-1">{report?.description || "Document preview window."}</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button 
              onClick={triggerPDFExport}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition"
            >
              <Download className="w-4 h-4" /> Export PDF
            </button>
          </div>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <span className="text-sm text-slate-400">Loading document layout...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-950/20 border border-red-900/50 rounded text-red-400 text-xs">
            {error}
          </div>
        ) : (
          <div className="space-y-8 bg-slate-900 border border-slate-800 p-8 rounded-lg shadow-lg">
            {report.sections.map((s: any, idx: number) => (
              <div key={s.id || idx} className="space-y-2 border-b border-slate-850 pb-6 last:border-b-0 last:pb-0">
                <h3 className="font-bold text-slate-200 text-sm">{s.title}</h3>
                {s.section_type === "TEXT" ? (
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{s.content_text}</p>
                ) : (
                  <div className="h-44 bg-slate-950 border border-slate-800 rounded flex items-center justify-center text-slate-500 text-xs">
                    [Chart Placeholder Canvas Widget]
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
