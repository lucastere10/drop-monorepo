"use client"

import { useCallback, useState } from "react"
import ReactMarkdown from "react-markdown"

import { ChartRenderer } from "@/components/analysis/chart-renderer"
import { TypewriterText } from "@/components/analysis/typewriter-text"
import type { ChartItem } from "@/lib/dashboard-layout"
import { Skeleton } from "@/components/ui/skeleton"
import {
  extractBullets,
  extractDecisionBullets,
  parseOverviewSections,
} from "@/lib/overview"
import { overviewTypedKey } from "@/lib/motion"

type QualityInfo = {
  score?: number
  grade?: string
  components?: { completeness?: number; uniqueness?: number; consistency?: number }
  recommendations?: string[]
}

function gradeReason(opts: {
  quality?: QualityInfo
  qualityBody?: string
}): string {
  const rec = opts.quality?.recommendations?.[0]
  if (rec) return rec

  if (opts.qualityBody) {
    const bullets = extractBullets(opts.qualityBody, 1)
    if (bullets[0]) return bullets[0]
  }

  const c = opts.quality?.components
  if (!c) return "Qualidade calculada a partir dos dados."
  const weakest = (
    [
      ["completude", c.completeness],
      ["unicidade", c.uniqueness],
      ["consistência", c.consistency],
    ] as const
  )
    .filter(([, v]) => v != null)
    .sort((a, b) => (a[1] ?? 100) - (b[1] ?? 100))[0]

  if (weakest && (weakest[1] ?? 100) < 90) {
    return `Nota limitada principalmente por ${weakest[0]} (${Math.round(weakest[1] ?? 0)}%).`
  }
  return "Dataset com boa qualidade para exploração."
}

function BulletList({ items }: { items: string[] }) {
  if (!items.length) return null
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item} className="flex items-start gap-2.5 text-sm leading-snug">
          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-foreground/55" />
          <span className="line-clamp-2 text-foreground/90">{item}</span>
        </li>
      ))}
    </ul>
  )
}

function GradeCard({
  grade,
  score,
  reason,
}: {
  grade?: string
  score?: number | null
  reason: string
}) {
  const displayScore =
    score != null && Number.isFinite(Number(score)) ? Math.round(Number(score)) : null

  return (
    <aside className="flex w-full flex-col justify-between bg-foreground px-4 py-4 text-background sm:w-44 md:w-48">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-widest text-background/55">nota</p>
        <p className="font-bebas mt-1 text-6xl leading-none tracking-wide">
          {grade || "—"}
        </p>
        <p className="mt-1 font-mono text-sm text-background/70">
          {displayScore != null ? `${displayScore}/100` : "—/100"}
        </p>
      </div>
      <p className="mt-4 border-t border-background/20 pt-3 text-[12px] leading-snug text-background/75 line-clamp-4">
        {reason}
      </p>
    </aside>
  )
}

