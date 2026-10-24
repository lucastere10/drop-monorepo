import { extractDecisionBullets, parseOverviewSections } from "@/lib/overview"

type SchemaCol = { name: string; dtype?: string; null_pct?: number }
type Summary = {
  schema?: SchemaCol[]
  missing_pct?: number
  outliers?: Record<string, { count: number; percentage?: number }>
}

const MAX = 8

export function buildSuggestedQuestions(
  summary?: Summary | null,
  overviewText?: string | null
): string[] {
  const questions: string[] = []
  const seen = new Set<string>()

  function add(q: string) {
    const key = q.trim().toLowerCase()
    if (!key || seen.has(key) || questions.length >= MAX) return
    seen.add(key)
    questions.push(q.trim())
  }

  const schema = summary?.schema || []
  const interesting = schema
    .filter((c) => c.name && !/^(id|index|unnamed)/i.test(c.name))
    .slice(0, 4)

  for (const col of interesting.slice(0, 2)) {
    add(`O que a coluna ${col.name} representa neste arquivo?`)
  }

  const highNull = [...schema]
    .filter((c) => (c.null_pct ?? 0) > 5)
    .sort((a, b) => (b.null_pct ?? 0) - (a.null_pct ?? 0))

  if ((summary?.missing_pct ?? 0) > 2 || highNull.length) {
    add("Quais colunas têm mais campos vazios?")
  }

  const outlierEntries = Object.entries(summary?.outliers || {})
    .sort((a, b) => (b[1]?.count ?? 0) - (a[1]?.count ?? 0))
  if (outlierEntries.length) {
    add(`Os valores extremos em ${outlierEntries[0][0]} merecem atenção?`)
  }

  if (overviewText) {
    const decisions = parseOverviewSections(overviewText).find((s) => s.id === "decisions")
    if (decisions?.body) {
      for (const bullet of extractDecisionBullets(decisions.body, 3)) {
        add(bullet)
      }
    }
  }

  if (interesting.length) {
    add("Quais tipos de dados temos neste arquivo?")
  }

  add("Resuma os principais padrões deste arquivo.")

  return questions.slice(0, MAX)
}
