"use client"

import Link from "next/link"
import { X } from "lucide-react"
import { useEffect, useState } from "react"

import { useCredits } from "@/hooks/use-credits"
import {
  isLowBalance,
  LOW_CREDITS_DISMISS_KEY,
  lowCreditsMessage,
} from "@/lib/credits"

function readDismissedBalance() {
  const raw = localStorage.getItem(LOW_CREDITS_DISMISS_KEY)
  if (raw === null || raw === "") return null
  const value = Number(raw)
  return Number.isFinite(value) ? value : null
}

function LowCreditsText({ balance }: { balance: number }) {
  return (
    <p className="text-sm">
      {lowCreditsMessage(balance)}{" "}
      <Link href="/plan" className="underline underline-offset-4">
        O uso é medido em créditos.
      </Link>
    </p>
  )
}

/** Persistent note for the profile page — not dismissible. */
export function LowCreditsNote({ balance }: { balance: number }) {
  if (!isLowBalance(balance)) return null
  return (
    <div className="animate-credit-pulse mt-3 border border-border bg-muted px-3 py-2.5">
      <LowCreditsText balance={balance} />
    </div>
  )
}

/** Top-of-app warning. Dismissal sticks until the balance changes. */
export function LowCreditsBanner() {
  const { data } = useCredits()
  const balance = data?.balance
  const [dismissedBalance, setDismissedBalance] = useState<number | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setDismissedBalance(readDismissedBalance())
    setReady(true)
  }, [])

  useEffect(() => {
    if (balance === undefined || isLowBalance(balance)) return
    localStorage.removeItem(LOW_CREDITS_DISMISS_KEY)
    setDismissedBalance(null)
  }, [balance])

  if (!ready || balance === undefined || !isLowBalance(balance)) return null
  if (dismissedBalance === balance) return null

  function dismiss() {
    localStorage.setItem(LOW_CREDITS_DISMISS_KEY, String(balance))
    setDismissedBalance(balance ?? null)
  }

  return (
    <div className="animate-credit-pulse flex items-start justify-between gap-3 border-b border-border bg-muted px-4 py-2.5">
      <LowCreditsText balance={balance} />
      <button
        type="button"
        onClick={dismiss}
        className="shrink-0 p-1 text-muted-foreground hover:text-foreground"
        aria-label="Fechar aviso de créditos"
      >
        <X className="size-4" strokeWidth={1.5} />
      </button>
    </div>
  )
}
