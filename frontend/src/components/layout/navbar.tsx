"use client"

import React, { useState } from "react"
import { useSidebar } from "@/providers/sidebar-provider"
import { useAuth } from "@/app/providers"
import { useTheme } from "@/providers/theme-provider"
import { Bell, Search, Menu, Building2, User, HelpCircle, LogOut } from "lucide-react"

export default function Navbar() {
  const { toggleMobileSidebar } = useSidebar()
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false)
  const [searchVal, setSearchVal] = useState("")

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30 text-slate-100">
      {/* Left section: toggler, workspace config */}
      <div className="flex items-center gap-4">
        <button onClick={toggleMobileSidebar} className="p-1 hover:bg-slate-800 rounded md:hidden">
          <Menu className="w-5 h-5 text-slate-300" />
        </button>

        <div className="flex items-center gap-3">
          {/* Organization indicator */}
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 border border-slate-800 rounded text-xs">
            <Building2 className="w-3.5 h-3.5 text-blue-500" />
            <span className="font-semibold">Acme Corp</span>
          </div>

          {/* Workspace select toggler */}
          <div className="flex items-center gap-1.5 bg-slate-950 px-3 py-1.5 border border-slate-800 rounded text-xs">
            <span className="font-semibold text-slate-400">WS:</span>
            <span className="font-semibold">Production BI</span>
          </div>
        </div>
      </div>

      {/* Middle section: Global search */}
      <div className="hidden md:flex items-center max-w-sm w-full bg-slate-950 border border-slate-800 px-3 py-1.5 rounded text-xs gap-2">
        <Search className="w-4 h-4 text-slate-500" />
        <input
          type="text"
          value={searchVal}
          onChange={(e) => setSearchVal(e.target.value)}
          placeholder="Search datasets, reports, configurations..."
          className="bg-transparent border-0 outline-none w-full text-slate-200"
        />
      </div>

      {/* Right section: notifications, profile */}
      <div className="flex items-center gap-4">
        <button className="p-2 hover:bg-slate-800 rounded-full relative">
          <Bell className="w-4 h-4 text-slate-400" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-blue-500 rounded-full" />
        </button>

        {/* Profile menu wrapper */}
        <div className="relative">
          <button
            onClick={() => setProfileDropdownOpen((prev) => !prev)}
            className="flex items-center gap-2 p-1.5 hover:bg-slate-800 rounded"
          >
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold text-white uppercase">
              {user?.email?.[0] || "U"}
            </div>
          </button>

          {profileDropdownOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setProfileDropdownOpen(false)} />
              <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-lg shadow-xl py-1 z-20 text-xs">
                <div className="px-4 py-2 border-b border-slate-850">
                  <p className="text-[10px] text-slate-400">Signed in as</p>
                  <p className="font-semibold truncate text-slate-200 mt-0.5">{user?.email || "user@datasense.ai"}</p>
                </div>
                
                <a href="/profile" className="flex items-center gap-2.5 px-4 py-2 hover:bg-slate-800 text-slate-300">
                  <User className="w-3.5 h-3.5" /> Profile Settings
                </a>
                <a href="/support" className="flex items-center gap-2.5 px-4 py-2 hover:bg-slate-800 text-slate-300">
                  <HelpCircle className="w-3.5 h-3.5" /> Help Center
                </a>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2.5 px-4 py-2 hover:bg-red-500/10 text-red-400 text-left"
                >
                  <LogOut className="w-3.5 h-3.5" /> Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
