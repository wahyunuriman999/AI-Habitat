/**
 * AI Habitat — API Client
 *
 * Consistent fetch wrapper for communicating with the backend API.
 * All responses follow the {success, data, error, meta} envelope.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiError {
  code: string;
  message: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
  meta: Record<string, unknown>;
}

/**
 * GET request to the API.
 * Returns the parsed response envelope.
 * Throws only on network-level failures (not API errors).
 */
export async function apiGet<T>(path: string): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.json() as Promise<ApiResponse<T>>;
}

/**
 * POST request to the API.
 */
export async function apiPost<T>(
  path: string,
  body: unknown,
): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return response.json() as Promise<ApiResponse<T>>;
}

/**
 * PATCH request to the API.
 */
export async function apiPatch<T>(
  path: string,
  body: unknown,
): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return response.json() as Promise<ApiResponse<T>>;
}

/**
 * DELETE request to the API.
 */
export async function apiDelete<T>(path: string): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  });
  return response.json() as Promise<ApiResponse<T>>;
}
