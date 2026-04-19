import { ChangeEvent, useState } from 'react';
import { SimpleTable } from '../components/Table';

export function ImportsPage() {
  const [preview, setPreview] = useState<any>(null);
  const [message, setMessage] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);

  async function handlePreview(selected: File) {
    const form = new FormData();
    form.append('file', selected);
    const response = await fetch('/api/imports/preview', { method: 'POST', body: form });
    setPreview(await response.json());
  }

  async function handleImport() {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    const response = await fetch('/api/imports', { method: 'POST', body: form });
    const result = await response.json();
    setMessage(`Imported ${result.rows} rows as ${result.import_type} (batch ${result.batch_id})`);
  }

  return (
    <div>
      <h2>Imports</h2>
      <div className="panel stack">
        <input
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(event: ChangeEvent<HTMLInputElement>) => {
            const selected = event.target.files?.[0];
            if (!selected) return;
            setFile(selected);
            void handlePreview(selected);
          }}
        />
        <div className="button-row">
          <button onClick={handleImport} disabled={!file}>Import file</button>
        </div>
        {message ? <p>{message}</p> : null}
        {preview ? (
          <>
            <div className="warning-row">
              <span>Detected type: <strong>{preview.detected_type}</strong></span>
              <span>Missing columns: {preview.missing_columns.join(', ') || 'none'}</span>
              <span>Extra columns: {preview.extra_columns.join(', ') || 'none'}</span>
            </div>
            <SimpleTable
              columns={preview.columns}
              rows={preview.preview_rows.map((row: any) => preview.columns.map((column: string) => row.data[column] ?? ''))}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
