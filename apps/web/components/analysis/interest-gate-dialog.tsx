"use client"

import { useEffect } from "react"

import { INTEREST_FEATURES, type InterestFeature } from "@/lib/interest"
import { cn } from "@/lib/utils"

type InterestGateDialogProps = {
  open: boolean
  feature: InterestFeature | null
  onClose: () => void
  onConfirm: () => void
}

export function InterestGateDialog({
  open,
  feature,
  onClose,
  onConfirm,
}: InterestGateDialogProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open || !feature) return null

  const label = INTEREST_FEATURES.find((item) => item.id === feature)?.label ?? "Esta funcionalidade"

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button
        type="button"
        aria-label="Fechar"
        className="absolute inset-0 bg-foreground/20 backdrop-blur-[1px] transition-opacity"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="interest-gate-title"
        className={cn(
          "relative z-10 w-full max-w-md border border-border bg-background animate-fade-up",
          "max-sm:border-x-0"
        )}
      >
        <div className="flex items-baseline justify-between border-b border-border px-5 py-4">
          <h2 id="interest-gate-title" className="font-mono text-xs uppercase tracking-widest">
            Conta
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="font-mono text-xs text-muted-foreground hover:text-foreground"
          >
            esc
          </button>
        </div>
        <div className="space-y-4 px-5 py-5">
          <p className="text-sm leading-relaxed text-muted-foreground">
            {label} está disponível apenas para usuários cadastrados. <br />
            Se tiver interesse, entre em contato conosco.
          </p>
          <button
            type="button"
            onClick={onConfirm}
            className="w-full border border-foreground bg-foreground py-2.5 text-sm text-background"
          >
            Tenho interesse
          </button>
        </div>
      </div>
    </div>
  )
}
