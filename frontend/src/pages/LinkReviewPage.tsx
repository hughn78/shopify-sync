import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { SimpleTable } from '../components/Table';

export function LinkReviewPage() {
  const [items, setItems] = useState<any[]>([]);

  const load = () => api('/link-review').then(setItems);
  useEffect(() => { load(); }, []);

  async function act(id: number, action: string) {
    await api(`/link-review/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, note: `${action} from UI` }),
    });
    load();
  }

  return (
    <div>
      <h2>Link Review</h2>
      <SimpleTable
        columns={['Source Title', 'Canonical Product', 'Status', 'Method', 'Confidence', 'AI Reason', 'Actions']}
        rows={items.map((item) => [
          item.source_product?.title || '',
          item.canonical_product?.canonical_name || '',
          item.link_status,
          item.link_method,
          item.confidence_score || item.fuzzy_score || '',
          item.ai_reason || '',
          <div className="button-row" key={item.id}>
            <button onClick={() => act(item.id, 'approve')}>Approve</button>
            <button onClick={() => act(item.id, 'reject')}>Reject</button>
            <button onClick={() => act(item.id, 'exclude')}>Exclude</button>
          </div>,
        ])}
      />
    </div>
  );
}
