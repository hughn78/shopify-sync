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
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`/api${path}`, {
    method: 'POST',
    body: form,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
