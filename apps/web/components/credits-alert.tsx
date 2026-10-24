import { cn } from "@/lib/utils"

/** Readable pulse: the bar breathes, the text stays still. */
export function CreditsAlert({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      role="status"
      className={cn(
        "animate-credit-pulse border border-border bg-muted px-3 py-2.5 text-sm",
        className
      )}
    >
      {children}
    </div>
  )
}
