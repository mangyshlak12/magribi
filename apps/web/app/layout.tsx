import type { Metadata } from "next";
import "./brand.css";
import "./globals.css";
export const metadata: Metadata = {
  title: "Magribi · Бонус картаң",
  description: "7 қарақ шай алсаң, 8-сі тегін",
  robots: { index: false, follow: false },
  icons: { icon: "/assets/arch.svg" },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="kk">
      <body data-palette="1">{children}</body>
    </html>
  );
}
