import { NextResponse } from "next/server"

import { apiFetchWithAuth } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

type Ctx = { params: Promise<{ id: string }> }

async function proxy(path: string, init?: RequestInit) {
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth(path, init)
  // 204/205/304 cannot carry a body in the Fetch Response constructor
  const empty = resp.status === 204 || resp.status === 205 || resp.status === 304
  const text = empty ? null : await resp.text()
  const headers = empty
    ? undefined
    : { "Content-Type": resp.headers.get("Content-Type") || "application/json" }
  const out = new NextResponse(text, { status: resp.status, headers })
  if (newAccess && newRefresh) {
    setAuthCookies(out, newAccess, newRefresh)
  }
  return out
}

export async function GET(_req: Request, ctx: Ctx) {
  const { id } = await ctx.params
  return proxy(`/api/analyses/${id}/`)
}

export async function PATCH(request: Request, ctx: Ctx) {
  const { id } = await ctx.params
  const body = await request.text()
  return proxy(`/api/analyses/${id}/`, { method: "PATCH", body })
}

export async function DELETE(_req: Request, ctx: Ctx) {
  const { id } = await ctx.params
  return proxy(`/api/analyses/${id}/`, { method: "DELETE" })
}
