import { NextResponse } from "next/server"

import { apiBaseUrl } from "@/lib/api"

type Ctx = { params: Promise<{ token: string }> }

export async function GET(_req: Request, ctx: Ctx) {
  const { token } = await ctx.params
  const resp = await fetch(`${apiBaseUrl()}/api/share/${token}/`, { cache: "no-store" })
  const text = await resp.text()
  return new NextResponse(text, {
    status: resp.status,
    headers: { "Content-Type": "application/json" },
  })
}
