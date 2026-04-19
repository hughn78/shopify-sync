import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export function SettingsPage() {
  const [settings, setSettings] = useState<Record<string, unknown>>({});
  useEffect(() => { api('/settings').then(setSettings); }, []);

  return (
    <div>
      <h2>Settings</h2>
      <div className="card-grid">
        {Object.entries(settings).map(([key, value]) => (
          <div key={key} className="panel stat-card">
            <span className="muted">{key}</span>
            <strong>{String(value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
