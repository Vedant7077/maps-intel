import { useQuery } from '@tanstack/react-query';
import { fetchProjects } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { ChevronDown, FolderOpen } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export default function ProjectSwitcher() {
  const { project, setProject } = useProject();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });

  // Auto-select first project if none selected
  useEffect(() => {
    if (!project && projects.length > 0) {
      setProject(projects[0]);
    }
  }, [projects, project, setProject]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg bg-[#141416] border border-[#27272A] text-sm hover:bg-[#1C1C1F] transition-colors"
      >
        <FolderOpen size={16} className="text-[#6366F1] shrink-0" />
        <span className="truncate flex-1 text-left text-[#FAFAFA]">
          {project?.name || 'Select project'}
        </span>
        <ChevronDown size={14} className={`text-[#A1A1AA] transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-[#141416] border border-[#27272A] rounded-lg shadow-xl z-50 overflow-hidden">
          {projects.length === 0 ? (
            <p className="px-3 py-2 text-sm text-[#A1A1AA]">No projects yet</p>
          ) : (
            projects.map((p) => (
              <button
                key={p.id}
                onClick={() => { setProject(p); setOpen(false); }}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-[#1C1C1F] transition-colors ${
                  p.id === project?.id ? 'text-[#6366F1] bg-[#6366F1]/5' : 'text-[#FAFAFA]'
                }`}
              >
                {p.name}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
