"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function SignupPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      router.push("/login")
    }, 1000)
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight text-blue-500">Register</h1>
        <p className="text-slate-400 text-xs mt-1">Create your DataSense AI analysis account</p>
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

        <div>
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Confirm Password</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
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
          {loading ? "Registering..." : "Create Account"}
        </button>
      </form>

      <div className="text-center text-xs text-slate-500">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-500 hover:underline">
          Sign In
        </Link>
      </div>
    </div>
  )
}
