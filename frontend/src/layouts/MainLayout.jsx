import Navbar from "../components/Navbar";

export default function MainLayout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-ink/10 py-6 mt-auto">
        <div className="max-w-6xl mx-auto px-6 text-sm text-ink-faint">
          SmartCivicAI — AI-powered civic complaint management (demo build)
        </div>
      </footer>
    </div>
  );
}
