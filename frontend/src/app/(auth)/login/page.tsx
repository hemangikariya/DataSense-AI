"use client"

import React, { useState } from "react"
import { useAuth } from "@/app/providers"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    // Perform simulated credentials validation login
    setTimeout(() => {
      login("mock-token-uuid-xyz-123", {
        email,
        active_workspace_id: "00000000-0000-0000-0000-000000000000",
        org_role: "ANALYST"
      })
      setLoading(false)
      router.push("/dashboard")
    }, 1000)
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight text-blue-500">Sign In</h1>
        <p className="text-slate-400 text-xs mt-1">Access your self-service analytics database</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
            placeholder="name@company.com"
            required
          />
        </div>

        <div>
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
            placeholder="••••••••"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 text-white rounded text-xs font-semibold transition"
        >
          {loading ? "Authenticating..." : "Sign In Session"}
        </button>
      </form>

      <div className="text-center text-xs text-slate-500">
        Don't have an account?{" "}
        <Link href="/signup" className="text-blue-500 hover:underline">
          Register
        </Link>
      </div>
    </div>
  )
}
