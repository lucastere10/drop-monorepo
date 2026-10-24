"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Check, Copy, Globe, Lock } from "lucide-react"
import { useState } from "react"

import { cn } from "@/lib/utils"

type Props = {
  analysisId: string
  isPublic: boolean
  shareToken?: string
}

export function ShareControls({ analysisId, isPublic, shareToken }: Props) {
  const qc = useQueryClient()
  const [copied, setCopied] = useState(false)

  const toggle = useMutation({
    mutationFn: async (next: boolean) => {
      const res = await fetch(`/api/analyses/${analysisId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_public: next }),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(body.message || "Falha ao atualizar o compartilhamento.")
      return body as { is_public?: boolean; share_token?: string }
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["analysis", analysisId] })
    },
  })

  const publicNow = toggle.data?.is_public ?? isPublic
  const token = toggle.data?.share_token || shareToken
  const canCopy = publicNow && Boolean(token)
  const statusLabel = publicNow ? "público" : "privado"

  async function copyLink() {
    if (!token) return
    const url = `${window.location.origin}/share/${token}`
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        disabled={toggle.isPending}
        onClick={() => toggle.mutate(!publicNow)}
        className={cn(
          "inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest transition-colors disabled:opacity-50",
          publicNow
            ? "text-foreground hover:opacity-70"
            : "text-muted-foreground hover:text-foreground"
        )}
        aria-pressed={publicNow}
        aria-label={publicNow ? "Tornar privado" : "Tornar público"}
      >
        {publicNow ? (
          <Globe className="size-3" strokeWidth={1.5} />
        ) : (
          <Lock className="size-3" strokeWidth={1.5} />
        )}
        {toggle.isPending ? "…" : statusLabel}
      </button>
      {canCopy ? (
        <button
          type="button"
          onClick={() => void copyLink()}
          className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground transition-colors hover:text-foreground"
          aria-label="Copiar link público"
        >
          {copied ? (
            <Check className="size-3" strokeWidth={1.5} />
          ) : (
            <Copy className="size-3" strokeWidth={1.5} />
          )}
          {copied ? "copiado" : "copiar"}
        </button>
      ) : null}
    </div>
  )
}
