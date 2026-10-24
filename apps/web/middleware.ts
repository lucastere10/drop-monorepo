import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const PUBLIC_PREFIXES = ["/login", "/auth", "/share", "/samples", "/brand", "/interesse"]

function isPublicPath(pathname: string) {
  if (pathname === "/") return true
  if (PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return true
  }
  if (/^\/analyses\/[^/]+$/.test(pathname)) return true
  return false
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname === "/favicon.ico" ||
    pathname.startsWith("/brand/")
  ) {
    return NextResponse.next()
  }

  const access = request.cookies.get("drop_access")?.value
  const refresh = request.cookies.get("drop_refresh")?.value
  const authed = Boolean(access || refresh)

  if (pathname === "/login") {
    return NextResponse.next()
  }

  if (authed && pathname === "/") {
    const url = request.nextUrl.clone()
    url.pathname = "/dashboard"
    return NextResponse.redirect(url)
  }

  if (!isPublicPath(pathname) && !authed) {
    const url = request.nextUrl.clone()
    url.pathname = "/login"
    url.searchParams.set("next", pathname)
    return NextResponse.redirect(url)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|brand/).*)"],
}
