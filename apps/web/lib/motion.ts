/** Central motion tokens for Drop web (Phase C). */

export const MOTION = {
  tab: 0.15,
  fade: 0.2,
  typewriterMs: 32,
} as const

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

export function overviewTypedKey(analysisId: string): string {
  return `drop:overview-typed:${analysisId}`
}

export function hasOverviewTyped(analysisId: string): boolean {
  if (typeof window === "undefined") return true
  return sessionStorage.getItem(overviewTypedKey(analysisId)) === "1"
}

export function markOverviewTyped(analysisId: string): void {
  if (typeof window === "undefined") return
  sessionStorage.setItem(overviewTypedKey(analysisId), "1")
}

/** Strip light markdown for typewriter plain text. */
export function stripMarkdownLight(text: string): string {
  return text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\*\*/g, "")
    .replace(/__/g, "")
    .replace(/`/g, "")
    .replace(/^#+\s*/gm, "")
    .replace(/\n+/g, " ")
    .trim()
}
