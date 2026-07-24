"use client"

import React, { useState } from "react"
import { useAuth } from "@/app/providers"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as zod from "zod"
import { Eye, EyeOff, ShieldAlert, CheckCircle2 } from "lucide-react"
import { authApi } from "@/lib/auth-api"

const loginSchema = zod.object({
  email: zod.string().email("Please enter a valid email address."),
  password: zod.string().min(8, "Password must be at least 8 characters long."),
  rememberMe: zod.boolean().optional()
})

type LoginFormValues = zod.infer<typeof loginSchema>

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionExpired = searchParams?.get("session") === "expired"

  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      rememberMe: false
    }
  })

  const onSubmit = async (data: LoginFormValues) => {
    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    try {
      const res = await authApi.login({
        email: data.email,
        password: data.password
      })
      login(res.access_token, res.user)
      setSuccessMsg("Session authenticated successfully! Routing dashboard...")
      
      setTimeout(() => {
        router.push("/dashboard")
      }, 800)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Authentication failed. Invalid email or password.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight text-blue-500">Sign In</h1>
        <p className="text-slate-400 text-xs mt-1">Access your self-service analytics database</p>
      </div>

      {sessionExpired && (
        <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 text-xs rounded">
          Your active session expired. Please sign in again.
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-400 text-xs rounded flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Email Address</label>
          <input
            type="email"
            {...register("email")}
            className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
            placeholder="name@company.com"
            disabled={loading}
          />
          {errors.email && <p className="text-[10px] text-red-500 mt-1">{errors.email.message}</p>}
        </div>

        <div>
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Password</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              {...register("password")}
              className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600 pr-10"
              placeholder="••••••••"
              disabled={loading}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-3 top-3 text-slate-400 hover:text-slate-200"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && <p className="text-[10px] text-red-500 mt-1">{errors.password.message}</p>}
        </div>

        <div className="flex items-center justify-between">
          <label className="inline-flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              {...register("rememberMe")}
              className="rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-0 w-3.5 h-3.5"
            />
            <span>Remember Me</span>
          </label>
          <Link href="/forgot-password" className="text-xs text-blue-500 hover:underline">
            Forgot Password?
          </Link>
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
