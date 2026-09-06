import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../../layouts/MainLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import StatusStamp from "../../components/StatusStamp";
import PriorityBadge from "../../components/PriorityBadge";
import { useAuth } from "../../contexts/AuthContext";
import { useLanguage } from "../../contexts/LanguageContext";
import { listMyComplaints } from "../../services/complaintService";
import { MODULE_LABEL_KEYS } from "../../utils/statusMeta";

export default function CitizenDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    listMyComplaints({ page, pageSize: 10 })
      .then(setData)
      .finally(() => setIsLoading(false));
  }, [page]);

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink">
              {t("dashboard")}
            </h1>
            <p className="text-ink-faint text-sm mt-1">
              {user?.full_name}
            </p>
          </div>
          <Link to="/complaints/new" className="btn-accent">
            {t("newComplaint")}
          </Link>
        </div>

        {isLoading ? (
          <LoadingSpinner />
        ) : !data || data.items.length === 0 ? (
          <div className="border border-dashed border-ink/20 py-16 text-center">
            <p className="text-ink-soft mb-4">{t("noComplaintsYet")}</p>
            <Link to="/complaints/new" className="btn-primary">
              {t("reportFirstIssue")}
            </Link>
          </div>
        ) : (
          <>
            <div className="bg-paper-raised border border-ink/10 px-6">
              {data.items.map((c) => (
                <Link key={c.id} to={`/complaints/${c.id}`} className="ledger-row flex items-center justify-between gap-4 group">
                  <div className="min-w-0">
                    <p className="font-mono text-sm text-ink-soft">{c.complaint_number}</p>
                    <p className="text-ink group-hover:underline underline-offset-2 truncate">
                      {t(MODULE_LABEL_KEYS[c.module])} {c.summary ? `— ${c.summary}` : ""}
                    </p>
                    <p className="text-xs text-ink-faint mt-0.5">
                      {t("submittedOn")} {new Date(c.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <PriorityBadge priority={c.priority} />
                    <StatusStamp status={c.status} />
                  </div>
                </Link>
              ))}
            </div>

            {data.total_pages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6">
                <button
                  disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
                  className="btn-secondary py-1.5 px-3.5 text-sm"
                >
                  ← 
                </button>
                <span className="text-sm text-ink-faint">
                  {page} / {data.total_pages}
                </span>
                <button
                  disabled={page >= data.total_pages} onClick={() => setPage((p) => p + 1)}
                  className="btn-secondary py-1.5 px-3.5 text-sm"
                >
                  →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </MainLayout>
  );
}
