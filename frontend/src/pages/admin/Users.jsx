import { useEffect, useState } from "react";
import AdminLayout from "../../layouts/AdminLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import { listDepartments } from "../../services/departmentService";
import { createOfficer, listUsers, updateUserStatus } from "../../services/userService";
import { apiErrorMessage } from "../../services/api";

const ROLES = ["CITIZEN", "OFFICER", "ADMIN"];

export default function Users() {
  const [role, setRole] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [officerForm, setOfficerForm] = useState({
    fullName: "", email: "", phone: "", password: "", departmentId: "",
  });
  const [showOfficerForm, setShowOfficerForm] = useState(false);

  const load = () => {
    setLoading(true);
    const params = { page, page_size: 20 };
    if (role) params.role = role;
    if (search) params.search = search;
    Promise.all([listUsers(params), listDepartments()])
      .then(([u, d]) => { setData(u); setDepartments(d); })
      .finally(() => setLoading(false));
  };
  useEffect(load, [role, search, page]);

  const handleToggleActive = async (user) => {
    setError("");
    try {
      await updateUserStatus(user.id, !user.is_active);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const handleCreateOfficer = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      await createOfficer({
        full_name: officerForm.fullName, email: officerForm.email, phone: officerForm.phone || undefined,
        password: officerForm.password, department_id: officerForm.departmentId,
      });
      setMessage("Officer account created.");
      setOfficerForm({ fullName: "", email: "", phone: "", password: "", departmentId: "" });
      setShowOfficerForm(false);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  return (
    <AdminLayout>
      <div className="p-8 max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="font-display text-2xl font-semibold text-ink">Users & Officers</h1>
          <button onClick={() => setShowOfficerForm((s) => !s)} className="btn-accent">
            {showOfficerForm ? "Cancel" : "New officer account"}
          </button>
        </div>

        {message && <p className="text-sm text-stamp-teal mb-4">{message}</p>}
        {error && <p className="text-sm text-stamp-red mb-4">{error}</p>}

        {showOfficerForm && (
          <form onSubmit={handleCreateOfficer} className="bg-paper-raised border border-ink/10 p-6 mb-6 grid sm:grid-cols-2 gap-3">
            <div>
              <label className="field-label">Full name</label>
              <input required value={officerForm.fullName} onChange={(e) => setOfficerForm((f) => ({ ...f, fullName: e.target.value }))} className="field-input" />
            </div>
            <div>
              <label className="field-label">Email</label>
              <input required type="email" value={officerForm.email} onChange={(e) => setOfficerForm((f) => ({ ...f, email: e.target.value }))} className="field-input" />
            </div>
            <div>
              <label className="field-label">Phone</label>
              <input value={officerForm.phone} onChange={(e) => setOfficerForm((f) => ({ ...f, phone: e.target.value }))} className="field-input" />
            </div>
            <div>
              <label className="field-label">Temporary password</label>
              <input required type="text" minLength={8} value={officerForm.password} onChange={(e) => setOfficerForm((f) => ({ ...f, password: e.target.value }))} className="field-input" />
            </div>
            <div className="sm:col-span-2">
              <label className="field-label">Department</label>
              <select required value={officerForm.departmentId} onChange={(e) => setOfficerForm((f) => ({ ...f, departmentId: e.target.value }))} className="field-input">
                <option value="">Select department</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name} ({d.module.replace("_", " ")})</option>)}
              </select>
            </div>
            <button type="submit" className="btn-primary sm:col-span-2">Create officer</button>
          </form>
        )}

        <div className="flex flex-wrap gap-3 mb-5">
          <input placeholder="Search name or email..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="field-input w-64" />
          <select value={role} onChange={(e) => { setRole(e.target.value); setPage(1); }} className="field-input w-48">
            <option value="">All roles</option>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
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
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((u) => (
                    <tr key={u.id} className="border-b border-dashed border-ink/10">
                      <td className="py-3 px-4">{u.full_name}</td>
                      <td className="py-3 px-4 text-ink-faint">{u.email}</td>
                      <td className="py-3 px-4">{u.role}</td>
                      <td className="py-3 px-4">
                        <span className={u.is_active ? "text-stamp-teal" : "text-stamp-red"}>
                          {u.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <button onClick={() => handleToggleActive(u)} className="text-xs underline underline-offset-2 text-ink-soft">
                          {u.is_active ? "Deactivate" : "Activate"}
                        </button>
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
