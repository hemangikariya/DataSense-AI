"use client"

import React, { useState } from "react"
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  VisibilityState
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronLeft, ChevronRight, Search } from "lucide-react"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchKey?: string
  loading?: boolean
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchKey,
  loading = false
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState("")
  const [rowSelection, setRowSelection] = useState({})
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      globalFilter,
      rowSelection,
      columnVisibility
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: setRowSelection,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      pagination: {
        pageSize: 5
      }
    }
  })

  return (
    <div className="space-y-4 text-slate-100 bg-slate-900 border border-slate-800 rounded-lg p-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        {/* Global Search */}
        {searchKey && (
          <div className="flex items-center bg-slate-950 border border-slate-800 px-3 py-2 rounded text-xs gap-2 max-w-sm w-full">
            <Search className="w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              placeholder="Search matching entries..."
              className="bg-transparent border-0 outline-none w-full text-slate-200"
              aria-label="Search entries"
            />
          </div>
        )}

        {/* Column Visibility Selector */}
        <div className="flex gap-2">
          {table.getAllLeafColumns().map((column) => {
            if (column.id === "select") return null
            return (
              <label key={column.id} className="inline-flex items-center gap-1.5 text-[10px] text-slate-400 font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={column.getIsVisible()}
                  onChange={(e) => column.toggleVisibility(!!e.target.checked)}
                  className="rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-0 w-3 h-3"
                />
                <span className="uppercase">{column.id}</span>
              </label>
            )
          })}
        </div>
      </div>

      <div className="overflow-x-auto border border-slate-850 rounded">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="p-3">
                    {header.isPlaceholder ? null : (
                      <div
                        onClick={header.column.getCanSort() ? header.column.getToggleSortingHandler() : undefined}
                        className={`flex items-center gap-1.5 select-none ${
                          header.column.getCanSort() ? "cursor-pointer hover:text-slate-200" : ""
                        }`}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && <ArrowUpDown className="w-3.5 h-3.5" />}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>

          <tbody>
            {loading ? (
              [1, 2, 3].map((i) => (
                <tr key={i} className="border-b border-slate-850 animate-pulse bg-slate-900/20">
                  {columns.map((_, colIdx) => (
                    <td key={colIdx} className="p-3">
                      <div className="h-4 bg-slate-800 rounded w-2/3" />
                    </td>
                  ))}
                </tr>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="p-8 text-center text-slate-500 font-medium">
                  No records matching target fields found.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-850 hover:bg-slate-850/20 transition">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-3 text-slate-300 font-medium">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination controls */}
      <div className="flex items-center justify-between border-t border-slate-850 pt-4 text-[10px] text-slate-400">
        <span>
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 border border-slate-800 rounded transition"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="p-1 hover:bg-slate-800 disabled:opacity-30 border border-slate-800 rounded transition"
            aria-label="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
