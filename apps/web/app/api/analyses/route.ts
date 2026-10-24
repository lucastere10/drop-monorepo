import { NextResponse } from "next/server"

import { apiFetchWithAuth } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

async function proxy(path: string, init?: RequestInit) {
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth(path, init)
  const text = await resp.text()
  const out = new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": resp.headers.get("Content-Type") || "application/json" },
  })
  if (newAccess && newRefresh) {
    setAuthCookies(out, newAccess, newRefresh)
  }
  return out
}

export async function GET() {
  return proxy("/api/analyses/")
}

export async function POST(request: Request) {
  const form = await request.formData()
  return proxy("/api/analyses/", { method: "POST", body: form, headers: {} })
}
