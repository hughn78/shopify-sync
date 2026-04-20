import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { FileDropZone } from '@/components/FileDropZone';
import { ProgressBar } from '@/components/ProgressBar';
import { SimpleTable } from '@/components/Table';
import { api, uploadFile, uploadFiles } from '@/lib/api';
import type { ImportBatch, ImportPreviewResponse, PaginatedResponse } from '@/lib/types';

interface ImportResult {
  batch_id: number;
  import_type: string;
  rows: number;
  filename: string;
  row_errors?: { row: number; error: string }[];
}

const IMPORT_FILTERS = ['ALL', 'SHOPIFY_PRODUCTS', 'SHOPIFY_INVENTORY', 'FOS', 'PRICEBOOK', 'MASTERCATALOG', 'SCRAPED_CATALOG'] as const;

export function ImportsPage() {
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [working, setWorking] = useState(false);
  const [stage, setStage] = useState<'idle' | 'previewing' | 'ready' | 'processing' | 'done' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('Choose files to begin.');
  const [progressCurrent, setProgressCurrent] = useState(0);
  const [progressTotal, setProgressTotal] = useState(0);
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
    setStage('previewing');
    setStatusMessage(`Inspecting ${file.name}...`);
    const data = await uploadFile<ImportPreviewResponse>('/imports/preview', file);
    setPreview(data);
    setStage('ready');
    setStatusMessage(`Ready to process ${selectedFiles.length || 1} file${(selectedFiles.length || 1) === 1 ? '' : 's'}. Review the preview, then press Process.`);
  }

  async function importSelected(files: File[]) {
    setWorking(true);
    setStage('processing');
    setProgressCurrent(0);
    setProgressTotal(files.length);
    setStatusMessage(`Uploading ${files.length} file${files.length === 1 ? '' : 's'} into the database...`);
    try {
      const result = await uploadFiles<{ imports: ImportResult[]; count: number }>('/imports', files);
      setProgressCurrent(result.count);
      setLastImports(result.imports);
      setStage('done');
      setStatusMessage(`Processed ${result.count} file${result.count === 1 ? '' : 's'} successfully.`);
      toast.success(`Imported ${result.count} file${result.count === 1 ? '' : 's'}`);
      loadBatches();
    } catch (error) {
      setStage('error');
      setStatusMessage(error instanceof Error ? error.message : 'Import failed');
      toast.error(error instanceof Error ? error.message : 'Import failed');
    } finally {
      setWorking(false);
    }
  }

  function resetSelection() {
    setSelectedFiles([]);
    setPreview(null);
    setLastImports([]);
    setStage('idle');
    setStatusMessage('Choose files to begin.');
    setProgressCurrent(0);
    setProgressTotal(0);
  }

  const canProcess = selectedFiles.length > 0 && !working;
  const stageTone = stage === 'error'
    ? 'border-red-200 bg-red-50'
    : stage === 'done'
      ? 'border-green-200 bg-green-50'
      : 'border-border bg-card';

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
            setProgressCurrent(0);
            setProgressTotal(files.length);
            setStage('ready');
            setStatusMessage(`${files.length} file${files.length === 1 ? '' : 's'} queued. Previewing the first file now.`);
            previewFile(files[0]).catch((e) => toast.error(e instanceof Error ? e.message : 'Preview failed'));
          }}
          label="Choose files for processing"
          hint="Select CSV or Excel files, review the preview, then press Process"
          selectedFiles={selectedFiles}
          isLoading={working}
        />
        <div className={`rounded-lg border p-4 transition-colors ${stageTone}`}>
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <div className="text-xs uppercase text-muted-foreground">Import status</div>
                <div className="text-sm font-medium mt-1">{statusMessage}</div>
              </div>
              <div className="flex gap-2 flex-wrap">
                <button onClick={() => importSelected(selectedFiles)} disabled={!canProcess}>
                  {working ? 'Processing...' : `Process ${selectedFiles.length ? selectedFiles.length : ''} ${selectedFiles.length === 1 ? 'file' : 'files'}`.trim()}
                </button>
                <button onClick={resetSelection} disabled={working || (!selectedFiles.length && !preview && !lastImports.length)}>
                  Clear
                </button>
              </div>
            </div>

            {progressTotal > 0 ? (
              <ProgressBar
                current={stage === 'done' ? progressTotal : progressCurrent}
                total={progressTotal}
                label={stage === 'processing' ? 'Uploading and importing' : 'Files prepared'}
              />
            ) : null}

            {selectedFiles.length ? (
              <div className="text-sm text-muted-foreground">
                {selectedFiles.map((file, index) => (
                  <div key={`${file.name}-${index}`}>
                    {index + 1}. {file.name}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {lastImports.length ? (
        <div className="rounded-lg border border-border bg-card p-4 mb-6 text-sm">
          <strong>Last import complete.</strong>
          <div className="mt-2">
            {lastImports.map((result) => (
              <div key={`${result.batch_id}-${result.filename}`}>
                <strong>[{result.import_type}]</strong> {result.filename}: batch {result.batch_id}, rows {result.rows}
                {result.row_errors?.length ? (
                  <div className="text-xs text-amber-700 mt-1">
                    {result.row_errors.length} row error{result.row_errors.length === 1 ? '' : 's'} captured during import
                  </div>
                ) : null}
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
