import { NextResponse } from "next/server"

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/api"

const isProd = process.env.NODE_ENV === "production"

export function setAuthCookies(res: NextResponse, access: string, refresh: string) {
  res.cookies.set(ACCESS_COOKIE, access, {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 15,
  })
  res.cookies.set(REFRESH_COOKIE, refresh, {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 14,
  })
}

export function clearAuthCookies(res: NextResponse) {
  res.cookies.set(ACCESS_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 })
  res.cookies.set(REFRESH_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 })
}
