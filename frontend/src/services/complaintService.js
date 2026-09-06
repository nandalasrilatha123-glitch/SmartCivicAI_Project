import api from "./api";

export async function submitComplaint({ module, categoryId, description, originalLanguage, latitude, longitude, address, image }) {
  const form = new FormData();
  form.append("module", module);
  if (categoryId) form.append("category_id", categoryId);
  form.append("description", description);
  form.append("original_language", originalLanguage);
  if (latitude != null) form.append("latitude", latitude);
  if (longitude != null) form.append("longitude", longitude);
  if (address) form.append("address", address);
  if (image) form.append("image", image);

  const { data } = await api.post("/complaints", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listMyComplaints({ page = 1, pageSize = 20 } = {}) {
  const { data } = await api.get("/complaints", { params: { page, page_size: pageSize } });
  return data;
}

export async function getComplaint(id) {
  const { data } = await api.get(`/complaints/${id}`);
  return data;
}

export async function getComplaintHistory(id) {
  const { data } = await api.get(`/complaints/${id}/history`);
  return data;
}

export async function submitFeedback(id, { rating, comment }) {
  const { data } = await api.post(`/complaints/${id}/feedback`, { rating, comment: comment || undefined });
  return data;
}

// --- Admin/officer functions ---

export async function listComplaints(filters = {}) {
  const { data } = await api.get("/complaints", { params: filters });
  return data;
}

export async function updateComplaintStatus(id, status, note) {
  const { data } = await api.patch(`/complaints/${id}/status`, { status, note: note || undefined });
  return data;
}

export async function assignComplaint(id, { departmentId, assignedOfficerId }) {
  const { data } = await api.patch(`/complaints/${id}/assign`, {
    department_id: departmentId || undefined,
    assigned_officer_id: assignedOfficerId || undefined,
  });
  return data;
}

export async function overrideComplaint(id, payload) {
  const { data } = await api.patch(`/complaints/${id}/override`, payload);
  return data;
}

export async function resolveComplaint(id, officerRemarks) {
  const { data } = await api.post(`/complaints/${id}/resolve`, { officer_remarks: officerRemarks });
  return data;
}

export async function acceptComplaint(id) {
  const { data } = await api.post(`/complaints/${id}/accept`);
  return data;
}

export async function uploadResolutionProof(id, file) {
  const form = new FormData();
  form.append("proof", file);
  const { data } = await api.post(`/complaints/${id}/resolution-proof`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
