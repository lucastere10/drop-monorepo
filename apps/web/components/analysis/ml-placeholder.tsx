"use client"

import { Badge } from "@/components/ui/badge"

export function MlPlaceholder({
  isAuthenticated = true,
  onInterest,
}: {
  isAuthenticated?: boolean
  onInterest?: () => void
}) {
  return (
    <div className="animate-fade-up max-w-lg space-y-4 py-6">
      <div className="flex items-center gap-3">
        <h2 className="font-bebas text-3xl tracking-wide">Machine Learning</h2>
        <Badge>em implementação</Badge>
      </div>
      {isAuthenticated ? (
        <p className="text-sm leading-relaxed text-muted-foreground">
          Previsões, segmentação e modelos guiados virão depois. Por enquanto, use o resumo, os
          gráficos e o chat para entender os dados.
        </p>
      ) : (
        <>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Esta funcionalidade está disponível apenas para usuários cadastrados. Se fizer sentido pra você, deixe seu interesse.
          </p>
          <button
            type="button"
            onClick={onInterest}
            className="font-mono text-xs tracking-wide hover:underline"
          >
            Tenho interesse
          </button>
        </>
      )}
    </div>
  )
}
