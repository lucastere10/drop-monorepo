"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"

export default function AnalysesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["analyses"],
    queryFn: async () => {
      const res = await fetch("/api/analyses")
      if (!res.ok) throw new Error("Falha ao listar")
      return res.json()
    },
  })

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <div className="flex items-end justify-between gap-4">
        <h1 className="font-bebas text-4xl tracking-wide">Análises</h1>
        <Link
          href="/dashboard"
          className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
        >
          nova
        </Link>
      </div>
      <div className="mt-8 divide-y divide-border border-y border-border">
        {isLoading ? (
          <p className="py-6 font-mono text-xs text-muted-foreground">carregando…</p>
        ) : null}
        {(data || []).map(
          (a: {
            id: string
            title: string
            n_rows: number
            n_cols: number
            quality_grade?: string
          }) => (
            <Link
              key={a.id}
              href={`/analyses/${a.id}`}
              className="flex items-center justify-between py-4 transition-colors hover:bg-muted/30"
            >
              <span className="text-sm">{a.title}</span>
              <span className="font-mono text-[11px] text-muted-foreground">
                {a.quality_grade || "—"} · {a.n_rows}×{a.n_cols}
              </span>
            </Link>
          )
        )}
        {!isLoading && (!data || data.length === 0) ? (
          <p className="py-6 font-mono text-xs text-muted-foreground">
            vazio · envie um arquivo no dashboard
          </p>
        ) : null}
      </div>
    </div>
  )
}
