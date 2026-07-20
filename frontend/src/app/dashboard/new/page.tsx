"use client"

import React, { useState } from "react"
import { Layout, ArrowLeft, Check, ShieldAlert } from "lucide-react"
import axios from "axios"
import Link from "next/link"
import { useRouter } from "next/navigation"

const TEMPLATES = [
  { id: "sales", name: "Sales Dashboard", desc: "Track conversions, pipeline sales values, and transactions summaries.", category: "Sales" },
  { id: "marketing", name: "Marketing Dashboard", desc: "Visualize CTR metrics, conversions, and email campaign targets.", category: "Marketing" },
  { id: "finance", name: "Finance Dashboard", desc: "Monitor operational costs, gross margins, and cash flow values.", category: "Finance" },
  { id: "operations", name: "Operations Dashboard", desc: "Audit logistical throughputs, delays, and processing times.", category: "Operations" },
  { id: "blank", name: "Blank Dashboard", desc: "Start with an empty responsive grid canvas and configure widgets.", category: "Blank" }
]

export default function NewDashboardPage() {
  const router = useRouter()
  const [selectedTemplateId, setSelectedTemplateId] = useState("blank")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    const template = TEMPLATES.find(t => t.id === selectedTemplateId)
    
    try {
      const token = localStorage.getItem("token")
      const res = await axios.post(`/api/v1/dashboards`, {
        name,
        description,
        category: template?.category || "Custom",
        is_template: false,
        template_name: template?.name || null
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      
      // Route user straight to edit canvas page
      router.push(`/dashboard/${res.data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create dashboard. Please verify workspace settings.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto">
        <Link 
          href="/dashboard"
          className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 mb-6 transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard List
        </Link>

        <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Create Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Select a starting template schema and configure layout details.</p>

        {error && (
          <div className="mt-6 p-4 bg-red-950/30 border border-red-900/50 rounded flex items-center gap-3 text-red-400 text-sm">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Left panel: Form */}
          <div className="md:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg shadow-lg space-y-6">
              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Dashboard Name</label>
                <input 
                  type="text" 
                  value={name} 
                  onChange={e => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-3 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
                  placeholder="e.g. Q3 Sales Report"
                  required
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Description</label>
                <textarea 
                  value={description} 
                  onChange={e => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-3 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
                  placeholder="Brief summary of metrics displayed..."
                  rows={3}
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={submitting}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded font-medium text-sm transition shadow-lg shadow-blue-500/20"
            >
              {submitting ? "Initializing..." : "Create and Launch Builder"}
            </button>
          </div>

          {/* Right panel: Template Grid */}
          <div className="space-y-4">
            <label className="block text-xs text-slate-400 font-semibold uppercase">Starting Template</label>
            <div className="space-y-3">
              {TEMPLATES.map(t => {
                const isSelected = selectedTemplateId === t.id
                return (
                  <div 
                    key={t.id}
                    onClick={() => setSelectedTemplateId(t.id)}
                    className={`relative p-4 rounded-lg border cursor-pointer transition flex items-start gap-3 bg-slate-900 ${
                      isSelected 
                        ? "border-blue-500 shadow-md shadow-blue-500/5" 
                        : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <Layout className={`w-5 h-5 flex-shrink-0 mt-0.5 ${isSelected ? "text-blue-500" : "text-slate-500"}`} />
                    <div>
                      <h4 className="font-semibold text-slate-200 text-xs">{t.name}</h4>
                      <p className="text-slate-400 text-[10px] mt-1 line-clamp-2">{t.desc}</p>
                    </div>

                    {isSelected && (
                      <div className="absolute top-2 right-2 bg-blue-600 rounded-full p-0.5">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
