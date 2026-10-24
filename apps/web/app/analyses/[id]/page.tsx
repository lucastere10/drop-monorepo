"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useParams, useRouter } from "next/navigation"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import { AnalysisShell, type AnalysisMode } from "@/components/analysis/analysis-shell"
import { useDashboardWatch } from "@/components/dashboard-watch"
import { ChartsWorkbench } from "@/components/analysis/charts-workbench"
import { ChatConsole } from "@/components/analysis/chat-console"
import { InsightsTimeline } from "@/components/analysis/insights-timeline"
import { InterestGateDialog } from "@/components/analysis/interest-gate-dialog"
import { MlPlaceholder } from "@/components/analysis/ml-placeholder"
import { OverviewPanel } from "@/components/analysis/overview-panel"
import { QualityRail } from "@/components/analysis/quality-rail"
import { AppChrome } from "@/components/app-chrome"
import { useAuth } from "@/components/auth-provider"
import type { ChartItem, DashboardLayout } from "@/lib/dashboard-layout"
import { interestHref, type InterestFeature } from "@/lib/interest"
import { buildSuggestedQuestions } from "@/lib/suggested-questions"

async function pollJob(jobId: string) {
  for (let i = 0; i < 60; i++) {
    const res = await fetch(`/api/jobs/${jobId}`)
    const data = await res.json()
    if (data.status === "succeeded" || data.status === "failed") return data
    await new Promise((r) => setTimeout(r, 1000))
  }
  throw new Error("Timeout do job")
}

