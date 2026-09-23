import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { ACCESS_COOKIE, signInRedirect } from "@/lib/session";

export function middleware(request: NextRequest) {
  const hasToken = Boolean(request.cookies.get(ACCESS_COOKIE)?.value);
  const target = signInRedirect(request.nextUrl.pathname, hasToken);
  if (target) {
    const url = request.nextUrl.clone();
    url.pathname = target;
    url.search = "";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*"],
};
