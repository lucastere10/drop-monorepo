export const INTEREST_FEATURES = [
  { id: "charts", label: "Gráficos" },
  { id: "insights", label: "Insights" },
  { id: "chat", label: "Chat" },
  { id: "ml", label: "Machine Learning" },
] as const

export type InterestFeature = (typeof INTEREST_FEATURES)[number]["id"]

export function isInterestFeature(value: string | null): value is InterestFeature {
  return INTEREST_FEATURES.some((feature) => feature.id === value)
}

export function interestHref(feature: InterestFeature, analysisId: string) {
  const params = new URLSearchParams({
    feature,
    next: `/analyses/${analysisId}`,
  })
  return `/interesse?${params.toString()}`
}
