import api from "./api";

export async function listUsers(params) {
  const { data } = await api.get("/users", { params });
  return data;
}

export async function createOfficer(payload) {
  const { data } = await api.post("/users/officers", payload);
  return data;
}

export async function updateUserStatus(userId, isActive) {
  const { data } = await api.patch(`/users/${userId}/status`, { is_active: isActive });
  return data;
}

export async function listAuditLogs(params) {
  const { data } = await api.get("/audit-logs", { params });
  return data;
}
