"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"

type Props = {
  analysisId: string
  title: string
}

export function DeleteAnalysisButton({ analysisId, title }: Props) {
  const qc = useQueryClient()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const remove = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/analyses/${analysisId}`, { method: "DELETE" })
      if (res.status === 204 || res.ok) return
      const body = await res.json().catch(() => ({}))
      throw new Error(body.message || "Falha ao excluir.")
    },
    onSuccess: () => {
      setOpen(false)
      void qc.invalidateQueries({ queryKey: ["analyses"] })
      void qc.removeQueries({ queryKey: ["analysis", analysisId] })
      router.replace("/analyses")
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const pending = remove.isPending

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !pending) setOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, pending])

  function close() {
    if (pending) return
    setOpen(false)
    setError(null)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setError(null)
          setOpen(true)
        }}
        className="inline-flex items-center text-muted-foreground transition-colors hover:text-foreground"
        aria-label="Excluir análise"
        title="Excluir"
      >
        <Trash2 className="size-3" strokeWidth={1.5} />
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
          <button
            type="button"
            aria-label="Fechar"
            disabled={pending}
            className="absolute inset-0 bg-foreground/20 backdrop-blur-[1px] transition-opacity"
            onClick={close}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-analysis-title"
            className={cn(
              "relative z-10 w-full max-w-sm border border-border bg-background animate-fade-up",
              "max-sm:border-x-0"
            )}
          >
            <div className="flex items-baseline justify-between border-b border-border px-5 py-4">
              <h2
                id="delete-analysis-title"
                className="font-mono text-xs uppercase tracking-widest"
              >
                Excluir análise
              </h2>
              <button
                type="button"
                onClick={close}
                disabled={pending}
                className="font-mono text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
              >
                esc
              </button>
            </div>
            <div className="px-5 py-5">
              <p className="text-sm text-muted-foreground">
                Excluir{" "}
                <span className="text-foreground">{title || "esta análise"}</span>? Essa ação não
                pode ser desfeita.
              </p>
              {error ? (
                <p className="mt-3 font-mono text-[11px] text-red-700" role="alert">
                  {error}
                </p>
              ) : null}
              <div className="mt-5 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={close}
                  disabled={pending}
                  className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
                >
                  cancelar
                </button>
                <button
                  type="button"
                  disabled={pending}
                  onClick={() => remove.mutate()}
                  className="bg-red-700 px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-white transition-opacity hover:opacity-90 disabled:opacity-50"
                >
                  {pending ? "excluindo…" : "excluir"}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}
