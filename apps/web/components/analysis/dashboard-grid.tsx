"use client"

import { useEffect, useMemo, useRef } from "react"
import ReactGridLayout, {
  useContainerWidth,
  useResponsiveLayout,
  type Layout,
} from "react-grid-layout"
import "react-grid-layout/css/styles.css"

import { ChartRenderer } from "@/components/analysis/chart-renderer"
import type { ChartItem, DashboardLayout, DashItem } from "@/lib/dashboard-layout"

function toItems(layout: Layout | undefined): DashItem[] {
  return (layout || []).map((it) => ({
    i: String(it.i),
    x: it.x,
    y: it.y,
    w: it.w,
    h: it.h,
  }))
}

export function DashboardGrid({
  charts,
  layout,
  editable,
  onCommit,
}: {
  charts: ChartItem[]
  layout: DashboardLayout
  editable: boolean
  onCommit?: (layout: DashboardLayout) => void
}) {
  const { width, containerRef, mounted } = useContainerWidth({ measureBeforeMount: true })
  const saved = useMemo(
    () => ({
      lg: layout.lg || [],
      md: layout.md || [],
      sm: layout.sm || [],
      xs: layout.sm || [],
      xxs: layout.sm || [],
    }),
    [layout]
  )
  const { layout: active, layouts, breakpoint, cols, setLayoutForBreakpoint } =
    useResponsiveLayout({
      width,
      layouts: saved,
      breakpoints: { lg: 800, md: 520, sm: 360, xs: 1, xxs: 0 },
      cols: { lg: 12, md: 12, sm: 12, xs: 12, xxs: 12 },
    })

  const layoutsRef = useRef(layouts)
  const bpRef = useRef(breakpoint)
  useEffect(() => {
    layoutsRef.current = layouts
    bpRef.current = breakpoint
  }, [layouts, breakpoint])

  const byId = new Map(charts.map((c) => [c.id, c]))
  const visible = active.filter((it) => byId.has(String(it.i)))

  function commit(current: Layout) {
    if (!editable || !onCommit) return
    const bp = bpRef.current
    const prev = layoutsRef.current
    const next: DashboardLayout = {
      lg: toItems(bp === "lg" ? current : prev.lg),
      md: toItems(bp === "md" ? current : prev.md),
      sm: toItems(bp === "sm" || bp === "xs" || bp === "xxs" ? current : prev.sm),
    }
    setLayoutForBreakpoint(bp, current)
    onCommit(next)
  }

  return (
    <div ref={containerRef} className="drop-dashboard">
      {mounted && width > 0 ? (
        <ReactGridLayout
          width={width}
          layout={visible}
          gridConfig={{ cols, rowHeight: 32, margin: [16, 16] }}
          dragConfig={{
            enabled: editable,
            handle: ".dashboard-drag-handle",
            bounded: false,
            threshold: 3,
          }}
          resizeConfig={{ enabled: editable }}
          onDragStop={(next) => commit(next)}
          onResizeStop={(next) => commit(next)}
        >
          {visible.map((item) => {
            const chart = byId.get(String(item.i))
            if (!chart) return null
            const description = chart.spec?.description
            return (
              <div key={item.i} className="h-full">
                <article className="flex h-full flex-col border border-border bg-background">
                  <header className="dashboard-drag-handle shrink-0 border-b border-border px-3 py-2">
                    <h3 className="text-sm font-medium leading-snug">{chart.title}</h3>
                    {description ? (
                      <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
                    ) : null}
                  </header>
                  <div className="min-h-0 flex-1 px-2 py-2">
                    <ChartRenderer chartType={chart.chart_type} spec={chart.spec} />
                  </div>
                </article>
              </div>
            )
          })}
        </ReactGridLayout>
      ) : null}
    </div>
  )
}
