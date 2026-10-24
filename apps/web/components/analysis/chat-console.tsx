"use client"

import ReactMarkdown from "react-markdown"

import { ChartRenderer } from "@/components/analysis/chart-renderer"
import { CreditsAlert } from "@/components/credits-alert"
import { ScrollArea } from "@/components/ui/scroll-area"
import { isCreditsNotice } from "@/lib/credits"
import { Skeleton } from "@/components/ui/skeleton"
import type { ChartItem } from "@/lib/dashboard-layout"

type Msg = { role: string; content: string; charts?: ChartItem[] }

export function ChatConsole({
  messages,
  input,
  onInputChange,
  onSend,
  busy,
  error,
  suggestions = [],
  onSuggestion,
  loadingHistory,
}: {
  messages: Msg[]
  input: string
  onInputChange: (v: string) => void
  onSend: () => void
  busy?: boolean
  error?: string
  suggestions?: string[]
  onSuggestion?: (q: string) => void
  loadingHistory?: boolean
}) {
  const showSuggestions = suggestions.length > 0 && !busy

  return (
    <div className="flex h-[min(70vh,640px)] flex-col border border-border">
      <div className="border-b border-border px-4 py-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        chat
      </div>

      {error ? (
        <div className="border-b border-border px-4 py-3">
          {isCreditsNotice(error) ? <CreditsAlert>{error}</CreditsAlert> : <p className="text-sm">{error}</p>}
        </div>
      ) : null}

      <ScrollArea className="min-h-0 flex-1 space-y-4 px-4 py-4">
        {loadingHistory ? (
          <div className="space-y-3">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-12 w-3/4" />
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-16 w-2/3" />
          </div>
        ) : null}

        {!loadingHistory && messages.length === 0 && !busy ? (
          <div className="space-y-4">
            <p className="font-mono text-xs text-muted-foreground">
              Pergunte sobre o arquivo — ou escolha uma sugestão.
            </p>
            {showSuggestions ? (
              <div className="flex flex-wrap gap-2">
                {suggestions.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => onSuggestion?.(q)}
                    className="max-w-full border border-border px-2.5 py-1.5 text-left text-xs leading-snug text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
                  >
                    {q}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        {messages.map((m, idx) => (
          <div key={idx} className="animate-fade-up">
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {m.role === "user" ? "você" : "drop"}
            </p>
            <div className="prose prose-neutral mt-1 max-w-none text-sm">
              <ReactMarkdown>{m.content}</ReactMarkdown>
            </div>
            {m.charts?.length ? (
              <div className="mt-3 max-w-xl border border-border px-3 py-3">
                {m.charts.map((c) => (
                  <div key={c.id}>
                    <p className="text-sm font-medium">{c.title}</p>
                    {c.spec?.description ? (
                      <p className="mt-0.5 text-xs text-muted-foreground">{c.spec.description}</p>
                    ) : null}
                    <div className="mt-2 h-48">
                      <ChartRenderer chartType={c.chart_type} spec={c.spec} />
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ))}
        {busy ? (
          <p className="font-mono text-xs text-muted-foreground">
            drop · pensando
            <span className="animate-stream-blink">_</span>
          </p>
        ) : null}
      </ScrollArea>

      {showSuggestions && messages.length > 0 ? (
        <div className="flex flex-wrap gap-2 border-t border-border px-4 py-2">
          {suggestions.slice(0, 4).map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onSuggestion?.(q)}
              className="max-w-full truncate border border-border px-2 py-1 font-mono text-[10px] text-muted-foreground hover:text-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex border-t border-border">
        <input
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSend()
          }}
          className="flex-1 bg-transparent px-4 py-3 text-sm outline-none placeholder:text-muted-foreground"
          placeholder="mensagem…"
          disabled={busy || loadingHistory}
        />
        <button
          type="button"
          disabled={busy || loadingHistory || !input.trim()}
          onClick={onSend}
          className="border-l border-border px-4 font-mono text-xs uppercase tracking-widest hover:bg-muted/40 disabled:opacity-40"
        >
          enviar
        </button>
      </div>
    </div>
  )
}
