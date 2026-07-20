"use client"

import React, { useState, useEffect } from "react"
import { X } from "lucide-react"
import axios from "axios"

interface WidgetEditorProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: any) => void
  widget?: any // Undefined if creating new
  workspaceId: string
}

export default function WidgetEditor({ isOpen, onClose, onSave, widget, workspaceId }: WidgetEditorProps) {
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState("")
  const [columns, setColumns] = useState<string[]>([])
  
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [widgetType, setWidgetType] = useState("Line Chart")
  const [xAxisCol, setXAxisCol] = useState("")
  const [yAxisCol, setYAxisCol] = useState("")
  const [aggregation, setAggregation] = useState("")
  const [colorTheme, setColorTheme] = useState("#3b82f6")
  const [refreshInterval, setRefreshInterval] = useState(30)

  // Fetch workspaces datasets
  useEffect(() => {
    if (!isOpen) return
    const fetchDatasets = async () => {
      try {
        const token = localStorage.getItem("token")
        const res = await axios.get(`/api/v1/datasets`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-ID": workspaceId
          }
        })
        setDatasets(res.data)
        
        // Pre-fill fields if editing
        if (widget) {
          setTitle(widget.title)
          setDescription(widget.description || "")
          setWidgetType(widget.widget_type)
          setSelectedDatasetId(widget.dataset_id)
          setXAxisCol(widget.x_axis_column || "")
          setYAxisCol(widget.y_axis_column || "")
          setAggregation(widget.aggregation || "")
          setColorTheme(widget.color_theme || "#3b82f6")
          setRefreshInterval(widget.refresh_interval || 30)
        }
      } catch (err) {
        logger.error("Failed to load dataset list inside editor")
      }
    }
    fetchDatasets()
  }, [isOpen, widget])

  // Fetch columns schemas when dataset selection updates
  useEffect(() => {
    if (!selectedDatasetId) return
    const fetchColumns = async () => {
      try {
        const token = localStorage.getItem("token")
        const res = await axios.get(`/api/v1/datasets/${selectedDatasetId}/metadata`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-ID": workspaceId
          }
        })
        if (res.data?.schema_json) {
          setColumns(Object.keys(res.data.schema_json))
        }
      } catch (err) {
        setColumns([])
      }
    }
    fetchColumns()
  }, [selectedDatasetId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave({
      dataset_id: selectedDatasetId,
      dataset_version: 1,
      title,
      description,
      widget_type: widgetType,
      x_axis_column: xAxisCol || null,
      y_axis_column: yAxisCol || null,
      aggregation: aggregation || null,
      color_theme: colorTheme,
      refresh_interval: Number(refreshInterval) || null
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 flex flex-col h-full overflow-y-auto text-slate-100">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
          <h3 className="font-bold text-lg text-blue-500">
            {widget ? "Configure Chart Widget" : "Add Layout Widget"}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 space-y-6">
          <div>
            <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Widget Title</label>
            <input 
              type="text" 
              value={title} 
              onChange={e => setTitle(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Description</label>
            <textarea 
              value={description} 
              onChange={e => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Visualization Type</label>
            <select 
              value={widgetType} 
              onChange={e => setWidgetType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
            >
              <option value="KPI Card">KPI Card</option>
              <option value="Line Chart">Line Chart</option>
              <option value="Bar Chart">Bar Chart</option>
              <option value="Pie Chart">Pie Chart</option>
              <option value="Donut Chart">Donut Chart</option>
              <option value="Area Chart">Area Chart</option>
              <option value="Gauge">Gauge Chart</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Source Dataset</label>
            <select 
              value={selectedDatasetId} 
              onChange={e => setSelectedDatasetId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
              required
            >
              <option value="">Select Ingested File...</option>
              {datasets.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          {columns.length > 0 && (
            <>
              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">X-Axis Column (Categories)</label>
                <select 
                  value={xAxisCol} 
                  onChange={e => setXAxisCol(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
                >
                  <option value="">None</option>
                  {columns.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Y-Axis Column (Numerical Series)</label>
                <select 
                  value={yAxisCol} 
                  onChange={e => setYAxisCol(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
                >
                  <option value="">None</option>
                  {columns.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Aggregation Operator</label>
                <select 
                  value={aggregation} 
                  onChange={e => setAggregation(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-600"
                >
                  <option value="">None (Raw Rows)</option>
                  <option value="COUNT">COUNT</option>
                  <option value="SUM">SUM</option>
                  <option value="AVG">AVERAGE</option>
                  <option value="MIN">MIN</option>
                  <option value="MAX">MAX</option>
                </select>
              </div>
            </>
          )}

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Theme Color</label>
              <input 
                type="color" 
                value={colorTheme} 
                onChange={e => setColorTheme(e.target.value)}
                className="w-full h-10 bg-transparent border-0 cursor-pointer"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-slate-400 font-semibold mb-2 uppercase">Auto-Refresh (s)</label>
              <input 
                type="number" 
                value={refreshInterval} 
                onChange={e => setRefreshInterval(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 p-2.5 rounded text-sm text-slate-100 focus:outline-none"
                min={10}
              />
            </div>
          </div>

          <div className="flex gap-4 pt-6 border-t border-slate-800">
            <button 
              type="button" 
              onClick={onClose}
              className="flex-1 py-2.5 text-center bg-slate-800 hover:bg-slate-700 text-white rounded text-sm font-medium border border-slate-700 transition"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="flex-1 py-2.5 text-center bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition"
            >
              Save Widget
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const logger = {
  error: (msg: string) => console.error(`[WidgetEditor] ${msg}`)
}
