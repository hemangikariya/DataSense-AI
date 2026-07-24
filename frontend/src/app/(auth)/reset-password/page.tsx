"use client"

import React, { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as zod from "zod"
import { ShieldAlert, CheckCircle2 } from "lucide-react"
import { authApi } from "@/lib/auth-api"

const schema = zod.object({
  password: zod.string().min(8, "Password must be at least 8 characters long.")
    .refine((val) => /[A-Z]/.test(val), "Password must include at least one uppercase letter.")
    .refine((val) => /[0-9]/.test(val), "Password must include at least one number."),
  confirmPassword: zod.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match.",
  path: ["confirmPassword"]
})

type FormValues = zod.infer<typeof schema>

export default function ResetPasswordPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams?.get("token")

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
    if (!token) {
      setErrorMsg("Password reset token is missing or invalid.")
      return
    }

    setLoading(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    try {
      await authApi.resetPassword({
        token,
        new_password: data.password
      })
      setSuccessMsg("Password changed successfully! Routing to sign in...")
      setTimeout(() => {
        router.push("/login")
      }, 1500)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Failed to reset password. Link may be expired.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold tracking-tight text-blue-500">Reset Password</h1>
        <p className="text-slate-400 text-xs mt-1">Specify your new credentials key</p>
      </div>

      {!token && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded">
          Warning: Missing reset token in URL parameters.
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
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">New Password</label>
          <input
            type="password"
            {...register("password")}
            className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
            placeholder="••••••••"
            disabled={loading || !token}
          />
          {errors.password && <p className="text-[10px] text-red-500 mt-1">{errors.password.message}</p>}
        </div>

        <div>
          <label className="block text-[10px] text-slate-400 font-semibold mb-1 uppercase">Confirm Password</label>
          <input
            type="password"
            {...register("confirmPassword")}
            className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
            placeholder="••••••••"
            disabled={loading || !token}
          />
          {errors.confirmPassword && <p className="text-[10px] text-red-500 mt-1">{errors.confirmPassword.message}</p>}
        </div>

        <button
          type="submit"
          disabled={loading || !token}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 text-white rounded text-xs font-semibold transition"
        >
          {loading ? "Saving Credentials..." : "Reset Password"}
        </button>
      </form>

      <div className="text-center text-xs text-slate-500">
        Return to{" "}
        <Link href="/login" className="text-blue-500 hover:underline">
          Sign In
        </Link>
      </div>
    </div>
  )
}
