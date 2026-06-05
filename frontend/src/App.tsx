import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WorldListPage from './pages/WorldListPage';
import WorldCreatePage from './pages/WorldCreatePage';
import WorldRunPage from './pages/WorldRunPage';
import WorldDetailPage from './pages/WorldDetailPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-900">
          <Routes>
            <Route path="/" element={<WorldListPage />} />
            <Route path="/create" element={<WorldCreatePage />} />
            <Route path="/worlds/:worldId" element={<WorldRunPage />} />
            <Route path="/worlds/:worldId/detail" element={<WorldDetailPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}