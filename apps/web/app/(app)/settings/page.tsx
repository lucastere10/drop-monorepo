"use client"

import Link from "next/link"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { ArrowLeft, Moon, PanelLeft, PanelRight, Sun } from "lucide-react"

import { useSidebarPrefs } from "@/hooks/use-sidebar-prefs"
import { cn } from "@/lib/utils"

export default function SettingsPage() {
  const { resolvedTheme, setTheme } = useTheme()
  const { side, setSide } = useSidebarPrefs()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const isInk = mounted && resolvedTheme === "dark"

  return (
    <div className="mx-auto max-w-lg px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="p-1.5 text-muted-foreground hover:text-foreground"
          aria-label="Voltar"
        >
          <ArrowLeft className="size-4" strokeWidth={1.5} />
        </Link>
        <h1 className="font-bebas text-4xl tracking-wide">Configurações</h1>
      </div>

      <div className="mt-8 divide-y divide-border border-y border-border">
        <div className="flex items-center justify-between gap-4 py-4">
          <div>
            <p className="text-sm">Tema</p>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Mist / Ink
            </p>
          </div>
          <button
            type="button"
            onClick={() => setTheme(isInk ? "light" : "dark")}
            className="inline-flex items-center gap-2 border border-border px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-widest transition-colors hover:bg-muted"
            aria-label={isInk ? "Mudar para Mist" : "Mudar para Ink"}
          >
            {isInk ? (
              <Moon className="size-3.5" strokeWidth={1.5} />
            ) : (
              <Sun className="size-3.5" strokeWidth={1.5} />
            )}
            <span>{isInk ? "Ink" : "Mist"}</span>
          </button>
        </div>

        <div className="flex items-center justify-between gap-4 py-4">
          <div>
            <p className="text-sm">Sidebar</p>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              lado
            </p>
          </div>
          <div className="inline-flex border border-border">
            <button
              type="button"
              onClick={() => setSide("left")}
              className={cn(
                "p-2 text-muted-foreground transition-colors hover:text-foreground",
                side === "left" && "bg-foreground text-background"
              )}
              aria-label="Sidebar à esquerda"
              title="Esquerda"
            >
              <PanelLeft className="size-3.5" strokeWidth={1.5} />
            </button>
            <button
              type="button"
              onClick={() => setSide("right")}
              className={cn(
                "p-2 text-muted-foreground transition-colors hover:text-foreground",
                side === "right" && "bg-foreground text-background"
              )}
              aria-label="Sidebar à direita"
              title="Direita"
            >
              <PanelRight className="size-3.5" strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
