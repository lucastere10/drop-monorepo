"use client"

import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { useAuth } from "@/components/auth-provider"

export function OnboardingDialog() {
  const { needsOnboarding, user, refresh } = useAuth()
  const qc = useQueryClient()
  const [name, setName] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  if (!needsOnboarding || !user) return null

  async function save(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      setError("Como prefere ser chamado?")
      return
    }
    setSaving(true)
    setError("")
    const res = await fetch("/api/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ first_name: trimmed }),
    })
    setSaving(false)
    if (!res.ok) {
      setError("Não foi possível salvar. Tente de novo.")
      return
    }
    await refresh()
    await qc.invalidateQueries({ queryKey: ["auth"] })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-foreground/25 backdrop-blur-[1px]" />
      <form
        onSubmit={save}
        className="relative z-10 w-full max-w-sm border border-border bg-background p-6 animate-fade-up"
      >
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          bem-vindo
        </p>
        <h2 className="font-bebas mt-2 text-4xl tracking-wide">Como prefere ser chamado?</h2>
        <p className="mt-2 text-sm text-muted-foreground">{user.email}</p>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-6 w-full border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-foreground"
          placeholder="Seu nome"
        />
        {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
        <button
          type="submit"
          disabled={saving}
          className="mt-4 w-full border border-foreground bg-foreground py-2.5 text-sm text-background disabled:opacity-50"
        >
          {saving ? "Salvando…" : "Continuar"}
        </button>
      </form>
    </div>
  )
}
