"use client"

import React from "react"
import Link from "next/link"
import { Lock } from "lucide-react"

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="text-center space-y-4 max-w-md">
        <Lock className="w-12 h-12 text-red-500 mx-auto animate-pulse" />
        <h1 className="text-3xl font-extrabold tracking-tight">403 - Forbidden</h1>
        <p className="text-slate-400 text-xs leading-relaxed">
          Your active workspace/org role does not possess the permissions required to view this dataset, dashboard, or layout configurations.
        </p>
        <Link
          href="/dashboard"
          className="inline-block px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition"
        >
          Return Home
        </Link>
      </div>
    </div>
  )
}
