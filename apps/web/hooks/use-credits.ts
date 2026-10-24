"use client"

import { useQuery } from "@tanstack/react-query"

export type CreditsSnapshot = {
  balance: number
  tier?: { slug?: string; name?: string }
}

export function useCredits() {
  return useQuery({
    queryKey: ["credits"],
    queryFn: async () => {
      const res = await fetch("/api/credits")
      if (!res.ok) return null
      return (await res.json()) as CreditsSnapshot
    },
    refetchInterval: 30_000,
  })
}
