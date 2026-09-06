import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import LanguageSwitcher from "./LanguageSwitcher";
import NotificationBell from "./NotificationBell";

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="border-b border-ink/10 bg-paper-raised">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="font-display text-xl font-semibold text-ink">
          {t("appName")}
        </Link>

        <div className="flex items-center gap-6">
          <LanguageSwitcher compact />
          {isAuthenticated ? (
            <nav className="flex items-center gap-5">
              <Link to="/dashboard" className="text-sm font-medium text-ink-soft hover:text-ink">
                {t("dashboard")}
              </Link>
              <Link to="/complaints/new" className="text-sm font-medium text-ink-soft hover:text-ink">
                {t("newComplaint")}
              </Link>
              <Link to="/profile" className="text-sm font-medium text-ink-soft hover:text-ink">
                {t("profile")}
              </Link>
              <span className="text-sm text-ink-faint hidden sm:inline">{user?.full_name}</span>
              <NotificationBell complaintPathPrefix="/complaints" />
              <button onClick={handleLogout} className="btn-secondary py-1.5 px-3.5 text-sm">
                {t("logout")}
              </button>
            </nav>
          ) : (
            <nav className="flex items-center gap-3">
              <Link to="/login" className="text-sm font-medium text-ink-soft hover:text-ink">
                {t("login")}
              </Link>
              <Link to="/register" className="btn-accent py-1.5 px-3.5 text-sm">
                {t("register")}
              </Link>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
}
