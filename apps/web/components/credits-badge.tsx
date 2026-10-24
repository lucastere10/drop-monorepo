"use client"

import { useQuery } from "@tanstack/react-query"

export function CreditsBadge() {
  const { data } = useQuery({
    queryKey: ["credits"],
    queryFn: async () => {
      const res = await fetch("/api/credits")
      if (!res.ok) return null
      return res.json()
    },
    refetchInterval: 30_000,
  })
  if (!data) return null
  return (
    <div className="text-sm text-muted-foreground">
      <span className="text-foreground">{data.balance}</span> créditos
    </div>
  )
}
