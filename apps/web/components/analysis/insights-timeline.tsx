"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"

import { CreditsAlert } from "@/components/credits-alert"
import { isCreditsNotice } from "@/lib/credits"

type Insight = { id: string; content: string }

export function InsightsTimeline({
  insights,
  busy,
  error,
  onGenerate,
}: {
  insights: Insight[]
  busy?: boolean
  error?: string
  onGenerate: () => void
}) {
  const [openId, setOpenId] = useState<string | null>(null)
  const activeId = openId ?? insights[0]?.id ?? null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          insight stream
        </p>
        <button
          type="button"
          disabled={busy}
          onClick={onGenerate}
          className="font-mono text-xs tracking-wide hover:underline disabled:opacity-50"
        >
          {busy ? (
            <>
              running<span className="animate-stream-blink">_</span>
            </>
          ) : (
            "> gerar insights"
          )}
        </button>
      </div>

      {error ? (
        isCreditsNotice(error) ? <CreditsAlert>{error}</CreditsAlert> : <p className="text-sm">{error}</p>
      ) : null}

      {!insights.length && !busy ? (
        <p className="font-mono text-xs text-muted-foreground">
          Nenhum insight encontrado. Execute para coletar evidências.
        </p>
      ) : null}

      <ul className="space-y-0">
        {insights.map((insight, idx) => {
          const open = activeId === insight.id
          const headline = insight.content.split("\n").find((l) => l.trim()) || "Insight"
          return (
            <li key={insight.id} className="border-b border-border py-4">
              <button
                type="button"
                className="flex w-full items-baseline justify-between gap-4 text-left"
                onClick={() => setOpenId(open ? "__none__" : insight.id)}
              >
                <span className="font-mono text-[10px] text-muted-foreground">
                  {String(idx + 1).padStart(2, "0")}
                </span>
                <span className="flex-1 truncate text-sm">
                  {headline.replace(/^#+\s*/, "").slice(0, 120)}
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {open ? "fold" : "expand"}
                </span>
              </button>
              {open ? (
                <div className="animate-fade-up prose prose-neutral mt-4 max-w-none pl-8 text-sm">
                  <ReactMarkdown>{insight.content}</ReactMarkdown>
                </div>
              ) : null}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
