"use client"

import { DashboardGrid } from "@/components/analysis/dashboard-grid"
import type { ChartItem, DashboardLayout } from "@/lib/dashboard-layout"
import { resolveBoard } from "@/lib/dashboard-layout"

export type { ChartItem }

export function ChartsWorkbench({
  charts,
  layout,
  locked,
  isAuthenticated,
  error,
  onCommitLayout,
}: {
  charts: ChartItem[]
  layout?: DashboardLayout
  locked?: boolean
  isAuthenticated: boolean
  error?: string
  onCommitLayout: (layout: DashboardLayout) => void
}) {
  const board = resolveBoard(charts, layout, "board")

  return (
    <div className="space-y-4">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        dashboard
      </p>
      {error ? <p className="font-mono text-xs text-muted-foreground">{error}</p> : null}

      {board.visible.length === 0 ? (
        <p className="font-mono text-xs text-muted-foreground">
          Nenhum gráfico automático para este arquivo.
        </p>
      ) : null}

      {board.visible.length > 0 ? (
        <DashboardGrid
          charts={board.visible}
          layout={board.layout}
          editable={isAuthenticated && !locked}
          onCommit={onCommitLayout}
        />
      ) : null}
    </div>
  )
}
