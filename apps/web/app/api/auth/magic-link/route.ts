import { NextResponse } from "next/server"

import { apiBaseUrl } from "@/lib/api"

export async function POST(request: Request) {
  const body = await request.json()
  const resp = await fetch(`${apiBaseUrl()}/api/auth/magic-link/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (resp.status === 204) {
    return new NextResponse(null, { status: 204 })
  }
  const data = await resp.json().catch(() => ({}))
  return NextResponse.json(data, { status: resp.status })
}
