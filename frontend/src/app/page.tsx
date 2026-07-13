"use client"

import React from "react"
import { useAuth } from "./providers"

export default function HomePage() {
  const { isAuthenticated, user, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-slate-950 text-slate-100">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 p-8 rounded-lg shadow-lg text-center">
        <h1 className="text-3xl font-bold tracking-tight text-blue-500 mb-2">DataSense AI</h1>
        <p className="text-slate-400 text-sm mb-6">
          AI-Powered Self-Service Business Intelligence Platform
        </p>

        {isAuthenticated ? (
          <div>
            <div className="mb-6 p-4 bg-slate-950 border border-slate-800 rounded text-left text-xs space-y-2">
              <p><span className="text-slate-500">Email:</span> {user?.email}</p>
              <p><span className="text-slate-500">Active Workspace:</span> {user?.active_workspace_id || "None"}</p>
              <p><span className="text-slate-500">System Role:</span> {user?.org_role || "ANALYST"}</p>
            </div>
            <button
              onClick={logout}
              className="w-full py-2 bg-red-600 hover:bg-red-700 text-white rounded font-medium transition duration-200"
            >
              Sign Out Session
            </button>
          </div>
        ) : (
          <div>
            <p className="text-slate-500 text-xs mb-6">
              Phase 1 Project Foundation Initialized. Please authenticate via API endpoints to boot.
            </p>
            <div className="flex gap-4">
              <a
                href="/login"
                className="flex-1 py-2 text-center bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition duration-200"
              >
                Sign In
              </a>
              <a
                href="/signup"
                className="flex-1 py-2 text-center bg-slate-800 hover:bg-slate-700 text-white rounded font-medium border border-slate-700 transition duration-200"
              >
                Register
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
