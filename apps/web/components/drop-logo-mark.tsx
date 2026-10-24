"use client"

import { animate, motion, useMotionValue } from "motion/react"
import { useEffect, useRef, useState } from "react"

import { cn } from "@/lib/utils"

// Cubic bezier equivalente ao easing Apple/Linear — aceleração rápida, deaceleração suave
const EASE_PREMIUM = [0.22, 1, 0.36, 1] as const

type Phase = "blink" | "rotate" | "glow" | "reveal" | "done"

interface DropLogoMarkProps {
  readonly animate?: boolean
  readonly className?: string
  readonly onComplete?: () => void
}

export function DropLogoMark({
  animate: shouldAnimate = false,
  className,
  onComplete,
}: DropLogoMarkProps) {
  const [phase, setPhase] = useState<Phase>(shouldAnimate ? "blink" : "done")
  const rotate = useMotionValue(0)
  const cancelled = useRef(false)

  useEffect(() => {
    if (!shouldAnimate) return

    cancelled.current = false

    const run = async () => {
      // Fase 1: cursor piscando (0–250ms)
      await new Promise<void>((r) => setTimeout(r, 250))
      if (cancelled.current) return

      // Fase 2: rotaciona | → /  (250–450ms)
      setPhase("rotate")
      await animate(rotate, 45, {
        duration: 0.2,
        ease: EASE_PREMIUM,
      })
      if (cancelled.current) return

      // Fase 3: glow (450–650ms)
      setPhase("glow")
      await new Promise<void>((r) => setTimeout(r, 200))
      if (cancelled.current) return

      // Fase 4: reveal DRO e P (650–1050ms)
      setPhase("reveal")
      await new Promise<void>((r) => setTimeout(r, 420))
      if (cancelled.current) return

      // Fase 5: done (1050ms+)
      setPhase("done")
      onComplete?.()
    }

    void run()

    return () => {
      cancelled.current = true
    }
  }, [shouldAnimate, onComplete, rotate])

  const isDone = phase === "done"
  const isRevealing = phase === "reveal" || isDone
  const isGlowing = phase === "glow"

  let droAnimate: Record<string, unknown> = {}
  if (isRevealing) droAnimate = { opacity: 1, x: 0 }
  else if (shouldAnimate) droAnimate = { opacity: 0, x: 10 }

  let pAnimate: Record<string, unknown> = {}
  if (isRevealing) pAnimate = { opacity: 1, x: 0 }
  else if (shouldAnimate) pAnimate = { opacity: 0, x: -10 }

  const glowAnimate = isGlowing
    ? {
        filter: [
          "drop-shadow(0 0 0px transparent)",
          "drop-shadow(0 0 12px currentColor)",
          "drop-shadow(0 0 0px transparent)",
        ],
      }
    : { filter: "drop-shadow(0 0 0px transparent)" }

  const glowTransition = isGlowing
    ? { duration: 0.2, times: [0, 0.5, 1] }
    : { duration: 0.15 }

  return (
    <span
      className={cn(
        "font-bebas inline-flex items-center tracking-[0.04em]",
        className,
      )}
    >
      {/* DRO — emerge da esquerda do slash */}
      <motion.span
        initial={shouldAnimate ? { opacity: 0, x: 10 } : false}
        animate={droAnimate}
        transition={{ duration: 0.38, ease: EASE_PREMIUM }}
        style={{ display: "inline-block" }}
      >
        DRO
      </motion.span>

      {/* Cursor | → slash / */}
      <motion.span
        style={{
          display: "inline-block",
          originX: "50%",
          originY: "50%",
          rotate: shouldAnimate ? rotate : 0,
        }}
        animate={glowAnimate}
        transition={glowTransition}
      >
        {phase === "blink" ? (
          <motion.span
            animate={{ opacity: [1, 0, 1, 0, 1] }}
            transition={{ duration: 0.25, times: [0, 0.25, 0.5, 0.75, 1] }}
          >
            |
          </motion.span>
        ) : (
          "/"
        )}
      </motion.span>

      {/* P — emerge à direita do slash */}
      <motion.span
        initial={shouldAnimate ? { opacity: 0, x: -10 } : false}
        animate={pAnimate}
        transition={{ duration: 0.38, ease: EASE_PREMIUM }}
        style={{ display: "inline-block" }}
      >
        P
      </motion.span>
    </span>
  )
}
