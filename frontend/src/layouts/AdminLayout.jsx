import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import NotificationBell from "../components/NotificationBell";

const NAV_ITEMS = [
  { to: "/admin/dashboard", label: "Dashboard" },
  { to: "/admin/complaints", label: "Complaints" },
  { to: "/admin/gis-map", label: "GIS Map" },
  { to: "/admin/departments", label: "Departments & Categories" },
  { to: "/admin/users", label: "Users & Officers" },
  { to: "/admin/audit-logs", label: "Audit Logs" },
];

export default function AdminLayout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex bg-paper">
      <aside className="w-60 shrink-0 border-r border-ink/10 bg-paper-raised flex flex-col">
        <div className="px-5 py-5 border-b border-ink/10">
          <Link to="/admin/dashboard" className="font-display text-lg font-semibold text-ink">
            SmartCivicAI
          </Link>
          <p className="text-xs text-ink-faint mt-0.5">Admin Console</p>
        </div>

        <nav className="flex-1 py-4">
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`block px-5 py-2.5 text-sm border-l-2 ${
                  isActive
                    ? "border-marigold bg-marigold/10 text-ink font-medium"
                    : "border-transparent text-ink-soft hover:bg-ink/5 hover:text-ink"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-5 py-4 border-t border-ink/10">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-ink truncate">{user?.full_name}</p>
            <NotificationBell complaintPathPrefix="/admin/complaints" />
          </div>
          <p className="text-xs text-ink-faint truncate mb-3">{user?.email}</p>
          <button onClick={handleLogout} className="btn-secondary text-sm py-1.5 px-3 w-full">
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
