import { NextResponse } from "next/server"

import { apiFetchWithAuth } from "@/lib/api"
import { setAuthCookies } from "@/lib/auth-cookies"

type Ctx = { params: Promise<{ id: string; action: string }> }

const ACTION_MAP: Record<string, string> = {
  overview: "overview",
  insights: "insights",
  charts: "charts",
  dashboard: "dashboard",
  chat: "chat",
  claim: "claim",
}

export async function POST(request: Request, ctx: Ctx) {
  const { id, action } = await ctx.params
  const mapped = ACTION_MAP[action]
  if (!mapped) {
    return NextResponse.json({ code: "not_found", message: "Ação inválida." }, { status: 404 })
  }
  const body = await request.text()
  const { resp, newAccess, newRefresh } = await apiFetchWithAuth(
    `/api/analyses/${id}/${mapped}/`,
    {
      method: "POST",
      body: body || "{}",
    }
  )
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
