"use client";
import { useEffect, useRef, useState } from "react";
import { err } from "@/lib/api";
export default function Scanner({
  onScan,
  onClose,
}: {
  onScan: (value: string) => void;
  onClose: () => void;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    let controls: { stop: () => void } | undefined;
    (async () => {
      try {
        const { BrowserQRCodeReader } = await import("@zxing/browser");
        if (cancelled || !video.current) return;
        controls = await new BrowserQRCodeReader().decodeFromConstraints(
          { video: { facingMode: { ideal: "environment" } }, audio: false },
          video.current,
          (result, _error, c) => {
            if (result && !cancelled) {
              cancelled = true;
              c.stop();
              onScan(result.getText());
            }
          },
        );
        if (cancelled) controls.stop();
      } catch (e) {
        if (!cancelled)
          setError(
            `Камера ашылмады: ${err(e)}. Карта сілтемесін енгізуге болады.`,
          );
      }
    })();
    return () => {
      cancelled = true;
      controls?.stop();
    };
  }, [onScan]);
  return (
    <div className="scanner">
      <video ref={video} muted playsInline />
      <p role="status">{error || "Клиенттің QR-кодын камераға көрсетіңіз"}</p>
      <button className="secondary" onClick={onClose}>
        Камераны жабу
      </button>
    </div>
  );
}
