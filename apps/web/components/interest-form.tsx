"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Suspense, useState } from "react"

import { Button } from "@/components/ui/button"
import { INTEREST_FEATURES, isInterestFeature, type InterestFeature } from "@/lib/interest"
import { cn } from "@/lib/utils"

const ANALYSIS_PATH = /^\/analyses\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i

function safeNext(value: string | null) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/"
  return value
}

function InterestFormInner() {
  const search = useSearchParams()
  const preset = search.get("feature")
  const next = safeNext(search.get("next"))
  const analysisId = next.match(ANALYSIS_PATH)?.[1] ?? null
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [selected, setSelected] = useState<InterestFeature[]>(() =>
    isInterestFeature(preset) ? [preset] : []
  )
  const [comment, setComment] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  function toggle(id: InterestFeature) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    if (!selected.length) {
      setError("Escolha ao menos uma funcionalidade.")
      return
    }
    setLoading(true)
    const res = await fetch("/api/interests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        email,
        interests: selected,
        comment,
        analysis_id: analysisId,
      }),
    })
    const data = res.status === 204 ? {} : await res.json().catch(() => ({}))
    setLoading(false)
    if (!res.ok) {
      setError(data.message || "Não foi possível registrar o interesse.")
      return
    }
    setDone(true)
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center px-6">
      <div className="animate-fade-up">
        <Link href="/">
          <p className="font-bebas mt-6 text-6xl tracking-[0.04em]">DRO/P</p>
        </Link>
        <h1 className="mt-6 text-lg">Tenho interesse</h1>
        <p className="mt-3 text-sm text-muted-foreground">
          Esta funcionalidade está disponível apenas para usuários cadastrados. Deixe seu nome, e-mail e o que você quer usar — a gente
          guarda o interesse.
        </p>
      </div>

      {done ? (
        <div className="mt-10 space-y-4 text-sm">
          <p>Interesse registrado. Quando abrirmos o acesso, entramos em contato.</p>
          <Link href={next} className="inline-block underline">
            {analysisId ? "Voltar para a análise" : "Voltar"}
          </Link>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="mt-10 space-y-4">
          <label className="block text-sm">
            Nome
            <input
              type="text"
              required
              maxLength={120}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full border border-border bg-background px-3 py-2 outline-none focus:border-foreground"
            />
          </label>
          <label className="block text-sm">
            E-mail
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full border border-border bg-background px-3 py-2 outline-none focus:border-foreground"
            />
          </label>
          <fieldset className="space-y-2">
            <legend className="text-sm">O que você quer usar</legend>
            <div className="flex flex-wrap gap-2">
              {INTEREST_FEATURES.map((feature) => {
                const on = selected.includes(feature.id)
                return (
                  <button
                    key={feature.id}
                    type="button"
                    aria-pressed={on}
                    onClick={() => toggle(feature.id)}
                    className={cn(
                      "border px-2.5 py-1.5 text-xs transition-colors",
                      on
                        ? "border-foreground text-foreground"
                        : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                    )}
                  >
                    {feature.label}
                  </button>
                )
              })}
            </div>
          </fieldset>
          <label className="block text-sm">
            Comentário
            <textarea
              value={comment}
              maxLength={2000}
              rows={3}
              onChange={(e) => setComment(e.target.value)}
              className="mt-1 w-full resize-y border border-border bg-background px-3 py-2 outline-none focus:border-foreground"
            />
          </label>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Enviando…" : "Enviar interesse"}
          </Button>
        </form>
      )}
    </div>
  )
}

export function InterestForm() {
  return (
    <Suspense>
      <InterestFormInner />
    </Suspense>
  )
}
