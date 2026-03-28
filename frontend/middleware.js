import { NextResponse } from "next/server";

const PROTECTED_PATHS = ["/monitoring", "/incidents", "/playbook", "/terminal"];

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(`${normalized}${padding}`);

  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

async function verifyJwt(token, secret) {
  const [encodedHeader, encodedPayload, encodedSignature] = token.split(".");

  if (!encodedHeader || !encodedPayload || !encodedSignature) {
    return false;
  }

  let header;
  let payload;

  try {
    header = JSON.parse(new TextDecoder().decode(decodeBase64Url(encodedHeader)));
    payload = JSON.parse(new TextDecoder().decode(decodeBase64Url(encodedPayload)));
  } catch (error) {
    return false;
  }

  if (header.alg !== "HS256" || header.typ !== "JWT") {
    return false;
  }

  if (payload.exp && Date.now() >= payload.exp * 1000) {
    return false;
  }

  const signingInput = new TextEncoder().encode(`${encodedHeader}.${encodedPayload}`);
  const signature = decodeBase64Url(encodedSignature);
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"]
  );

  return crypto.subtle.verify("HMAC", key, signature, signingInput);
}

export async function middleware(request) {
  const token = request.cookies.get("auth_token")?.value;
  const jwtSecret = process.env.JWT_SECRET;
  const { pathname } = request.nextUrl;

  if (!PROTECTED_PATHS.some((protectedPath) => pathname.startsWith(protectedPath))) {
    return NextResponse.next();
  }

  if (!token || !jwtSecret) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  const isValid = await verifyJwt(token, jwtSecret);

  if (isValid) {
    return NextResponse.next();
  }

  const response = NextResponse.redirect(new URL("/", request.url));
  response.cookies.delete("auth_token");
  return response;
}

export const config = {
  matcher: ["/monitoring/:path*", "/incidents/:path*", "/playbook/:path*", "/terminal/:path*"],
};
