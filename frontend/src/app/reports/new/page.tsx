"use client"

import React, { useState } from "react"
import { ArrowLeft, Plus, Trash2, ShieldAlert } from "lucide-react"
import axios from "axios"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function NewReportPage() {
  const router = useRouter()
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [sections, setSections] = useState<any[]>([])
  
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const addTextSection = () => {
    setSections(prev => [
      ...prev,
      {
        section_type: "TEXT",
        title: "Report Chapter Section",
        content_text: "Input your markdown summaries details here.",
        sort_order: prev.length
      }
    ])
  }

  const addChartSection = () => {
    setSections(prev => [
      ...prev,
      {
        section_type: "CHART",
        title: "Metric Distribution Chart",
        content_text: "",
        sort_order: prev.length
      }
    ])
  }

  const deleteSection = (idx: number) => {
    setSections(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSectionChange = (idx: number, field: string, value: string) => {
    setSections(prev => {
      const copy = [...prev]
      copy[idx] = { ...copy[idx], [field]: value }
      return copy
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const token = localStorage.getItem("token")
      await axios.post(`/api/v1/reports`, {
        name,
        description,
        category: "Custom",
        sections
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      router.push("/reports")
    } catch (err: any) {
      setError("Failed to create report layout structure.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto">
        <Link 
          href="/reports"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 mb-6 transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to list
        </Link>

        <h1 className="text-3xl font-extrabold tracking-tight">Create Report layout</h1>
        <p className="text-slate-400 text-sm mt-1">Configure text chapters and visualization widgets blocks.</p>

        {error && (
          <div className="mt-6 p-4 bg-red-950/20 border border-red-900/40 text-red-400 text-xs rounded flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 space-y-8">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg space-y-6">
            <div>
              <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Report Title</label>
              <input 
                type="text" 
                value={name} 
                onChange={e => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 p-3 rounded text-sm text-slate-100 focus:outline-none"
                placeholder="e.g. Q3 Operational Audit"
                required
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Summary Description</label>
              <textarea 
                value={description} 
                onChange={e => setDescription(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 p-3 rounded text-sm text-slate-100 focus:outline-none"
                placeholder="Briefly summarize report goals..."
                rows={2}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <label className="block text-xs text-slate-400 font-semibold uppercase">Report Sections</label>
              <div className="flex gap-2">
                <button 
                  type="button" 
                  onClick={addTextSection}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-white border border-slate-700 transition"
                >
                  + Add Text Block
                </button>
                <button 
                  type="button" 
                  onClick={addChartSection}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded text-white border border-slate-700 transition"
                >
                  + Add Chart Block
                </button>
              </div>
            </div>

            {sections.length === 0 ? (
              <div className="text-center py-10 bg-slate-900/50 border border-slate-850 rounded border-dashed text-slate-500 text-xs">
                No sections added. Click buttons above to write content.
              </div>
            ) : (
              <div className="space-y-4">
                {sections.map((s, idx) => (
                  <div key={idx} className="p-5 bg-slate-900 border border-slate-800 rounded-lg flex gap-4">
                    <div className="flex-1 space-y-4">
                      <div className="flex gap-4">
                        <div className="flex-1">
                          <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Section Title</label>
                          <input 
                            type="text" 
                            value={s.title} 
                            onChange={e => handleSectionChange(idx, "title", e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 p-2 rounded text-xs text-slate-100"
                          />
                        </div>
                        <div className="w-28">
                          <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Type</label>
                          <span className="block px-3 py-2 bg-slate-950 border border-slate-800 rounded text-xs font-semibold text-slate-400 uppercase tracking-wide text-center">
                            {s.section_type}
                          </span>
                        </div>
                      </div>

                      {s.section_type === "TEXT" && (
                        <div>
                          <label className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Paragraph Text Content</label>
                          <textarea 
                            value={s.content_text} 
                            onChange={e => handleSectionChange(idx, "content_text", e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 p-2 rounded text-xs text-slate-200"
                            rows={3}
                          />
                        </div>
                      )}
                    </div>

                    <button 
                      type="button" 
                      onClick={() => deleteSection(idx)}
                      className="self-start p-2 hover:bg-red-500/10 text-slate-500 hover:text-red-500 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button 
            type="submit" 
            disabled={submitting}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 text-white rounded font-semibold text-sm transition"
          >
            {submitting ? "Compiling..." : "Save Report Layout"}
          </button>
        </form>
      </div>
    </div>
  )
}
