"use client"

import React from "react"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-6">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 p-8 rounded-lg shadow-2xl relative overflow-hidden">
        {/* Visual glassmorphism accents */}
        <div className="absolute -top-12 -left-12 w-24 h-24 bg-blue-500/10 rounded-full blur-xl" />
        <div className="absolute -bottom-12 -right-12 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl" />
        
        <div className="relative z-10">{children}</div>
      </div>
    </div>
  )
}
