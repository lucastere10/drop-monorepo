"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { useMemo, useState, type ReactNode } from "react"
import {
  ArrowRight,
  Check,
  Columns3,
  FileSpreadsheet,
  Layers,
  Sparkles,
  Upload,
} from "lucide-react"

import { CreditsAlert } from "@/components/credits-alert"
import { isCreditsNotice } from "@/lib/credits"
import { extractDecisionBullets, parseOverviewSections } from "@/lib/overview"
import { cn } from "@/lib/utils"

type AnalysisListItem = {
  id: string
  title: string
  n_rows: number
  n_cols: number
  quality_grade?: string
}

function collectFindings(overviewText?: string): string[] {
  if (!overviewText) return []
  const sections = parseOverviewSections(overviewText)
  const out: string[] = []
  for (const id of ["positives", "explore", "decisions"] as const) {
    const s = sections.find((x) => x.id === id)
    if (!s?.body) continue
    for (const b of extractDecisionBullets(s.body, 2)) {
      out.push(b.replace(/\?$/, ""))
      if (out.length >= 4) return out
    }
  }
  return out
}

function SectionLabel({
  children,
  action,
}: {
  children: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        {children}
      </p>
      {action}
    </div>
  )
}

export default function DashboardPage() {
  const router = useRouter()
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState("")
  const [uploading, setUploading] = useState(false)

  const analyses = useQuery({
    queryKey: ["analyses"],
    queryFn: async () => {
      const res = await fetch("/api/analyses")
      if (!res.ok) throw new Error("Falha ao listar")
      return (await res.json()) as AnalysisListItem[]
    },
  })

  const latestId = analyses.data?.[0]?.id

  const latestDetail = useQuery({
    queryKey: ["analysis", latestId, "findings"],
    enabled: Boolean(latestId),
    queryFn: async () => {
      const res = await fetch(`/api/analyses/${latestId}`)
      if (!res.ok) return null
      return res.json() as Promise<{ overview_text?: string; title?: string }>
    },
  })

  const findings = useMemo(
    () => collectFindings(latestDetail.data?.overview_text),
    [latestDetail.data?.overview_text]
  )

  async function upload(file: File) {
    setUploading(true)
    setError("")
    try {
      const form = new FormData()
      form.append("file", file)
      const res = await fetch("/api/analyses", { method: "POST", body: form })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.message || "Falha no upload.")
      }
      const data = await res.json()
      router.push(`/analyses/${data.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha no upload.")
      setUploading(false)
    }
  }

  const recent = analyses.data || []
  const continueItem = recent[0]
  const totalRows = recent.reduce((acc, a) => acc + (a.n_rows || 0), 0)
  const totalCols = recent.reduce((acc, a) => acc + (a.n_cols || 0), 0)

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-bebas text-4xl tracking-wide sm:text-5xl">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">Próximo passo · contexto · histórico</p>
        </div>
        <div className="flex items-center gap-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <Layers className="size-3.5" strokeWidth={1.5} />
            {recent.length}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <FileSpreadsheet className="size-3.5" strokeWidth={1.5} />
            {totalRows.toLocaleString("pt-BR")}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Columns3 className="size-3.5" strokeWidth={1.5} />
            {totalCols}
          </span>
        </div>
      </header>

      <div className="mt-8 grid gap-10 lg:grid-cols-12 lg:gap-12">
        <section className="lg:col-span-5">
          <SectionLabel>nova</SectionLabel>
          <label
            className={cn(
              "flex min-h-[10rem] cursor-pointer flex-col items-center justify-center gap-3 border border-dashed px-5 py-8 transition-colors",
              dragging
                ? "border-foreground bg-muted/40"
                : "border-border hover:border-foreground/45 hover:bg-muted/20",
              uploading && "pointer-events-none opacity-60"
            )}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              const f = e.dataTransfer.files?.[0]
              if (f) void upload(f)
            }}
          >
            <Upload className="size-6 text-foreground" strokeWidth={1.4} />
            <span className="text-center text-sm text-muted-foreground">
              {uploading ? "Enviando…" : "CSV · XLSX · JSON"}
            </span>
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.json,text/csv,application/json"
              className="sr-only"
              disabled={uploading}
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) void upload(f)
              }}
            />
          </label>
          {error ? (
            isCreditsNotice(error) ? (
              <CreditsAlert className="mt-2">{error}</CreditsAlert>
            ) : (
              <p className="mt-2 text-sm text-destructive">{error}</p>
            )
          ) : null}
        </section>

        <section className="lg:col-span-7">
          {continueItem ? (
            <>
              <SectionLabel>continuar</SectionLabel>
              <Link
                href={`/analyses/${continueItem.id}`}
                className="group flex items-center gap-3 border-y border-border py-3.5 transition-colors hover:bg-muted/30"
              >
                <Sparkles className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.5} />
                <span className="min-w-0 flex-1 truncate text-sm font-medium">
                  {continueItem.title}
                </span>
                <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
                  {continueItem.quality_grade || "—"} · {continueItem.n_rows}×{continueItem.n_cols}
                </span>
                <ArrowRight
                  className="size-3.5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-foreground"
                  strokeWidth={1.5}
                />
              </Link>
            </>
          ) : (
            <div className="flex h-full min-h-[8rem] items-center">
              <p className="font-mono text-xs text-muted-foreground">
                {analyses.isLoading ? "…" : "Nada para continuar ainda."}
              </p>
            </div>
          )}
        </section>
      </div>

      <section className="mt-10">
        <SectionLabel>
          <span className="inline-flex items-center gap-1.5">
            <Check className="size-3" strokeWidth={2} />
            achados
          </span>
        </SectionLabel>
        {findings.length > 0 ? (
          <>
            <ul className="space-y-2.5">
              {findings.map((f) => (
                <li key={f} className="flex items-start gap-2.5 text-sm leading-snug">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-foreground/60" />
                  <span className="line-clamp-2 text-foreground/90">{f}</span>
                </li>
              ))}
            </ul>
            {continueItem ? (
              <p className="mt-3 truncate font-mono text-[10px] text-muted-foreground">
                ← {latestDetail.data?.title || continueItem.title}
              </p>
            ) : null}
          </>
        ) : (
          <p className="font-mono text-xs text-muted-foreground">
            {analyses.isLoading ? "…" : "Achados aparecem após a primeira análise."}
          </p>
        )}
      </section>

      <section className="mt-10">
        <SectionLabel
          action={
            <Link
              href="/analyses"
              className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
            >
              todas
              <ArrowRight className="size-3" strokeWidth={1.5} />
            </Link>
          }
        >
          recentes
        </SectionLabel>
        <div className="divide-y divide-border border-y border-border">
          {analyses.isLoading ? (
            <p className="py-3.5 font-mono text-xs text-muted-foreground">carregando…</p>
          ) : null}
          {recent.slice(0, 6).map((a) => (
            <Link
              key={a.id}
              href={`/analyses/${a.id}`}
              className="flex items-center justify-between gap-4 py-3 transition-colors hover:bg-muted/30"
            >
              <span className="min-w-0 truncate text-sm">{a.title}</span>
              <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
                {a.quality_grade || "—"} · {a.n_rows}×{a.n_cols}
              </span>
            </Link>
          ))}
          {!analyses.isLoading && recent.length === 0 ? (
            <p className="py-3.5 font-mono text-xs text-muted-foreground">
              Nenhuma análise — envie um arquivo acima.
            </p>
          ) : null}
        </div>
      </section>
    </div>
  )
}
