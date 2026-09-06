import { useEffect, useState } from "react";
import AdminLayout from "../../layouts/AdminLayout";
import LoadingSpinner from "../../components/LoadingSpinner";
import { listModules } from "../../services/catalogService";
import {
  createCategory, createDepartment, deleteCategory, deleteDepartment, listDepartments, updateCategory,
} from "../../services/departmentService";
import { apiErrorMessage } from "../../services/api";

const MODULES = ["GOVERNMENT_SCHOOLS", "AGRICULTURE", "HEALTHCARE", "TRAFFIC"];

export default function Departments() {
  const [departments, setDepartments] = useState([]);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [newDept, setNewDept] = useState({ name: "", module: MODULES[0], contactEmail: "" });
  const [newCategory, setNewCategory] = useState({ moduleId: "", nameEn: "", nameTe: "", nameHi: "", keywords: "" });

  const load = () => {
    setLoading(true);
    Promise.all([listDepartments(), listModules()])
      .then(([d, m]) => { setDepartments(d); setModules(m); })
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const handleCreateDept = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await createDepartment({ name: newDept.name, module: newDept.module, contact_email: newDept.contactEmail || undefined });
      setNewDept({ name: "", module: MODULES[0], contactEmail: "" });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const handleDeleteDept = async (id) => {
    if (!confirm("Delete this department? Complaints assigned to it will become unassigned.")) return;
    try {
      await deleteDepartment(id);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await createCategory({
        module_id: newCategory.moduleId, name_en: newCategory.nameEn, name_te: newCategory.nameTe || newCategory.nameEn,
        name_hi: newCategory.nameHi || newCategory.nameEn, keywords: newCategory.keywords || undefined,
      });
      setNewCategory({ moduleId: "", nameEn: "", nameTe: "", nameHi: "", keywords: "" });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const handleToggleCategory = async (cat) => {
    try {
      await updateCategory(cat.id, { is_active: !cat.is_active });
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!confirm("Delete this category?")) return;
    try {
      await deleteCategory(id);
      load();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <LoadingSpinner />
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="p-8 max-w-4xl space-y-8">
        <h1 className="font-display text-2xl font-semibold text-ink">Departments & Categories</h1>
        {error && <p className="text-sm text-stamp-red">{error}</p>}

        {/* Departments */}
        <section className="bg-paper-raised border border-ink/10 p-6">
          <h2 className="font-display text-lg font-semibold text-ink mb-4">Departments</h2>
          <div className="mb-5">
            {departments.map((d) => (
              <div key={d.id} className="ledger-row flex items-center justify-between">
                <div>
                  <p className="text-ink font-medium">{d.name}</p>
                  <p className="text-xs text-ink-faint">{d.module.replace("_", " ")} {d.contact_email ? `· ${d.contact_email}` : ""}</p>
                </div>
                <button onClick={() => handleDeleteDept(d.id)} className="text-xs text-stamp-red">Delete</button>
              </div>
            ))}
          </div>
          <form onSubmit={handleCreateDept} className="flex flex-wrap items-end gap-3 border-t border-dashed border-ink/15 pt-4">
            <div>
              <label className="field-label">Name</label>
              <input required value={newDept.name} onChange={(e) => setNewDept((f) => ({ ...f, name: e.target.value }))} className="field-input w-56" />
            </div>
            <div>
              <label className="field-label">Module</label>
              <select value={newDept.module} onChange={(e) => setNewDept((f) => ({ ...f, module: e.target.value }))} className="field-input w-48">
                {MODULES.map((m) => <option key={m} value={m}>{m.replace("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Contact email</label>
              <input value={newDept.contactEmail} onChange={(e) => setNewDept((f) => ({ ...f, contactEmail: e.target.value }))} className="field-input w-56" />
            </div>
            <button type="submit" className="btn-primary">Add department</button>
          </form>
        </section>

        {/* Categories */}
        <section className="bg-paper-raised border border-ink/10 p-6">
          <h2 className="font-display text-lg font-semibold text-ink mb-4">Categories</h2>
          {modules.map((m) => (
            <div key={m.id} className="mb-5">
              <p className="text-sm font-medium text-ink-soft mb-1">{m.name_en}</p>
              {m.categories.map((c) => (
                <div key={c.id} className="ledger-row flex items-center justify-between">
                  <span className={c.is_active ? "text-ink" : "text-ink-faint line-through"}>{c.name_en}</span>
                  <div className="flex items-center gap-3 text-xs">
                    <button onClick={() => handleToggleCategory(c)} className="text-ink-soft underline underline-offset-2">
                      {c.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button onClick={() => handleDeleteCategory(c.id)} className="text-stamp-red">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          ))}

          <form onSubmit={handleCreateCategory} className="grid sm:grid-cols-2 gap-3 border-t border-dashed border-ink/15 pt-4">
            <div>
              <label className="field-label">Module</label>
              <select
                required value={newCategory.moduleId}
                onChange={(e) => setNewCategory((f) => ({ ...f, moduleId: e.target.value }))} className="field-input"
              >
                <option value="">Select module</option>
                {modules.map((m) => <option key={m.id} value={m.id}>{m.name_en}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Name (English)</label>
              <input required value={newCategory.nameEn} onChange={(e) => setNewCategory((f) => ({ ...f, nameEn: e.target.value }))} className="field-input" />
            </div>
            <div>
              <label className="field-label">Name (Telugu)</label>
              <input value={newCategory.nameTe} onChange={(e) => setNewCategory((f) => ({ ...f, nameTe: e.target.value }))} className="field-input" />
            </div>
            <div>
              <label className="field-label">Name (Hindi)</label>
              <input value={newCategory.nameHi} onChange={(e) => setNewCategory((f) => ({ ...f, nameHi: e.target.value }))} className="field-input" />
            </div>
            <div className="sm:col-span-2">
              <label className="field-label">Keywords (comma-separated, powers demo AI matching)</label>
              <input value={newCategory.keywords} onChange={(e) => setNewCategory((f) => ({ ...f, keywords: e.target.value }))} className="field-input" />
            </div>
            <button type="submit" className="btn-primary sm:col-span-2">Add category</button>
          </form>
        </section>
      </div>
    </AdminLayout>
  );
}
