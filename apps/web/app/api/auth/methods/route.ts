import { NextResponse } from "next/server"

import { apiBaseUrl } from "@/lib/api"

export async function GET() {
  const resp = await fetch(`${apiBaseUrl()}/api/auth/methods/`, { cache: "no-store" })
  const data = await resp.json().catch(() => ({ methods: ["magic_link"] }))
  return NextResponse.json(data, { status: resp.status })
}
