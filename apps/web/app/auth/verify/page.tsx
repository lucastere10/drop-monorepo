"use client"

import { useQueryClient } from "@tanstack/react-query"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"

function VerifyInner() {
  const params = useSearchParams()
  const router = useRouter()
  const qc = useQueryClient()
  const token = params.get("token")
  const [error, setError] = useState(token ? "" : "Token ausente.")
  const [status, setStatus] = useState(token ? "Validando acesso…" : "Token ausente.")

  useEffect(() => {
    if (!token) return
    let cancelled = false
    fetch("/api/auth/magic-link/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.message || "Link inválido.")
        }
        if (cancelled) return
        await qc.invalidateQueries({ queryKey: ["auth"] })
        const next =
          typeof window !== "undefined"
            ? sessionStorage.getItem("drop_auth_next") || "/dashboard"
            : "/dashboard"
        sessionStorage.removeItem("drop_auth_next")
        router.replace(next.startsWith("/") ? next : "/dashboard")
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setStatus(err.message)
        }
      })
    return () => {
      cancelled = true
    }
  }, [token, router, qc])

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center px-6">
      <p className="font-bebas text-4xl tracking-wide">DRO/P</p>
      <p className="mt-4 text-sm text-muted-foreground">{error || status}</p>
    </div>
  )
}

export default function VerifyPage() {
  return (
    <Suspense>
      <VerifyInner />
    </Suspense>
  )
}
