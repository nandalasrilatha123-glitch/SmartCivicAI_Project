import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import OfficerLayout from "../../layouts/OfficerLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import StatusStamp from "../../components/StatusStamp";
import PriorityBadge from "../../components/PriorityBadge";
import StatCard from "../../components/admin/StatCard";
import { useAuth } from "../../contexts/AuthContext";
import { getMyDepartmentOverview } from "../../services/analyticsService";
import { acceptComplaint, listComplaints } from "../../services/complaintService";
import { apiErrorMessage } from "../../services/api";

const TABS = [
  { key: "unassigned", label: "Unassigned" },
  { key: "mine", label: "Assigned to me" },
  { key: "all", label: "All in department" },
];

export default function OfficerDashboard() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [tab, setTab] = useState("unassigned");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [acceptingId, setAcceptingId] = useState(null);

  useEffect(() => {
    getMyDepartmentOverview().then(setOverview).catch(() => {});
  }, []);

  const load = () => {
    setLoading(true);
    listComplaints({ page, page_size: 20 })
      .then(setData)
      .finally(() => setLoading(false));
  };
  useEffect(load, [page]);

  const filteredItems = (data?.items || []).filter((c) => {
    if (tab === "unassigned") return !c.assigned_officer_id;
    if (tab === "mine") return c.assigned_officer_id === user.id;
    return true;
  });

  const handleAccept = async (id) => {
    setError("");
    setAcceptingId(id);
    try {
      await acceptComplaint(id);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setAcceptingId(null);
    }
  };

  return (
    <OfficerLayout>
      <div className="max-w-5xl mx-auto px-6 py-10">
        <h1 className="font-display text-2xl font-semibold text-ink mb-1">Officer Dashboard</h1>
        <p className="text-ink-faint text-sm mb-6">{user?.full_name}</p>

        {overview && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8">
            <StatCard label="Total" value={overview.total} accent />
            <StatCard label="Unassigned" value={overview.pending} />
            <StatCard label="Assigned" value={overview.assigned} />
            <StatCard label="In progress" value={overview.in_progress} />
            <StatCard label="Resolved" value={overview.resolved} />
          </div>
        )}

        {error && <p className="text-sm text-stamp-red mb-4">{error}</p>}

        <div className="flex gap-2 mb-4">
          {TABS.map((t) => (
            <button
              key={t.key} onClick={() => setTab(t.key)}
              className={`text-sm px-3 py-1.5 border ${tab === t.key ? "border-ink bg-ink text-paper" : "border-ink/20 text-ink-soft"}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading || !data ? (
          <LoadingSpinner />
        ) : (
          <div className="bg-paper-raised border border-ink/10">
            {filteredItems.length === 0 ? (
              <p className="text-ink-faint text-sm py-10 text-center">Nothing here right now.</p>
            ) : (
              filteredItems.map((c) => (
                <div key={c.id} className="ledger-row flex items-center justify-between gap-4 px-5">
                  <Link to={`/officer/complaints/${c.id}`} className="min-w-0 flex-1">
                    <p className="font-mono text-xs text-ink-soft">{c.complaint_number}</p>
                    <p className="text-ink truncate hover:underline underline-offset-2">
                      {c.module.replace("_", " ")} {c.summary ? `— ${c.summary}` : ""}
                    </p>
                  </Link>
                  <div className="flex items-center gap-3 shrink-0">
                    <PriorityBadge priority={c.priority} />
                    <StatusStamp status={c.status} />
                    {!c.assigned_officer_id && (
                      <button
                        onClick={() => handleAccept(c.id)} disabled={acceptingId === c.id}
                        className="btn-accent text-xs py-1.5 px-3"
                      >
                        {acceptingId === c.id ? "…" : "Accept"}
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-center gap-4 mt-6">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="btn-secondary py-1.5 px-3.5 text-sm">←</button>
            <span className="text-sm text-ink-faint">{page} / {data.total_pages}</span>
            <button disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)} className="btn-secondary py-1.5 px-3.5 text-sm">→</button>
          </div>
        )}
      </div>
    </OfficerLayout>
  );
}
