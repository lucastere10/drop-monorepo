"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, Coins, Shield } from "lucide-react"

export default function PlanPage() {
  const { data: me } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const res = await fetch("/api/me")
      if (!res.ok) throw new Error("auth")
      return res.json()
    },
  })
  const credits = useQuery({
    queryKey: ["credits"],
    queryFn: async () => {
      const res = await fetch("/api/credits")
      if (!res.ok) return null
      return res.json()
    },
  })

  const tier = credits.data?.tier?.slug || me?.tier || "—"
  const balance = credits.data?.balance ?? me?.credits_balance ?? "—"

  return (
    <div className="mx-auto max-w-lg px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="p-1.5 text-muted-foreground hover:text-foreground"
          aria-label="Voltar"
        >
          <ArrowLeft className="size-4" strokeWidth={1.5} />
        </Link>
        <h1 className="font-bebas text-4xl tracking-wide">Plano</h1>
      </div>

      <dl className="mt-8 divide-y divide-border border-y border-border">
        <div className="flex items-center gap-3 py-3.5">
          <Shield className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.5} />
          <dt className="w-16 shrink-0 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            tier
          </dt>
          <dd className="min-w-0 flex-1 truncate text-right text-sm">{tier}</dd>
        </div>
        <div className="flex items-center gap-3 py-3.5">
          <Coins className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.5} />
          <dt className="w-16 shrink-0 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            saldo
          </dt>
          <dd className="min-w-0 flex-1 truncate text-right text-sm">{balance}</dd>
        </div>
      </dl>

      <p className="mt-4 text-sm text-muted-foreground">
        Billing ainda não está no escopo do v1 — o uso é medido em créditos.
      </p>
    </div>
  )
}
