"use client"

import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/** Minimal tooltip via native title + accessible hint. */
export function Tooltip({
  content,
  children,
  className,
}: {
  content: string
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn("inline-flex cursor-help", className)}
      title={content}
      aria-label={content}
    >
      {children}
    </span>
  )
}
