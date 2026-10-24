"use client"

import { AnimatePresence, motion } from "motion/react"
import type { ReactNode } from "react"
import { useEffect, useState } from "react"

import { MOTION, prefersReducedMotion } from "@/lib/motion"

export function Sheet({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  children: ReactNode
}) {
  const [reduce, setReduce] = useState(true)

  useEffect(() => {
    setReduce(prefersReducedMotion())
  }, [])

  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onOpenChange(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open, onOpenChange])

  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            type="button"
            aria-label="Fechar"
            className="fixed inset-0 z-40 bg-foreground/20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduce ? 0 : MOTION.fade }}
            onClick={() => onOpenChange(false)}
          />
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label={title}
            className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-background"
            initial={reduce ? false : { x: "100%" }}
            animate={{ x: 0 }}
            exit={reduce ? undefined : { x: "100%" }}
            transition={{ duration: reduce ? 0 : MOTION.fade, ease: "easeOut" }}
          >
            <div className="flex h-11 items-center justify-between border-b border-border px-5">
              <h2 className="truncate font-mono text-[11px] uppercase tracking-widest">{title}</h2>
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground"
              >
                fechar
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-6">{children}</div>
          </motion.aside>
        </>
      ) : null}
    </AnimatePresence>
  )
}
