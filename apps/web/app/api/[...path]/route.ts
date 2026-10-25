import { NextRequest } from "next/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const base = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
  const destination = new URL(
    `/api/${path.map(encodeURIComponent).join("/")}/${request.nextUrl.search}`,
    base,
  );
  const headers = new Headers();
  for (const key of [
    "accept",
    "content-type",
    "cookie",
    "authorization",
    "x-csrftoken",
    "origin",
    "referer",
  ]) {
    const value = request.headers.get(key);
    if (value) headers.set(key, value);
  }
  let body: Uint8Array | undefined;
  if (!["GET", "HEAD"].includes(request.method) && request.body) {
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 32768) {
        await reader.cancel();
        return Response.json({ detail: "Сұраныс тым үлкен" }, { status: 413 });
      }
      chunks.push(value);
    }
    body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.length;
    }
  }
  try {
    const upstream = await fetch(destination, {
      method: request.method,
      headers,
      body: body as BodyInit | undefined,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(15000),
    });
    const out = new Headers({
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
    });
    for (const key of ["content-type", "location", "retry-after"]) {
      const value = upstream.headers.get(key);
      if (value) out.set(key, value);
    }
    for (const cookie of upstream.headers.getSetCookie())
      out.append("set-cookie", cookie);
    return new Response(upstream.body, {
      status: upstream.status,
      headers: out,
    });
  } catch {
    return Response.json(
      { detail: "Сервер уақытша қолжетімсіз. Қайта көріңіз" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
export {
  proxy as GET,
  proxy as POST,
  proxy as PATCH,
  proxy as DELETE,
  proxy as OPTIONS,
};
