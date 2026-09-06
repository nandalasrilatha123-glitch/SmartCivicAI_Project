import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AdminLayout from "../../layouts/AdminLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import StatusStamp from "../../components/StatusStamp";
import PriorityBadge from "../../components/PriorityBadge";
import {
  assignComplaint, getComplaint, getComplaintHistory, overrideComplaint, updateComplaintStatus,
} from "../../services/complaintService";
import { listDepartments } from "../../services/departmentService";
import { listUsers } from "../../services/userService";
import { listModules } from "../../services/catalogService";
import { apiErrorMessage } from "../../services/api";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];
const STATUSES = ["NEW", "PENDING", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED", "ESCALATED", "REQUIRES_ADMIN_REVIEW"];
const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");

export default function AdminComplaintDetail() {
  const { id } = useParams();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [officers, setOfficers] = useState([]);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [statusForm, setStatusForm] = useState({ status: "", note: "" });
  const [assignForm, setAssignForm] = useState({ departmentId: "", assignedOfficerId: "" });
  const [overrideForm, setOverrideForm] = useState({ module: "", categoryId: "", priority: "", departmentId: "" });

  const load = () => {
    setLoading(true);
    Promise.all([getComplaint(id), getComplaintHistory(id), listDepartments(), listModules(), listUsers({ role: "OFFICER", page_size: 100 })])
      .then(([c, h, depts, mods, off]) => {
        setComplaint(c);
        setHistory(h);
        setDepartments(depts);
        setModules(mods);
        setOfficers(off.items);
        setStatusForm({ status: c.status, note: "" });
        setAssignForm({ departmentId: c.department_id || "", assignedOfficerId: c.assigned_officer_id || "" });
        setOverrideForm({ module: c.module, categoryId: c.category_id || "", priority: c.priority, departmentId: c.department_id || "" });
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

  const currentModuleCategories = modules.find((m) => m.code === overrideForm.module)?.categories || [];
  const officersInDept = officers.filter((o) => o.department_id === assignForm.departmentId);

  if (loading || !complaint) {
    return (
      <AdminLayout>
        <LoadingSpinner />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="p-8 max-w-3xl">
        <Link to="/admin/complaints" className="text-sm text-ink-faint hover:text-ink mb-4 inline-block">
          ← Back to complaints
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
          {complaint.images?.length > 0 && (
            <div className="mt-4 flex gap-3 flex-wrap">
              {complaint.images.map((img) => (
                <img key={img.id} src={`${API_ORIGIN}/uploads/${img.file_path}`} alt="" className="w-28 h-28 object-cover border border-ink/10" />
              ))}
            </div>
          )}
        </div>

        {message && <p className="text-sm text-stamp-teal mb-4">{message}</p>}
        {error && <p className="text-sm text-stamp-red mb-4">{error}</p>}

        {/* Status update */}
        <Section title="Update status">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="field-label">Status</label>
              <select
                value={statusForm.status} onChange={(e) => setStatusForm((f) => ({ ...f, status: e.target.value }))}
                className="field-input w-56"
              >
                {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
              </select>
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className="field-label">Note (optional)</label>
              <input
                value={statusForm.note} onChange={(e) => setStatusForm((f) => ({ ...f, note: e.target.value }))}
                className="field-input"
              />
            </div>
            <button
              onClick={() => withFeedback(() => updateComplaintStatus(id, statusForm.status, statusForm.note))}
              className="btn-primary"
            >
              Update
            </button>
          </div>
        </Section>

        {/* Assignment */}
        <Section title="Assign department / officer">
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="field-label">Department</label>
              <select
                value={assignForm.departmentId}
                onChange={(e) => setAssignForm({ departmentId: e.target.value, assignedOfficerId: "" })}
                className="field-input w-56"
              >
                <option value="">—</option>
                {departments.filter((d) => d.module === complaint.module).map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="field-label">Officer</label>
              <select
                value={assignForm.assignedOfficerId}
                onChange={(e) => setAssignForm((f) => ({ ...f, assignedOfficerId: e.target.value }))}
                className="field-input w-56" disabled={!assignForm.departmentId}
              >
                <option value="">—</option>
                {officersInDept.map((o) => <option key={o.id} value={o.id}>{o.full_name}</option>)}
              </select>
            </div>
            <button onClick={() => withFeedback(() => assignComplaint(id, assignForm))} className="btn-primary">
              Assign
            </button>
          </div>
        </Section>

        {/* AI override */}
        <Section title="Override AI decision" subtitle="Every change here is recorded in the audit log.">
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="field-label">Module</label>
              <select
                value={overrideForm.module}
                onChange={(e) => setOverrideForm((f) => ({ ...f, module: e.target.value, categoryId: "" }))}
                className="field-input"
              >
                {MODULES.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Category</label>
              <select
                value={overrideForm.categoryId}
                onChange={(e) => setOverrideForm((f) => ({ ...f, categoryId: e.target.value }))}
                className="field-input"
              >
                <option value="">—</option>
                {currentModuleCategories.map((c) => <option key={c.id} value={c.id}>{c.name_en}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Priority</label>
              <select
                value={overrideForm.priority}
                onChange={(e) => setOverrideForm((f) => ({ ...f, priority: e.target.value }))}
                className="field-input"
              >
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Department</label>
              <select
                value={overrideForm.departmentId}
                onChange={(e) => setOverrideForm((f) => ({ ...f, departmentId: e.target.value }))}
                className="field-input"
              >
                <option value="">—</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={() =>
              withFeedback(() =>
                overrideComplaint(id, {
                  module: overrideForm.module || undefined,
                  category_id: overrideForm.categoryId || undefined,
                  priority: overrideForm.priority || undefined,
                  department_id: overrideForm.departmentId || undefined,
                })
              )
            }
            className="btn-secondary mt-4"
          >
            Apply override
          </button>
        </Section>

        {/* History */}
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
    </AdminLayout>
  );
}

function Section({ title, subtitle, children }) {
  return (
    <div className="bg-paper-raised border border-ink/10 p-6 mb-6">
      <h2 className="font-display text-lg font-semibold text-ink mb-1">{title}</h2>
      {subtitle && <p className="text-xs text-ink-faint mb-4">{subtitle}</p>}
      {!subtitle && <div className="mb-1" />}
      {children}
    </div>
  );
}
