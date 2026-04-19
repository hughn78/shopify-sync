import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { api } from '@/lib/api';
import type { CanonicalProduct, CandidateSummary, LinkReviewItem } from '@/lib/types';

const FILTERS = ['ALL', 'NEEDS_REVIEW', 'APPROVED', 'AUTO_ACCEPTED', 'REJECTED', 'EXCLUDED', 'CONFLICT'] as const;

export function LinkReviewPage() {
  const [items, setItems] = useState<LinkReviewItem[]>([]);
  const [canonicals, setCanonicals] = useState<CanonicalProduct[]>([]);
  const [statusFilter, setStatusFilter] = useState<(typeof FILTERS)[number]>('ALL');
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    api<LinkReviewItem[]>('/link-review').then(setItems).catch(console.error);
  }

  useEffect(() => {
    load();
    api<CanonicalProduct[]>('/review-options').then(setCanonicals).catch(console.error);
  }, []);

  const filtered = useMemo(() => {
    if (statusFilter === 'ALL') return items;
    return items.filter((item) => item.link_status === statusFilter);
  }, [items, statusFilter]);

  async function act(id: number, action: string, extra?: Record<string, unknown>) {
    setBusyId(id);
    try {
      await api(`/link-review/${id}`, {
        method: 'POST',
        body: JSON.stringify({ action, note: `${action} from integrated frontend`, ...(extra || {}) }),
      });
      toast.success(`Link ${action}d`);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Action failed');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <PageHeader title="Link Review" subtitle="Review source-to-canonical links and keep uncertain matches out of auto-flow." />
      <div className="flex gap-2 mb-4 flex-wrap">
        {FILTERS.map((filter) => (
          <button key={filter} onClick={() => setStatusFilter(filter)} disabled={busyId !== null && statusFilter === filter}>
            {filter} ({filter === 'ALL' ? items.length : items.filter((item) => item.link_status === filter).length})
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {filtered.map((item) => (
          <ReviewCard key={item.id} item={item} canonicals={canonicals} busy={busyId === item.id} onAction={act} />
        ))}
      </div>
    </div>
  );
}

function ReviewCard({
  item,
  canonicals,
  onAction,
  busy,
}: {
  item: LinkReviewItem;
  canonicals: CanonicalProduct[];
  onAction: (id: number, action: string, extra?: Record<string, unknown>) => void;
  busy: boolean;
}) {
  const [selectedCanonicalId, setSelectedCanonicalId] = useState<number | ''>(item.canonical_product?.id || '');
  const warnings: string[] = [];
  if (item.link_method === 'CREATED_NEW_CANONICAL') warnings.push('New canonical was created automatically. Review before trusting.');
  if ((item.confidence_score ?? 0) < 90) warnings.push('Confidence below auto-accept threshold.');
  if (item.locked) warnings.push('This link is locked.');
  if (item.excluded) warnings.push('This link is excluded from matching.');

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="text-xs text-muted-foreground uppercase">Source product</div>
          <div className="text-2xl font-bold">{item.source_product.title}</div>
          <div className="text-sm text-muted-foreground mt-2">
            Handle: {item.source_product.handle || 'n/a'} · SKU: {item.source_product.sku || 'n/a'} · APN: {item.source_product.apn || 'n/a'} · PDE: {item.source_product.pde || 'n/a'}
          </div>
        </div>
        <div className="text-sm">
          <div><strong>Status:</strong> {item.link_status}</div>
          <div><strong>Method:</strong> {item.link_method}</div>
          <div><strong>Confidence:</strong> {item.confidence_score ?? item.fuzzy_score ?? 'n/a'}</div>
        </div>
      </div>

      <div className="rounded border border-border p-4 mb-4" style={{ background: '#f8f9fc' }}>
        <div className="text-xs text-muted-foreground uppercase">Current canonical target</div>
        <div className="text-sm font-medium mt-2">{item.canonical_product.canonical_name}</div>
        <div className="text-sm text-muted-foreground mt-1">
          Barcode: {item.canonical_product.primary_barcode || 'n/a'} · APN: {item.canonical_product.primary_apn || 'n/a'} · PDE: {item.canonical_product.primary_pde || 'n/a'}
        </div>
        {item.ai_reason ? <div className="text-sm mt-2"><strong>AI reason:</strong> {item.ai_reason}</div> : null}
        {item.review_notes ? <div className="text-sm mt-2"><strong>Review note:</strong> {item.review_notes}</div> : null}
      </div>

      {warnings.length ? (
        <div className="rounded border p-3 mb-4" style={{ background: '#fff7e6', borderColor: '#f0d08a' }}>
          {warnings.map((warning) => (
            <div key={warning} className="text-sm">• {warning}</div>
          ))}
        </div>
      ) : null}

      {item.candidates?.length ? (
        <div className="mb-4">
          <div className="text-xs text-muted-foreground uppercase mb-2">Candidate shortlist</div>
          <div className="space-y-2">
            {item.candidates.map((candidate) => (
              <CandidateRow key={candidate.id} candidate={candidate} />
            ))}
          </div>
        </div>
      ) : null}

      <div className="rounded border border-border p-4 mb-4">
        <div className="text-xs text-muted-foreground uppercase mb-2">Manual controls</div>
        <div className="flex gap-2 flex-wrap items-center">
          <select
            value={selectedCanonicalId}
            onChange={(e) => setSelectedCanonicalId(e.target.value ? Number(e.target.value) : '')}
            disabled={busy}
          >
            <option value="">Select canonical</option>
            {canonicals.map((canonical) => (
              <option key={canonical.id} value={canonical.id}>
                {canonical.canonical_name}
              </option>
            ))}
          </select>
          <button
            onClick={() => selectedCanonicalId && onAction(item.id, 'reassign', { canonical_product_id: selectedCanonicalId })}
            disabled={busy || !selectedCanonicalId}
          >
            Reassign
          </button>
          <button onClick={() => onAction(item.id, 'create_canonical')} disabled={busy}>Create canonical</button>
          <button onClick={() => onAction(item.id, 'approve')} disabled={busy}>Approve</button>
          <button onClick={() => onAction(item.id, 'reject')} disabled={busy}>Reject</button>
          <button onClick={() => onAction(item.id, 'exclude')} disabled={busy}>Exclude</button>
          <button onClick={() => onAction(item.id, 'approve', { locked: !item.locked })} disabled={busy}>
            {item.locked ? 'Unlock + approve' : 'Lock + approve'}
          </button>
        </div>
      </div>
    </div>
  );
}

function CandidateRow({ candidate }: { candidate: CandidateSummary }) {
  return (
    <div className="rounded border border-border p-3 text-sm">
      <div><strong>#{candidate.candidate_rank}</strong> {candidate.canonical_product?.canonical_name || 'Unknown canonical'}</div>
      <div className="text-muted-foreground">Method: {candidate.match_method} · Fuzzy: {candidate.fuzzy_score ?? 'n/a'} · Proposed: {candidate.proposed_action || 'n/a'}</div>
      {candidate.ai_reason ? <div className="text-muted-foreground">AI: {candidate.ai_reason}</div> : null}
    </div>
  );
}
