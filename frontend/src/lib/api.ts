const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("access_token")
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    if (typeof window !== "undefined") window.location.href = "/login"
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail || "Request failed")
  }
  return res.json()
}

export const auth = {
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string; refresh_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string) =>
    apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => apiFetch<{ id: number; email: string }>("/auth/me"),
}

export const urls = {
  list: (workspace_id: number) =>
    apiFetch<{ id: number; short_code: string; original_url: string; created_at: string }[]>(
      `/urls/?workspace_id=${workspace_id}`
    ),
  create: (data: { original_url: string; workspace_id: number; custom_alias?: string }) =>
    apiFetch("/urls/", { method: "POST", body: JSON.stringify(data) }),
  delete: (id: number) =>
    apiFetch(`/urls/${id}`, { method: "DELETE" }),
}

export const workspaces = {
  list: () => apiFetch<{ id: number; name: string; owner_id: number }[]>("/workspaces/"),
}
