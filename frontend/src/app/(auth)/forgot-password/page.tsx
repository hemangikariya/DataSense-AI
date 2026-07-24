"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as zod from "zod"
import { ShieldAlert, CheckCircle2 } from "lucide-react"
import { authApi } from "@/lib/auth-api"

const schema = zod.object({
  email: zod.string().email("Please enter a valid email address.")
})

type FormValues = zod.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<FormValues>({
    resolver: zodResolver(schema)
  })

  const onSubmit = async (data: FormValues) => {
    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    try {
      await authApi.forgotPassword(data.email)
      setSuccessMsg("If this email exists, a password reset link has been dispatched.")
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Failed to trigger recovery email.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight text-blue-500">Recover Password</h1>
        <p className="text-slate-400 text-xs mt-1">Enter your email to request recovery link</p>
      </div>

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

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 text-white rounded text-xs font-semibold transition"
        >
          {loading ? "Processing Request..." : "Request Reset Link"}
        </button>
      </form>

      <div className="text-center text-xs text-slate-500">
        Remember your details?{" "}
        <Link href="/login" className="text-blue-500 hover:underline">
          Sign In
        </Link>
      </div>
    </div>
  )
}
