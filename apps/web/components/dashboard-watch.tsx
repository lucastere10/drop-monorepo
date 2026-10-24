"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react"

const STORAGE_KEY = "drop.dashboard-job"

type Watch = { analysisId: string; jobId: string }

export type DashboardDone = {
  analysisId: string
  jobId: string
  status: "succeeded" | "failed"
  result?: {
    charts?: {
      id: string
      title: string
      chart_type: string
      spec: { labels?: string[]; values?: number[]; description?: string; source?: string }
    }[]
    dashboard_layout?: { lg?: { i: string; x: number; y: number; w: number; h: number }[] }
  }
  error?: string
}

type Toast = { id: string; title: string; body?: string; tone: "running" | "ok" | "err" }

type Ctx = {
  runningAnalysisId: string | null
  lastDone: DashboardDone | null
  start: (analysisId: string, jobId: string) => void
}

const DashboardWatchContext = createContext<Ctx | null>(null)

function readWatch(): Watch | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Watch
    if (!parsed?.analysisId || !parsed?.jobId) return null
    return parsed
  } catch {
    return null
  }
}

function writeWatch(watch: Watch | null) {
  if (!watch) localStorage.removeItem(STORAGE_KEY)
  else localStorage.setItem(STORAGE_KEY, JSON.stringify(watch))
}

export function useDashboardWatch() {
  const ctx = useContext(DashboardWatchContext)
  if (!ctx) {
    throw new Error("useDashboardWatch precisa do DashboardWatchProvider")
  }
  return ctx
}

export function DashboardWatchProvider({ children }: { children: React.ReactNode }) {
  const [watch, setWatch] = useState<Watch | null>(null)
  const [lastDone, setLastDone] = useState<DashboardDone | null>(null)
  const [toast, setToast] = useState<Toast | null>(null)
  const [ready, setReady] = useState(false)

  const start = useCallback((analysisId: string, jobId: string) => {
    const next = { analysisId, jobId }
    writeWatch(next)
    setWatch((prev) => (prev?.jobId === jobId ? prev : next))
    setToast({
      id: jobId,
      tone: "running",
      title: "Montando o dashboard",
      body: "Pode continuar navegando. Avisamos quando ficar pronto.",
    })
  }, [])

  useEffect(() => {
    const saved = readWatch()
    queueMicrotask(() => {
      if (saved) {
        setWatch(saved)
        setToast({
          id: saved.jobId,
          tone: "running",
          title: "Montando o dashboard",
          body: "Pode continuar navegando. Avisamos quando ficar pronto.",
        })
      }
      setReady(true)
    })
  }, [])

  useEffect(() => {
    if (!ready || !watch) return
    let stop = false

    async function tick() {
      try {
        const res = await fetch(`/api/jobs/${watch.jobId}`)
        if (!res.ok || stop) return
        const data = await res.json()
        if (data.status !== "succeeded" && data.status !== "failed") return
        if (stop) return
        writeWatch(null)
        setWatch(null)
        const done: DashboardDone = {
          analysisId: watch.analysisId,
          jobId: watch.jobId,
          status: data.status,
          result: data.result,
          error: data.error,
        }
        setLastDone(done)
        setToast(
          data.status === "succeeded"
            ? { id: `${watch.jobId}-ok`, tone: "ok", title: "Dashboard pronto" }
            : {
                id: `${watch.jobId}-err`,
                tone: "err",
                title: "Não foi possível montar o dashboard",
                body: data.error || "Tente de novo.",
              }
        )
      } catch {
        /* keep polling */
      }
    }

    void tick()
    const timer = window.setInterval(() => void tick(), 1000)
    return () => {
      stop = true
      window.clearInterval(timer)
    }
  }, [ready, watch])

  useEffect(() => {
    if (!toast || toast.tone === "running") return
    const timer = window.setTimeout(() => setToast(null), 6000)
    return () => window.clearTimeout(timer)
  }, [toast])

  return (
    <DashboardWatchContext.Provider
      value={{ runningAnalysisId: watch?.analysisId ?? null, lastDone, start }}
    >
      {children}
      {toast ? (
        <div
          role="status"
          className="fixed bottom-4 right-4 z-50 w-[min(22rem,calc(100vw-2rem))] border border-border bg-card px-4 py-3 shadow-none"
        >
          <p className="text-sm font-medium">{toast.title}</p>
          {toast.body ? (
            <p className="mt-1 text-xs leading-snug text-muted-foreground">{toast.body}</p>
          ) : null}
          {toast.tone === "running" ? (
            <span className="mt-2 block h-px w-10 bg-foreground/40 animate-drop-pulse" />
          ) : null}
        </div>
      ) : null}
    </DashboardWatchContext.Provider>
  )
}