export default function AnalysisDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params.id
  const router = useRouter()
  const qc = useQueryClient()
  const { isAuthenticated } = useAuth()
  const { runningAnalysisId, lastDone, start: startDashboard } = useDashboardWatch()
  const dashboardRunning = runningAnalysisId === id
  const appliedDashboardJob = useRef<string | null>(null)
  const [mode, setMode] = useState<AnalysisMode>("overview")
  const [chatInput, setChatInput] = useState("")
  const [chatLog, setChatLog] = useState<
    { role: string; content: string; charts?: ChartItem[] }[]
  >([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [chatHistoryLoading, setChatHistoryLoading] = useState(false)
  const [busy, setBusy] = useState("")
  const [notice, setNotice] = useState("")
  const [interestFeature, setInterestFeature] = useState<InterestFeature | null>(null)

  const goInterest = useCallback((feature: InterestFeature) => {
    setInterestFeature(feature)
  }, [])

  const closeInterestGate = useCallback(() => {
    setInterestFeature(null)
  }, [])

  const confirmInterest = useCallback(() => {
    if (!interestFeature) return
    const feature = interestFeature
    setInterestFeature(null)
    router.push(interestHref(feature, id))
  }, [id, interestFeature, router])

  const [charts, setCharts] = useState<ChartItem[]>([])
  const [dashboardLayout, setDashboardLayout] = useState<DashboardLayout>({})
  const [insights, setInsights] = useState<{ id: string; content: string }[]>([])
  const [overviewRunning, setOverviewRunning] = useState(false)

  const { data, refetch, isLoading } = useQuery({
    queryKey: ["analysis", id],
    queryFn: async () => {
      const res = await fetch(`/api/analyses/${id}`)
      if (!res.ok) throw new Error("Falha")
      return res.json()
    },
    refetchInterval: (query) => {
      const d = query.state.data as { overview_job_id?: string; overview_text?: string } | undefined
      if (d?.overview_job_id && !(d.overview_text && d.overview_text.length > 160)) {
        return 2000
      }
      return false
    },
  })

  // Claim anonymous analysis as soon as the user is authenticated.
  useEffect(() => {
    if (!isAuthenticated || !data?.is_anonymous) return
    let cancelled = false
    void (async () => {
      const res = await fetch(`/api/analyses/${id}/claim`, { method: "POST", body: "{}" })
      if (!cancelled && res.ok) {
        void refetch()
        void qc.invalidateQueries({ queryKey: ["analyses"] })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isAuthenticated, data?.is_anonymous, id, refetch, qc])

  const reloadCharts = useCallback(async () => {
    const cRes = await fetch(`/api/analyses/${id}/charts-list`)
    if (cRes.ok) setCharts(await cRes.json())
  }, [id])

  useEffect(() => {
    if (!data?.overview_job_id) return
    const jobId = String(data.overview_job_id)
    const looksReady = Boolean(data.overview_text && data.overview_text.length > 160)
    if (!looksReady) setOverviewRunning(true)
    let cancelled = false
    void (async () => {
      try {
        const job = await pollJob(jobId)
        if (cancelled) return
        setOverviewRunning(false)
        void refetch()
        if (job.status === "succeeded") void reloadCharts()
      } catch {
        if (!cancelled) setOverviewRunning(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [data?.overview_job_id, data?.overview_text, refetch, reloadCharts])

  const layoutAnalysisId = useRef<string | null>(null)
  useEffect(() => {
    if (!data?.id || layoutAnalysisId.current === data.id) return
    layoutAnalysisId.current = data.id
    setDashboardLayout((data.dashboard_layout as DashboardLayout) || {})
  }, [data?.id, data?.dashboard_layout])

  useEffect(() => {
    if (data?.dashboard_job_id) startDashboard(id, String(data.dashboard_job_id))
  }, [data?.dashboard_job_id, id, startDashboard])

  useEffect(() => {
    if (!lastDone || lastDone.analysisId !== id || appliedDashboardJob.current === lastDone.jobId) {
      return
    }
    appliedDashboardJob.current = lastDone.jobId
    if (lastDone.status !== "succeeded") return
    const created = (lastDone.result?.charts || []) as ChartItem[]
    if (created.length) {
      setCharts((prev) => {
        const ids = new Set(created.map((c) => c.id))
        return [...created, ...prev.filter((c) => !ids.has(c.id))]
      })
    }
    if (lastDone.result?.dashboard_layout) {
      setDashboardLayout(lastDone.result.dashboard_layout)
    }
    void refetch()
  }, [lastDone, id, refetch])

  useEffect(() => {
    async function loadExtras() {
      const [iRes, cRes] = await Promise.all([
        fetch(`/api/analyses/${id}/insights-list`),
        fetch(`/api/analyses/${id}/charts-list`),
      ])
      if (iRes.ok) setInsights(await iRes.json())
      if (cRes.ok) setCharts(await cRes.json())
    }
    void loadExtras()
  }, [id, data?.id])

  // Restore default conversation history when authenticated.
  useEffect(() => {
    if (!isAuthenticated || !data?.id) {
      setChatHistoryLoading(false)
      return
    }
    let cancelled = false
    setChatHistoryLoading(true)
    void (async () => {
      try {
        const res = await fetch(`/api/analyses/${id}/conversations`)
        if (!res.ok) return
        const list = (await res.json()) as {
          id: string
          messages: { role: string; content: string; charts?: ChartItem[] }[]
        }[]
        if (cancelled) return
        const first = list[0]
        if (first) {
          setConversationId(first.id)
          setChatLog(
            (first.messages || [])
              .filter((m) => m.role === "user" || m.role === "assistant")
              .map((m) => ({ role: m.role, content: m.content, charts: m.charts }))
          )
        }
      } finally {
        if (!cancelled) setChatHistoryLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isAuthenticated, data?.id, id])

  const suggestions = useMemo(
    () => buildSuggestedQuestions(data?.summary, data?.overview_text),
    [data?.summary, data?.overview_text]
  )

  const runAction = useMutation({
    mutationFn: async (action: string) => {
      setBusy(action)
      setNotice("")
      const res = await fetch(`/api/analyses/${id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
      const body = await res.json()
      if (res.status === 401) {
        const feature: InterestFeature = action === "insights" ? "insights" : "charts"
        goInterest(feature)
        throw new Error("auth")
      }
      if (!res.ok) throw new Error(body.message || "Erro")
      const job = await pollJob(body.job_id)
      if (job.status === "failed") throw new Error(job.error || "Job falhou")
      return job
    },
    onSettled: () => {
      setBusy("")
      void refetch()
      void qc.invalidateQueries({ queryKey: ["credits"] })
    },
  })

  const sendChat = useCallback(
    async (override?: string) => {
      const question = (override ?? chatInput).trim()
      if (!question) return
      if (!isAuthenticated) {
        goInterest("chat")
        return
      }
      setChatInput("")
      setChatLog((prev) => [...prev, { role: "user", content: question }])
      setBusy("chat")
      setNotice("")
      try {
        const payload: { message: string; conversation_id?: string } = { message: question }
        if (conversationId) payload.conversation_id = conversationId
        const res = await fetch(`/api/analyses/${id}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
        const body = await res.json()
        if (res.status === 401) {
          goInterest("chat")
          setChatLog((prev) => prev.slice(0, -1))
          setChatInput(question)
          return
        }
        if (!res.ok) {
          setChatLog((prev) => prev.slice(0, -1))
          setChatInput(question)
          setNotice(body.message || "Erro")
          return
        }
        const job = await pollJob(body.job_id)
        if (job.status === "failed") throw new Error(job.error || "Job falhou")
        if (job.result?.conversation_id) {
          setConversationId(job.result.conversation_id)
        }
        setChatLog((prev) => [
          ...prev,
          {
            role: "assistant",
            content: job.result?.answer || "",
            charts: job.result?.charts || [],
          },
        ])
        void qc.invalidateQueries({ queryKey: ["credits"] })
      } catch (e) {
        setChatLog((prev) => [
          ...prev,
          { role: "assistant", content: e instanceof Error ? e.message : "Erro" },
        ])
      } finally {
        setBusy("")
      }
    },
    [chatInput, conversationId, goInterest, id, isAuthenticated, qc]
  )

  function handleSuggestion(q: string) {
    if (!isAuthenticated) {
      goInterest("chat")
      return
    }
    void sendChat(q)
  }

  function handleAskFromOverview(q: string) {
    if (!isAuthenticated) {
      goInterest("chat")
      return
    }
    setMode("chat")
    void sendChat(q)
  }

  if (isLoading || !data) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="font-mono text-xs text-muted-foreground">
          loading workspace
          <span className="animate-stream-blink">_</span>
        </p>
      </div>
    )
  }

  return (
    <MaybeChrome embedded={isAuthenticated}>
    <AnalysisShell
      analysisId={id}
      title={data.title}
      isAnonymous={data.is_anonymous}
      isPublic={data.is_public}
      shareToken={data.share_token}
      mode={mode}
      onModeChange={setMode}
      embedded={isAuthenticated}
    >
      {mode === "overview" ? (
        <OverviewPanel
          text={data.overview_text}
          loading={overviewRunning}
          grade={data.quality_grade}
          score={data.quality_score}
          quality={data.summary?.quality}
          analysisId={id}
          chartTitles={charts.map((c) => c.title)}
          previewCharts={charts.filter((c) => c.spec?.source === "deterministic").slice(0, 2)}
          onOpenCharts={() => setMode("charts")}
          onAsk={handleAskFromOverview}
        />
      ) : null}

      {mode === "charts" ? (
        <ChartsWorkbench
          charts={charts}
          layout={dashboardLayout}
          locked={dashboardRunning}
          isAuthenticated={isAuthenticated}
          error={notice}
          onCommitLayout={(next) => {
            if (dashboardRunning) return
            setDashboardLayout(next)
            if (!isAuthenticated) return
            void fetch(`/api/analyses/${id}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ dashboard_layout: next }),
            })
          }}
        />
      ) : null}

      {mode === "insights" ? (
        <InsightsTimeline
          insights={insights}
          busy={busy === "insights"}
          error={notice}
          onGenerate={async () => {
            if (!isAuthenticated) {
              goInterest("insights")
              return
            }
            try {
              const job = await runAction.mutateAsync("insights")
              if (job.result?.content) {
                setInsights((prev) => [
                  { id: job.result.insight_id, content: job.result.content },
                  ...prev,
                ])
              }
            } catch (e) {
              if (e instanceof Error && e.message !== "auth") setNotice(e.message)
            }
          }}
        />
      ) : null}

      {mode === "chat" ? (
        <ChatConsole
          messages={chatLog}
          input={chatInput}
          onInputChange={setChatInput}
          onSend={() => void sendChat()}
          busy={busy === "chat"}
          error={notice}
          suggestions={suggestions}
          onSuggestion={handleSuggestion}
          loadingHistory={chatHistoryLoading}
        />
      ) : null}

      {mode === "health" ? (
        <QualityRail
          variant="page"
          grade={data.quality_grade}
          score={data.quality_score}
          quality={data.summary?.quality}
          missingPct={data.summary?.missing_pct}
          duplicates={data.summary?.duplicates}
          outliers={data.summary?.outliers}
          schema={data.summary?.schema}
        />
      ) : null}

      {mode === "ml" ? (
        <MlPlaceholder
          isAuthenticated={isAuthenticated}
          onInterest={() => goInterest("ml")}
        />
      ) : null}
    </AnalysisShell>
    <InterestGateDialog
      open={interestFeature !== null}
      feature={interestFeature}
      onClose={closeInterestGate}
      onConfirm={confirmInterest}
    />
    </MaybeChrome>
  )
}

function MaybeChrome({
  embedded,
  children,
}: {
  embedded: boolean
  children: React.ReactNode
}) {
  if (!embedded) return children
  return <AppChrome>{children}</AppChrome>
}
