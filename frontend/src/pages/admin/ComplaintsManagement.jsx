import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AdminLayout from "../../layouts/AdminLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import StatusStamp from "../../components/StatusStamp";
import PriorityBadge from "../../components/PriorityBadge";
import { listComplaints } from "../../services/complaintService";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];
const STATUSES = ["NEW", "PENDING", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED", "ESCALATED", "REQUIRES_ADMIN_REVIEW"];
const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function ComplaintsManagement() {
  const [filters, setFilters] = useState({ module: "", status: "", priority: "", search: "" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = { page, page_size: 20 };
    if (filters.module) params.module = filters.module;
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    if (filters.search) params.search = filters.search;

    listComplaints(params).then(setData).finally(() => setLoading(false));
  }, [filters, page]);

  const updateFilter = (key) => (e) => {
    setFilters((f) => ({ ...f, [key]: e.target.value }));
    setPage(1);
  };

  return (
    <AdminLayout>
      <div className="p-8 max-w-[1400px]">
        <h1 className="font-display text-2xl font-semibold text-ink mb-6">Complaints</h1>

        <div className="flex flex-wrap gap-3 mb-5">
          <input
            placeholder="Search by number or text..." value={filters.search} onChange={updateFilter("search")}
            className="field-input w-64"
          />
          <select value={filters.module} onChange={updateFilter("module")} className="field-input w-48">
            <option value="">All modules</option>
            {MODULES.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
          </select>
          <select value={filters.status} onChange={updateFilter("status")} className="field-input w-48">
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
          </select>
          <select value={filters.priority} onChange={updateFilter("priority")} className="field-input w-40">
            <option value="">All priorities</option>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        {loading || !data ? (
          <LoadingSpinner />
        ) : (
          <>
            <div className="bg-paper-raised border border-ink/10 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-faint border-b border-ink/10">
                    <th className="py-3 px-4">Number</th>
                    <th className="py-3 px-4">Module</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Language</th>
                    <th className="py-3 px-4">Submitted</th>
                    <th className="py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((c) => (
                    <tr key={c.id} className="border-b border-dashed border-ink/10 hover:bg-white">
                      <td className="py-3 px-4 font-mono text-xs">{c.complaint_number}</td>
                      <td className="py-3 px-4">{c.module.replace("_", " ")}</td>
                      <td className="py-3 px-4"><PriorityBadge priority={c.priority} /></td>
                      <td className="py-3 px-4"><StatusStamp status={c.status} /></td>
                      <td className="py-3 px-4 text-ink-faint uppercase text-xs">{c.original_language}</td>
                      <td className="py-3 px-4 text-ink-faint text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
                      <td className="py-3 px-4">
                        <Link to={`/admin/complaints/${c.id}`} className="text-ink font-medium underline underline-offset-2 text-xs">
                          Manage
                        </Link>
                      </td>
                    </tr>
                  ))}
                  {data.items.length === 0 && (
                    <tr><td colSpan={7} className="py-8 text-center text-ink-faint">No complaints match these filters.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between mt-4 text-sm text-ink-faint">
              <span>{data.total} total</span>
              <div className="flex items-center gap-3">
                <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="btn-secondary py-1 px-3 text-xs">←</button>
                <span>{page} / {data.total_pages}</span>
                <button disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)} className="btn-secondary py-1 px-3 text-xs">→</button>
              </div>
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  );
}
