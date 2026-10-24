"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { FileSearch, Scale, ScanSearch, Upload } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { CreditsAlert } from "@/components/credits-alert"
import { isCreditsNotice } from "@/lib/credits"
import { DropIntroOverlay } from "@/components/drop-intro-overlay"
import { SampleDialog } from "@/components/sample-dialog"
import { SiteHeader } from "@/components/site-header"
import { cn } from "@/lib/utils"

const SAMPLES = [
  {
    id: "grade-prediction",
    title: "Predição de Notas",
    file: "/samples/grade-prediction.csv",
    filename: "grade-prediction.csv",
  },
  {
    id: "work-stress",
    title: "Estresse no Trabalho",
    file: "/samples/work-stress.csv",
    filename: "work-stress.csv",
  },
  {
    id: "customer-segmentation",
    title: "Segmentação de Clientes",
    file: "/samples/customer-segmentation.csv",
    filename: "customer-segmentation.csv",
  },
  {
    id: "real-estate",
    title: "Preço de Imóveis",
    file: "/samples/real-estate-pricing.csv",
    filename: "real-estate-pricing.csv",
  },
  {
    id: "health-risk",
    title: "Risco Cardiovascular",
    file: "/samples/health-risk.csv",
    filename: "health-risk.csv",
  },
]

const PILLARS = [
  { label: "Enviar", Icon: Upload },
  { label: "Analisar", Icon: FileSearch },
  { label: "Entender", Icon: ScanSearch },
  { label: "Decidir", Icon: Scale },
]

const LOADING_MSGS = [
  "Lendo arquivo…",
  "Limpando colunas…",
  "Perfilando qualidade…",
  "Gerando resumo…",
]

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [samplesOpen, setSamplesOpen] = useState(false)
  const [msgIdx, setMsgIdx] = useState(0)
  const [introDone, setIntroDone] = useState(false)

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace("/dashboard")
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (!loading) return
    const id = window.setInterval(() => {
      setMsgIdx((i) => (i + 1) % LOADING_MSGS.length)
    }, 1200)
    return () => window.clearInterval(id)
  }, [loading])

  async function upload(file: File) {
    setLoading(true)
    setError("")
    setMsgIdx(0)
    setSamplesOpen(false)
    try {
      const form = new FormData()
      form.append("file", file)
      const res = await fetch("/api/analyses", { method: "POST", body: form })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.message || "Falha no upload.")
      }
      const data = await res.json()
      router.push(`/analyses/${data.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha no upload.")
      setLoading(false)
    }
  }

  async function loadSample(sample: (typeof SAMPLES)[number]) {
    setLoading(true)
    setError("")
    setMsgIdx(0)
    setSamplesOpen(false)
    try {
      const res = await fetch(sample.file)
      const blob = await res.blob()
      const file = new File([blob], sample.filename, { type: "text/csv" })
      await upload(file)
    } catch {
      setError("Não foi possível carregar o sample.")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-svh">
      <DropIntroOverlay onDone={() => setIntroDone(true)} />
      <SiteHeader />

      <main className="mx-auto flex max-w-2xl flex-col px-5 pb-16 pt-10">
        <div className={cn("text-center", introDone && "animate-fade-up")}>
          <h1 className="font-bebas text-7xl tracking-[0.04em] md:text-8xl">DRO/P</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Dados limpos, Insights claros.
          </p>
        </div>

        <ul className="mt-8 grid grid-cols-4 gap-2 border-y border-border py-5">
          {PILLARS.map(({ label, Icon }, i) => (
            <li
              key={label}
              className={cn(
                "flex flex-col items-center gap-2",
                introDone && "animate-fade-up",
              )}
              style={introDone ? { animationDelay: `${120 + i * 80}ms` } : undefined}
            >
              <Icon className="size-4 text-foreground" strokeWidth={1.5} />
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                {label}
              </span>
            </li>
          ))}
        </ul>

        <label
          className={cn(
            "relative mt-8 flex cursor-pointer flex-col items-center justify-center border border-dashed px-6 py-14 transition-all duration-300",
            dragging && "scale-[1.01] border-foreground bg-muted/30",
            !dragging && "border-border hover:border-foreground/50",
            loading && "pointer-events-none"
          )}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            const file = e.dataTransfer.files?.[0]
            if (file) void upload(file)
          }}
        >
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            className="hidden"
            disabled={loading}
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) void upload(file)
            }}
          />
          {loading ? (
            <div className="flex flex-col items-center gap-3">
              <div className="size-2 rounded-full bg-foreground animate-drop-pulse" />
              <p className="font-mono text-xs tracking-wide text-muted-foreground">
                {LOADING_MSGS[msgIdx]}
                <span className="animate-stream-blink">_</span>
              </p>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-sm">Arraste CSV, XLSX ou JSON</p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                ou clique para selecionar
              </p>
            </div>
          )}
        </label>

        {error ? (
          isCreditsNotice(error) ? (
            <CreditsAlert className="mt-3">{error}</CreditsAlert>
          ) : (
            <p className="mt-3 text-center text-sm text-red-700">{error}</p>
          )
        ) : null}

        <button
          type="button"
          disabled={loading}
          onClick={() => setSamplesOpen(true)}
          className="mt-5 w-full border border-dashed border-border py-3 text-sm text-muted-foreground transition-colors hover:border-foreground hover:text-foreground disabled:opacity-50"
        >
          Testar com um sample →
        </button>

        <p className="mt-8 text-center font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {isAuthenticated ? (
            "Upload vinculado à sua conta"
          ) : (
            <>
              Anônimo · 24h ·{" "}
              <Link href="/login" className="underline hover:text-foreground">
                entrar para salvar
              </Link>
            </>
          )}
        </p>
      </main>

      <SampleDialog
        open={samplesOpen}
        onClose={() => setSamplesOpen(false)}
        samples={SAMPLES}
        onSelect={(s) => void loadSample(s)}
        disabled={loading}
      />
    </div>
  )
}
