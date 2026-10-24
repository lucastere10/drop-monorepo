"use client"

import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet } from "@/components/ui/sheet"
import { Tooltip } from "@/components/ui/tooltip"

type Quality = {
  score?: number
  grade?: string
  components?: { completeness?: number; uniqueness?: number; consistency?: number }
  recommendations?: string[]
}

type SchemaCol = {
  name: string
  dtype: string
  null_pct: number
  example?: string
  n_unique?: number
}

type Props = {
  grade?: string
  score?: number | null
  quality?: Quality
  missingPct?: number
  duplicates?: { count?: number; percentage?: number }
  outliers?: Record<string, { count: number; percentage: number }>
  schema?: SchemaCol[]
  /** Full-width layout for Saúde dos dados tab */
  variant?: "rail" | "page"
}

function Meter({ label, value }: { label: string; value?: number }) {
  const v = Number(value) || 0
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        <span>{label}</span>
        <span>{value != null ? `${value}%` : "—"}</span>
      </div>
      <div className="h-px bg-border">
        <div
          className="h-px bg-foreground transition-all duration-700"
          style={{ width: `${Math.min(100, v)}%` }}
        />
      </div>
    </div>
  )
}

export function QualityRail({
  grade,
  score,
  quality,
  missingPct,
  duplicates,
  outliers,
  schema = [],
  variant = "rail",
}: Props) {
  const components = quality?.components || {}
  const outlierEntries = Object.entries(outliers || {}).slice(0, 8)
  const isPage = variant === "page"
  const [selected, setSelected] = useState<SchemaCol | null>(null)

  return (
    <div
      className={
        isPage
          ? "animate-fade-up grid gap-10 lg:grid-cols-[240px_1fr]"
          : "space-y-8 border-r border-border pr-6 max-lg:border-r-0 max-lg:border-b max-lg:pb-8 max-lg:pr-0"
      }
    >
      <div className={isPage ? "space-y-8" : "contents"}>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            nota
          </p>
          <Tooltip content="Nota de qualidade dos dados">
            <p className="font-bebas mt-1 text-7xl leading-none tracking-wide">
              {grade || quality?.grade || "—"}
            </p>
          </Tooltip>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {score ?? quality?.score ?? "—"}/100
          </p>
        </div>

        <div className="space-y-4">
          <Meter label="completude" value={components.completeness} />
          <Meter label="unicidade" value={components.uniqueness} />
          <Meter label="consistência" value={components.consistency} />
        </div>

        <dl className="space-y-3 font-mono text-[11px]">
          <div className="flex justify-between gap-4 border-t border-border pt-3">
            <dt className="text-muted-foreground">campos vazios</dt>
            <dd>{missingPct ?? 0}%</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted-foreground">linhas repetidas</dt>
            <dd>
              {duplicates?.count ?? 0} ({duplicates?.percentage ?? 0}%)
            </dd>
          </div>
          <div className="border-t border-border pt-3">
            <dt className="mb-2 text-muted-foreground">valores extremos</dt>
            <dd className="space-y-1">
              {outlierEntries.length === 0 ? (
                <span className="text-muted-foreground">nenhum sinalizado</span>
              ) : (
                outlierEntries.map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-2">
                    <span className="truncate">{k}</span>
                    <span>{v.count}</span>
                  </div>
                ))
              )}
            </dd>
          </div>
        </dl>

        {(quality?.recommendations || []).length ? (
          <ul className="space-y-2 border-t border-border pt-3 text-xs text-muted-foreground">
            {(quality?.recommendations || []).map((r) => (
              <li key={r}>· {r}</li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className={isPage ? "" : "border-t border-border pt-3"}>
        {isPage ? (
          <>
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              schema · {schema.length} colunas
            </p>
            <ScrollArea className="mt-4 max-h-[28rem] border-y border-border">
              <table className="w-full text-left font-mono text-[11px]">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="py-2 pr-3 font-normal">coluna</th>
                    <th className="py-2 pr-3 font-normal">tipo</th>
                    <th className="py-2 pr-3 font-normal">vazios</th>
                    <th className="py-2 font-normal">exemplo</th>
                  </tr>
                </thead>
                <tbody>
                  {schema.map((col) => (
                    <tr
                      key={col.name}
                      className="cursor-pointer border-b border-border/60 transition-colors hover:bg-muted/40"
                      onClick={() => setSelected(col)}
                    >
                      <td className="py-2 pr-3">{col.name}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{col.dtype}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{col.null_pct}%</td>
                      <td className="max-w-[12rem] truncate py-2 text-muted-foreground">
                        {col.example || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollArea>

            <Sheet
              open={Boolean(selected)}
              onOpenChange={(o) => {
                if (!o) setSelected(null)
              }}
              title={selected?.name || "coluna"}
            >
              {selected ? (
                <dl className="space-y-4 font-mono text-sm">
                  <div>
                    <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">
                      nome
                    </dt>
                    <dd className="mt-1">{selected.name}</dd>
                  </div>
                  <div>
                    <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">
                      tipo
                    </dt>
                    <dd className="mt-1">
                      <Badge>{selected.dtype}</Badge>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">
                      campos vazios
                    </dt>
                    <dd className="mt-1">{selected.null_pct}%</dd>
                  </div>
                  {selected.n_unique != null ? (
                    <div>
                      <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">
                        valores únicos
                      </dt>
                      <dd className="mt-1">{selected.n_unique}</dd>
                    </div>
                  ) : null}
                  <div>
                    <dt className="text-[10px] uppercase tracking-widest text-muted-foreground">
                      exemplo
                    </dt>
                    <dd className="mt-1 break-all text-muted-foreground">
                      {selected.example || "—"}
                    </dd>
                  </div>
                </dl>
              ) : null}
            </Sheet>
          </>
        ) : (
          <details>
            <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground">
              schema · {schema.length} cols
            </summary>
            <ScrollArea className="mt-3 max-h-64">
              <table className="w-full text-left font-mono text-[10px]">
                <tbody>
                  {schema.map((col) => (
                    <tr key={col.name} className="border-b border-border/60">
                      <td className="py-1.5 pr-2">{col.name}</td>
                      <td className="py-1.5 pr-2 text-muted-foreground">{col.dtype}</td>
                      <td className="py-1.5 text-muted-foreground">{col.null_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollArea>
          </details>
        )}
      </div>
    </div>
  )
}
