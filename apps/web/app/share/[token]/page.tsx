"use client"

import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { useParams } from "next/navigation"
import { useMemo } from "react"
import ReactMarkdown from "react-markdown"

import { DashboardGrid } from "@/components/analysis/dashboard-grid"
import { DropIcon } from "@/components/drop-icon"
import { resolveBoard, type ChartItem } from "@/lib/dashboard-layout"

type ShareChart = ChartItem

type SharePayload = {
  title: string
  n_rows?: number
  n_cols?: number
  quality_grade?: string
  quality_score?: number
  overview_text?: string
  charts?: ShareChart[]
  dashboard_layout?: { lg?: { i: string; x: number; y: number; w: number; h: number }[] }
}

export default function SharePage() {
  const params = useParams<{ token: string }>()
  const { data, error, isLoading } = useQuery({
    queryKey: ["share", params.token],
    queryFn: async () => {
      const res = await fetch(`/api/share/${params.token}`)
      if (!res.ok) throw new Error("Não encontrado")
      return (await res.json()) as SharePayload
    },
  })

  const board = useMemo(
    () => resolveBoard(data?.charts || [], data?.dashboard_layout, "share"),
    [data?.charts, data?.dashboard_layout]
  )

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <Link
        href="/"
        aria-label="DRO/P"
        className="text-muted-foreground hover:text-foreground"
      >
        <DropIcon />
      </Link>
      {isLoading ? (
        <p className="mt-8 font-mono text-xs text-muted-foreground">
          <span>loading</span>
          <span className="animate-stream-blink">_</span>
        </p>
      ) : null}
      {error ? (
        <p className="mt-8 text-sm text-destructive">Compartilhamento inválido.</p>
      ) : null}
      {data ? (
        <div className="mt-8 space-y-10">
          <header className="space-y-2">
            <h1 className="font-bebas text-4xl tracking-wide">{data.title}</h1>
            <p className="font-mono text-xs text-muted-foreground">
              {data.n_rows} × {data.n_cols} · grade {data.quality_grade || data.quality_score}
            </p>
          </header>

          <section className="border-t border-border pt-6">
            <p className="mb-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              resumo
            </p>
            {data.overview_text ? (
              <div className="prose prose-neutral max-w-none text-sm dark:prose-invert">
                <ReactMarkdown>{data.overview_text}</ReactMarkdown>
              </div>
            ) : (
              <p className="font-mono text-xs text-muted-foreground">
                resumo ainda não disponível
              </p>
            )}
          </section>

          <section className="border-t border-border pt-6">
            <p className="mb-6 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              gráficos
            </p>
            {board.visible.length === 0 ? (
              <p className="font-mono text-xs text-muted-foreground">
                sem gráficos automáticos
              </p>
            ) : (
              <DashboardGrid
                charts={board.visible}
                layout={board.layout}
                editable={false}
              />
            )}
          </section>
        </div>
      ) : null}
    </div>
  )
}
