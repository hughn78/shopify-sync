import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { Sidebar } from '@/components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { ImportsPage } from './pages/ImportsPage';
import { CanonicalRegistryPage } from './pages/CanonicalRegistryPage';
import { SourceProductsPage } from './pages/SourceProductsPage';
import { LinkReviewPage } from './pages/LinkReviewPage';
import { InventorySyncPage } from './pages/InventorySyncPage';
import { ExportsPage } from './pages/ExportsPage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 min-w-0 px-6 py-6">
        <div className="mx-auto max-w-[1400px]">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/imports" element={<ImportsPage />} />
            <Route path="/registry" element={<CanonicalRegistryPage />} />
            <Route path="/source-products" element={<SourceProductsPage />} />
            <Route path="/review" element={<LinkReviewPage />} />
            <Route path="/sync" element={<InventorySyncPage />} />
            <Route path="/exports" element={<ExportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
      <Toaster richColors position="top-right" />
    </div>
  );
}
