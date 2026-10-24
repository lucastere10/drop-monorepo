"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"

type Overview = {
  users_total: number
  users_active: number
  analyses_total: number
  analyses_anonymous: number
  jobs_by_status: Record<string, number>
  credits_balance_sum: number
  tiers: { slug: string; name: string }[]
}

type AdminUser = {
  id: string
  email: string
  is_active: boolean
  is_staff: boolean
  last_login: string | null
  date_joined: string
  tier: string | null
  balance: number
  analysis_count: number
}

type AdminAnalysis = {
  id: string
  title: string
  user_email: string | null
  is_anonymous: boolean
  n_rows: number
  n_cols: number
  created_at: string
  expires_at: string | null
}

const FIELD =
  "h-8 border border-border bg-background px-2 text-sm outline-none focus-visible:border-foreground"

function formatWhen(value: string | null) {
  if (!value) return "nunca"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "nunca"
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
}

async function readError(res: Response, fallback: string) {
  const data = await res.json().catch(() => ({}))
  return typeof data?.message === "string" && data.message ? data.message : fallback
}

function SectionLabel({ children }: { children: string }) {
  return (
    <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
      {children}
    </p>
  )
}

function UserRow({
  user,
  tiers,
  selfId,
}: {
  user: AdminUser
  tiers: { slug: string; name: string }[]
  selfId?: string
}) {
  const qc = useQueryClient()
  const [delta, setDelta] = useState("100")
  const [reason, setReason] = useState("teste local")
  const [error, setError] = useState("")

  const patch = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const res = await fetch(`/api/admin/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(await readError(res, "Falha ao atualizar."))
      return res.json()
    },
    onSuccess: async () => {
      setError("")
      await qc.invalidateQueries({ queryKey: ["admin"] })
    },
    onError: (err: Error) => setError(err.message),
  })

  const adjust = useMutation({
    mutationFn: async () => {
      const amount = Number(delta)
      if (!Number.isInteger(amount) || amount === 0) {
        throw new Error("Informe um delta inteiro diferente de zero.")
      }
      const res = await fetch(`/api/admin/users/${user.id}/credits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ delta: amount, reason: reason.trim() }),
      })
      if (!res.ok) throw new Error(await readError(res, "Falha ao ajustar créditos."))
      return res.json()
    },
    onSuccess: async () => {
      setError("")
      await qc.invalidateQueries({ queryKey: ["admin"] })
      await qc.invalidateQueries({ queryKey: ["credits"] })
      await qc.invalidateQueries({ queryKey: ["auth", "me"] })
    },
    onError: (err: Error) => setError(err.message),
  })

  const busy = patch.isPending || adjust.isPending
  const isSelf = selfId === user.id

  return (
    <div className="py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="text-sm">{user.email}</p>
        <p className="font-mono text-[11px] text-muted-foreground">
          {user.balance} {user.balance === 1 ? "crédito" : "créditos"} · {user.analysis_count}{" "}
          {user.analysis_count === 1 ? "análise" : "análises"}
        </p>
      </div>
      <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        {user.is_active ? "ativo" : "inativo"}
        {user.is_staff ? " · staff" : ""}
        {" · "}
        último acesso {formatWhen(user.last_login)}
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor={`tier-${user.id}`}>
          Tier de {user.email}
        </label>
        <select
          id={`tier-${user.id}`}
          className={FIELD}
          value={user.tier ?? ""}
          disabled={busy || tiers.length === 0}
          onChange={(event) => patch.mutate({ tier: event.target.value })}
        >
          {user.tier && !tiers.some((tier) => tier.slug === user.tier) ? (
            <option value={user.tier}>{user.tier}</option>
          ) : null}
          {tiers.map((tier) => (
            <option key={tier.slug} value={tier.slug}>
              {tier.slug}
            </option>
          ))}
        </select>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy || (isSelf && user.is_active)}
          title={isSelf && user.is_active ? "Você não pode desativar a própria conta." : undefined}
          onClick={() => patch.mutate({ is_active: !user.is_active })}
        >
          {user.is_active ? "Desativar" : "Ativar"}
        </Button>
      </div>
      <form
        className="mt-2 flex flex-wrap items-center gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          setError("")
          adjust.mutate()
        }}
      >
        <label className="sr-only" htmlFor={`delta-${user.id}`}>
          Delta de créditos de {user.email}
        </label>
        <input
          id={`delta-${user.id}`}
          inputMode="numeric"
          className={`${FIELD} w-24`}
          value={delta}
          onChange={(event) => setDelta(event.target.value)}
        />
        <label className="sr-only" htmlFor={`reason-${user.id}`}>
          Motivo do ajuste de {user.email}
        </label>
        <input
          id={`reason-${user.id}`}
          className={`${FIELD} min-w-40 flex-1`}
          value={reason}
          placeholder="motivo"
          onChange={(event) => setReason(event.target.value)}
        />
        <Button type="submit" size="sm" disabled={busy}>
          Aplicar
        </Button>
      </form>
      {error ? (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  )
}

