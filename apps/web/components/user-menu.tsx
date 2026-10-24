"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useId, useLayoutEffect, useRef, useState } from "react"
import { LogOut } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { useCredits } from "@/hooks/use-credits"
import type { SidebarSide } from "@/hooks/use-sidebar-prefs"
import { formatCredits, isLowBalance } from "@/lib/credits"
import { cn } from "@/lib/utils"

export function UserMenu({
  side,
  collapsed,
}: {
  side: SidebarSide
  collapsed?: boolean
}) {
  const { user, logout } = useAuth()
  const { data: credits } = useCredits()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const menuId = useId()
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null)

  const name = user?.first_name?.trim() || user?.email?.split("@")[0] || "conta"
  const email = user?.email || ""
  const initial = name.slice(0, 1).toUpperCase()
  const balance = credits?.balance
  const balanceLabel = typeof balance === "number" ? formatCredits(balance) : null
  const lowBalance = typeof balance === "number" && isLowBalance(balance)

  function placePanel() {
    const el = triggerRef.current
    const panel = panelRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const pw = panel?.offsetWidth ?? 220
    const ph = panel?.offsetHeight ?? 240
    const gap = 8
    let left = side === "left" ? r.right + gap : r.left - pw - gap
    let top = r.bottom - ph
    // Keep on screen
    left = Math.min(Math.max(8, left), window.innerWidth - pw - 8)
    top = Math.min(Math.max(8, top), window.innerHeight - ph - 8)
    setCoords({ top, left })
  }

  useLayoutEffect(() => {
    if (!open) {
      setCoords(null)
      return
    }
    placePanel()
  }, [open, side, collapsed])

  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false)
    }
    function onResize() {
      placePanel()
    }
    window.addEventListener("keydown", onKey)
    window.addEventListener("resize", onResize)
    return () => {
      window.removeEventListener("keydown", onKey)
      window.removeEventListener("resize", onResize)
    }
  }, [open, side])

  return (
    <div className="relative border-t border-border">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2.5 px-3 py-3 text-left transition-colors hover:bg-muted/40",
          collapsed && "md:justify-center md:px-2"
        )}
        title={email || name}
      >
        <span className="flex size-8 shrink-0 items-center justify-center border border-border font-mono text-[11px] uppercase">
          {initial}
        </span>
        <span className={cn("min-w-0 flex-1", collapsed && "md:hidden")}>
          <span className="block truncate text-sm leading-tight">{name}</span>
          {email ? (
            <span className="mt-0.5 block truncate text-[11px] leading-tight text-muted-foreground">
              {email}
            </span>
          ) : null}
        </span>
      </button>

      {open ? (
        <>
          <button
            type="button"
            aria-label="Fechar menu"
            className="fixed inset-0 z-[60]"
            onClick={() => setOpen(false)}
          />
          <div
            ref={panelRef}
            id={menuId}
            role="dialog"
            aria-label="Conta"
            className={cn(
              "fixed z-[70] w-60 border border-border bg-background shadow-sm",
              !coords && "invisible"
            )}
            style={
              coords
                ? { top: coords.top, left: coords.left }
                : { top: 0, left: 0 }
            }
          >
            <div className="flex items-center gap-2.5 px-3 py-3">
              <span className="flex size-8 shrink-0 items-center justify-center border border-border font-mono text-[11px] uppercase">
                {initial}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm leading-tight">{name}</span>
                {email ? (
                  <span className="mt-0.5 block truncate text-[11px] leading-tight text-muted-foreground">
                    {email}
                  </span>
                ) : null}
              </span>
            </div>

            <div className="border-t border-border py-1">
              <Link
                href="/profile"
                onClick={() => setOpen(false)}
                className="block px-3 py-2 text-sm transition-colors hover:bg-muted/50"
              >
                Perfil
              </Link>
              <Link
                href="/plan"
                onClick={() => setOpen(false)}
                className="flex items-center justify-between gap-3 px-3 py-2 text-sm transition-colors hover:bg-muted/50"
              >
                <span>Plano</span>
                {balanceLabel ? (
                  <span
                    className={cn(
                      "shrink-0 font-mono text-[11px] leading-none",
                      lowBalance
                        ? "animate-credit-pulse border border-border bg-muted px-1.5 py-1 text-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {balanceLabel}
                  </span>
                ) : null}
              </Link>
              <Link
                href="/settings"
                onClick={() => setOpen(false)}
                className="block px-3 py-2 text-sm transition-colors hover:bg-muted/50"
              >
                Configurações
              </Link>
            </div>

            <div className="border-t border-border">
              <button
                type="button"
                className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted/50"
                onClick={async () => {
                  setOpen(false)
                  await logout()
                  router.push("/")
                }}
              >
                <LogOut className="size-3.5 shrink-0" strokeWidth={1.5} />
                <span className="font-mono text-[12px] tracking-wide">{"Logout"}</span>
              </button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
