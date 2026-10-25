"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import Login, { useStaff } from "./Login";
import Scanner from "./Scanner";
import { Activity, ErrorBox, Icon, StaffHeader } from "./Shared";
import {
  api,
  err,
  tokenFrom,
  type Card,
  type History,
  type Operation,
  type Staff,
} from "@/lib/api";
export default function Cashier() {
  const { user, setUser, loading, error } = useStaff();
  if (loading)
    return <main className="standalone-panel">Кабинет ашылып жатыр…</main>;
  if (!user)
    return (
      <>
        <ErrorBox message={error} />
        <Login onLogin={setUser} />
      </>
    );
  return (
    <CashierDashboard
      key={user.id}
      user={user}
      onLogout={() => setUser(null)}
    />
  );
}
function CashierDashboard({
  user,
  onLogout,
}: {
  user: Staff;
  onLogout: () => void;
}) {
  const [card, setCard] = useState<Card | null>(null);
  const [lookupText, setLookupText] = useState("");
  const [cardToken, setCardToken] = useState("");
  const [qty, setQty] = useState(1);
  const [confirmation, setConfirmation] = useState<{
    kind: "purchase" | "redeem";
    key: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [history, setHistory] = useState<History>({
    items: [],
    page: 1,
    has_more: false,
  });
  const [scanning, setScanning] = useState(false);
  const refreshOps = useCallback(
    () => api<History>("/staff/operations/").then(setHistory),
    [],
  );
  useEffect(() => {
    if (user) refreshOps().catch((e) => setError(err(e)));
  }, [user, refreshOps]);
  const lookup = useCallback(async (value: string) => {
    setScanning(false);
    setError("");
    setBusy(true);
    try {
      const token = tokenFrom(value);
      const result = await api<Card>("/staff/lookup/", {
        method: "POST",
        body: { token },
      });
      setCard(result);
      setCardToken(token);
      setQty(1);
      setConfirmation(null);
      setLookupText("");
      setNotice("");
    } catch (e) {
      setError(err(e));
    } finally {
      setBusy(false);
    }
  }, []);
  async function execute() {
    if (!confirmation || !card || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<{ card: Card; operation: Operation }>(
        `/staff/${confirmation.kind}/`,
        {
          method: "POST",
          body: {
            card_id: card.id,
            quantity: confirmation.kind === "redeem" ? 1 : qty,
            request_key: confirmation.key,
          },
        },
      );
      setCard(result.card);
      setNotice(
        confirmation.kind === "redeem" ? "Сыйлық берілді" : "Шай қосылды",
      );
      setConfirmation(null);
      await refreshOps();
    } catch (e) {
      setError(err(e));
      try {
        setCard(
          await api<Card>("/staff/lookup/", {
            method: "POST",
            body: { token: cardToken },
          }),
        );
      } catch {}
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="staff-shell">
      <StaffHeader user={user} onLogout={onLogout} />
      <main>
        <div className="section-heading">
          <span className="eyebrow">{user.branch || "MAGRIBI"}</span>
          <h1>Картаны растау</h1>
        </div>
        <ErrorBox message={error} />
        {notice && (
          <p className="success-box" role="status">
            {notice}
          </p>
        )}
        <section className="staff-panel">
          {!card ? (
            <>
              <div className="scan-state">
                <span>
                  <Icon name="scan" />
                </span>
                <h2>Клиенттің картасы</h2>
                <p>
                  QR-кодты сканерлеңіз немесе
                  <br />
                  картаның сілтемесін енгізіңіз.
                </p>
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => setScanning(true)}
                >
                  <Icon name="scan" />
                  Камерамен сканерлеу
                </button>
              </div>
              {scanning && (
                <Scanner onScan={lookup} onClose={() => setScanning(false)} />
              )}
              <form
                className="lookup-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void lookup(lookupText);
                }}
              >
                <label>
                  Карта сілтемесі
                  <input
                    value={lookupText}
                    onChange={(e) => setLookupText(e.target.value)}
                    autoComplete="off"
                    placeholder="https://…/#card=…"
                    required
                  />
                </label>
                <button className="secondary" disabled={busy}>
                  {busy ? "Ашылуда…" : "Картаны ашу"}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="staff-customer">
                <span>Қ</span>
                <div>
                  <strong>Қонақтың картасы</strong>
                  <small>{card.id.slice(0, 8).toUpperCase()}</small>
                </div>
                <button
                  aria-label="Картаны жабу"
                  disabled={busy}
                  onClick={() => {
                    setCard(null);
                    setConfirmation(null);
                  }}
                >
                  ×
                </button>
              </div>
              <div className="staff-balance">
                <div>
                  <small>Жиналған шай</small>
                  <strong>
                    {card.stamps}
                    <span>/7</span>
                  </strong>
                </div>
                <div>
                  <small>Дайын сыйлық</small>
                  <strong>
                    {card.rewards}
                    <Icon name="gift" />
                  </strong>
                </div>
              </div>
              {confirmation ? (
                <div className="confirmation">
                  <span className="eyebrow">ОПЕРАЦИЯНЫ РАСТАУ</span>
                  <h2>
                    {confirmation.kind === "redeem"
                      ? "1 тегін шай берілсін бе?"
                      : `${qty} карак шай қосылсын ба?`}
                  </h2>
                  <div className="confirm-buttons">
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => setConfirmation(null)}
                    >
                      Бас тарту
                    </button>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => void execute()}
                    >
                      <Icon name="check" />
                      {busy ? "Сақталуда…" : "Растау"}
                    </button>
                  </div>
                  <p className="staff-hint">
                    Байланыс үзілсе, «Растау» батырмасын қайта басуға болады:
                    операция бір рет қана жазылады.
                  </p>
                </div>
              ) : (
                <div className="quantity-section">
                  <span>Сатып алынған карак шай</span>
                  <div className="quantity">
                    <button
                      aria-label="Шай санын азайту"
                      disabled={qty <= 1}
                      onClick={() => setQty((q) => q - 1)}
                    >
                      −
                    </button>
                    <output>{qty}</output>
                    <button
                      aria-label="Шай санын көбейту"
                      disabled={qty >= 100}
                      onClick={() => setQty((q) => q + 1)}
                    >
                      +
                    </button>
                    <span>дана</span>
                  </div>
                  <button
                    className="primary"
                    onClick={() =>
                      setConfirmation({
                        kind: "purchase",
                        key: crypto.randomUUID(),
                      })
                    }
                  >
                    <Icon name="cup" />
                    {qty} шай қосу
                    <Icon name="arrow" />
                  </button>
                  {card.rewards > 0 && (
                    <button
                      className="redeem"
                      onClick={() =>
                        setConfirmation({
                          kind: "redeem",
                          key: crypto.randomUUID(),
                        })
                      }
                    >
                      <Icon name="gift" />1 тегін шайды беру
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </section>
        <section className="staff-history">
          <h2>Соңғы әрекеттер</h2>
          <Activity items={history.items} />
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
        {user.role === "manager" && (
          <Link className="text-button" href="/manager">
            Басқарушы кабинеті <Icon name="arrow" />
          </Link>
        )}
      </main>
    </div>
  );
}
