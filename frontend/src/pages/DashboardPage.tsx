import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export function DashboardPage() {
  const [data, setData] = useState<any>();

  useEffect(() => {
    api('/dashboard').then(setData);
  }, []);

  if (!data) return <div className="panel">Loading dashboard…</div>;

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="card-grid">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="panel stat-card">
            <span className="muted">{key.replaceAll('_', ' ')}</span>
            <strong>{String(value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
