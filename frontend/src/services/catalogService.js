import api from "./api";

export async function listModules() {
  const { data } = await api.get("/modules");
  return data;
}
