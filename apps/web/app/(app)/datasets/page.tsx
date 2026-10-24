import { Badge } from "@/components/ui/badge"

export default function DatasetsPage() {
  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <div className="flex items-center gap-3">
        <h1 className="font-bebas text-4xl tracking-wide">Datasets</h1>
        <Badge>em breve</Badge>
      </div>
      <p className="mt-6 max-w-md text-sm leading-relaxed text-muted-foreground">
        Em breve você poderá reutilizar arquivos, acompanhar qualidade e conectar datasets a novas
        análises — sem reenviar o mesmo CSV toda vez.
      </p>
    </div>
  )
}
