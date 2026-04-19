import { useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { FileDropZone } from '@/components/FileDropZone';
import { SimpleTable } from '@/components/Table';
import { uploadFile, uploadFiles } from '@/lib/api';
import type { ImportPreviewResponse } from '@/lib/types';

interface ImportResult {
  batch_id: number;
  import_type: string;
  rows: number;
  filename: string;
}

export function ImportsPage() {
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [working, setWorking] = useState(false);
  const [lastImports, setLastImports] = useState<ImportResult[]>([]);

  async function previewFile(file: File) {
    const data = await uploadFile<ImportPreviewResponse>('/imports/preview', file);
    setPreview(data);
  }

  async function importSelected(files: File[]) {
    setWorking(true);
    try {
      const result = await uploadFiles<{ imports: ImportResult[]; count: number }>('/imports', files);
      setLastImports(result.imports);
      toast.success(`Imported ${result.count} file${result.count === 1 ? '' : 's'}`);
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
          multiple
          onFiles={(files: File[]) => {
            setSelectedFiles(files);
            setLastImports([]);
            previewFile(files[0]).catch((e) => toast.error(e instanceof Error ? e.message : 'Preview failed'));
          }}
          label="Preview or queue files"
          hint="Accepts CSV and Excel uploads, including multiple files at once"
          selectedFiles={selectedFiles}
          isLoading={working}
        />
        {selectedFiles.length ? (
          <div className="flex gap-3 flex-wrap items-center">
            <button onClick={() => importSelected(selectedFiles)} disabled={working}>
              {working ? 'Importing...' : `Import ${selectedFiles.length} file${selectedFiles.length === 1 ? '' : 's'}`}
            </button>
            <div className="text-sm text-muted-foreground">
              {selectedFiles.map((file) => file.name).join(', ')}
            </div>
          </div>
        ) : null}
      </div>

      {lastImports.length ? (
        <div className="rounded-lg border border-border bg-card p-4 mb-6 text-sm">
          <strong>Last import complete.</strong>
          <div className="mt-2">
            {lastImports.map((result) => (
              <div key={`${result.batch_id}-${result.filename}`}>
                {result.filename}: batch {result.batch_id}, type {result.import_type}, rows {result.rows}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {preview ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-card p-4 text-sm">
            <div><strong>Detected:</strong> {preview.detected_type}</div>
            <div><strong>Missing columns:</strong> {preview.missing_columns.join(', ') || 'none'}</div>
            <div><strong>Extra columns:</strong> {preview.extra_columns.join(', ') || 'none'}</div>
            <div><strong>Preview rows:</strong> {preview.preview_rows.length}</div>
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
