import { NextResponse } from "next/server"

import { apiFetchWithAuth } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

type Ctx = { params: Promise<{ id: string }> }

export async function GET(_req: Request, ctx: Ctx) {
  const { id } = await ctx.params
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth(`/api/jobs/${id}/`)
  const text = await resp.text()
  const out = new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  })
  if (newAccess && newRefresh) {
    setAuthCookies(out, newAccess, newRefresh)
  }
  return out
}
