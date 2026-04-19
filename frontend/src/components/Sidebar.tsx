import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  Database,
  Layers,
  GitMerge,
  RefreshCw,
  Download,
  Settings as SettingsIcon,
  Pill,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
}

const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/imports', label: 'Imports', icon: Upload },
  { to: '/registry', label: 'Canonical Registry', icon: Database },
  { to: '/source-products', label: 'Source Products', icon: Layers },
  { to: '/review', label: 'Link Review', icon: GitMerge },
  { to: '/sync', label: 'Inventory Sync', icon: RefreshCw },
  { to: '/exports', label: 'Exports', icon: Download },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export function Sidebar() {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <aside className="w-[220px] shrink-0 bg-slate-950 text-white flex flex-col h-screen sticky top-0">
      <div className="px-5 py-5 border-b border-slate-800 flex items-center gap-2">
        <div className="h-8 w-8 rounded-md bg-slate-800 flex items-center justify-center">
          <Pill className="h-4 w-4 text-white" />
        </div>
        <div>
          <div className="font-semibold text-base leading-tight">Stock Sync</div>
          <div className="text-[11px] text-slate-400 leading-tight">Pharmacy reconciliation</div>
        </div>
      </div>

      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map((item) => {
          const Icon = item.icon;
          const isActive = item.to === '/' ? currentPath === '/' : currentPath.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={cn(
                'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-slate-800 text-white font-medium'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white',
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="flex-1 truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-3 border-t border-slate-800 text-[11px] text-slate-400">
        <div>Integrated frontend</div>
        <div>Powered by FastAPI + SQLite</div>
      </div>
    </aside>
  );
}
