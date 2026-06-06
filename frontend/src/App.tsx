import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnimatePresence } from 'framer-motion';
import { Toaster } from 'sonner';
import WorldListPage from './pages/WorldListPage';
import WorldCreatePage from './pages/WorldCreatePage';
import WorldRunPage from './pages/WorldRunPage';
import WorldDetailPage from './pages/WorldDetailPage';
import WorldSpectatorPage from './pages/WorldSpectatorPage';
import WorldLivePage from './pages/WorldLivePage';
import ModelConfigPage from './pages/ModelConfigPage';
import PageTransition from './components/ui/PageTransition';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1 },
  },
});

function RoutesWithTransition() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageTransition><WorldListPage /></PageTransition>} />
        <Route path="/create" element={<PageTransition><WorldCreatePage /></PageTransition>} />
        <Route path="/worlds/:worldId" element={<PageTransition><WorldRunPage /></PageTransition>} />
        <Route path="/worlds/:worldId/detail" element={<PageTransition><WorldDetailPage /></PageTransition>} />
        <Route path="/worlds/:worldId/spectate" element={<PageTransition><WorldSpectatorPage /></PageTransition>} />
        <Route path="/worlds/:worldId/live" element={<PageTransition><WorldLivePage /></PageTransition>} />
        <Route path="/settings/models" element={<PageTransition><ModelConfigPage /></PageTransition>} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster richColors position="top-right" />
        <div className="min-h-screen bg-ink-950">
          <RoutesWithTransition />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
