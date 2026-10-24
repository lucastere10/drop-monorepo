export type OverviewSection = {
  id: string
  title: string
  body: string
}

const KNOWN = [
  { match: /em uma frase/i, id: "lead" },
  { match: /qualidade/i, id: "quality" },
  { match: /pontos positivos/i, id: "positives" },
  { match: /a explorar/i, id: "explore" },
  { match: /decis/i, id: "decisions" },
]

export function parseOverviewSections(text: string): OverviewSection[] {
  const parts = text.split(/\n(?=##\s+)/)
  const sections: OverviewSection[] = []
  for (const part of parts) {
    const trimmed = part.trim()
    if (!trimmed) continue
    const m = trimmed.match(/^##\s+(.+?)\s*\n([\s\S]*)$/)
    if (!m) {
      if (!trimmed.startsWith("##")) {
        sections.push({ id: "raw", title: "", body: trimmed })
      }
      continue
    }
    const title = m[1].trim()
    const body = m[2].trim()
    const known = KNOWN.find((k) => k.match.test(title))
    sections.push({ id: known?.id || "other", title, body })
  }
  return sections
}

function stripMd(text: string): string {
  return text.replace(/\*\*|__/g, "").replace(/`/g, "").trim()
}

/** Extract bullet / numbered / short lines from a markdown section body. */
export function extractBullets(body: string, limit = 4): string[] {
  const lines = body.split("\n")
  const out: string[] = []
  for (const line of lines) {
    const m = line.match(/^\s*(?:[-*]|\d+[.)])\s+(.+)$/)
    if (m) {
      const text = stripMd(m[1])
      if (text) {
        out.push(text)
        if (out.length >= limit) return out
      }
      continue
    }
    const plain = stripMd(line)
    if (!plain || plain.startsWith("#")) continue
    // Split long paragraphs into sentences when there are no list markers
    if (!body.match(/^\s*(?:[-*]|\d+[.)])/m)) {
      for (const sentence of plain.split(/(?<=[.!?])\s+/)) {
        const s = sentence.trim()
        if (s.length < 8) continue
        out.push(s.replace(/[.!]+$/, ""))
        if (out.length >= limit) return out
      }
    }
  }
  return out
}

/** Extract bullet / numbered lines as plain questions from a markdown section body. */
export function extractDecisionBullets(body: string, limit = 3): string[] {
  return extractBullets(body, limit).map((text) => {
    if (/[?？]$/.test(text)) return text
    return text.replace(/[.!]+$/, "") + "?"
  })
}
