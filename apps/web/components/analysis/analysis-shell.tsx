"use client"

import { AnimatePresence, motion } from "motion/react"
import Link from "next/link"
import { useEffect, useState } from "react"

import { DeleteAnalysisButton } from "@/components/analysis/delete-analysis-button"
import { ShareControls } from "@/components/analysis/share-controls"
import { DropIcon } from "@/components/drop-icon"
import { useAuth } from "@/components/auth-provider"
import { Tooltip } from "@/components/ui/tooltip"
import { MOTION, prefersReducedMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"

export type AnalysisMode =
  | "overview"
  | "charts"
  | "insights"
  | "chat"
  | "health"
  | "ml"

const MODES: { id: AnalysisMode; label: string }[] = [
  { id: "overview", label: "Resumo" },
  { id: "charts", label: "Gráficos" },
  { id: "insights", label: "Insights" },
  { id: "chat", label: "Chat" },
  { id: "health", label: "Saúde dos dados" },
  { id: "ml", label: "Machine Learning" },
]

type Props = {
  analysisId: string
  title: string
  isAnonymous?: boolean
  mode: AnalysisMode
  onModeChange: (mode: AnalysisMode) => void
  stream?: React.ReactNode
  children: React.ReactNode
  /** Inside AppChrome — lean header */
  embedded?: boolean
  isPublic?: boolean
  shareToken?: string
}

export function AnalysisShell({
  analysisId,
  title,
  isAnonymous,
  mode,
  onModeChange,
  stream,
  children,
  embedded,
  isPublic,
  shareToken,
}: Props) {
  const { isAuthenticated, user, logout, loading } = useAuth()
  const shortId = analysisId.slice(0, 8)
  const label = user?.first_name?.trim() || user?.email?.split("@")[0] || "conta"
  const canManage = Boolean(embedded && isAuthenticated && !isAnonymous)
  const [reduce, setReduce] = useState(true)

  useEffect(() => {
    setReduce(prefersReducedMotion())
  }, [])

  return (
    <div className={embedded ? "flex min-h-full flex-col" : "flex min-h-svh flex-col"}>
      <header className="border-b border-border">
        <div className="mx-auto flex h-11 max-w-6xl items-center gap-4 px-5">
          {!embedded ? (
            <>
              <Link href="/" aria-label="DRO/P" className="text-foreground hover:opacity-70">
                <DropIcon />
              </Link>
              <span className="text-border">|</span>
            </>
          ) : null}
          <span className="truncate text-sm">{title}</span>
          {canManage ? (
            <>
              <ShareControls
                analysisId={analysisId}
                isPublic={Boolean(isPublic)}
                shareToken={shareToken}
              />
              <DeleteAnalysisButton analysisId={analysisId} title={title} />
            </>
          ) : null}
          <span className="ml-auto hidden font-mono text-[10px] uppercase tracking-widest text-muted-foreground sm:inline">
            {shortId}
            {isAnonymous && !isAuthenticated ? (
              <Tooltip content="Análise anônima expira em 24h">
                <span> · anon/24h</span>
              </Tooltip>
            ) : null}
          </span>
          {embedded ? null : loading ? (
            <span className="font-mono text-[10px] text-muted-foreground">…</span>
          ) : isAuthenticated ? (
            <>
              <Link
                href="/dashboard"
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                dash
              </Link>
              <Link
                href="/analyses"
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                lista
              </Link>
              <Link
                href="/profile"
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
                title={user?.email}
              >
                {label}
              </Link>
              <button
                type="button"
                onClick={() => void logout()}
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                sair
              </button>
            </>
          ) : (
            <Link
              href={`/login?next=${encodeURIComponent(`/analyses/${analysisId}`)}`}
              className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
            >
              entrar
            </Link>
          )}
        </div>
      </header>

      {stream ? (
        <div className="border-b border-border bg-muted/20">
          <div className="mx-auto max-w-6xl px-5 py-2">{stream}</div>
        </div>
      ) : null}

      <nav className="border-b border-border">
        <div className="mx-auto flex max-w-6xl gap-4 overflow-x-auto px-5 sm:gap-6">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => onModeChange(m.id)}
              className={cn(
                "shrink-0 py-3 font-mono text-[11px] uppercase tracking-widest transition-colors",
                mode === m.id
                  ? "border-b border-foreground text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={reduce ? undefined : { opacity: 0 }}
            transition={{ duration: reduce ? 0 : MOTION.tab }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}
