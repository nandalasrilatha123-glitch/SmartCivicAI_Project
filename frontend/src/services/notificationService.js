import api from "./api";

export async function listNotifications(params = {}) {
  const { data } = await api.get("/notifications", { params });
  return data;
}

export async function getUnreadCount() {
  const { data } = await api.get("/notifications/unread-count");
  return data.unread_count;
}

export async function markNotificationRead(id) {
  const { data } = await api.patch(`/notifications/${id}/read`);
  return data;
}

export async function markAllRead() {
  await api.patch("/notifications/read-all");
}
