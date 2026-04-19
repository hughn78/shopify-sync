import { useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { SimpleTable } from '@/components/Table';
import { api } from '@/lib/api';

export function InventorySyncPage() {
  const [runId, setRunId] = useState<number | null>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [exportPath, setExportPath] = useState('');

  async function run() {
    try {
      const result = await api<{ run_id: number }>('/reconciliation-runs', { method: 'POST' });
      setRunId(result.run_id);
      const data = await api<any[]>(`/reconciliation-rows/${result.run_id}`);
      setRows(data);
      toast.success('Reconciliation run created');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Reconciliation failed');
    }
  }

  async function exportInventory() {
    if (!runId) return;
    try {
      const result = await api<{ file_path: string }>(`/exports/inventory/${runId}`, { method: 'POST' });
      setExportPath(result.file_path);
      toast.success('Inventory export created');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Export failed');
    }
  }

  return (
    <div>
      <PageHeader title="Inventory Sync" subtitle="Run reconciliation through canonical products and generate Shopify inventory output." />
      <div className="flex gap-3 mb-4">
        <button onClick={run}>Run reconciliation</button>
        <button onClick={exportInventory} disabled={!runId}>Export Shopify inventory CSV</button>
      </div>
      {exportPath ? <div className="rounded-lg border border-border bg-card p-3 mb-4 text-sm">Saved: {exportPath}</div> : null}
      <SimpleTable
        columns={['Handle', 'Shopify Title', 'FOS Name', 'Current', 'FOS SOH', 'Proposed', 'Delta', 'Status']}
        rows={rows.map((row) => [row.shopify_handle || '', row.shopify_title || '', row.fos_stock_name || '', row.shopify_current_on_hand ?? '', row.fos_soh ?? '', row.proposed_shopify_on_hand ?? '', row.delta ?? '', row.sync_status])}
      />
    </div>
  );
}
