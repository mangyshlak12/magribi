"use client";
import Link from "next/link";
import { useState } from "react";
import type { Operation, Staff } from "@/lib/api";
import { api, dateLabel, err } from "@/lib/api";
const paths: Record<string, React.ReactNode> = {
  qr: (
    <path d="M3 3h6v6H3Zm12 0h6v6h-6ZM3 15h6v6H3Zm12 0h2v2h-2Zm4 4h2v2h-2Zm0-6h2v3h-2Zm-6 6h3v2h-3Z" />
  ),
  gift: (
    <>
      <path d="M4 10h16v4H4Zm2 4v8h12v-8M12 10v12M12 10C5 10 4 4 8 4s4 6 4 6Zm0 0c7 0 8-6 4-6s-4 6-4 6Z" />
    </>
  ),
  cup: (
    <path d="M5 8h13v8a6 6 0 0 1-6 6h-1a5 5 0 0 1-5-5V8Zm13 2h2a3 3 0 0 1 0 6h-2M8 2v3m5-3v3" />
  ),
  check: <path d="m5 12 4 4L19 6" />,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  wallet: (
    <path d="M4 5h15a2 2 0 0 1 2 2v12H5a3 3 0 0 1-3-3V6a2 2 0 0 1 2-2h13M16 10h5v5h-5a2.5 2.5 0 0 1 0-5Z" />
  ),
  history: <path d="M3 10a9 9 0 1 1 0 5M3 4v6h6m3-3v6l4 2" />,
  scan: <path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M2 12h20" />,
  copy: (
    <>
      <rect x="8" y="8" width="12" height="13" rx="2" />
      <path d="M16 8V3H3v13h5" />
    </>
  ),
};
export function Icon({ name }: { name: string }) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.history}
    </svg>
  );
}
export function Brand({ staff = false }: { staff?: boolean }) {
  return (
    <Link className="brand" href="/">
      <img src="/assets/arch.svg" alt="" width="35" height="35" />
      <span>
        magribi
        <small>{staff ? "қызметкер кабинеті" : "coffee & karak tea"}</small>
      </span>
    </Link>
  );
}
export function StaffHeader({
  user,
  onLogout,
}: {
  user: Staff;
  onLogout: () => void;
}) {
  const [error, setError] = useState("");
  return (
    <>
      <header className="staff-header">
        <Brand staff />
        <div className="staff-account">
          <span>
            {user.name || user.username}
            <small>{user.role === "manager" ? "Басқарушы" : "Кассир"}</small>
          </span>
          <button
            className="text-button"
            onClick={async () => {
              try {
                await api("/auth/logout/", { method: "POST" });
                onLogout();
              } catch (e) {
                setError(err(e));
              }
            }}
          >
            Шығу
          </button>
        </div>
      </header>
      <ErrorBox message={error} />
    </>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return message ? (
    <p className="error-box" role="alert">
      {message}
    </p>
  ) : null;
}
export function Activity({
  items,
  manager,
  onReverse,
}: {
  items: Operation[];
  manager?: boolean;
  onReverse?: (op: Operation) => void;
}) {
  return (
    <div className="history-list">
      {items.map((op) => (
        <div className="history-row" key={op.id}>
          <span
            className={`history-icon ${op.kind === "redeem" ? "gift-event" : ""}`}
          >
            <Icon
              name={
                op.kind === "redeem"
                  ? "gift"
                  : op.kind === "reversal"
                    ? "history"
                    : "cup"
              }
            />
          </span>
          <div>
            <strong>
              {op.kind === "purchase"
                ? "Карак шай алынды"
                : op.kind === "redeem"
                  ? "Сыйлық шай берілді"
                  : "Операция кері қайтарылды"}
              {op.reversed && (
                <span className="reversed-label"> · кері қайтарылған</span>
              )}
            </strong>
            <time>
              {dateLabel(op.created_at)} · {op.branch}
              {op.actor ? ` · ${op.actor}` : ""}
            </time>
            {op.reason && <p className="operation-reason">{op.reason}</p>}
            {manager && op.kind !== "reversal" && !op.reversed && (
              <button className="reverse-link" onClick={() => onReverse?.(op)}>
                Кері қайтару
              </button>
            )}
          </div>
          <b className="history-value">
            {op.kind === "purchase"
              ? `+${op.quantity}`
              : op.kind === "redeem"
                ? "−1"
                : op.paid_delta || "+1"}
          </b>
        </div>
      ))}
    </div>
  );
}
