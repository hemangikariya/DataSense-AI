"use client"

import React, { createContext, useContext, useState, useCallback } from "react"
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react"

export type NotificationType = "success" | "error" | "info" | "warning"

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message?: string
}

interface NotificationContextType {
  notifications: Notification[]
  notify: (type: NotificationType, title: string, message?: string) => void
  dismiss: (id: string) => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const dismiss = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((item) => item.id !== id))
  }, [])

  const notify = useCallback((type: NotificationType, title: string, message?: string) => {
    const id = Math.random().toString(36).substring(2, 9)
    setNotifications((prev) => [...prev, { id, type, title, message }])
    
    // Automatically clear notifications after 5 seconds
    setTimeout(() => {
      dismiss(id)
    }, 5000)
  }, [dismiss])

  return (
    <NotificationContext.Provider value={{ notifications, notify, dismiss }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 rounded-lg shadow-lg border flex items-start gap-3 transition-all duration-300 transform translate-y-0 bg-slate-900 border-slate-800 text-slate-100`}
          >
            {n.type === "success" && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
            {n.type === "error" && <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
            {n.type === "warning" && <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0" />}
            {n.type === "info" && <Info className="w-5 h-5 text-blue-500 flex-shrink-0" />}
            
            <div className="flex-1">
              <h4 className="text-xs font-bold">{n.title}</h4>
              {n.message && <p className="text-[10px] text-slate-400 mt-1">{n.message}</p>}
            </div>

            <button onClick={() => dismiss(n.id)} className="p-0.5 hover:bg-slate-850 rounded">
              <X className="w-3.5 h-3.5 text-slate-500" />
            </button>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error("useNotifications must be executed within a NotificationProvider wrapper.")
  }
  return context
}
