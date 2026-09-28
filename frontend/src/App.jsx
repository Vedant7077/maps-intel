import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectProvider } from './context/ProjectContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Rivals from './pages/Rivals';
import MyBusiness from './pages/MyBusiness';
import ScrapeMonitor from './pages/ScrapeMonitor';
import Repository from './pages/Repository';
import Analysis from './pages/Analysis';
import Generator from './pages/Generator';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ProjectProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/rivals" element={<Rivals />} />
              <Route path="/my-business" element={<MyBusiness />} />
              <Route path="/monitor/:jobId" element={<ScrapeMonitor />} />
              <Route path="/repository" element={<Repository />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/gaps" element={<Navigate to="/analysis" replace />} />
              <Route path="/generator" element={<Generator />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ProjectProvider>
    </QueryClientProvider>
  );
}
