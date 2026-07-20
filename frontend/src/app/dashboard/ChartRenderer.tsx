"use client"

import React, { useEffect, useRef, useState } from "react"
import * as echarts from "echarts"
import { Maximize2, Minimize2, Download, RefreshCw } from "lucide-react"

interface Widget {
  id: string
  title: string
  description?: string
  widget_type: string
  x_axis_column?: string
  y_axis_column?: string
  aggregation?: string
  color_theme?: string
  refresh_interval?: number
}

interface ChartRendererProps {
  widget: Widget
  previewData?: any
  theme?: "dark" | "light"
}

export default function ChartRenderer({ widget, previewData, theme = "dark" }: ChartRendererProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [chartInstance, setChartInstance] = useState<echarts.ECharts | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Generate options based on chart type and datasets previewData
  const getChartOption = (): echarts.EChartsOption => {
    // Fallback/Sample data if previewData is unavailable
    const xData = previewData?.columns && widget.x_axis_column 
      ? previewData.preview_data.map((row: any) => row[widget.x_axis_column!])
      : ["Category A", "Category B", "Category C", "Category D", "Category E"]
      
    const yData = previewData?.columns && widget.y_axis_column
      ? previewData.preview_data.map((row: any) => Number(row[widget.y_axis_column!]) || 0)
      : [320, 450, 280, 610, 520]

    const textStyle = {
      color: theme === "dark" ? "#94a3b8" : "#475569"
    }

    const baseOptions: echarts.EChartsOption = {
      backgroundColor: "transparent",
      textStyle,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" }
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "3%",
        containLabel: true
      }
    }

    switch (widget.widget_type) {
      case "KPI Card":
        return {} // Handled visually by parent
        
      case "Line Chart":
      case "Area Chart":
        return {
          ...baseOptions,
          xAxis: {
            type: "category",
            data: xData,
            axisLabel: textStyle
          },
          yAxis: {
            type: "value",
            splitLine: { lineStyle: { color: theme === "dark" ? "#1e293b" : "#e2e8f0" } }
          },
          series: [
            {
              data: yData,
              type: "line",
              smooth: true,
              color: widget.color_theme || "#3b82f6",
              areaStyle: widget.widget_type === "Area Chart" ? { opacity: 0.2 } : undefined
            }
          ]
        }

      case "Bar Chart":
      case "Histogram":
        return {
          ...baseOptions,
          xAxis: {
            type: "category",
            data: xData,
            axisLabel: textStyle
          },
          yAxis: {
            type: "value",
            splitLine: { lineStyle: { color: theme === "dark" ? "#1e293b" : "#e2e8f0" } }
          },
          series: [
            {
              data: yData,
              type: "bar",
              color: widget.color_theme || "#3b82f6",
              barMaxWidth: 40
            }
          ]
        }

      case "Pie Chart":
      case "Donut Chart":
        const pieData = xData.map((lbl: string, idx: number) => ({
          value: yData[idx] || 0,
          name: String(lbl)
        }))
        return {
          ...baseOptions,
          tooltip: { trigger: "item" },
          series: [
            {
              name: widget.title,
              type: "pie",
              radius: widget.widget_type === "Donut Chart" ? ["40%", "70%"] : "70%",
              avoidLabelOverlap: false,
              itemStyle: {
                borderRadius: 6,
                borderColor: theme === "dark" ? "#0f172a" : "#fff",
                borderWidth: 2
              },
              label: {
                show: true,
                color: theme === "dark" ? "#94a3b8" : "#475569"
              },
              data: pieData
            }
          ]
        }

      case "Gauge":
        return {
          ...baseOptions,
          series: [
            {
              type: "gauge",
              progress: { show: true, width: 8 },
              axisLine: { lineStyle: { width: 8 } },
              axisTick: { show: false },
              splitLine: { length: 12, lineStyle: { width: 2, color: "#999" } },
              detail: {
                valueAnimation: true,
                formatter: "{value}%",
                color: theme === "dark" ? "#fff" : "#000",
                fontSize: 20
              },
              data: [{ value: yData[0] || 75, name: widget.x_axis_column || "Completion" }]
            }
          ]
        }

      default:
        // Default Line chart fallback option
        return {
          ...baseOptions,
          xAxis: { type: "category", data: xData },
          yAxis: { type: "value" },
          series: [{ data: yData, type: "line" }]
        }
    }
  }

  useEffect(() => {
    if (!chartRef.current) return

    const option = getChartOption()
    
    // Dispose previous instance to avoid cache
    if (chartInstance) {
      chartInstance.dispose()
    }

    const chart = echarts.init(chartRef.current)
    chart.setOption(option)
    setChartInstance(chart)

    const handleResize = () => {
      chart.resize()
    }
    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
      chart.dispose()
    }
  }, [widget, previewData, theme, isFullscreen])

  // Handles PNG exports
  const exportToPNG = () => {
    if (!chartInstance) return
    const url = chartInstance.getDataURL({
      type: "png",
      pixelRatio: 2,
      backgroundColor: theme === "dark" ? "#0f172a" : "#ffffff"
    })
    const link = document.createElement("a")
    link.download = `${widget.title.replace(/\s+/g, "_")}.png`
    link.href = url
    link.click()
  }

  // Toggle fullscreen canvas
  const toggleFullscreen = () => {
    if (!containerRef.current) return
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true))
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false))
    }
  }

  return (
    <div 
      ref={containerRef}
      className={`relative w-full h-full flex flex-col p-4 bg-slate-900 border border-slate-800 rounded-lg shadow-lg ${
        isFullscreen ? "bg-slate-950 p-8" : ""
      }`}
    >
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-2">
        <div>
          <h4 className="font-semibold text-slate-100 text-sm">{widget.title}</h4>
          {widget.description && (
            <p className="text-slate-400 text-xs">{widget.description}</p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={exportToPNG}
            className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition"
            title="Export PNG"
          >
            <Download className="w-4 h-4" />
          </button>
          <button 
            onClick={toggleFullscreen}
            className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition"
            title="Fullscreen Mode"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {widget.widget_type === "KPI Card" ? (
        <div className="flex-1 flex flex-col justify-center items-center">
          <span className="text-4xl font-extrabold text-blue-500">
            {previewData?.preview_data?.[0]?.[widget.y_axis_column!] || "$1,240,000"}
          </span>
          <span className="text-slate-400 text-xs mt-2 uppercase tracking-wider font-semibold">
            {widget.y_axis_column || "KPI metric"}
          </span>
        </div>
      ) : (
        <div ref={chartRef} className="flex-1 w-full min-h-[220px]" />
      )}
    </div>
  )
}