export function OverviewPanel({
  text,
  loading,
  grade,
  score,
  quality,
  analysisId,
  onOpenCharts,
  chartTitles,
  previewCharts,
  onAsk,
}: {
  text?: string
  loading?: boolean
  grade?: string
  score?: number | null
  quality?: QualityInfo
  analysisId?: string
  onOpenCharts?: () => void
  chartTitles?: string[]
  previewCharts?: ChartItem[]
  onAsk?: (question: string) => void
}) {
  const [leadDone, setLeadDone] = useState(!analysisId)
  const onLeadDone = useCallback(() => setLeadDone(true), [])

  if (loading && !text) {
    return (
      <div className="grid gap-6 md:grid-cols-[1fr_12rem]">
        <div className="space-y-4">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  const raw = text || ""
  const sections = parseOverviewSections(raw)
  const structured =
    sections.some((s) => s.id === "lead") ||
    sections.some((s) => s.id === "positives") ||
    sections.some((s) => s.id === "quality")

  const resolvedGrade = grade || quality?.grade
  const resolvedScore = score ?? quality?.score ?? null

  if (!structured) {
    const reason = gradeReason({ quality })
    return (
      <div className="animate-fade-up grid gap-6 md:grid-cols-[1fr_auto]">
        <article className="prose prose-neutral max-w-none prose-p:text-sm prose-li:text-sm">
          <ReactMarkdown>{raw || "—"}</ReactMarkdown>
        </article>
        <GradeCard grade={resolvedGrade} score={resolvedScore} reason={reason} />
      </div>
    )
  }

  const byId = (id: string) => sections.find((s) => s.id === id)
  const lead = byId("lead")
  const qualitySection = byId("quality")
  const positives = byId("positives")
  const explore = byId("explore")
  const decisions = byId("decisions")
  const positiveItems = positives?.body ? extractBullets(positives.body, 4) : []
  const exploreItems = explore?.body ? extractBullets(explore.body, 4) : []
  const decisionItems = decisions?.body ? extractDecisionBullets(decisions.body, 4) : []
  const showRest = leadDone || !lead
  const reason = gradeReason({
    quality,
    qualityBody: qualitySection?.body,
  })

  return (
    <div className="space-y-8">
      <div className="grid items-stretch gap-5 md:grid-cols-[1fr_auto]">
        <header className="flex min-w-0 flex-col justify-center space-y-3">
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            resumo
          </p>
          {lead ? (
            <TypewriterText
              text={lead.body}
              analysisId={analysisId}
              storageKey={analysisId ? overviewTypedKey(analysisId) : undefined}
              className="text-lg font-medium leading-snug md:text-xl"
              onDone={onLeadDone}
            />
          ) : (
            <p className="text-sm text-muted-foreground">—</p>
          )}
        </header>
        <GradeCard grade={resolvedGrade} score={resolvedScore} reason={reason} />
      </div>

      {!showRest ? (
        <div className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </div>
      ) : (
        <div className="animate-fade-up space-y-8">
          <div className="grid gap-8 border-t border-border pt-6 md:grid-cols-2">
            {positiveItems.length > 0 ? (
              <section className="space-y-3">
                <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  + positivos
                </p>
                <BulletList items={positiveItems} />
              </section>
            ) : null}
            {exploreItems.length > 0 ? (
              <section className="space-y-3">
                <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  → explorar
                </p>
                <BulletList items={exploreItems} />
              </section>
            ) : null}
          </div>

          {decisionItems.length > 0 ? (
            <section className="space-y-3 border-t border-border pt-6">
              <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                próximos passos
              </p>
              {onAsk ? (
                <ul className="space-y-2">
                  {decisionItems.map((q) => (
                    <li key={q}>
                      <button
                        type="button"
                        onClick={() => onAsk(q)}
                        className="flex items-start gap-2.5 text-left text-sm leading-snug hover:underline"
                      >
                        <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-foreground/55" />
                        <span className="line-clamp-2">{q}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <BulletList items={decisionItems} />
              )}
            </section>
          ) : null}

          {previewCharts && previewCharts.length > 0 ? (
            <section className="space-y-4 border-t border-border pt-6">
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  gráficos · {chartTitles?.length || previewCharts.length}
                </p>
                {onOpenCharts ? (
                  <button
                    type="button"
                    onClick={onOpenCharts}
                    className="font-mono text-[10px] uppercase tracking-widest hover:underline"
                  >
                    ver dashboard →
                  </button>
                ) : null}
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                {previewCharts.map((c) => (
                  <article key={c.id} className="border border-border px-3 py-3">
                    <h3 className="text-sm font-medium">{c.title}</h3>
                    {c.spec?.description ? (
                      <p className="mt-0.5 text-xs text-muted-foreground">{c.spec.description}</p>
                    ) : null}
                    <div className="mt-2 h-44">
                      <ChartRenderer chartType={c.chart_type} spec={c.spec} />
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ) : chartTitles && chartTitles.length > 0 && onOpenCharts ? (
            <section className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-border pt-5">
              <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                gráficos · {chartTitles.length}
              </p>
              <button
                type="button"
                onClick={onOpenCharts}
                className="font-mono text-[10px] uppercase tracking-widest hover:underline"
              >
                ver dashboard →
              </button>
            </section>
          ) : null}
        </div>
      )}
    </div>
  )
}
