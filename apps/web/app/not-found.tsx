import Link from "next/link";
export default function NotFound() {
  return (
    <main className="standalone-panel">
      <h1>Бет табылмады</h1>
      <Link className="primary" href="/">
        Картаға оралу
      </Link>
    </main>
  );
}
