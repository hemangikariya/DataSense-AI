"use client"

import React, { useEffect, useState } from "react"
import { Plus, Layout, Heart, Copy, Trash2, ArrowRight } from "lucide-react"
import axios from "axios"
import Link from "next/link"

export default function DashboardsListPage() {
  const [dashboards, setDashboards] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const fetchDashboards = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem("token")
      const res = await axios.get(`/api/v1/dashboards`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      setDashboards(res.data)
      setError(null)
    } catch (err: any) {
      setError("Failed to load dashboards list. Please configure workspace active parameters.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboards()
  }, [])

  // Favorite toggle service call
  const toggleFavorite = async (id: string, isFav: boolean) => {
    try {
      const token = localStorage.getItem("token")
      const headers = {
        Authorization: `Bearer ${token}`,
        "X-Workspace-ID": workspaceId
      }
      if (isFav) {
        await axios.delete(`/api/v1/dashboards/${id}/favorite`, { headers })
      } else {
        await axios.post(`/api/v1/dashboards/${id}/favorite`, {}, { headers })
      }
      fetchDashboards()
    } catch (err) {
      console.error(err)
    }
  }

  // Clone call
  const cloneDashboard = async (id: string) => {
    try {
      const token = localStorage.getItem("token")
      await axios.post(`/api/v1/dashboards/${id}/clone`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      fetchDashboards()
    } catch (err) {
      console.error(err)
    }
  }

  // Delete call
  const deleteDashboard = async (id: string) => {
    try {
      const token = localStorage.getItem("token")
      await axios.delete(`/api/v1/dashboards/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      fetchDashboards()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between border-b border-slate-800 pb-6 mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">Interactive Dashboards</h1>
            <p className="text-slate-400 text-sm mt-1">
              Visualize metric distributions, profiles, and analytical metrics.
            </p>
          </div>
          <Link 
            href="/dashboard/new"
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm transition shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" /> Create Dashboard
          </Link>
        </div>

        {loading ? (
          // Loading Skeletons
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-44 bg-slate-900 border border-slate-800 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="p-4 bg-red-950/30 border border-red-900/50 rounded text-red-400 text-sm">
            {error}
          </div>
        ) : dashboards.length === 0 ? (
          // Empty State
          <div className="text-center py-16 bg-slate-900 border border-slate-800 border-dashed rounded-lg">
            <Layout className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-200">No dashboards created yet</h3>
            <p className="text-slate-400 text-xs mt-1 mb-6">Create layouts and widgets to build reports canvas.</p>
            <Link 
              href="/dashboard/new"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-xs text-white border border-slate-700 transition"
            >
              Get Started
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {dashboards.map(d => {
              const isFav = d.favorites && d.favorites.length > 0
              return (
                <div key={d.id} className="group relative flex flex-col justify-between p-6 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition shadow-lg">
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-bold text-slate-200 group-hover:text-blue-500 transition text-base">
                        {d.name}
                      </h3>
                      <button 
                        onClick={() => toggleFavorite(d.id, isFav)}
                        className={`p-1.5 rounded-full border transition ${
                          isFav 
                            ? "bg-red-500/10 border-red-500/30 text-red-500" 
                            : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        <Heart className="w-3.5 h-3.5 fill-current" />
                      </button>
                    </div>
                    <p className="text-slate-400 text-xs line-clamp-2 mb-4">{d.description || "No description provided."}</p>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-800/80 pt-4 mt-4">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase ${
                      d.status === "Published" ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                    }`}>
                      {d.status}
                    </span>

                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => cloneDashboard(d.id)}
                        className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition"
                        title="Clone Layout"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => deleteDashboard(d.id)}
                        className="p-1.5 hover:bg-red-500/10 text-slate-400 hover:text-red-500 rounded transition"
                        title="Delete Dashboard"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <Link 
                        href={`/dashboard/${d.id}`}
                        className="p-1.5 hover:bg-blue-600/10 text-slate-400 hover:text-blue-500 rounded transition"
                      >
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
