"use client"

import { useEffect } from "react"

import { cn } from "@/lib/utils"

type SampleDialogProps = {
  open: boolean
  onClose: () => void
  samples: { id: string; title: string; file: string; filename: string }[]
  onSelect: (sample: { id: string; title: string; file: string; filename: string }) => void
  disabled?: boolean
}

export function SampleDialog({ open, onClose, samples, onSelect, disabled }: SampleDialogProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onClose])

  if (!open) return null

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
        aria-labelledby="sample-dialog-title"
        className={cn(
          "relative z-10 w-full max-w-md border border-border bg-background animate-fade-up",
          "max-sm:border-x-0"
        )}
      >
        <div className="flex items-baseline justify-between border-b border-border px-5 py-4">
          <h2 id="sample-dialog-title" className="font-mono text-xs uppercase tracking-widest">
            Samples
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="font-mono text-xs text-muted-foreground hover:text-foreground"
          >
            esc
          </button>
        </div>
        <ul className="divide-y divide-border">
          {samples.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onSelect(s)}
                className="flex w-full items-center justify-between px-5 py-4 text-left text-sm transition-colors hover:bg-muted/40 disabled:opacity-50"
              >
                <span>{s.title}</span>
                <span className="font-mono text-xs text-muted-foreground">run →</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
