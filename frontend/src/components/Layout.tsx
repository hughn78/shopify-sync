import { NavLink } from 'react-router-dom';
import { ReactNode } from 'react';

const navItems = [
  ['/', 'Dashboard'],
  ['/imports', 'Imports'],
  ['/registry', 'Canonical Registry'],
  ['/source-products', 'Source Products'],
  ['/link-review', 'Link Review'],
  ['/inventory-sync', 'Inventory Sync'],
  ['/exports', 'Exports'],
  ['/settings', 'Settings'],
];

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <h1>Pharmacy Stock Sync</h1>
          <p className="muted">Canonical product registry for pharmacy operations</p>
        </div>
        <nav>
          {navItems.map(([path, label]) => (
            <NavLink key={path} to={path} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
