import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { FileDropZone } from '@/components/FileDropZone';
import { SimpleTable } from '@/components/Table';
import { api, uploadFile, uploadFiles } from '@/lib/api';
import type { ImportBatch, ImportPreviewResponse, PaginatedResponse } from '@/lib/types';

interface ImportResult {
  batch_id: number;
  import_type: string;
  rows: number;
  filename: string;
}

const IMPORT_FILTERS = ['ALL', 'SHOPIFY_PRODUCTS', 'SHOPIFY_INVENTORY', 'FOS', 'PRICEBOOK', 'MASTERCATALOG', 'SCRAPED_CATALOG'] as const;

export function ImportsPage() {
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [working, setWorking] = useState(false);
  const [lastImports, setLastImports] = useState<ImportResult[]>([]);
  const [importBatches, setImportBatches] = useState<ImportBatch[]>([]);
  const [filter, setFilter] = useState<(typeof IMPORT_FILTERS)[number]>('ALL');

  function loadBatches() {
    const suffix = filter === 'ALL' ? '' : `?import_type=${encodeURIComponent(filter)}`;
    api<PaginatedResponse<ImportBatch>>(`/import-batches${suffix}`).then(r => setImportBatches(r.items)).catch(console.error);
  }

  useEffect(() => {
    loadBatches();
  }, [filter]);

  const importCounts = useMemo(() => {
    const counts = Object.fromEntries(IMPORT_FILTERS.map((value) => [value, 0])) as Record<(typeof IMPORT_FILTERS)[number], number>;
    counts.ALL = importBatches.length;
    for (const batch of importBatches) {
      const key = batch.import_type as (typeof IMPORT_FILTERS)[number];
      if (key in counts) counts[key] += 1;
    }
    return counts;
  }, [importBatches]);

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
      loadBatches();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Import failed');
    } finally {
      setWorking(false);
    }
  }

  return (
    <div>
      <PageHeader title="Imports" subtitle="Upload Shopify, FOS, pricebooks, mastercatalogs, and scraped catalog files into the registry." />
      <div className="flex gap-2 mb-4 flex-wrap">
        {IMPORT_FILTERS.map((value) => (
          <button key={value} onClick={() => setFilter(value)}>
            {value} ({value === 'ALL' ? importBatches.length : importBatches.filter((batch) => batch.import_type === value).length})
          </button>
        ))}
      </div>

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
                <strong>[{result.import_type}]</strong> {result.filename}: batch {result.batch_id}, rows {result.rows}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {preview ? (
        <div className="space-y-4 mb-6">
          <div className="rounded-lg border border-border bg-card p-4 text-sm">
            <div><strong>Detected:</strong> <Badge value={preview.detected_type} /></div>
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

      <SimpleTable
        columns={['ID', 'Type', 'Filename', 'Rows', 'Status', 'Created']}
        rows={importBatches.map((batch) => [
          batch.id,
          <Badge value={batch.import_type} />,
          batch.filename,
          batch.row_count,
          batch.status,
          new Date(batch.created_at).toLocaleString(),
        ])}
      />
    </div>
  );
}

function Badge({ value }: { value: string }) {
  return <span className="rounded border px-2 py-1 text-xs">{value}</span>;
}
