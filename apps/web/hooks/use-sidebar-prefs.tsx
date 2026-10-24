"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

const COLLAPSED_KEY = "drop:sidebar-collapsed"
const SIDE_KEY = "drop:sidebar-side"

export type SidebarSide = "left" | "right"

type SidebarPrefsValue = {
  collapsed: boolean
  side: SidebarSide
  ready: boolean
  /** Mobile drawer open (overlay). Independent of desktop collapsed. */
  mobileOpen: boolean
  setCollapsed: (v: boolean) => void
  setSide: (s: SidebarSide) => void
  toggleCollapsed: () => void
  setMobileOpen: (v: boolean) => void
  toggleMobile: () => void
}

const SidebarPrefsContext = createContext<SidebarPrefsValue | null>(null)

export function SidebarPrefsProvider({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsedState] = useState(false)
  const [side, setSideState] = useState<SidebarSide>("left")
  const [mobileOpen, setMobileOpen] = useState(false)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try {
      setCollapsedState(localStorage.getItem(COLLAPSED_KEY) === "1")
      const s = localStorage.getItem(SIDE_KEY)
      if (s === "left" || s === "right") setSideState(s)
    } catch {
      /* ignore */
    }
    setReady(true)
  }, [])

  // Close mobile drawer on resize to desktop
  useEffect(() => {
    function onResize() {
      if (window.matchMedia("(min-width: 768px)").matches) {
        setMobileOpen(false)
      }
    }
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  const setCollapsed = useCallback((v: boolean) => {
    setCollapsedState(v)
    try {
      localStorage.setItem(COLLAPSED_KEY, v ? "1" : "0")
    } catch {
      /* ignore */
    }
  }, [])

  const setSide = useCallback((v: SidebarSide) => {
    setSideState(v)
    try {
      localStorage.setItem(SIDE_KEY, v)
    } catch {
      /* ignore */
    }
  }, [])

  const toggleCollapsed = useCallback(() => {
    setCollapsedState((prev) => {
      const next = !prev
      try {
        localStorage.setItem(COLLAPSED_KEY, next ? "1" : "0")
      } catch {
        /* ignore */
      }
      return next
    })
  }, [])

  const toggleMobile = useCallback(() => {
    setMobileOpen((v) => !v)
  }, [])

  const value = useMemo(
    () => ({
      collapsed,
      side,
      ready,
      mobileOpen,
      setCollapsed,
      setSide,
      toggleCollapsed,
      setMobileOpen,
      toggleMobile,
    }),
    [
      collapsed,
      side,
      ready,
      mobileOpen,
      setCollapsed,
      setSide,
      toggleCollapsed,
      toggleMobile,
    ]
  )

  return (
    <SidebarPrefsContext.Provider value={value}>{children}</SidebarPrefsContext.Provider>
  )
}

export function useSidebarPrefs() {
  const ctx = useContext(SidebarPrefsContext)
  if (!ctx) throw new Error("useSidebarPrefs must be used within SidebarPrefsProvider")
  return ctx
}
