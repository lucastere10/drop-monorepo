"use client"

import { cn } from "@/lib/utils"

export type StreamEvent = {
  id: string
  label: string
  active?: boolean
  done?: boolean
}

export function ActivityStream({ events }: { events: StreamEvent[] }) {
  if (!events.length) {
    return (
      <p className="font-mono text-[11px] tracking-wide text-muted-foreground">
        idle<span className="animate-stream-blink">_</span>
      </p>
    )
  }

  return (
    <ul className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] tracking-wide">
      {events.map((e, i) => (
        <li key={e.id} className="flex items-center gap-3">
          {i > 0 ? <span className="text-border">·</span> : null}
          <span
            className={cn(
              e.active && "text-foreground",
              e.done && "text-muted-foreground",
              !e.active && !e.done && "text-muted-foreground"
            )}
          >
            {e.active ? (
              <>
                <span className="mr-1.5 inline-block size-1.5 rounded-full bg-foreground align-middle animate-drop-pulse" />
                {e.label}
                <span className="animate-stream-blink">_</span>
              </>
            ) : (
              e.label
            )}
          </span>
        </li>
      ))}
    </ul>
  )
}
