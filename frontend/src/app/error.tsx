"use client"

import React, { useEffect } from "react"
import { ShieldAlert } from "lucide-react"

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="text-center space-y-4 max-w-md">
        <ShieldAlert className="w-12 h-12 text-red-500 mx-auto" />
        <h1 className="text-3xl font-extrabold tracking-tight">500 - Server Error</h1>
        <p className="text-slate-400 text-xs leading-relaxed">
          An unexpected exception interrupted the data ingestion pipeline or layout rendering process.
        </p>
        <button
          onClick={reset}
          className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-semibold border border-slate-750 transition"
        >
          Retry Load
        </button>
      </div>
    </div>
  )
}
