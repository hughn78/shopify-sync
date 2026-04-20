import { useMemo, useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { api } from '@/lib/api';
import type { ReconciliationRow } from '@/lib/types';

export function InventorySyncPage() {
  const [runId, setRunId] = useState<number | null>(null);
  const [rows, setRows] = useState<ReconciliationRow[]>([]);
  const [exportPath, setExportPath] = useState('');
  const [running, setRunning] = useState(false);

  const summary = useMemo(() => ({
    total: rows.length,
    ready: rows.filter((row) => row.sync_status === 'READY').length,
    review: rows.filter((row) => row.sync_status !== 'READY').length,
  }), [rows]);

  async function run() {
    setRunning(true);
    try {
      const result = await api<{ run_id: number }>('/reconciliation-runs', { method: 'POST' });
      setRunId(result.run_id);
      const data = await api<ReconciliationRow[]>(`/reconciliation-rows/${result.run_id}`);
      setRows(data);
      toast.success('Reconciliation run created');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Reconciliation failed');
    } finally {
      setRunning(false);
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
        <button onClick={run} disabled={running}>{running ? 'Running...' : 'Run reconciliation'}</button>
        <button onClick={exportInventory} disabled={!runId || summary.ready === 0}>Export Shopify inventory CSV</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard label="Rows" value={summary.total} />
        <StatCard label="Ready" value={summary.ready} />
        <StatCard label="Needs review" value={summary.review} />
      </div>

      {exportPath ? <div className="rounded-lg border border-border bg-card p-3 mb-4 text-sm">Saved: {exportPath}</div> : null}

      <div className="space-y-4">
        {rows.map((row) => (
          <div key={row.id} className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <div className="text-xs text-muted-foreground uppercase">Shopify product</div>
                <div className="text-sm font-medium">{row.shopify_title || 'Unknown Shopify product'}</div>
                <div className="text-sm text-muted-foreground mt-1">
                  Handle: {row.shopify_handle || 'n/a'} · Variant ID: {row.shopify_variant_id || 'n/a'} · Inventory Item ID: {row.shopify_inventory_item_id || 'n/a'}
                </div>
                <div className="text-sm text-muted-foreground mt-1">Location: {row.shopify_location_name || 'n/a'} ({row.shopify_location_id || 'no id'})</div>
              </div>
              <div className="text-sm"><strong>Status:</strong> {row.sync_status}</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Metric label="Current Shopify" value={row.shopify_current_on_hand} />
              <Metric label="FOS SOH" value={row.fos_soh} />
              <Metric label="Proposed" value={row.proposed_shopify_on_hand} />
              <Metric label="Delta" value={row.delta} />
            </div>

            <div className="text-sm mt-4"><strong>FOS match:</strong> {row.fos_stock_name || 'n/a'}</div>
            {row.warning_flags_json?.warnings?.length ? (
              <div className="rounded border p-3 mt-3" style={{ background: '#fff7e6', borderColor: '#f0d08a' }}>
                {row.warning_flags_json.warnings.map((warning) => (
                  <div key={warning} className="text-sm">• {warning}</div>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-2xl font-bold mt-2">{value}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded border border-border p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-xl font-bold mt-2">{value ?? 'n/a'}</div>
    </div>
  );
}
