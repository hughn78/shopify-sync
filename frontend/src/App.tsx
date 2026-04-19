import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
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
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/imports" element={<ImportsPage />} />
        <Route path="/registry" element={<CanonicalRegistryPage />} />
        <Route path="/source-products" element={<SourceProductsPage />} />
        <Route path="/link-review" element={<LinkReviewPage />} />
        <Route path="/inventory-sync" element={<InventorySyncPage />} />
        <Route path="/exports" element={<ExportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </Layout>
  );
}
