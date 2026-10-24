"use client"

import {
  Database,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  ScanSearch,
  Shield,
  X,
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect } from "react"

import { useAuth } from "@/components/auth-provider"
import { DropIcon } from "@/components/drop-icon"
import { UserMenu } from "@/components/user-menu"
import { useSidebarPrefs } from "@/hooks/use-sidebar-prefs"
import { cn } from "@/lib/utils"

const NAV = [
  { href: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
  { href: "/analyses", label: "Análises", Icon: ScanSearch },
  { href: "/datasets", label: "Datasets", Icon: Database },
  { href: "/admin", label: "Admin", Icon: Shield, staffOnly: true },
]

export function AppSidebar() {
  const pathname = usePathname()
  const { user } = useAuth()
  const navItems = NAV.filter((item) => !item.staffOnly || user?.is_staff)
  const {
    collapsed,
    side,
    toggleCollapsed,
    mobileOpen,
    setMobileOpen,
  } = useSidebarPrefs()

  // Close drawer on navigation (mobile)
  useEffect(() => {
    setMobileOpen(false)
  }, [pathname, setMobileOpen])

  // Lock body scroll when mobile drawer open
  useEffect(() => {
    if (!mobileOpen) return
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      document.body.style.overflow = prev
    }
  }, [mobileOpen])

  const nav = (
    <nav className="flex flex-1 flex-col gap-0.5 p-2">
      {navItems.map(({ href, label, Icon }) => {
        const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href))
        return (
          <Link
            key={href}
            href={href}
            title={label}
            className={cn(
              "flex items-center gap-2 rounded-none px-2 py-2 font-mono text-[11px] uppercase tracking-widest transition-colors",
              active
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
              collapsed && "md:justify-center md:px-0"
            )}
          >
            <Icon className="size-4 shrink-0" strokeWidth={1.5} />
            <span className={cn(collapsed && "md:hidden")}>{label}</span>
          </Link>
        )
      })}
    </nav>
  )

  const header = (
    <div
      className={cn(
        "flex h-11 items-center border-b border-border",
        collapsed ? "justify-center px-1 md:justify-center" : "justify-between px-3",
        "max-md:justify-between max-md:px-3"
      )}
    >
      <Link
        href="/dashboard"
        aria-label="DRO/P"
        className={cn("text-foreground hover:opacity-70", collapsed && "md:hidden")}
      >
        <DropIcon />
      </Link>
      {/* Desktop collapse */}
      <button
        type="button"
        onClick={toggleCollapsed}
        className="hidden p-1.5 text-muted-foreground hover:text-foreground md:inline-flex"
        aria-label={collapsed ? "Expandir sidebar" : "Recolher sidebar"}
      >
        {collapsed ? (
          <PanelLeftOpen className="size-4" strokeWidth={1.5} />
        ) : (
          <PanelLeftClose className="size-4" strokeWidth={1.5} />
        )}
      </button>
      {/* Mobile close */}
      <button
        type="button"
        onClick={() => setMobileOpen(false)}
        className="p-1.5 text-muted-foreground hover:text-foreground md:hidden"
        aria-label="Fechar menu"
      >
        <X className="size-4" strokeWidth={1.5} />
      </button>
    </div>
  )

  const mobileHiddenClass =
    side === "left" ? "-translate-x-full" : "translate-x-full"

  return (
    <>
      {/* Mobile backdrop */}
      <button
        type="button"
        aria-label="Fechar menu"
        className={cn(
          "fixed inset-0 z-40 bg-foreground/25 transition-opacity md:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={() => setMobileOpen(false)}
      />

      <aside
        className={cn(
          "flex h-svh shrink-0 flex-col border-border bg-card",
          "fixed inset-y-0 z-50 w-64 transition-transform duration-200 ease-out md:static md:z-auto md:translate-x-0 md:transition-none",
          side === "left" ? "left-0 border-r" : "right-0 border-l",
          mobileOpen ? "translate-x-0" : mobileHiddenClass,
          collapsed ? "md:w-14" : "md:w-52"
        )}
      >
        {header}
        {nav}
        <UserMenu side={side} collapsed={collapsed} />
      </aside>
    </>
  )
}
