import { NextResponse } from "next/server";

const PROTECTED_PATHS = ["/monitoring", "/incidents", "/playbook", "/terminal"];

export async function middleware(request) {
  const sessionToken = request.cookies.get("trustsphere_session")?.value;
  const { pathname } = request.nextUrl;

  if (!PROTECTED_PATHS.some((protectedPath) => pathname.startsWith(protectedPath))) {
    return NextResponse.next();
  }

  if (!sessionToken) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/monitoring/:path*", "/incidents/:path*", "/playbook/:path*", "/terminal/:path*"],
};
