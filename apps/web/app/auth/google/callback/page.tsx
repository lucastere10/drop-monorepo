"use client"

import { useQueryClient } from "@tanstack/react-query"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useEffect, useState } from "react"

function CallbackInner() {
  const params = useSearchParams()
  const router = useRouter()
  const qc = useQueryClient()
  const code = params.get("code")
  const state = params.get("state")
  const [message, setMessage] = useState(
    !code || !state ? "Callback incompleto." : "Entrando com Google…"
  )

  useEffect(() => {
    if (!code || !state) return
    let cancelled = false
    const expected = sessionStorage.getItem("google_oauth_state")
    if (expected && expected !== state) {
      queueMicrotask(() => {
        if (!cancelled) setMessage("State inválido.")
      })
      return () => {
        cancelled = true
      }
    }
    fetch("/api/auth/google/callback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, state }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.message || "Falha no Google.")
        }
        if (cancelled) return
        await qc.invalidateQueries({ queryKey: ["auth"] })
        const next = sessionStorage.getItem("drop_auth_next") || "/dashboard"
        sessionStorage.removeItem("drop_auth_next")
        router.replace(next.startsWith("/") ? next : "/dashboard")
      })
      .catch((err) => {
        if (!cancelled) setMessage(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [code, state, router, qc])

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center px-6">
      <p className="font-bebas text-4xl tracking-wide">DRO/P</p>
      <p className="mt-4 text-sm text-muted-foreground">{message}</p>
    </div>
  )
}

export default function GoogleCallbackPage() {
  return (
    <Suspense>
      <CallbackInner />
    </Suspense>
  )
}
