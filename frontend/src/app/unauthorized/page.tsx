"use client"

import React from "react"
import Link from "next/link"
import { ShieldAlert } from "lucide-react"

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100 p-6">
      <div className="text-center space-y-4 max-w-md">
        <ShieldAlert className="w-12 h-12 text-yellow-500 mx-auto" />
        <h1 className="text-3xl font-extrabold tracking-tight">401 - Unauthorized</h1>
        <p className="text-slate-400 text-xs leading-relaxed">
          Authentication credentials are missing or expired. Please sign in to establish a session.
        </p>
        <Link
          href="/login"
          className="inline-block px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold transition"
        >
          Sign In
        </Link>
      </div>
    </div>
  )
}
