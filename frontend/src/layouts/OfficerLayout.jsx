import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import NotificationBell from "../components/NotificationBell";

export default function OfficerLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-ink/10 bg-paper-raised">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <Link to="/officer/dashboard" className="font-display text-lg font-semibold text-ink">
              SmartCivicAI
            </Link>
            <p className="text-xs text-ink-faint">Officer Console</p>
          </div>
          <div className="flex items-center gap-4">
            <NotificationBell complaintPathPrefix="/officer/complaints" />
            <span className="text-sm text-ink-faint hidden sm:inline">{user?.full_name}</span>
            <button onClick={handleLogout} className="btn-secondary py-1.5 px-3.5 text-sm">
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
