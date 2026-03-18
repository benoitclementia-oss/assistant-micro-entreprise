import type { ProfilData, SidebarData } from "@/types"

const BASE = "/api"

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...init,
  })
  if (res.status === 401) {
    throw new Error("API 401: Session expiree")
  }
  if (!res.ok) {
    let detail = ""
    try {
      const json = await res.json()
      detail = json.detail || ""
    } catch {
      detail = await res.text()
    }
    throw new Error(detail || `API ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function sendMessage(message: string): Promise<string> {
  const data = await apiFetch<{ response: string }>("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
    signal: AbortSignal.timeout(120_000),
  })
  return data.response
}

export async function clearHistory(): Promise<void> {
  await apiFetch("/chat/clear", { method: "POST" })
}

export async function getSidebarData(): Promise<SidebarData> {
  return apiFetch<SidebarData>("/sidebar")
}

export async function updateProfil(champs: Partial<ProfilData>): Promise<ProfilData> {
  return apiFetch<ProfilData>("/profil", {
    method: "PATCH",
    body: JSON.stringify(champs),
  })
}

export async function marquerEcheanceFaite(id: number): Promise<void> {
  await apiFetch(`/echeances/${id}/fait`, { method: "PATCH" })
}

export async function getDocumentContent(
  filename: string
): Promise<{ fichier: string; contenu: string }> {
  return apiFetch<{ fichier: string; contenu: string }>(
    `/documents/${encodeURIComponent(filename)}`
  )
}

export async function checkAuth(): Promise<boolean> {
  try {
    const data = await apiFetch<{ authenticated: boolean }>("/auth/check")
    return data.authenticated
  } catch {
    return false
  }
}

export async function login(password: string): Promise<{ status: string; message?: string }> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ password }),
  })
  return res.json()
}

export async function logout(): Promise<void> {
  await fetch(`${BASE}/auth/logout`, {
    method: "POST",
    credentials: "include",
  })
}
