"use client"

import React from "react"
import { BarChart3, LineChart, PieChart, Activity } from "lucide-react"

interface ChartCardProps {
  title: string
  chartType: "Bar" | "Line" | "Area" | "Pie" | "Donut" | "Gauge" | "Heatmap"
}

export function ChartCard({ title, chartType }: ChartCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 flex flex-col justify-between h-[300px] text-slate-100 shadow">
      <div className="flex justify-between items-center border-b border-slate-850 pb-2 mb-4">
        <h4 className="font-semibold text-xs text-slate-350">{title}</h4>
        <span className="px-2 py-0.5 rounded text-[8px] bg-blue-500/10 text-blue-400 font-semibold uppercase tracking-wider">
          {chartType}
        </span>
      </div>

      <div className="flex-1 flex flex-col justify-center items-center bg-slate-950/40 rounded border border-slate-850/50 p-4">
        {chartType === "Bar" && <BarChart3 className="w-8 h-8 text-slate-700 animate-pulse" />}
        {chartType === "Line" && <LineChart className="w-8 h-8 text-slate-700 animate-pulse" />}
        {chartType === "Area" && <Activity className="w-8 h-8 text-slate-700 animate-pulse" />}
        {chartType === "Pie" && <PieChart className="w-8 h-8 text-slate-700 animate-pulse" />}
        {chartType === "Donut" && <PieChart className="w-8 h-8 text-slate-700 animate-pulse" />}
        {chartType === "Gauge" && <Activity className="w-8 h-8 text-slate-700 animate-pulse" />}
        {chartType === "Heatmap" && <BarChart3 className="w-8 h-8 text-slate-700 animate-pulse" />}

        <span className="text-[10px] text-slate-500 font-medium mt-3 uppercase tracking-widest">
          Chart Visual Canvas
        </span>
      </div>
    </div>
  )
}
