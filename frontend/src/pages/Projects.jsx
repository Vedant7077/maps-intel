import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchProjects, createProject } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Plus, X, FolderKanban } from 'lucide-react';

export default function Projects() {
  const { setProject } = useProject();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setProject(newProject);
      setShowModal(false);
      navigate('/');
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#FAFAFA]">Projects</h1>
          <p className="text-sm text-[#A1A1AA] mt-1">Manage your intelligence projects</p>
        </div>
        <button onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors">
          <Plus size={16} /> New Project
        </button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(2)].map((_, i) => <div key={i} className="h-32 bg-[#141416] rounded-xl border border-[#27272A] animate-pulse" />)}
        </div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-center">
          <FolderKanban size={40} className="text-[#A1A1AA] mb-3" />
          <p className="text-[#A1A1AA]">No projects yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {projects.map((p) => (
            <button key={p.id} onClick={() => { setProject(p); navigate('/'); }}
              className="text-left bg-[#141416] border border-[#27272A] rounded-xl p-5 hover:bg-[#1C1C1F] hover:border-[#6366F1]/40 transition-all">
              <h3 className="text-[#FAFAFA] font-medium">{p.name}</h3>
              <p className="text-sm text-[#A1A1AA] mt-1">Client: {p.client_name || '—'}</p>
              <p className="text-xs text-[#A1A1AA] font-mono mt-2">ID: {p.id?.slice(0, 8)}…</p>
            </button>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && <NewProjectModal onClose={() => setShowModal(false)} mutation={mutation} />}
    </div>
  );
}

function NewProjectModal({ onClose, mutation }) {
  const [form, setForm] = useState({ name: '', client_name: '', client_maps_url: '' });

  const submit = (e) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={onClose}>
      <form onSubmit={submit} onClick={(e) => e.stopPropagation()}
        className="bg-[#141416] border border-[#27272A] rounded-xl w-full max-w-md p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-[#FAFAFA]">New Project</h2>
          <button type="button" onClick={onClose} className="text-[#A1A1AA] hover:text-[#FAFAFA]"><X size={18} /></button>
        </div>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm text-[#A1A1AA]">Project name</span>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors" />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm text-[#A1A1AA]">Client business name</span>
          <input required value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })}
            className="px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors" />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm text-[#A1A1AA]">Google Maps URL</span>
          <input required value={form.client_maps_url} onChange={(e) => setForm({ ...form, client_maps_url: e.target.value })}
            className="px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors" />
        </label>

        <button type="submit" disabled={mutation.isPending}
          className="px-4 py-2.5 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors disabled:opacity-50">
          {mutation.isPending ? 'Creating…' : 'Create Project'}
        </button>
        {mutation.isError && <p className="text-sm text-[#EF4444]">{mutation.error.message}</p>}
      </form>
    </div>
  );
}
