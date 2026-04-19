import { useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { FileDropZone } from '@/components/FileDropZone';
import { SimpleTable } from '@/components/Table';
import { uploadFile } from '@/lib/api';
import type { ImportPreviewResponse } from '@/lib/types';

export function ImportsPage() {
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [working, setWorking] = useState(false);

  async function previewFile(file: File) {
    setSelectedFile(file);
    const data = await uploadFile<ImportPreviewResponse>('/imports/preview', file);
    setPreview(data);
  }

  async function importSelected(file: File) {
    setWorking(true);
    try {
      const result = await uploadFile<{ batch_id: number; import_type: string; rows: number }>('/imports', file);
      toast.success(`Imported ${result.rows} rows as ${result.import_type}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Import failed');
    } finally {
      setWorking(false);
    }
  }

  return (
    <div>
      <PageHeader title="Imports" subtitle="Upload Shopify Products, Shopify Inventory, and FOS files into the canonical registry." />
      <div className="rounded-lg border border-border bg-card p-5 flex flex-col gap-4 mb-6">
        <FileDropZone
          accept=".csv,.xlsx,.xls"
          onFile={(file: File) => {
            previewFile(file).catch((e) => toast.error(e instanceof Error ? e.message : 'Preview failed'));
          }}
          label="Preview file"
          hint="Accepts CSV and Excel uploads"
          selectedFile={selectedFile}
          isLoading={working}
        />
        {selectedFile ? (
          <div className="flex gap-3">
            <button onClick={() => importSelected(selectedFile)} disabled={working}>
              {working ? 'Importing...' : 'Import file'}
            </button>
          </div>
        ) : null}
      </div>

      {preview ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4 text-sm">
            <div><strong>Detected:</strong> {preview.detected_type}</div>
            <div><strong>Missing columns:</strong> {preview.missing_columns.join(', ') || 'none'}</div>
            <div><strong>Extra columns:</strong> {preview.extra_columns.join(', ') || 'none'}</div>
          </div>
          <SimpleTable
            columns={preview.columns}
            rows={preview.preview_rows.map((row: ImportPreviewResponse['preview_rows'][number]) =>
              preview.columns.map((column: string) => String(row.data[column] ?? '')),
            )}
          />
        </div>
      ) : null}
    </div>
  );
}