export default function AdminPage() {
  const { user, loading } = useAuth()
  const isStaff = Boolean(user?.is_staff)

  const overview = useQuery({
    queryKey: ["admin", "overview"],
    enabled: isStaff,
    queryFn: async () => {
      const res = await fetch("/api/admin/overview")
      if (!res.ok) throw new Error(await readError(res, "Falha ao carregar o resumo."))
      return (await res.json()) as Overview
    },
  })

  const users = useQuery({
    queryKey: ["admin", "users"],
    enabled: isStaff,
    queryFn: async () => {
      const res = await fetch("/api/admin/users")
      if (!res.ok) throw new Error(await readError(res, "Falha ao listar usuários."))
      return (await res.json()) as AdminUser[]
    },
  })

  const analyses = useQuery({
    queryKey: ["admin", "analyses"],
    enabled: isStaff,
    queryFn: async () => {
      const res = await fetch("/api/admin/analyses")
      if (!res.ok) throw new Error(await readError(res, "Falha ao listar análises."))
      return (await res.json()) as AdminAnalysis[]
    },
  })

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl px-5 py-10">
        <p className="font-mono text-xs text-muted-foreground">carregando…</p>
      </div>
    )
  }

  if (!isStaff) {
    return (
      <div className="mx-auto max-w-3xl px-5 py-10">
        <h1 className="font-bebas text-4xl tracking-wide">Operação</h1>
        <p className="mt-6 font-mono text-xs text-muted-foreground">
          Esta área é só para operadores.
        </p>
      </div>
    )
  }

  const jobs = overview.data?.jobs_by_status
  const stats = overview.data
    ? [
        ["usuários", overview.data.users_total],
        ["ativos", overview.data.users_active],
        ["análises", overview.data.analyses_total],
        ["anônimas", overview.data.analyses_anonymous],
        ["saldo", overview.data.credits_balance_sum],
      ]
    : []

  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <h1 className="font-bebas text-4xl tracking-wide">Operação</h1>
      <p className="mt-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        staff
      </p>

      <section className="mt-8">
        <SectionLabel>Resumo</SectionLabel>
        {overview.isLoading ? (
          <p className="mt-4 font-mono text-xs text-muted-foreground">carregando…</p>
        ) : null}
        {overview.error ? (
          <p role="alert" className="mt-4 text-sm text-destructive">
            {overview.error.message}
          </p>
        ) : null}
        {stats.length > 0 ? (
          <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-4 border-y border-border py-4 sm:grid-cols-5">
            {stats.map(([label, value]) => (
              <div key={label}>
                <dt className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {label}
                </dt>
                <dd className="mt-1 font-bebas text-3xl leading-none tracking-wide">{value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        {jobs ? (
          <p className="mt-3 font-mono text-[11px] text-muted-foreground">
            fila {jobs.queued ?? 0} · rodando {jobs.running ?? 0} · ok {jobs.succeeded ?? 0} · falha{" "}
            {jobs.failed ?? 0}
          </p>
        ) : null}
      </section>

      <section className="mt-10">
        <SectionLabel>Usuários</SectionLabel>
        <div className="mt-3 divide-y divide-border border-y border-border">
          {users.isLoading ? (
            <p className="py-6 font-mono text-xs text-muted-foreground">carregando…</p>
          ) : null}
          {users.error ? (
            <p role="alert" className="py-6 text-sm text-destructive">
              {users.error.message}
            </p>
          ) : null}
          {(users.data || []).map((row) => (
            <UserRow
              key={row.id}
              user={row}
              tiers={overview.data?.tiers || []}
              selfId={user?.id}
            />
          ))}
          {!users.isLoading && !users.error && (users.data || []).length === 0 ? (
            <p className="py-6 font-mono text-xs text-muted-foreground">nenhum usuário</p>
          ) : null}
        </div>
      </section>

      <section className="mt-10">
        <SectionLabel>Análises</SectionLabel>
        <div className="mt-3 divide-y divide-border border-y border-border">
          {analyses.isLoading ? (
            <p className="py-6 font-mono text-xs text-muted-foreground">carregando…</p>
          ) : null}
          {analyses.error ? (
            <p role="alert" className="py-6 text-sm text-destructive">
              {analyses.error.message}
            </p>
          ) : null}
          {(analyses.data || []).map((row) => (
            <div key={row.id} className="flex items-baseline justify-between gap-4 py-4">
              <div className="min-w-0">
                <p className="truncate text-sm">{row.title}</p>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {row.is_anonymous ? "anônimo" : row.user_email}
                  {" · "}
                  {formatWhen(row.created_at)}
                  {row.expires_at ? ` · expira ${formatWhen(row.expires_at)}` : ""}
                </p>
              </div>
              <p className="shrink-0 font-mono text-[11px] text-muted-foreground">
                {row.n_rows}×{row.n_cols}
              </p>
            </div>
          ))}
          {!analyses.isLoading && !analyses.error && (analyses.data || []).length === 0 ? (
            <p className="py-6 font-mono text-xs text-muted-foreground">nenhuma análise</p>
          ) : null}
        </div>
      </section>
    </div>
  )
}
