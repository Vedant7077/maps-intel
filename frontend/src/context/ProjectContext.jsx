import { createContext, useContext, useState } from 'react';

const ProjectContext = createContext(null);

export const DEFAULT_SEED_PROJECT = {
  id: '7c4f2d91-3a61-4e8b-9d25-6f7a1c3b82e4',
  name: 'Boojee Cafe',
  client_name: 'Boojee Cafe',
  client_maps_url: 'https://www.google.com/maps/search/?api=1&query=Boojee+Cafe+Bandra+West+Mumbai',
};

const STORAGE_KEY = 'mapspy_active_project';

export function ProjectProvider({ children }) {
  const [project, setProjectState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch {
      // ignore
    }
    return DEFAULT_SEED_PROJECT;
  });

  const setProject = (p) => {
    setProjectState(p);
    try {
      if (p) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // ignore
    }
  };

  return (
    <ProjectContext.Provider value={{ project, setProject }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error('useProject must be used within ProjectProvider');
  return ctx;
}
