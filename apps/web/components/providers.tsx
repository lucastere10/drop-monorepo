"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

import { AuthProvider } from "@/components/auth-provider"
import { DashboardWatchProvider } from "@/components/dashboard-watch"
import { OnboardingDialog } from "@/components/onboarding-dialog"
import { ThemeProvider } from "@/components/theme-provider"

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <AuthProvider>
          <DashboardWatchProvider>
            {children}
            <OnboardingDialog />
          </DashboardWatchProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
