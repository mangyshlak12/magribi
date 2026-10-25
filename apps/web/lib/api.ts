export type Card = {
  id: string;
  stamps: number;
  rewards: number;
  paid_units: number;
  redeemed_units: number;
};
export type Staff = {
  id: number;
  username: string;
  name: string;
  role: "cashier" | "manager";
  is_active: boolean;
  branch_id: string | null;
  branch: string | null;
};
export type Branch = {
  id: string;
  name: string;
  address: string;
  is_active: boolean;
};
export type Operation = {
  id: string;
  card_id?: string;
  kind: "purchase" | "redeem" | "reversal";
  quantity: number;
  paid_delta: number;
  redeemed_delta: number;
  actor?: string;
  branch: string;
  reason?: string;
  reverses: string | null;
  reversed: boolean;
  created_at: string;
};
export type History = { items: Operation[]; page: number; has_more: boolean };
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
function message(data: unknown): string {
  if (!data) return "Сұраныс орындалмады";
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.map(message).join(" · ");
  if (typeof data === "object") {
    const d = data as Record<string, unknown>;
    return d.detail
      ? message(d.detail)
      : Object.values(d).map(message).join(" · ");
  }
  return String(data);
}
export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string } = {},
): Promise<T> {
  const method = options.method || "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.token) headers.Authorization = `Bearer ${options.token}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET" && !options.token) {
    const c = await fetch("/api/auth/csrf", {
      credentials: "same-origin",
      cache: "no-store",
    });
    if (!c.ok) throw new ApiError(c.status, "Серверге қосылу мүмкін емес");
    headers["X-CSRFToken"] = (await c.json()).csrfToken;
  }
  let response: Response;
  try {
    response = await fetch(`/api${path.replace(/\/(?=\?|$)/, "")}`, {
      method,
      headers,
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "Сервермен байланыс жоқ. Қайта көріңіз");
  }
  const data = await response
    .json()
    .catch(() => ({ detail: "Сервер уақытша қолжетімсіз" }));
  if (!response.ok) throw new ApiError(response.status, message(data));
  return data as T;
}
export function err(e: unknown) {
  return e instanceof Error ? e.message : "Қате орын алды";
}
export function newToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}
export function tokenFrom(value: string) {
  const raw = value.trim();
  if (/^[A-Za-z0-9_-]{43}$/.test(raw)) return raw;
  try {
    const u = new URL(raw);
    const t = new URLSearchParams(u.hash.slice(1)).get("card");
    if (t && /^[A-Za-z0-9_-]{43}$/.test(t)) return t;
  } catch {}
  throw new Error("Клиенттің QR-кодын немесе карта сілтемесін қолданыңыз");
}
export function cardLink(token: string) {
  return `${location.origin}/#card=${token}`;
}
export function dateLabel(at: string) {
  return new Intl.DateTimeFormat("ru-KZ", {
    timeZone: "Asia/Almaty",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(at));
}
