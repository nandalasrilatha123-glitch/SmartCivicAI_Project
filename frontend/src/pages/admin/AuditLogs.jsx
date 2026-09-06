import { useEffect, useState } from "react";
import AdminLayout from "../../layouts/AdminLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import { listAuditLogs } from "../../services/userService";

export default function AuditLogs() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listAuditLogs({ page, page_size: 25 }).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <AdminLayout>
      <div className="p-8 max-w-5xl">
        <h1 className="font-display text-2xl font-semibold text-ink mb-6">Audit Logs</h1>

        {loading || !data ? (
          <LoadingSpinner />
        ) : (
          <>
            <div className="bg-paper-raised border border-ink/10 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-ink-faint border-b border-ink/10">
                    <th className="py-3 px-4">When</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Before</th>
                    <th className="py-3 px-4">After</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((log) => (
                    <tr key={log.id} className="border-b border-dashed border-ink/10 align-top">
                      <td className="py-3 px-4 text-xs text-ink-faint whitespace-nowrap">{new Date(log.created_at).toLocaleString()}</td>
                      <td className="py-3 px-4 text-xs">{log.action.replace(/_/g, " ")}</td>
                      <td className="py-3 px-4 text-xs text-ink-faint">{log.entity_type} {log.entity_id ? `#${log.entity_id.slice(0, 8)}` : ""}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-ink-faint max-w-xs truncate">
                        {log.before_value ? JSON.stringify(log.before_value) : "—"}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-ink-faint max-w-xs truncate">
                        {log.after_value ? JSON.stringify(log.after_value) : "—"}
                      </td>
                    </tr>
                  ))}
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
