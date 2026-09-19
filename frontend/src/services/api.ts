/**
 * Single fetch wrapper every service module goes through. Centralizing
 * this — base URL, auth header injection, error handling — means a
 * change to any of those only happens here, never in a component.
 */
const configuredBaseUrl = String(import.meta.env.VITE_API_BASE_URL ?? "").trim();
const API_BASE_URL = (configuredBaseUrl || "http://localhost:8000/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("ems_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      /* no JSON body */
    }
    if (response.status === 401) {
      localStorage.removeItem("ems_access_token");
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

export const api = {
  get: <T>(path: string) =>
    fetch(`${API_BASE_URL}${path}`, { headers: { ...authHeaders() } }).then((r) => handleResponse<T>(r)),

  post: <T>(path: string, body?: object) =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }).then((r) => handleResponse<T>(r)),

  put: <T>(path: string, body: object) =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body),
    }).then((r) => handleResponse<T>(r)),

  patch: <T>(path: string, body: object) =>
    fetch(`${API_BASE_URL}${path}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(body),
    }).then((r) => handleResponse<T>(r)),

  delete: <T>(path: string) =>
    fetch(`${API_BASE_URL}${path}`, { method: "DELETE", headers: { ...authHeaders() } }).then((r) =>
      handleResponse<T>(r)
    ),

  upload: <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { ...authHeaders() },
      body: formData,
    }).then((r) => handleResponse<T>(r));
  },
};
