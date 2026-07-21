"use client"

import React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useSidebar } from "@/providers/sidebar-provider"
import { useAuth } from "@/app/providers"
import { useTheme } from "@/providers/theme-provider"
import {
  LayoutDashboard,
  Database,
  BarChart3,
  MessageSquare,
  FileText,
  TrendingUp,
  Building2,
  Users,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sun,
  Moon
} from "lucide-react"

const MENU_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Datasets", href: "/datasets", icon: Database },
  { label: "AI Assistant", href: "/ai", icon: MessageSquare },
  { label: "Reports", href: "/reports", icon: FileText },
  { label: "Predictions", href: "/predictions", icon: TrendingUp },
  { label: "Organization", href: "/organizations", icon: Building2 },
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "Support", href: "/support", icon: HelpCircle }
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const { isCollapsed, toggleSidebar, isMobileOpen, closeMobileSidebar } = useSidebar()

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between bg-slate-900 border-r border-slate-800 text-slate-100 py-6">
      <div>
        {/* Logo brand */}
        <div className="px-6 mb-8 flex items-center justify-between">
          {!isCollapsed && <span className="font-extrabold text-blue-500 tracking-tight text-sm">DataSense AI</span>}
          <button onClick={toggleSidebar} className="p-1 hover:bg-slate-800 rounded hidden md:block">
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1.5 px-3">
          {MENU_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeMobileSidebar}
                className={`flex items-center gap-3 px-3 py-2.5 rounded text-xs font-semibold transition ${
                  isActive ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Footer controls */}
      <div className="px-3 space-y-2">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 transition"
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          {!isCollapsed && <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>}
        </button>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-red-500/10 transition"
        >
          <LogOut className="w-4 h-4" />
          {!isCollapsed && <span>Logout</span>}
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside className={`hidden md:block transition-all duration-300 ${isCollapsed ? "w-16" : "w-64"} h-screen sticky top-0`}>
        {sidebarContent}
      </aside>

      {/* Mobile sidebar sliding drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="fixed inset-0 bg-black/60" onClick={closeMobileSidebar} />
          <aside className="relative w-64 h-full z-10">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  )
}
