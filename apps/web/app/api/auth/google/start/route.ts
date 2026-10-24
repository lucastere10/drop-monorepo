import { NextResponse } from "next/server"

import { apiBaseUrl } from "@/lib/api"

export async function GET() {
  const resp = await fetch(`${apiBaseUrl()}/api/auth/google/start/`, { cache: "no-store" })
  const data = await resp.json()
  return NextResponse.json(data, { status: resp.status })
}
