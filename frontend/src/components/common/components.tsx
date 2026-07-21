"use client"

import React from "react"
import * as AvatarPrimitive from "@radix-ui/react-avatar"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import * as SeparatorPrimitive from "@radix-ui/react-separator"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import * as TabsPrimitive from "@radix-ui/react-tabs"

// --- ACCESSIBLE BUTTON ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost"
  size?: "sm" | "md" | "lg"
}
export function Button({ variant = "primary", size = "md", className = "", children, ...props }: ButtonProps) {
  const baseStyle = "inline-flex items-center justify-center font-semibold rounded transition duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 outline-none text-xs"
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/10",
    secondary: "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700",
    danger: "bg-red-600 hover:bg-red-700 text-white",
    ghost: "bg-transparent hover:bg-slate-850 text-slate-400 hover:text-slate-200"
  }
  const sizes = {
    sm: "px-3 py-1.5",
    md: "px-4 py-2.5",
    lg: "px-6 py-3.5"
  }
  return (
    <button className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  )
}

// --- ACCESSIBLE INPUT ---
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}
export function Input({ label, error, className = "", ...props }: InputProps) {
  return (
    <div className="space-y-1.5 w-full">
      {label && <label className="block text-[10px] text-slate-400 font-semibold uppercase">{label}</label>}
      <input
        className={`w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-900 ${className}`}
        {...props}
      />
      {error && <p className="text-[10px] text-red-500">{error}</p>}
    </div>
  )
}

// --- ACCESSIBLE TEXTAREA ---
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}
export function Textarea({ label, error, className = "", ...props }: TextareaProps) {
  return (
    <div className="space-y-1.5 w-full">
      {label && <label className="block text-[10px] text-slate-400 font-semibold uppercase">{label}</label>}
      <textarea
        className={`w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-xs text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-900 ${className}`}
        {...props}
      />
      {error && <p className="text-[10px] text-red-500">{error}</p>}
    </div>
  )
}

// --- RADIX AVATAR ---
export function Avatar({ src, fallbackText }: { src?: string; fallbackText: string }) {
  return (
    <AvatarPrimitive.Root className="inline-flex items-center justify-center overflow-hidden rounded-full w-8 h-8 bg-slate-800 select-none">
      <AvatarPrimitive.Image className="w-full h-full object-cover" src={src} alt="Avatar profile" />
      <AvatarPrimitive.Fallback className="w-full h-full flex items-center justify-center text-xs font-bold text-slate-200 uppercase" delayMs={600}>
        {fallbackText}
      </AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  )
}

// --- RADIX PROGRESS BAR ---
export function Progress({ value }: { value: number }) {
  return (
    <ProgressPrimitive.Root className="relative overflow-hidden bg-slate-950 rounded-full w-full h-2 border border-slate-850" value={value}>
      <ProgressPrimitive.Indicator className="bg-blue-500 w-full h-full transition-transform duration-500" style={{ transform: `translateX(-${100 - value}%)` }} />
    </ProgressPrimitive.Root>
  )
}

// --- RADIX SEPARATOR ---
export function Separator() {
  return (
    <SeparatorPrimitive.Root className="bg-slate-800 h-[1px] w-full my-4" />
  )
}

// --- RADIX TOOLTIP ---
export function Tooltip({ trigger, content }: { trigger: React.ReactNode; content: string }) {
  return (
    <TooltipPrimitive.Provider>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>{trigger}</TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content className="z-50 overflow-hidden rounded bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-slate-200 shadow shadow-black/10 animate-in fade-in-0 zoom-in-95" sideOffset={4}>
            {content}
            <TooltipPrimitive.Arrow className="fill-slate-900" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}

// --- RADIX TABS ---
export function Tabs({ tabs }: { tabs: { value: string; label: string; content: React.ReactNode }[] }) {
  return (
    <TabsPrimitive.Root className="flex flex-col w-full" defaultValue={tabs[0]?.value}>
      <TabsPrimitive.List className="flex border-b border-slate-800 mb-4 gap-4">
        {tabs.map((tab) => (
          <TabsPrimitive.Trigger
            key={tab.value}
            value={tab.value}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 border-b-2 border-transparent data-[state=active]:border-blue-500 data-[state=active]:text-slate-100 focus-visible:outline-none focus:outline-none transition"
          >
            {tab.label}
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>
      {tabs.map((tab) => (
        <TabsPrimitive.Content key={tab.value} value={tab.value} className="focus-visible:outline-none focus:outline-none">
          {tab.content}
        </TabsPrimitive.Content>
      ))}
    </TabsPrimitive.Root>
  )
}

// --- REUSABLE CARD ---
export function Card({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-lg ${className}`}>
      {children}
    </div>
  )
}

// --- REUSABLE BADGE ---
export function Badge({ children, variant = "info" }: { children: React.ReactNode; variant?: "success" | "error" | "warning" | "info" }) {
  const styles = {
    success: "bg-green-500/10 text-green-400 border border-green-500/20",
    error: "bg-red-500/10 text-red-400 border border-red-500/20",
    warning: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
    info: "bg-blue-500/10 text-blue-400 border border-blue-500/20"
  }
  return (
    <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${styles[variant]}`}>
      {children}
    </span>
  )
}

// --- REUSABLE SPINNER ---
export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div className={`w-5 h-5 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin ${className}`} />
  )
}

// --- METRIC CARD ---
export function MetricCard({ title, value, change, changeType = "positive" }: { title: string; value: string; change?: string; changeType?: "positive" | "negative" }) {
  return (
    <Card className="flex flex-col justify-between">
      <div>
        <span className="block text-[10px] text-slate-500 font-semibold uppercase mb-1">{title}</span>
        <span className="text-2xl font-extrabold text-slate-100">{value}</span>
      </div>
      {change && (
        <span className={`text-[10px] font-medium mt-3 ${changeType === "positive" ? "text-green-500" : "text-red-500"}`}>
          {change}
        </span>
      )}
    </Card>
  )
}
