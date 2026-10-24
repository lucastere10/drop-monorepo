import Link from "next/link"

import { CreditsBadge } from "@/components/credits-badge"

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-svh">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/" className="font-[family-name:var(--font-display)] text-lg tracking-tight">
              DROP
            </Link>
            <Link href="/analyses" className="text-muted-foreground hover:text-foreground">
              Análises
            </Link>
            <Link href="/profile" className="text-muted-foreground hover:text-foreground">
              Perfil
            </Link>
          </nav>
          <CreditsBadge />
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  )
}
