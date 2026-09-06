import api from "./api";

export async function listDepartments(module) {
  const { data } = await api.get("/departments", { params: module ? { module } : {} });
  return data;
}

export async function createDepartment(payload) {
  const { data } = await api.post("/departments", payload);
  return data;
}

export async function updateDepartment(id, payload) {
  const { data } = await api.patch(`/departments/${id}`, payload);
  return data;
}

export async function deleteDepartment(id) {
  await api.delete(`/departments/${id}`);
}

export async function createCategory(payload) {
  const { data } = await api.post("/categories", payload);
  return data;
}

export async function updateCategory(id, payload) {
  const { data } = await api.patch(`/categories/${id}`, payload);
  return data;
}

export async function deleteCategory(id) {
  await api.delete(`/categories/${id}`);
}
