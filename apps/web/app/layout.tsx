import type { Metadata } from "next"
import { Bebas_Neue, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google"

import "./globals.css"
import { cn } from "@/lib/utils"
import { Providers } from "@/components/providers"

const bebas = Bebas_Neue({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-bebas",
})

const plex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
})

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: "DRO/P",
  description: "Dados limpos, Insights claros.",
  icons: {
    icon: [
      {
        url: "/brand/icon-black.svg",
        type: "image/svg+xml",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/brand/icon-white.svg",
        type: "image/svg+xml",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/brand/favicon-64-light.png",
        type: "image/png",
        sizes: "64x64",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/brand/favicon-64-dark.png",
        type: "image/png",
        sizes: "64x64",
        media: "(prefers-color-scheme: dark)",
      },
    ],
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="pt-BR"
      suppressHydrationWarning
      className={cn("antialiased", bebas.variable, plex.variable, plexMono.variable, "font-sans")}
    >
      <body className="min-h-svh bg-background text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
