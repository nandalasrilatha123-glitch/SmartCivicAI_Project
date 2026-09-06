import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getUnreadCount, listNotifications, markAllRead, markNotificationRead,
} from "../services/notificationService";

export default function NotificationBell({ complaintPathPrefix = "/complaints" }) {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    getUnreadCount().then(setUnread).catch(() => {});
    const interval = setInterval(() => {
      getUnreadCount().then(setUnread).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleOpen = () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoading(true);
      listNotifications({ page_size: 10 }).then((data) => {
        setNotifications(data.items);
        setUnread(data.unread_count);
      }).finally(() => setLoading(false));
    }
  };

  const handleItemClick = async (n) => {
    if (!n.is_read) {
      await markNotificationRead(n.id);
      setUnread((u) => Math.max(0, u - 1));
      setNotifications((items) => items.map((i) => (i.id === n.id ? { ...i, is_read: true } : i)));
    }
    if (n.complaint_id) {
      setOpen(false);
      navigate(`${complaintPathPrefix}/${n.complaint_id}`);
    }
  };

  const handleMarkAllRead = async () => {
    await markAllRead();
    setUnread(0);
    setNotifications((items) => items.map((i) => ({ ...i, is_read: true })));
  };

  return (
    <div className="relative" ref={ref}>
      <button onClick={toggleOpen} className="relative p-1.5 text-ink-soft hover:text-ink" aria-label="Notifications">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-5 h-5">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-stamp-red text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-ink/15 shadow-lg z-50 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-ink/10">
            <span className="text-sm font-medium text-ink">Notifications</span>
            {unread > 0 && (
              <button onClick={handleMarkAllRead} className="text-xs text-ink-faint underline underline-offset-2">
                Mark all read
              </button>
            )}
          </div>
          {loading ? (
            <p className="text-sm text-ink-faint text-center py-6">Loading...</p>
          ) : notifications.length === 0 ? (
            <p className="text-sm text-ink-faint text-center py-6">No notifications yet.</p>
          ) : (
            notifications.map((n) => (
              <button
                key={n.id} onClick={() => handleItemClick(n)}
                className={`block w-full text-left px-4 py-3 border-b border-dashed border-ink/10 hover:bg-paper ${!n.is_read ? "bg-marigold/5" : ""}`}
              >
                <p className="text-sm text-ink font-medium">{n.title}</p>
                <p className="text-xs text-ink-faint mt-0.5">{n.message}</p>
                <p className="text-[10px] text-ink-faint mt-1">{new Date(n.created_at).toLocaleString()}</p>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
