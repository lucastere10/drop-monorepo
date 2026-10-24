"use client"

import { AnimatePresence, motion } from "motion/react"
import { useEffect, useState } from "react"

import { DropLogoMark } from "@/components/drop-logo-mark"
import { prefersReducedMotion } from "@/lib/motion"

const SESSION_KEY = "drop-intro-seen"

function shouldSkipIntro(): boolean {
  if (typeof window === "undefined") return true
  if (prefersReducedMotion()) return true
  return sessionStorage.getItem(SESSION_KEY) === "1"
}

interface DropIntroOverlayProps {
  readonly onDone?: () => void
}

export function DropIntroOverlay({ onDone }: DropIntroOverlayProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (shouldSkipIntro()) {
      onDone?.()
      return
    }
    setVisible(true)
  }, [onDone])

  function handleAnimComplete() {
    sessionStorage.setItem(SESSION_KEY, "1")
    setTimeout(() => {
      setVisible(false)
      onDone?.()
    }, 320)
  }

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="drop-intro"
          className="fixed inset-0 z-50 flex items-center justify-center bg-background"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          aria-hidden
        >
          <DropLogoMark
            animate
            className="text-7xl md:text-8xl"
            onComplete={handleAnimComplete}
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
}
