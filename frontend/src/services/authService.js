import api from "./api";

export async function register({ fullName, email, phone, password, preferredLanguage }) {
  const { data } = await api.post("/auth/register", {
    full_name: fullName,
    email,
    phone: phone || undefined,
    password,
    preferred_language: preferredLanguage,
  });
  return data;
}

export async function login({ email, password }) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function getMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function updateMe(payload) {
  const { data } = await api.patch("/auth/me", payload);
  return data;
}
