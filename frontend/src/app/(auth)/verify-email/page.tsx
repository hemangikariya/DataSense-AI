"use client"

import React, { useEffect, useState, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ShieldAlert, CheckCircle2 } from "lucide-react"
import { Spinner } from "@/components/common/components"
import { authApi } from "@/lib/auth-api"

export default function VerifyEmailPage() {
  const searchParams = useSearchParams()
  const token = searchParams?.get("token")
  const router = useRouter()
  
  const [statusState, setStatusState] = useState<"loading" | "success" | "error" | "no-token">("loading")
  const [msg, setMsg] = useState("")
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMsg, setResendMsg] = useState("")

  // Use a ref to ensure the API call is only triggered once on load
  const hasTriggeredRef = useRef(false)

  useEffect(() => {
    if (!token) {
      setStatusState("no-token")
      return
    }

    if (hasTriggeredRef.current) return
    hasTriggeredRef.current = true

    const doVerify = async () => {
      try {
        await authApi.verifyEmail(token)
        setStatusState("success")
        setMsg("Your email address was successfully verified! Redirecting to login...")
        setTimeout(() => {
          router.push("/login")
        }, 3000)
      } catch (err: any) {
        setStatusState("error")
        setMsg(err.response?.data?.detail || "Invalid or expired email verification token link.")
      }
    }

    doVerify()
  }, [token, router])

  const handleResend = async () => {
    setResendLoading(true)
    setResendMsg("")
    try {
      // resend verification simulations
      await authApi.resendVerification()
      setResendMsg("A new verification simulation code has been logged to the system logs.")
    } catch (err: any) {
      setResendMsg("Failed to resend. Please make sure you are logged in first.")
    } finally {
      setResendLoading(false)
    }
  }

  return (
    <div className="space-y-6 text-center">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-blue-500">Email Verification</h1>
      </div>

      {statusState === "loading" && (
        <div className="space-y-4 py-6">
          <div className="w-8 h-8 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Verifying security token context...</p>
        </div>
      )}

      {statusState === "no-token" && (
        <div className="space-y-4 py-4">
          <ShieldAlert className="w-12 h-12 text-yellow-500 mx-auto" />
          <p className="text-xs text-slate-350">
            No verification token was detected. Please check the anchor link in your registration email.
          </p>
          <div className="pt-2">
            <Link href="/login" className="px-4 py-2 bg-blue-600 hover:bg-blue-750 text-white rounded text-xs font-semibold">
              Return to Login
            </Link>
          </div>
        </div>
      )}

      {statusState === "success" && (
        <div className="space-y-4 py-4">
          <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto" />
          <p className="text-xs text-green-400 font-semibold">{msg}</p>
          <div className="pt-2">
            <Link href="/login" className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-slate-200 rounded text-xs font-semibold">
              Sign In Now
            </Link>
          </div>
        </div>
      )}

      {statusState === "error" && (
        <div className="space-y-4 py-4">
          <ShieldAlert className="w-12 h-12 text-red-500 mx-auto" />
          <p className="text-xs text-red-400 font-semibold">{msg}</p>
          
          <div className="bg-slate-950 p-4 border border-slate-850 rounded text-left space-y-3">
            <p className="text-[10px] text-slate-400">
              Verification links expire after 24 hours. Request a new link if required:
            </p>
            <button
              onClick={handleResend}
              disabled={resendLoading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-750 disabled:bg-slate-850 text-white text-xs font-semibold rounded transition"
            >
              {resendLoading ? "Requesting Link..." : "Resend Verification Link"}
            </button>
            {resendMsg && <p className="text-[10px] text-slate-350 mt-1">{resendMsg}</p>}
          </div>

          <div className="pt-2">
            <Link href="/login" className="text-xs text-blue-500 hover:underline">
              Return to Sign In
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
