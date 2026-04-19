import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { SimpleTable } from '@/components/Table';
import { api } from '@/lib/api';
import type { LinkReviewItem } from '@/lib/types';

export function LinkReviewPage() {
  const [items, setItems] = useState<LinkReviewItem[]>([]);

  function load() {
    api<LinkReviewItem[]>('/link-review').then(setItems).catch(console.error);
  }

  useEffect(() => {
    load();
  }, []);

  async function act(id: number, action: string) {
    try {
      await api(`/link-review/${id}`, {
        method: 'POST',
        body: JSON.stringify({ action, note: `${action} from integrated frontend` }),
      });
      toast.success(`Link ${action}d`);
      load();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Action failed');
    }
  }

  return (
    <div>
      <PageHeader title="Link Review" subtitle="Review and approve source-to-canonical links before operational use." />
      <SimpleTable
        columns={['Source Title', 'Canonical Product', 'Status', 'Method', 'Confidence', 'AI Reason', 'Actions']}
        rows={items.map((item) => [
          item.source_product?.title || '',
          item.canonical_product?.canonical_name || '',
          item.link_status,
          item.link_method,
          String(item.confidence_score ?? item.fuzzy_score ?? ''),
          item.ai_reason || '',
          `Approve / Reject / Exclude`,
        ])}
      />
      <div className="mt-4 flex flex-wrap gap-2">
        {items.slice(0, 10).map((item) => (
          <div key={item.id} className="rounded border border-border p-3 bg-card flex items-center gap-2">
            <span className="text-sm flex-1">{item.source_product?.title}</span>
            <button onClick={() => act(item.id, 'approve')}>Approve</button>
            <button onClick={() => act(item.id, 'reject')}>Reject</button>
            <button onClick={() => act(item.id, 'exclude')}>Exclude</button>
          </div>
        ))}
      </div>
    </div>
  );
}
