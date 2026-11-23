/**
 * Cliente HTTP para a API do Web ERP.
 *
 * Os erros da API chegam como {code, message, details}; são convertidos em ApiError
 * para os ecrãs mostrarem a mensagem certa (ver i18n/pt-MZ.json).
 */
export const API_URL = process.env.WEBERP_API_URL ?? process.env.NEXT_PUBLIC_WEBERP_API_URL ?? '/api/v1';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiOptions extends Omit<RequestInit, 'body'> {
  accessToken?: string | null;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { accessToken, body, query, headers, ...init } = options;
  const url = new URL(`${API_URL}${path}`, typeof window === 'undefined' ? 'http://localhost' : window.location.origin);
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined) url.searchParams.set(key, String(value));
  });

  const res = await fetch(API_URL.startsWith('http') ? url : `${url.pathname}${url.search}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers
    },
    body: body !== undefined ? JSON.stringify(body) : undefined
  });

  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(res.status, data?.code ?? 'UNKNOWN_ERROR', data?.message ?? res.statusText, data?.details);
  }
  return data as T;
}
