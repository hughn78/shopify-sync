export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    try {
      const body = await response.json();
      // FastAPI validation errors return detail as an array of {loc, msg, type}
      let message: string;
      if (Array.isArray(body?.detail)) {
        message = body.detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join('; ');
      } else {
        message = String(body?.detail ?? body?.message ?? JSON.stringify(body));
      }
      return new ApiError(response.status, message, body);
    } catch {
      // fall through to text
    }
  }
  const text = await response.text();
  return new ApiError(response.status, text || `Request failed: ${response.status}`);
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'Content-Type': init?.body instanceof FormData ? undefined as never : 'application/json',
      ...(init?.headers || {}),
    },
    body: init?.body,
  });
  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
  return response.json();
}

// Single file upload — field name 'file' (matches FastAPI's preview endpoint)
export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`/api${path}`, { method: 'POST', body: form });
  if (!response.ok) throw await parseErrorResponse(response);
  return response.json();
}

// Multi-file upload — field name 'files' (matches FastAPI's import endpoint)
export async function uploadFiles<T>(path: string, files: File[]): Promise<T> {
  const form = new FormData();
  for (const file of files) {
    form.append('files', file);
  }
  const response = await fetch(`/api${path}`, { method: 'POST', body: form });
  if (!response.ok) throw await parseErrorResponse(response);
  return response.json();
}
