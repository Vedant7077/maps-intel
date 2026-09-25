import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchCompetitors, createCompetitor, startScrape } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Plus, X, Play, Swords, FolderKanban, Clock } from 'lucide-react';
import EmptyState from '../components/EmptyState';

function timeAgo(dateStr) {
  if (!dateStr) return 'Never scraped';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function Rivals() {
  const { project } = useProject();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const { data: rivals = [], isLoading } = useQuery({
    queryKey: ['competitors', project?.id, false],
    queryFn: () => fetchCompetitors(project.id, false),
    enabled: !!project?.id,
  });

  const scrapeMutation = useMutation({
    mutationFn: startScrape,
    onSuccess: (data) => navigate(`/monitor/${data.job_id}`),
  });

  const addMutation = useMutation({
    mutationFn: createCompetitor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      setShowModal(false);
    },
  });

  if (!project) return <EmptyState icon={FolderKanban} title="No project selected" message="Select a project first." ctaLabel="Go to Projects" ctaTo="/projects" />;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#FAFAFA]">Rivals</h1>
          <p className="text-sm text-[#A1A1AA] mt-1">Competitor businesses you're tracking</p>
        </div>
        <button onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors">
          <Plus size={16} /> Add Rival
        </button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => <div key={i} className="h-36 bg-[#141416] rounded-xl border border-[#27272A] animate-pulse" />)}
        </div>
      ) : rivals.length === 0 ? (
        <EmptyState icon={Swords} title="No rivals yet" message="Add a competitor to start tracking their Google Maps posts." />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {rivals.map((r) => (
            <div key={r.id} className="bg-[#141416] border border-[#27272A] rounded-xl p-5 flex flex-col gap-3 hover:bg-[#1C1C1F] transition-colors">
              <div>
                <h3 className="text-[#FAFAFA] font-medium">{r.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-[#A1A1AA] font-mono">{r.posts_count ?? 0} posts</span>
                  <span className="text-[#27272A]">·</span>
                  <span className="flex items-center gap-1 text-xs text-[#A1A1AA]">
                    <Clock size={12} /> {timeAgo(r.last_scraped_at)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => scrapeMutation.mutate({ competitor_id: r.id, project_id: project.id })}
                disabled={scrapeMutation.isPending}
                className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] hover:border-[#6366F1]/40 transition-all disabled:opacity-50"
              >
                <Play size={14} /> Scrape Now
              </button>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <AddRivalModal
          projectId={project.id}
          onClose={() => setShowModal(false)}
          mutation={addMutation}
        />
      )}
    </div>
  );
}

function AddRivalModal({ projectId, onClose, mutation }) {
  const [form, setForm] = useState({ name: '', maps_url: '' });

  const submit = (e) => {
    e.preventDefault();
    mutation.mutate({ project_id: projectId, ...form });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={onClose}>
      <form onSubmit={submit} onClick={(e) => e.stopPropagation()}
        className="bg-[#141416] border border-[#27272A] rounded-xl w-full max-w-md p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-[#FAFAFA]">Add Rival</h2>
          <button type="button" onClick={onClose} className="text-[#A1A1AA] hover:text-[#FAFAFA]"><X size={18} /></button>
        </div>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm text-[#A1A1AA]">Business name</span>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors" />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-sm text-[#A1A1AA]">Google Maps URL</span>
          <input required value={form.maps_url} onChange={(e) => setForm({ ...form, maps_url: e.target.value })}
            className="px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors" />
        </label>
        <button type="submit" disabled={mutation.isPending}
          className="px-4 py-2.5 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors disabled:opacity-50">
          {mutation.isPending ? 'Adding…' : 'Add Rival'}
        </button>
        {mutation.isError && <p className="text-sm text-[#EF4444]">{mutation.error.message}</p>}
      </form>
    </div>
  );
}
