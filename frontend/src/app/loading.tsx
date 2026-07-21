"use client"

import React from "react"
import { Spinner } from "@/components/common/components"

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100">
      <div className="text-center space-y-4">
        <Spinner className="w-10 h-10 mx-auto" />
        <p className="text-xs text-slate-400 font-semibold tracking-wider uppercase animate-pulse">
          Loading DataSense BI Canvas...
        </p>
      </div>
    </div>
  )
}
