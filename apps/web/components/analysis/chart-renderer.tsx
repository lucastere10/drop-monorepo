"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

const SERIES = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
]

export type ChartSpecView = {
  title?: string
  chart_type?: string
  labels?: string[]
  values?: number[]
  source?: string
  rule?: string
  value_label?: string
  orientation?: string
}

function toRows(spec: ChartSpecView) {
  return (spec.labels || []).map((label, idx) => ({
    name: label,
    value: Number(spec.values?.[idx] ?? 0),
  }))
}

const tooltipStyle = {
  background: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: 0,
  color: "var(--foreground)",
  fontSize: 12,
}

export function ChartRenderer({
  chartType,
  spec,
  height = "100%",
}: {
  chartType: string
  spec: ChartSpecView
  height?: number | string
}) {
  const data = toRows(spec)
  const type = (chartType || spec.chart_type || "bar").toLowerCase()
  const measure = spec.value_label || "frequência"
  const horizontal = spec.orientation === "horizontal"

  if (!data.length) {
    return (
      <p className="font-mono text-xs text-muted-foreground">sem pontos para plotar</p>
    )
  }

  if (type === "pie") {
    return (
      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="46%"
              outerRadius={68}
              stroke="var(--background)"
              strokeWidth={1}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={SERIES[i % SERIES.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => [value, measure]}
            />
            <Legend
              wrapperStyle={{ fontSize: 11, color: "var(--muted-foreground)" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (type === "line") {
    return (
      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="2 4" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => [value, measure]}
            />
            <Line type="monotone" dataKey="value" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout={horizontal ? "vertical" : "horizontal"}
          margin={horizontal ? { left: 8, right: 8 } : undefined}
        >
          <CartesianGrid strokeDasharray="2 4" stroke="var(--border)" vertical={false} />
          {horizontal ? (
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
          ) : (
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
          )}
          {horizontal ? (
            <YAxis
              type="category"
              dataKey="name"
              width={108}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
          ) : (
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              axisLine={false}
              tickLine={false}
            />
          )}
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value) => [value, measure]}
          />
          <Bar dataKey="value" fill="var(--chart-1)" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
