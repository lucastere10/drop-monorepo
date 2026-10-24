"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"

import { useAuth } from "@/components/auth-provider"
import { DropIcon } from "@/components/drop-icon"

export function SiteHeader({ rightExtra }: { rightExtra?: React.ReactNode }) {
  const { user, isAuthenticated, loading, logout } = useAuth()
  const router = useRouter()

  async function onLogout() {
    await logout()
    router.push("/")
    router.refresh()
  }

  const label = user?.first_name?.trim() || user?.email?.split("@")[0] || "conta"

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-12 max-w-2xl items-center justify-between px-5 md:max-w-6xl">
        <Link href="/" aria-label="DRO/P" className="text-foreground hover:opacity-70">
          <DropIcon />
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {rightExtra}
          {loading ? (
            <span className="font-mono text-[10px] text-muted-foreground">…</span>
          ) : isAuthenticated ? (
            <>
              <Link
                href="/dashboard"
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                dashboard
              </Link>
              <Link
                href="/profile"
                className="text-muted-foreground hover:text-foreground"
                title={user?.email}
              >
                {label}
              </Link>
              <button
                type="button"
                onClick={() => void onLogout()}
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                sair
              </button>
            </>
          ) : (
            <Link href="/login" className="text-muted-foreground hover:text-foreground">
              Entrar
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
