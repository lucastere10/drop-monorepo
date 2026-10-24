"use client"

import { useEffect, useRef, useState } from "react"

import {
  MOTION,
  hasOverviewTyped,
  markOverviewTyped,
  prefersReducedMotion,
  stripMarkdownLight,
} from "@/lib/motion"

export function TypewriterText({
  text,
  storageKey,
  analysisId,
  className,
  onDone,
}: {
  text: string
  storageKey?: string
  analysisId?: string
  className?: string
  onDone?: () => void
}) {
  const plain = stripMarkdownLight(text)
  const onDoneRef = useRef(onDone)
  onDoneRef.current = onDone

  const [display, setDisplay] = useState("")
  const [done, setDone] = useState(false)

  useEffect(() => {
    function finish() {
      setDisplay(plain)
      setDone(true)
      if (analysisId) markOverviewTyped(analysisId)
      if (storageKey) sessionStorage.setItem(storageKey, "1")
      onDoneRef.current?.()
    }

    const skip =
      prefersReducedMotion() ||
      (analysisId ? hasOverviewTyped(analysisId) : false) ||
      (storageKey ? sessionStorage.getItem(storageKey) === "1" : false)

    if (skip || !plain) {
      finish()
      return
    }

    setDisplay("")
    setDone(false)
    let i = 0
    const id = window.setInterval(() => {
      i += 1
      setDisplay(plain.slice(0, i))
      if (i >= plain.length) {
        window.clearInterval(id)
        finish()
      }
    }, MOTION.typewriterMs)

    return () => window.clearInterval(id)
  }, [plain, analysisId, storageKey])

  return (
    <p className={className}>
      {display}
      {!done ? <span className="animate-stream-blink">_</span> : null}
    </p>
  )
}
