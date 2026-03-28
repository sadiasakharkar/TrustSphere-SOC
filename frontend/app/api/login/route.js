import { NextResponse } from "next/server";

const BACKEND_AUTH_URL =
  process.env.TRUSTSPHERE_BACKEND_URL || "http://127.0.0.1:8000";
const ENABLE_DEMO_FALLBACK =
  (process.env.TRUSTSPHERE_ENABLE_DEMO_LOGIN_FALLBACK || "true").toLowerCase() !== "false";

function extractCookieValue(setCookieHeader, cookieName) {
  if (!setCookieHeader) {
    return null;
  }

  const pattern = new RegExp(`${cookieName}=([^;]+)`);
  const match = setCookieHeader.match(pattern);
  return match ? match[1] : null;
}

function buildDemoResponse(email, message) {
  const response = NextResponse.json(
    {
      message,
      user: {
        email,
        role: "analyst",
        auth_mode: "frontend_demo_fallback",
      },
    },
    { status: 200 }
  );

  response.cookies.set({
    name: "trustsphere_session",
    value: `demo-${Buffer.from(email).toString("base64url")}`,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12,
  });

  return response;
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

    let upstream;
    try {
      upstream = await fetch(`${BACKEND_AUTH_URL}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        cache: "no-store",
      });
    } catch (error) {
      if (ENABLE_DEMO_FALLBACK) {
        return buildDemoResponse(
          payload.email,
          "Login successful. TrustSphere is running in local demo mode because the backend is unavailable."
        );
      }
      throw error;
    }

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
    if (ENABLE_DEMO_FALLBACK) {
      try {
        const payload = await request.clone().json();
        if (payload?.email && payload?.password) {
          return buildDemoResponse(
            payload.email,
            "Login successful. TrustSphere is running in local demo mode."
          );
        }
      } catch {
        // ignore and return the original error below
      }
    }

    return NextResponse.json(
      { error: "Unable to connect to the TrustSphere backend." },
      { status: 500 }
    );
  }
}
