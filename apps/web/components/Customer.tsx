"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import {
  api,
  ApiError,
  err,
  newToken,
  cardLink,
  type Card,
  type History,
} from "@/lib/api";
import { Activity, Brand, Icon, ErrorBox } from "./Shared";
export default function Customer() {
  const [token, setToken] = useState("");
  const [card, setCard] = useState<Card | null>(null);
  const [view, setView] = useState<"card" | "history">("card");
  const [history, setHistory] = useState<History>({
    items: [],
    page: 1,
    has_more: false,
  });
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [qr, setQr] = useState("");
  const [retry, setRetry] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const fromHash = new URLSearchParams(location.hash.slice(1)).get(
          "card",
        );
        if (fromHash && !/^[A-Za-z0-9_-]{43}$/.test(fromHash))
          throw new Error("Карта сілтемесі жарамсыз");
        let t = fromHash || localStorage.getItem("magribi-card-token");
        if (!t) t = newToken();
        if (!/^[A-Za-z0-9_-]{43}$/.test(t))
          throw new Error("Сақталған карта сілтемесі жарамсыз");
        localStorage.setItem("magribi-card-token", t);
        if (fromHash) window.history.replaceState(null, "", location.pathname);
        let c: Card;
        try {
          c = await api<Card>("/cards/current/", { token: t });
        } catch (e) {
          if (e instanceof ApiError && e.status === 404)
            c = await api<Card>("/cards/", {
              method: "POST",
              token: t,
              body: { token: t },
            });
          else throw e;
        }
        if (live) {
          setToken(t);
          setCard(c);
          setError("");
        }
      } catch (e) {
        if (live) setError(err(e));
      }
    })();
    return () => {
      live = false;
    };
  }, [retry]);
  const refresh = useCallback(async () => {
    if (!token) return;
    setCard(await api<Card>("/cards/current/", { token }));
    if (view === "history") {
      const h = await api<History>("/cards/history/", { token });
      setHistory((prev) =>
        prev.page === 1
          ? h
          : {
              ...prev,
              items: [
                ...h.items,
                ...prev.items.filter(
                  (item) => !h.items.some((n) => n.id === item.id),
                ),
              ],
            },
      );
    }
  }, [token, view]);
  useEffect(() => {
    if (!token) return;
    let live = true;
    const run = () => {
      if (document.visibilityState === "visible")
        refresh().catch((e) => {
          if (live) setError(err(e));
        });
    };
    run();
    const id = setInterval(run, 5000);
    window.addEventListener("focus", run);
    return () => {
      live = false;
      clearInterval(id);
      window.removeEventListener("focus", run);
    };
  }, [refresh, token]);
  useEffect(() => {
    if (token)
      QRCode.toDataURL(cardLink(token), {
        width: 280,
        margin: 4,
        errorCorrectionLevel: "M",
        color: { dark: "#000000", light: "#ffffff" },
      })
        .then(setQr)
        .catch((e) => setError(err(e)));
  }, [token]);
  const shown = card ? (card.rewards > 0 ? 7 : card.stamps) : 0;
  return (
    <div className="app-shell">
      <header className="app-header">
        <Brand />
      </header>
      <main id="main">
        <ErrorBox message={error} />
        {!card ? (
          <div className="loading-state">
            <p>
              {error ? "Картаны ашу мүмкін болмады" : "Картаңыз ашылып жатыр…"}
            </p>
            {error && (
              <button
                className="text-button"
                onClick={() => setRetry((v) => v + 1)}
              >
                Қайта көру
              </button>
            )}
          </div>
        ) : view === "card" ? (
          <section className="card-view">
            <div className="welcome">
              <h1>Бонус картаң</h1>
            </div>
            <section
              className={`bonus-card design-1 ${card.rewards ? "reward-ready" : ""}`}
              aria-label="Карак жинақ картасы"
            >
              <div className="bonus-edge" />
              <div className="bonus-top">
                <span className="bonus-brand">
                  <img src="/assets/arch.svg" alt="" />
                  magribi
                </span>
              </div>
              <div className="bonus-intro">
                <h2>
                  7 қарақ шай алсаң,<em>8-сі тегін.</em>
                </h2>
                <div className="bonus-count" aria-label={`${shown} / 7 шай`}>
                  <span>
                    <strong>{shown}</strong>
                    <b>/ 7</b>
                  </span>
                </div>
              </div>
              <div className="tea-stamps">
                {Array.from({ length: 8 }, (_, i) => (
                  <div
                    className={`tea-stamp ${i < shown || (i === 7 && card.rewards > 0) ? "collected" : ""} ${i === 7 ? "gift-cup" : ""}`}
                    key={i}
                    aria-label={
                      i === 7
                        ? "Сыйлық шай"
                        : `${i + 1}-ші шай${i < shown ? " жиналды" : ""}`
                    }
                  >
                    <div className="takeaway">
                      <div className="cup-lid" />
                      <div className="cup-body">
                        <span className="cup-number">{i + 1}</span>
                        <span className="cup-mark">
                          {i === 7 ? <Icon name="gift" /> : "m"}
                        </span>
                      </div>
                      {(i < shown || (i === 7 && card.rewards > 0)) && (
                        <span className="cup-tick">
                          <Icon name="check" />
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="bonus-footer">
                <span>Бір карак шай — бір белгі</span>
              </div>
              <div className="bonus-pattern" />
            </section>
            {card.rewards > 0 && (
              <p className="reward-message">
                <Icon name="gift" />
                {card.rewards} сыйлық шай дайын
                {card.stamps > 0 && (
                  <small>Келесі айналымда {card.stamps} / 7</small>
                )}
              </p>
            )}
            <div className="save-card">
              <button
                className="text-button"
                onClick={async () => {
                  setCopied(true);
                  try {
                    await navigator.clipboard.writeText(cardLink(token));
                  } catch {}
                }}
              >
                <Icon name={copied ? "check" : "copy"} />
                {copied ? "Сілтеме көшірілді" : "Карта сілтемесін сақтау"}
              </button>
              {copied && (
                <label className="share-link">
                  Жеке карта сілтемесі
                  <input
                    aria-label="Жеке карта сілтемесі"
                    readOnly
                    value={cardLink(token)}
                    onFocus={(e) => e.currentTarget.select()}
                  />
                </label>
              )}
              <p>
                Сілтемені сақтап қой — басқа телефоннан да ашылады.
                <br />
                Бұл жеке картаңның кілті, бөгде адамға жіберме.
              </p>
            </div>
          </section>
        ) : (
          <section className="history-view">
            <div className="section-heading">
              <span className="eyebrow">СІЗДІҢ КАРТАҢЫЗ</span>
              <h1>Карта тарихы</h1>
            </div>
            <div className="history-summary">
              <div>
                <strong>
                  {card.stamps}
                  <span> / 7</span>
                </strong>
                <small>осы картада</small>
              </div>
              <div>
                <strong>{card.rewards}</strong>
                <small>дайын сыйлық</small>
              </div>
            </div>
            {history.items.length ? (
              <>
                <Activity items={history.items} />
                {history.has_more && (
                  <button
                    className="text-button"
                    onClick={async () => {
                      try {
                        const next = await api<History>(
                          `/cards/history/?page=${history.page + 1}`,
                          { token },
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
              </>
            ) : (
              <div className="empty-history">
                <span className="empty-illustration">
                  <Icon name="history" />
                </span>
                <h2>Алғашқы сәт әлі алда</h2>
                <p>
                  Кассир қосқан белгілер мен
                  <br />
                  сыйлықтарыңыз осында көрінеді.
                </p>
                <button className="text-button" onClick={() => setView("card")}>
                  Картаға оралу <Icon name="arrow" />
                </button>
              </div>
            )}
          </section>
        )}
      </main>
      <nav className="bottom-nav" aria-label="Негізгі мәзір">
        <button
          aria-current={view === "card" ? "page" : undefined}
          onClick={() => setView("card")}
        >
          <Icon name="wallet" />
          <span>Карта</span>
        </button>
        <button
          className="qr-trigger"
          disabled={!card || !qr}
          onClick={() => dialog.current?.showModal()}
        >
          <Icon name="qr" />
          <span>QR көрсету</span>
        </button>
        <button
          aria-current={view === "history" ? "page" : undefined}
          onClick={() => setView("history")}
        >
          <Icon name="history" />
          <span>Тарих</span>
        </button>
      </nav>
      <dialog
        id="qr-dialog"
        ref={dialog}
        onClick={(e) => {
          if (e.target === dialog.current) {
            const r = dialog.current.getBoundingClientRect();
            if (
              e.clientX < r.left ||
              e.clientX > r.right ||
              e.clientY < r.top ||
              e.clientY > r.bottom
            )
              dialog.current.close();
          }
        }}
      >
        <div className="sheet-handle" />
        <button
          className="close-dialog"
          aria-label="QR-кодты жабу"
          onClick={() => dialog.current?.close()}
        >
          ×
        </button>
        <div className="qr-brand-panel">
          <div className="modal-brand">
            <img src="/assets/arch.svg" alt="" />
            <strong>magribi</strong>
          </div>
          <h2>Кассирге көрсетіңіз</h2>
          <p>Бір карак шай — бір белгі.</p>
        </div>
        <div className="qr-paper">
          <div className="qr-corner tl" />
          <div className="qr-corner tr" />
          {qr && (
            <img src={qr} alt="Жеке карта QR-коды" width="224" height="224" />
          )}
          <div className="qr-corner bl" />
          <div className="qr-corner br" />
        </div>
        <div className="qr-status">
          {card?.rewards
            ? `${card.rewards} сыйлық шай дайын`
            : `${card?.stamps || 0} / 7 шай`}
        </div>
        <button className="sheet-done" onClick={() => dialog.current?.close()}>
          Дайын <Icon name="check" />
        </button>
      </dialog>
    </div>
  );
}
