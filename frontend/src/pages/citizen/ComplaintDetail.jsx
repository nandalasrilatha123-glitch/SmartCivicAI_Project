import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MainLayout from "../../layouts/MainLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import StatusStamp from "../../components/StatusStamp";
import PriorityBadge from "../../components/PriorityBadge";
import { useLanguage } from "../../contexts/LanguageContext";
import { getComplaint, getComplaintHistory, submitFeedback } from "../../services/complaintService";
import { apiErrorMessage } from "../../services/api";
import { MODULE_LABEL_KEYS } from "../../utils/statusMeta";

const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");

export default function ComplaintDetail() {
  const { id } = useParams();
  const { t } = useLanguage();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [feedbackState, setFeedbackState] = useState("idle"); // idle | submitting | done | error
  const [feedbackError, setFeedbackError] = useState("");

  useEffect(() => {
    Promise.all([getComplaint(id), getComplaintHistory(id)])
      .then(([c, h]) => {
        setComplaint(c);
        setHistory(h);
      })
      .finally(() => setIsLoading(false));
  }, [id]);

  const handleFeedback = async (e) => {
    e.preventDefault();
    setFeedbackState("submitting");
    setFeedbackError("");
    try {
      await submitFeedback(id, { rating, comment });
      setFeedbackState("done");
    } catch (err) {
      setFeedbackState("error");
      setFeedbackError(apiErrorMessage(err, "Could not submit feedback."));
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <LoadingSpinner />
      </MainLayout>
    );
  }

  if (!complaint) {
    return (
      <MainLayout>
        <p className="max-w-2xl mx-auto px-6 py-12 text-ink-soft">Complaint not found.</p>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-2xl mx-auto px-6 py-12">
        <Link to="/dashboard" className="text-sm text-ink-faint hover:text-ink mb-6 inline-block">
          ← {t("backToComplaints")}
        </Link>

        <div className="bg-paper-raised border border-ink/10 p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-sm text-ink-soft">{complaint.complaint_number}</p>
              <h1 className="font-display text-xl font-semibold text-ink mt-1">
                {t(MODULE_LABEL_KEYS[complaint.module])}
              </h1>
            </div>
            <div className="flex flex-col items-end gap-2">
              <StatusStamp status={complaint.status} />
              <PriorityBadge priority={complaint.priority} />
            </div>
          </div>

          <div className="mt-5 pt-5 border-t border-dashed border-ink/15">
            <p className="text-ink whitespace-pre-wrap leading-relaxed">{complaint.original_text}</p>
          </div>

          {complaint.summary && (
            <div className="mt-4 bg-white border border-ink/10 p-3 text-sm text-ink-soft">
              <span className="font-medium text-ink-faint">{t("aiSummary")}: </span>
              {complaint.summary}
            </div>
          )}

          {complaint.address && (
            <p className="text-sm text-ink-faint mt-4">{t("address")}: {complaint.address}</p>
          )}

          {complaint.images?.length > 0 && (
            <div className="mt-4 flex gap-3 flex-wrap">
              {complaint.images.map((img) => (
                <img
                  key={img.id}
                  src={`${API_ORIGIN}/uploads/${img.file_path}`}
                  alt={img.original_filename}
                  className="w-28 h-28 object-cover border border-ink/10"
                />
              ))}
            </div>
          )}

          {complaint.officer_remarks && (
            <div className="mt-4 bg-stamp-teal/5 border border-stamp-teal/20 p-3 text-sm text-ink-soft">
              <span className="font-medium text-stamp-teal">Officer remarks: </span>
              {complaint.officer_remarks}
            </div>
          )}
        </div>

        {/* Status history */}
        <div className="bg-paper-raised border border-ink/10 p-6 mb-6">
          <h2 className="font-display text-lg font-semibold text-ink mb-4">{t("statusHistory")}</h2>
          <div className="space-y-0">
            {history.map((h) => (
              <div key={h.id} className="ledger-row flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <StatusStamp status={h.to_status} />
                  {h.note && <span className="text-sm text-ink-faint">{h.note}</span>}
                </div>
                <span className="text-xs text-ink-faint shrink-0">
                  {new Date(h.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Feedback */}
        {complaint.status === "RESOLVED" && (
          <div className="bg-paper-raised border border-ink/10 p-6">
            <h2 className="font-display text-lg font-semibold text-ink mb-4">{t("leaveFeedback")}</h2>

            {feedbackState === "done" ? (
              <p className="text-stamp-teal text-sm">{t("feedbackThanks")}</p>
            ) : (
              <form onSubmit={handleFeedback} className="space-y-4">
                <div>
                  <label className="field-label">{t("rating")}</label>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n} type="button" onClick={() => setRating(n)}
                        className={`w-9 h-9 border ${rating >= n ? "bg-marigold border-marigold-dark" : "border-ink/20"}`}
                        aria-label={`${n} stars`}
                      />
                    ))}
                  </div>
                </div>
                <div>
                  <label className="field-label" htmlFor="comment">{t("comment")}</label>
                  <textarea
                    id="comment" rows={3} value={comment} onChange={(e) => setComment(e.target.value)}
                    className="field-input resize-none"
                  />
                </div>
                {feedbackError && <p className="text-sm text-stamp-red">{feedbackError}</p>}
                <button type="submit" disabled={feedbackState === "submitting"} className="btn-primary">
                  {t("submitFeedback")}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
