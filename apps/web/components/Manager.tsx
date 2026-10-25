"use client";
import Link from "next/link";
import { useCallback, useEffect, useState, useRef } from "react";
import Login, { useStaff } from "./Login";
import { Activity, ErrorBox, StaffHeader } from "./Shared";
import {
  api,
  err,
  type Staff,
  type Branch,
  type History,
  type Operation,
} from "@/lib/api";
type Summary = {
  cards: number;
  paid_units: number;
  redeemed_units: number;
  operations: number;
  cashiers: number;
};
export default function Manager() {
  const { user, setUser, loading, error } = useStaff();
  if (loading)
    return <main className="standalone-panel">Кабинет ашылып жатыр…</main>;
  if (!user)
    return (
      <>
        <ErrorBox message={error} />
        <Login manager onLogin={setUser} />
      </>
    );
  if (user.role !== "manager")
    return (
      <main className="standalone-panel">
        <h1>Бұл бет басқарушыға арналған</h1>
        <Link className="primary" href="/cashier">
          Кассирге өту
        </Link>
      </main>
    );
  return (
    <ManagerDashboard
      key={user.id}
      user={user}
      onLogout={() => setUser(null)}
    />
  );
}
function ManagerDashboard({
  user,
  onLogout,
}: {
  user: Staff;
  onLogout: () => void;
}) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [history, setHistory] = useState<History>({
    items: [],
    page: 1,
    has_more: false,
  });
  const [tab, setTab] = useState<"operations" | "staff" | "branches">(
    "operations",
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [reversal, setReversal] = useState<{
    op: Operation;
    key: string;
    reason: string;
  } | null>(null);
  const reversalDialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (reversal && !reversalDialog.current?.open)
      reversalDialog.current?.showModal();
    if (!reversal) reversalDialog.current?.close();
  }, [reversal]);
  const reload = useCallback(async () => {
    const [s, u, b, h] = await Promise.all([
      api<Summary>("/manager/summary/"),
      api<Staff[]>("/manager/staff/"),
      api<Branch[]>("/manager/branches/"),
      api<History>("/staff/operations/"),
    ]);
    setSummary(s);
    setStaff(u);
    setBranches(b);
    setHistory(h);
  }, []);
  useEffect(() => {
    if (user?.role === "manager") reload().catch((e) => setError(err(e)));
  }, [user, reload]);
  async function submitAction(action: () => Promise<unknown>, done: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      await reload();
      setNotice(done);
      return true;
    } catch (e) {
      setError(err(e));
      return false;
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="staff-shell manager-shell">
      <StaffHeader user={user} onLogout={onLogout} />
      <main>
        <div className="section-heading">
          <span className="eyebrow">MAGRIBI</span>
          <h1>Басқарушы кабинеті</h1>
        </div>
        <ErrorBox message={error} />
        {notice && (
          <p className="success-box" role="status">
            {notice}
          </p>
        )}
        {summary && (
          <div className="manager-stats">
            <div>
              <strong>{summary.cards}</strong>
              <small>Клиент картасы</small>
            </div>
            <div>
              <strong>{summary.paid_units}</strong>
              <small>Сатып алынған шай</small>
            </div>
            <div>
              <strong>{summary.redeemed_units}</strong>
              <small>Берілген сыйлық</small>
            </div>
            <div>
              <strong>{summary.cashiers}</strong>
              <small>Белсенді кассир</small>
            </div>
          </div>
        )}
        <div
          className="manager-tabs"
          role="group"
          aria-label="Басқару бөлімдері"
        >
          {(
            [
              ["operations", "Операциялар"],
              ["staff", "Қызметкерлер"],
              ["branches", "Филиалдар"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              aria-pressed={tab === id}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </div>
        {tab === "operations" ? (
          <section className="staff-panel">
            <h2>Операциялар тарихы</h2>
            <Activity
              items={history.items}
              manager
              onReverse={(op) => {
                setReversal({ op, key: crypto.randomUUID(), reason: "" });
                setError("");
              }}
            />
            {!history.items.length && (
              <p className="staff-hint">Әзірге операция жоқ.</p>
            )}
            {history.has_more && (
              <button
                className="text-button"
                onClick={async () => {
                  try {
                    const next = await api<History>(
                      `/staff/operations/?page=${history.page + 1}`,
                    );
                    setHistory((h) => ({
                      ...next,
                      items: [...h.items, ...next.items],
                    }));
                  } catch (e) {
                    setError(err(e));
                  }
                }}
              >
                Тағы көрсету
              </button>
            )}
          </section>
        ) : tab === "staff" ? (
          <>
            <section className="staff-panel">
              <h2>Қызметкер қосу</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.currentTarget;
                  const d = new FormData(form);
                  const ok = await submitAction(
                    () =>
                      api("/manager/staff/", {
                        method: "POST",
                        body: Object.fromEntries(d),
                      }),
                    "Қызметкер қосылды",
                  );
                  if (ok) form.reset();
                }}
              >
                <label>
                  Аты
                  <input name="name" required maxLength={100} />
                </label>
                <label>
                  Логин
                  <input
                    name="username"
                    required
                    pattern="[a-zA-Z0-9_.-]{3,80}"
                    autoComplete="off"
                  />
                </label>
                <label>
                  Құпиясөз
                  <input
                    name="password"
                    type="password"
                    minLength={10}
                    maxLength={128}
                    autoComplete="new-password"
                    required
                  />
                </label>
                <label>
                  Филиал
                  <select name="branch_id" required>
                    {branches
                      .filter((b) => b.is_active)
                      .map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Рөлі
                  <select name="role">
                    <option value="cashier">Кассир</option>
                    <option value="manager">Басқарушы</option>
                  </select>
                </label>
                <button className="primary" disabled={busy}>
                  Қызметкерді қосу
                </button>
              </form>
            </section>
            <section className="staff-panel panel-gap">
              <h2>Қызметкерлер</h2>
              {staff.map((s) => (
                <div className="member-row" key={s.id}>
                  <div>
                    <strong>{s.name}</strong>
                    <small>
                      {s.username} ·{" "}
                      {s.role === "manager" ? "Басқарушы" : "Кассир"} ·{" "}
                      {s.branch}
                    </small>
                  </div>
                  <button
                    className="secondary"
                    disabled={busy || s.id === user.id}
                    onClick={() =>
                      void submitAction(
                        () =>
                          api(`/manager/staff/${s.id}/`, {
                            method: "PATCH",
                            body: { is_active: !s.is_active },
                          }),
                        "Мәртебе жаңарды",
                      )
                    }
                  >
                    {s.is_active ? "Бұғаттау" : "Қосу"}
                  </button>
                </div>
              ))}
            </section>
          </>
        ) : (
          <>
            <section className="staff-panel">
              <h2>Филиал қосу</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.currentTarget;
                  const ok = await submitAction(
                    () =>
                      api("/manager/branches/", {
                        method: "POST",
                        body: Object.fromEntries(new FormData(form)),
                      }),
                    "Филиал қосылды",
                  );
                  if (ok) form.reset();
                }}
              >
                <label>
                  Атауы
                  <input name="name" maxLength={100} required />
                </label>
                <label>
                  Мекенжайы
                  <input name="address" maxLength={200} />
                </label>
                <button className="primary" disabled={busy}>
                  Филиалды қосу
                </button>
              </form>
            </section>
            <section className="staff-panel panel-gap">
              {branches.map((b) => (
                <div className="member-row" key={b.id}>
                  <div>
                    <strong>{b.name}</strong>
                    <small>{b.address}</small>
                  </div>
                </div>
              ))}
            </section>
          </>
        )}
        <Link className="text-button" href="/cashier">
          Кассир экранына өту →
        </Link>
      </main>
      <dialog
        ref={reversalDialog}
        className="reversal-dialog"
        aria-labelledby="reversal-title"
        onCancel={(e) => {
          if (busy) e.preventDefault();
          else setReversal(null);
        }}
      >
        {reversal && (
          <section className="staff-panel">
            <h2 id="reversal-title">Операцияны кері қайтару</h2>
            <p className="staff-hint">
              Жазба өшірілмейді. Себебі мен кері қайтару тарихта сақталады.
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const ok = await submitAction(
                  () =>
                    api(`/manager/operations/${reversal.op.id}/reverse/`, {
                      method: "POST",
                      body: {
                        request_key: reversal.key,
                        reason: reversal.reason,
                      },
                    }),
                  "Операция кері қайтарылды",
                );
                if (ok) setReversal(null);
              }}
            >
              <label>
                Себебі
                <textarea
                  autoFocus
                  minLength={5}
                  maxLength={500}
                  required
                  value={reversal.reason}
                  onChange={(e) =>
                    setReversal((r) =>
                      r ? { ...r, reason: e.target.value } : null,
                    )
                  }
                />
              </label>
              <ErrorBox message={error} />
              <div className="confirm-buttons">
                <button
                  className="secondary"
                  type="button"
                  disabled={busy}
                  onClick={() => setReversal(null)}
                >
                  Бас тарту
                </button>
                <button className="primary" disabled={busy}>
                  {busy ? "Сақталуда…" : "Растау"}
                </button>
              </div>
            </form>
          </section>
        )}
      </dialog>
    </div>
  );
}
