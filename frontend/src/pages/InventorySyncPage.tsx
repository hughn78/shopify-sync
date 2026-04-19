import { useState } from 'react';
import { api } from '../lib/api';
import { SimpleTable } from '../components/Table';

export function InventorySyncPage() {
  const [runId, setRunId] = useState<number | null>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [exportPath, setExportPath] = useState<string>('');

  async function run() {
    const result = await api<{ run_id: number }>('/reconciliation-runs', { method: 'POST' });
    setRunId(result.run_id);
    const data = await api<any[]>(`/reconciliation-rows/${result.run_id}`);
    setRows(data);
  }

  async function exportInventory() {
    if (!runId) return;
    const result = await api<{ file_path: string }>(`/exports/inventory/${runId}`, { method: 'POST' });
    setExportPath(result.file_path);
  }

  return (
    <div>
      <h2>Inventory Sync</h2>
      <div className="button-row panel">
        <button onClick={run}>Run reconciliation</button>
        <button onClick={exportInventory} disabled={!runId}>Export Shopify inventory CSV</button>
        {exportPath ? <span className="muted">Saved: {exportPath}</span> : null}
      </div>
      <SimpleTable
        columns={['Handle', 'Shopify Title', 'FOS Name', 'Current', 'FOS SOH', 'Proposed', 'Delta', 'Status']}
        rows={rows.map((row) => [row.shopify_handle || '', row.shopify_title || '', row.fos_stock_name || '', row.shopify_current_on_hand ?? '', row.fos_soh ?? '', row.proposed_shopify_on_hand ?? '', row.delta ?? '', row.sync_status])}
      />
    </div>
  );
}
