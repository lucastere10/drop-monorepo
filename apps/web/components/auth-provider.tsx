"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createContext, useCallback, useContext, useMemo } from "react"

export type AuthUser = {
  id: string
  email: string
  first_name: string
  last_name: string
  is_staff?: boolean
  credits_balance?: number
  tier?: string
}

type AuthContextValue = {
  user: AuthUser | null
  loading: boolean
  isAuthenticated: boolean
  needsOnboarding: boolean
  refresh: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient()
  const { data, isLoading, refetch, isFetched } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const res = await fetch("/api/me")
      if (res.status === 401) return null
      if (!res.ok) return null
      return (await res.json()) as AuthUser
    },
    staleTime: 30_000,
    retry: false,
  })

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" })
    qc.setQueryData(["auth", "me"], null)
    await qc.invalidateQueries({ queryKey: ["auth"] })
    await qc.invalidateQueries({ queryKey: ["credits"] })
    await qc.invalidateQueries({ queryKey: ["analyses"] })
  }, [qc])

  const refresh = useCallback(async () => {
    await refetch()
  }, [refetch])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: data ?? null,
      loading: isLoading && !isFetched,
      isAuthenticated: Boolean(data?.id),
      needsOnboarding: Boolean(data?.id && !(data.first_name || "").trim()),
      refresh,
      logout,
    }),
    [data, isLoading, isFetched, refresh, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
