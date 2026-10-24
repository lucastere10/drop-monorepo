"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { ArrowLeft, LogOut, Mail, Shield, UserRound } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { LowCreditsNote } from "@/components/low-credits-notice"
import { Button, buttonVariants } from "@/components/ui/button"
import { useCredits } from "@/hooks/use-credits"
import { cn } from "@/lib/utils"

export default function ProfilePage() {
  const router = useRouter()
  const { logout } = useAuth()
  const { data } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const res = await fetch("/api/me")
      if (!res.ok) throw new Error("auth")
      return res.json()
    },
  })
  const credits = useCredits()
  const balance = credits.data?.balance ?? data?.credits_balance

  const rows = [
    {
      Icon: UserRound,
      label: "nome",
      value: data?.first_name || "—",
    },
    {
      Icon: Mail,
      label: "email",
      value: data?.email || "—",
    },
    {
      Icon: Shield,
      label: "tier",
      value: credits.data?.tier?.slug || data?.tier || "—",
    },
  ]

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
        <h1 className="font-bebas text-4xl tracking-wide">Perfil</h1>
      </div>

      <div className="mt-8 border border-border px-4 py-4">
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          saldo
        </p>
        <p className="mt-1 font-bebas text-5xl leading-none tracking-wide">
          {typeof balance === "number" ? balance : "—"}
          <span className="ml-2 align-middle font-sans text-sm font-normal tracking-normal text-muted-foreground">
            {typeof balance === "number" ? (balance === 1 ? "crédito" : "créditos") : "créditos"}
          </span>
        </p>
        {typeof balance === "number" ? <LowCreditsNote balance={balance} /> : null}
      </div>

      <dl className="mt-4 divide-y divide-border border border-border">
        {rows.map(({ Icon, label, value }) => (
          <div key={label} className="flex items-center gap-3 px-4 py-3.5">
            <Icon className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.5} />
            <dt className="w-16 shrink-0 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {label}
            </dt>
            <dd className="min-w-0 flex-1 truncate text-right text-sm">{value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-8 flex flex-col gap-2 sm:flex-row">
        <Link
          href="/dashboard"
          className={cn(
            buttonVariants({ variant: "outline" }),
            "h-9 flex-1 justify-center gap-2 rounded-none"
          )}
        >
          Dashboard
        </Link>
        <Button
          variant="outline"
          className="h-9 flex-1 justify-center gap-2 rounded-none"
          onClick={async () => {
            await logout()
            router.push("/")
          }}
        >
          <LogOut className="size-4" strokeWidth={1.5} />
          Logout
        </Button>
      </div>
    </div>
  )
}
