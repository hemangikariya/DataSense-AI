"use client"

import React, { useEffect, useState } from "react"
import { ArrowLeft, Cpu, ShieldAlert } from "lucide-react"
import axios from "axios"
import Link from "next/link"
import { useParams } from "next/navigation"

export default function PredictionDetailsPage() {
  const params = useParams()
  const id = params?.id as string

  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  useEffect(() => {
    if (!id) return
    const fetchPredictionDetails = async () => {
      try {
        const token = localStorage.getItem("token")
        const res = await axios.get(`/api/v1/predictions/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-ID": workspaceId
          }
        })
        setJob(res.data)
      } catch (err) {
        setError("Failed to load model details.")
      } finally {
        setLoading(false)
      }
    }
    fetchPredictionDetails()
  }, [id])

  const result = job?.results?.[0]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 border-b border-slate-800 pb-6 mb-8">
          <Link 
            href="/predictions"
            className="p-2 hover:bg-slate-900 rounded-full border border-slate-800 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Model Analysis Report</h1>
            <p className="text-slate-400 text-xs mt-1">Algorithm outputs, accuracy scores, and explainability summaries.</p>
          </div>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <span className="text-sm text-slate-400">Loading model matrices...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-950/20 border border-red-900/40 text-red-400 text-xs rounded">
            {error}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg text-center">
                <span className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Algorithm</span>
                <span className="text-base font-bold text-slate-200">{job.algorithm}</span>
              </div>
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg text-center">
                <span className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Target Target</span>
                <span className="text-base font-bold text-slate-200">{job.target_column}</span>
              </div>
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg text-center">
                <span className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">Confidence Score</span>
                <span className="text-base font-extrabold text-blue-500">{(result?.confidence_score * 100).toFixed(0)}%</span>
              </div>
            </div>

            {result && (
              <>
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg space-y-4">
                  <h3 className="font-bold text-slate-200 text-sm border-b border-slate-800 pb-2">Explainable Summary</h3>
                  <p className="text-xs text-slate-350 leading-relaxed">{result.plain_explanation}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg space-y-4">
                    <h3 className="font-bold text-slate-200 text-sm border-b border-slate-800 pb-2">Metrics Accuracy</h3>
                    <div className="text-xs space-y-2">
                      {Object.entries(result.metrics_json || {}).map(([k, v]: any) => (
                        <p key={k} className="flex justify-between">
                          <span className="text-slate-500 uppercase font-semibold">{k}</span>
                          <span className="text-slate-300 font-bold">{v}</span>
                        </p>
                      ))}
                    </div>
                  </div>

                  <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg space-y-4">
                    <h3 className="font-bold text-slate-200 text-sm border-b border-slate-800 pb-2">Feature Importance</h3>
                    <div className="text-xs space-y-2">
                      {Object.entries(result.feature_importance_json || {}).map(([k, v]: any) => (
                        <p key={k} className="flex justify-between">
                          <span className="text-slate-500 font-semibold">{k}</span>
                          <span className="text-slate-300 font-bold">{(v * 100).toFixed(0)}%</span>
                        </p>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                  <h3 className="font-bold text-slate-200 text-sm border-b border-slate-800 pb-2 text-yellow-500">Model Limitations</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{result.limitations}</p>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
