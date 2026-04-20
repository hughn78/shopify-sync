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
      const message = body?.detail ?? body?.message ?? JSON.stringify(body);
      return new ApiError(response.status, String(message), body);
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

export async function uploadFiles<T>(path: string, files: File[]): Promise<T> {
  const form = new FormData();
  for (const file of files) {
    form.append('files', file);
  }
  const response = await fetch(`/api${path}`, {
    method: 'POST',
    body: form,
  });
  if (!response.ok) {
    throw await parseErrorResponse(response);
  }
  return response.json();
}

export async function uploadFile<T>(path: string, file: File): Promise<T> {
  return uploadFiles<T>(path, [file]);
}
