"use client";
import { useEffect, useState } from "react";
import type { Staff } from "@/lib/api";
import { api, err, ApiError } from "@/lib/api";
import { Brand, ErrorBox } from "./Shared";
export function useStaff() {
  const [user, setUser] = useState<Staff | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Staff>("/auth/me/")
      .then(setUser)
      .catch((e) => {
        if (!(e instanceof ApiError) || ![401, 403].includes(e.status))
          setError(err(e));
      })
      .finally(() => setLoading(false));
  }, []);
  return { user, setUser, loading, error };
}
export default function Login({
  onLogin,
  manager = false,
}: {
  onLogin: (user: Staff) => void;
  manager?: boolean;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <main className="standalone-panel login-panel">
      <Brand staff />
      <div className="section-heading">
        <span className="eyebrow">MAGRIBI</span>
        <h1>{manager ? "Басқарушы кабинеті" : "Кассир кабинеті"}</h1>
      </div>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const data = new FormData(e.currentTarget);
          setBusy(true);
          setError("");
          try {
            onLogin(
              await api<Staff>("/auth/login/", {
                method: "POST",
                body: {
                  username: data.get("username"),
                  password: data.get("password"),
                },
              }),
            );
          } catch (e) {
            setError(err(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Логин
          <input
            name="username"
            autoComplete="username"
            required
            maxLength={150}
          />
        </label>
        <label>
          Құпиясөз
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={128}
          />
        </label>
        <ErrorBox message={error} />
        <button className="primary" disabled={busy}>
          {busy ? "Кіру…" : "Кіру"}
        </button>
      </form>
      <p className="staff-disclaimer">
        Аккаунтты басқарушы береді. Клиентке тіркелудің қажеті жоқ.
      </p>
    </main>
  );
}
