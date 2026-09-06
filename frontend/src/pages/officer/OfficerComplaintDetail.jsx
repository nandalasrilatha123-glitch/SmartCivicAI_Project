import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import OfficerLayout from "../../layouts/OfficerLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import StatusStamp from "../../components/StatusStamp";
import PriorityBadge from "../../components/PriorityBadge";
import {
  getComplaint, getComplaintHistory, resolveComplaint, updateComplaintStatus, uploadResolutionProof,
} from "../../services/complaintService";
import { apiErrorMessage } from "../../services/api";

const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");
const NEXT_STATUSES = ["ASSIGNED", "IN_PROGRESS", "ESCALATED", "REJECTED"];

export default function OfficerComplaintDetail() {
  const { id } = useParams();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [nextStatus, setNextStatus] = useState("");
  const [note, setNote] = useState("");
  const [remarks, setRemarks] = useState("");
  const [proofFile, setProofFile] = useState(null);

  const load = () => {
    setLoading(true);
    Promise.all([getComplaint(id), getComplaintHistory(id)])
      .then(([c, h]) => {
        setComplaint(c);
        setHistory(h);
        setNextStatus(c.status);
      })
      .finally(() => setLoading(false));
  };
  useEffect(load, [id]);

  const withFeedback = async (fn) => {
    setMessage("");
    setError("");
    try {
      await fn();
      setMessage("Saved.");
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  if (loading || !complaint) {
    return (
      <OfficerLayout>
        <LoadingSpinner />
      </OfficerLayout>
    );
  }

  return (
    <OfficerLayout>
      <div className="max-w-2xl mx-auto px-6 py-10">
        <Link to="/officer/dashboard" className="text-sm text-ink-faint hover:text-ink mb-4 inline-block">
          ← Back to dashboard
        </Link>

        <div className="bg-paper-raised border border-ink/10 p-6 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-mono text-sm text-ink-soft">{complaint.complaint_number}</p>
              <h1 className="font-display text-xl font-semibold text-ink mt-1">{complaint.module.replace("_", " ")}</h1>
            </div>
            <div className="flex flex-col items-end gap-2">
              <StatusStamp status={complaint.status} />
              <PriorityBadge priority={complaint.priority} />
            </div>
          </div>

          <p className="mt-4 text-ink whitespace-pre-wrap leading-relaxed border-t border-dashed border-ink/15 pt-4">
            {complaint.original_text}
          </p>

          {complaint.summary && (
            <p className="mt-3 text-sm text-ink-soft bg-white border border-ink/10 p-3">
              <span className="font-medium text-ink-faint">AI summary: </span>{complaint.summary}
            </p>
          )}

          {complaint.address && <p className="text-sm text-ink-faint mt-3">Location: {complaint.address}</p>}
          {complaint.latitude && (
            <p className="text-xs text-ink-faint font-mono">{complaint.latitude}, {complaint.longitude}</p>
          )}

          {complaint.images?.length > 0 && (
            <div className="mt-4 flex gap-3 flex-wrap">
              {complaint.images.map((img) => (
                <img key={img.id} src={`${API_ORIGIN}/uploads/${img.file_path}`} alt="" className="w-32 h-32 object-cover border border-ink/10" />
              ))}
            </div>
          )}
        </div>

        {message && <p className="text-sm text-stamp-teal mb-4">{message}</p>}
        {error && <p className="text-sm text-stamp-red mb-4">{error}</p>}

        {complaint.status !== "RESOLVED" && complaint.status !== "REJECTED" && (
          <>
            <Section title="Update status">
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="field-label">Status</label>
                  <select value={nextStatus} onChange={(e) => setNextStatus(e.target.value)} className="field-input w-48">
                    {NEXT_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
                  </select>
                </div>
                <div className="flex-1 min-w-[180px]">
                  <label className="field-label">Note (optional)</label>
                  <input value={note} onChange={(e) => setNote(e.target.value)} className="field-input" />
                </div>
                <button onClick={() => withFeedback(() => updateComplaintStatus(id, nextStatus, note))} className="btn-primary">
                  Update
                </button>
              </div>
            </Section>

            <Section title="Resolve this complaint">
              <div className="space-y-3">
                <div>
                  <label className="field-label">Resolution remarks</label>
                  <textarea rows={3} value={remarks} onChange={(e) => setRemarks(e.target.value)} className="field-input resize-none" />
                </div>
                <div>
                  <label className="field-label">Resolution proof photo (optional)</label>
                  <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setProofFile(e.target.files?.[0] || null)} className="text-sm" />
                </div>
                <div className="flex gap-3">
                  {proofFile && (
                    <button onClick={() => withFeedback(() => uploadResolutionProof(id, proofFile))} className="btn-secondary">
                      Upload proof
                    </button>
                  )}
                  <button
                    disabled={remarks.trim().length < 3}
                    onClick={() => withFeedback(() => resolveComplaint(id, remarks))}
                    className="btn-accent"
                  >
                    Mark resolved
                  </button>
                </div>
              </div>
            </Section>
          </>
        )}

        <Section title="Status history">
          {history.map((h) => (
            <div key={h.id} className="ledger-row flex items-center justify-between">
              <div className="flex items-center gap-3">
                <StatusStamp status={h.to_status} />
                {h.note && <span className="text-sm text-ink-faint">{h.note}</span>}
              </div>
              <span className="text-xs text-ink-faint">{new Date(h.created_at).toLocaleString()}</span>
            </div>
          ))}
        </Section>
      </div>
    </OfficerLayout>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-paper-raised border border-ink/10 p-6 mb-6">
      <h2 className="font-display text-lg font-semibold text-ink mb-4">{title}</h2>
      {children}
    </div>
  );
}
