"use client"

import React, { createContext, useContext, useState, useCallback } from "react"
import { AlertTriangle, Trash2, CheckCircle2, ShieldAlert } from "lucide-react"

type ModalType = "confirm" | "delete" | "success" | "error" | "loading" | null

interface ModalOptions {
  title: string
  message: string
  onConfirm?: () => void | Promise<void>
  confirmLabel?: string
  cancelLabel?: string
}

interface ModalContextType {
  openModal: (type: ModalType, options: ModalOptions) => void
  closeModal: () => void
  loadingState: boolean
}

const ModalContext = createContext<ModalContextType | undefined>(undefined)

export function ModalProvider({ children }: { children: React.ReactNode }) {
  const [modalType, setModalType] = useState<ModalType>(null)
  const [options, setOptions] = useState<ModalOptions | null>(null)
  const [loadingState, setLoadingState] = useState(false)

  const openModal = useCallback((type: ModalType, opts: ModalOptions) => {
    setModalType(type)
    setOptions(opts)
  }, [])

  const closeModal = useCallback(() => {
    setModalType(null)
    setOptions(null)
    setLoadingState(false)
  }, [])

  const handleConfirm = async () => {
    if (options?.onConfirm) {
      setLoadingState(true)
      try {
        await options.onConfirm()
      } catch (err) {
        console.error(err)
      } finally {
        closeModal()
      }
    } else {
      closeModal()
    }
  }

  return (
    <ModalContext.Provider value={{ openModal, closeModal, loadingState }}>
      {children}
      {modalType && options && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg shadow-xl w-full max-w-md p-6 text-slate-100 space-y-6">
            <div className="flex items-start gap-4">
              {modalType === "delete" && (
                <div className="p-3 bg-red-500/10 text-red-500 rounded-full">
                  <Trash2 className="w-6 h-6" />
                </div>
              )}
              {modalType === "confirm" && (
                <div className="p-3 bg-yellow-500/10 text-yellow-500 rounded-full">
                  <AlertTriangle className="w-6 h-6" />
                </div>
              )}
              {modalType === "success" && (
                <div className="p-3 bg-green-500/10 text-green-500 rounded-full">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              )}
              {modalType === "error" && (
                <div className="p-3 bg-red-500/10 text-red-500 rounded-full">
                  <ShieldAlert className="w-6 h-6" />
                </div>
              )}

              <div className="flex-1">
                <h3 className="text-sm font-bold text-slate-200">{options.title}</h3>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">{options.message}</p>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                onClick={closeModal}
                disabled={loadingState}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded transition"
              >
                {options.cancelLabel || "Cancel"}
              </button>
              {(modalType === "confirm" || modalType === "delete") && (
                <button
                  onClick={handleConfirm}
                  disabled={loadingState}
                  className={`px-4 py-2 text-white text-xs font-semibold rounded transition ${
                    modalType === "delete" ? "bg-red-600 hover:bg-red-700" : "bg-blue-600 hover:bg-blue-700"
                  }`}
                >
                  {loadingState ? "Processing..." : options.confirmLabel || "Confirm"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </ModalContext.Provider>
  )
}

export function useModals() {
  const context = useContext(ModalContext)
  if (!context) {
    throw new Error("useModals must be executed within a ModalProvider wrapper.")
  }
  return context
}
