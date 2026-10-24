export type ChartItem = {
  id: string
  title: string
  chart_type: string
  spec: {
    labels?: string[]
    values?: number[]
    title?: string
    description?: string
    source?: string
    rule?: string
    chart_type?: string
    value_label?: string
    orientation?: "horizontal" | "vertical"
  }
}

export type DashItem = { i: string; x: number; y: number; w: number; h: number }

export type DashboardLayout = {
  lg?: DashItem[]
  md?: DashItem[]
  sm?: DashItem[]
}

function pack(charts: { id: string; chart_type: string }[], forceFull: boolean): DashItem[] {
  const cols = 12
  const items: DashItem[] = []
  let x = 0
  let y = 0
  let rowH = 0
  for (const chart of charts) {
    const w = forceFull || chart.chart_type === "line" ? cols : Math.max(cols / 2, 1)
    const h = 8
    if (x + w > cols) {
      x = 0
      y += rowH || h
      rowH = 0
    }
    items.push({ i: chart.id, x, y, w, h })
    x += w
    rowH = Math.max(rowH, h)
    if (x >= cols) {
      x = 0
      y += rowH
      rowH = 0
    }
  }
  return items
}

export function defaultDashboardLayout(
  charts: { id: string; chart_type: string }[]
): DashboardLayout {
  return {
    lg: pack(charts, false),
    md: pack(charts, false),
    sm: pack(charts, true),
  }
}

function keep(layout: DashboardLayout | undefined, ids: Set<string>): DashboardLayout {
  const pick = (items?: DashItem[]) => (items || []).filter((it) => ids.has(it.i))
  return { lg: pick(layout?.lg), md: pick(layout?.md), sm: pick(layout?.sm) }
}

export function resolveBoard(
  charts: ChartItem[],
  saved: DashboardLayout | undefined,
  mode: "board" | "share"
): { visible: ChartItem[]; layout: DashboardLayout } {
  if (mode === "share") {
    const visible = charts.filter((c) => c.spec?.source === "deterministic")
    const ids = new Set(visible.map((c) => c.id))
    const lg = (saved?.lg || []).filter((it) => ids.has(it.i))
    if (visible.length > 0 && lg.length === visible.length) {
      return { visible, layout: keep(saved, ids) }
    }
    return { visible, layout: defaultDashboardLayout(visible) }
  }

  const lg = saved?.lg || []
  if (lg.length) {
    const ids = new Set(lg.map((it) => it.i))
    const visible = charts.filter((c) => ids.has(c.id))
    return { visible, layout: keep(saved, new Set(visible.map((c) => c.id))) }
  }

  const deterministic = charts.filter((c) => c.spec?.source === "deterministic")
  const visible = deterministic.length
    ? deterministic
    : charts.filter((c) => c.spec?.source !== "chat")
  return { visible, layout: defaultDashboardLayout(visible) }
}
