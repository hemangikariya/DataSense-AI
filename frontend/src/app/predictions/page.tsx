"use client"

import React, { useEffect, useState } from "react"
import { Play, TrendingUp, Cpu, Calendar, ShieldAlert } from "lucide-react"
import axios from "axios"
import Link from "next/link"

export default function PredictionsListPage() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  
  const [selectedDatasetId, setSelectedDatasetId] = useState("")
  const [algorithm, setAlgorithm] = useState("Linear Regression")
  const [targetColumn, setTargetColumn] = useState("")
  
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const fetchData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem("token")
      const headers = {
        Authorization: `Bearer ${token}`,
        "X-Workspace-ID": workspaceId
      }
      
      const resDatasets = await axios.get(`/api/v1/datasets`, { headers })
      setDatasets(resDatasets.data)
      
      const resJobs = await axios.get(`/api/v1/predictions`, { headers })
      setJobs(resJobs.data)
      
      setError(null)
    } catch (err: any) {
      setError("Failed to load predictive modeling datasets or histories.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const token = localStorage.getItem("token")
      await axios.post(`/api/v1/predictions`, {
        dataset_id: selectedDatasetId,
        algorithm,
        target_column: targetColumn
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      fetchData()
      setTargetColumn("")
    } catch (err: any) {
      setError("Failed to enqueue ML model calculation task.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="border-b border-slate-800 pb-6 mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight">Predictive Analytics</h1>
          <p className="text-slate-400 text-sm mt-1">Execute regression, classification, or k-means algorithms on ingested schemas.</p>
        </div>

        {error && (
          <div className="p-4 bg-red-950/20 border border-red-900/40 text-red-400 text-xs rounded mb-6 flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Config form */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-lg shadow-lg h-fit space-y-6">
            <h3 className="font-bold text-slate-200 text-sm border-b border-slate-800 pb-2">Run Forecast Model</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Source Dataset</label>
                <select 
                  value={selectedDatasetId} 
                  onChange={e => setSelectedDatasetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100"
                  required
                >
                  <option value="">Select Ingestion Source...</option>
                  {datasets.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Algorithm Model</label>
                <select 
                  value={algorithm} 
                  onChange={e => setAlgorithm(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100"
                >
                  <option value="Linear Regression">Linear Regression</option>
                  <option value="Polynomial Regression">Polynomial Regression</option>
                  <option value="Moving Average Forecast">Moving Average Forecast</option>
                  <option value="Exponential Smoothing">Exponential Smoothing</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Target Predict Column</label>
                <input 
                  type="text" 
                  value={targetColumn} 
                  onChange={e => setTargetColumn(e.target.value)}
                  placeholder="e.g. revenue"
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100"
                  required
                />
              </div>

              <button 
                type="submit" 
                disabled={submitting}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 text-white rounded font-semibold text-xs transition flex items-center justify-center gap-2"
              >
                <Play className="w-3.5 h-3.5" /> {submitting ? "Processing..." : "Train and Predict"}
              </button>
            </form>
          </div>

          {/* History list */}
          <div className="md:col-span-2 space-y-4">
            <h3 className="font-bold text-slate-200 text-sm">Prediction Executions History</h3>
            {loading ? (
              <div className="h-32 bg-slate-900 border border-slate-800 rounded animate-pulse" />
            ) : jobs.length === 0 ? (
              <div className="text-center py-12 bg-slate-900 border border-slate-850 rounded text-slate-500 text-xs border-dashed">
                No model training runs found. Trigger one from configuration panel.
              </div>
            ) : (
              <div className="space-y-4">
                {jobs.map(j => (
                  <div key={j.id} className="p-4 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-slate-250 text-xs">{j.algorithm}</span>
                        <span className={`px-2 py-0.5 rounded text-[8px] font-semibold uppercase tracking-wider ${
                          j.status === "Completed" ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                        }`}>
                          {j.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1">Target column: {j.target_column}</p>
                    </div>

                    <Link 
                      href={`/predictions/${j.id}`}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 rounded text-xs transition"
                    >
                      View Outputs
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
