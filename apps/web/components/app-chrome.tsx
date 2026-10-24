"use client"

import type { ReactNode } from "react"
import { Menu } from "lucide-react"
import Link from "next/link"

import { AppSidebar } from "@/components/app-sidebar"
import { DropIcon } from "@/components/drop-icon"
import { LowCreditsBanner } from "@/components/low-credits-notice"
import { SidebarPrefsProvider, useSidebarPrefs } from "@/hooks/use-sidebar-prefs"
import { cn } from "@/lib/utils"

function MobileTopBar() {
  const { toggleMobile, side } = useSidebarPrefs()

  return (
    <header className="flex h-11 shrink-0 items-center gap-3 border-b border-border bg-card px-3 md:hidden">
      <button
        type="button"
        onClick={toggleMobile}
        className="p-1.5 text-muted-foreground hover:text-foreground"
        aria-label="Abrir menu"
      >
        <Menu className="size-5" strokeWidth={1.5} />
      </button>
      <Link
        href="/dashboard"
        aria-label="DRO/P"
        className={cn("text-foreground hover:opacity-70", side === "right" && "ml-auto")}
      >
        <DropIcon />
      </Link>
    </header>
  )
}

function ChromeInner({ children }: { children: ReactNode }) {
  const { side, ready } = useSidebarPrefs()

  return (
    <div
      className={cn(
        "flex h-svh overflow-hidden bg-background",
        ready && side === "right" && "flex-row-reverse"
      )}
    >
      <AppSidebar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <MobileTopBar />
        <LowCreditsBanner />
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  )
}

/** Authenticated app chrome: fixed viewport sidebar + scrollable main. */
export function AppChrome({ children }: { children: ReactNode }) {
  return (
    <SidebarPrefsProvider>
      <ChromeInner>{children}</ChromeInner>
    </SidebarPrefsProvider>
  )
}
