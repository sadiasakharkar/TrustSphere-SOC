import { NextResponse } from "next/server";

const BACKEND_AUTH_URL =
  process.env.TRUSTSPHERE_BACKEND_URL || "http://127.0.0.1:8000";

function extractCookieValue(setCookieHeader, cookieName) {
  if (!setCookieHeader) {
    return null;
  }

  const pattern = new RegExp(`${cookieName}=([^;]+)`);
  const match = setCookieHeader.match(pattern);
  return match ? match[1] : null;
}

export async function POST(request) {
  try {
    const payload = await request.json();

    if (!payload?.email || !payload?.password) {
      return NextResponse.json(
        { error: "Email and password are required." },
        { status: 400 }
      );
    }

    const upstream = await fetch(`${BACKEND_AUTH_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const data = await upstream.json().catch(() => ({
      error: "Unable to parse backend login response.",
    }));

    if (!upstream.ok) {
      return NextResponse.json(
        { error: data.detail || data.error || "Unable to sign in." },
        { status: upstream.status }
      );
    }

    const sessionToken = extractCookieValue(
      upstream.headers.get("set-cookie"),
      "trustsphere_session"
    );

    const response = NextResponse.json(data, { status: 200 });

    if (sessionToken) {
      response.cookies.set({
        name: "trustsphere_session",
        value: sessionToken,
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: 60 * 60 * 12,
      });
    }

    return response;
  } catch (error) {
    return NextResponse.json(
      { error: "Unable to connect to the TrustSphere backend." },
      { status: 500 }
    );
  }
}
