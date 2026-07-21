"use client"

import React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { CheckCircle2, AlertTriangle, AlertCircle, X } from "lucide-react"
import { Button, Spinner } from "./components"

interface CommonDialogProps {
  isOpen: boolean
  onClose: () => void
  title: string
  message: string
}

export function SuccessDialog({ isOpen, title, message, onClose }: CommonDialogProps) {
  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs" />
        <DialogPrimitive.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-sm translate-x-[-50%] translate-y-[-50%] bg-slate-900 border border-slate-800 p-6 rounded-lg shadow-xl text-center space-y-4 text-slate-100 focus-visible:outline-none focus:outline-none">
          <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto" />
          <DialogPrimitive.Title className="font-bold text-sm">{title}</DialogPrimitive.Title>
          <DialogPrimitive.Description className="text-[10px] text-slate-400 leading-relaxed">
            {message}
          </DialogPrimitive.Description>
          <Button onClick={onClose} variant="primary" size="sm" className="w-full">
            Dismiss
          </Button>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

export function ErrorDialog({ isOpen, title, message, onClose }: CommonDialogProps) {
  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs" />
        <DialogPrimitive.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-sm translate-x-[-50%] translate-y-[-50%] bg-slate-900 border border-slate-800 p-6 rounded-lg shadow-xl text-center space-y-4 text-slate-100 focus-visible:outline-none focus:outline-none">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
          <DialogPrimitive.Title className="font-bold text-sm">{title}</DialogPrimitive.Title>
          <DialogPrimitive.Description className="text-[10px] text-slate-400 leading-relaxed">
            {message}
          </DialogPrimitive.Description>
          <Button onClick={onClose} variant="danger" size="sm" className="w-full">
            Dismiss
          </Button>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

export function ConfirmationDialog({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm",
  onConfirm,
  onCancel
}: {
  isOpen: boolean
  title: string
  message: string
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
}) {
  return (
    <DialogPrimitive.Root open={isOpen} onOpenChange={(open) => !open && onCancel()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs" />
        <DialogPrimitive.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-sm translate-x-[-50%] translate-y-[-50%] bg-slate-900 border border-slate-800 p-6 rounded-lg shadow-xl space-y-5 text-slate-100 focus-visible:outline-none focus:outline-none">
          <div className="flex gap-3">
            <AlertTriangle className="w-8 h-8 text-yellow-500 flex-shrink-0" />
            <div>
              <DialogPrimitive.Title className="font-bold text-xs">{title}</DialogPrimitive.Title>
              <DialogPrimitive.Description className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                {message}
              </DialogPrimitive.Description>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button onClick={onCancel} variant="secondary" size="sm">
              Cancel
            </Button>
            <Button onClick={onConfirm} variant="primary" size="sm">
              {confirmLabel}
            </Button>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

export function LoadingDialog({ isOpen, message = "Processing task..." }: { isOpen: boolean; message?: string }) {
  return (
    <DialogPrimitive.Root open={isOpen}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs" />
        <DialogPrimitive.Content className="fixed left-[50%] top-[50%] z-50 w-fit translate-x-[-50%] translate-y-[-50%] bg-slate-900 border border-slate-800 p-6 rounded-lg shadow-xl text-center space-y-4 min-w-[200px] text-slate-100 focus-visible:outline-none focus:outline-none">
          <Spinner className="mx-auto w-8 h-8" />
          <DialogPrimitive.Title className="text-[10px] text-slate-350 font-medium">{message}</DialogPrimitive.Title>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
