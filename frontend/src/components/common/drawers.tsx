"use client"

import React from "react"
import { X } from "lucide-react"

interface DrawerProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}

export function SideDrawer({ isOpen, onClose, title, children }: DrawerProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      {/* Backdrop overlay */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-xs" onClick={onClose} />
      
      {/* Slide drawer */}
      <div className="relative w-full max-w-sm bg-slate-900 border-l border-slate-800 p-6 flex flex-col h-full z-10 text-slate-100 overflow-y-auto">
        <div className="flex items-center justify-between border-b border-slate-850 pb-4 mb-6">
          <h3 className="font-bold text-slate-200 text-sm">{title}</h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded">
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
        <div className="flex-1 space-y-4">{children}</div>
      </div>
    </div>
  )
}
