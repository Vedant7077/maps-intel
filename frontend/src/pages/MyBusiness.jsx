import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchClientBusiness, upsertClientBusiness, startScrape } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import EmptyState from '../components/EmptyState';
import { Building2, Play, Pencil, FolderKanban, Clock } from 'lucide-react';

export default function MyBusiness() {
  const { project } = useProject();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['client-business', project?.id],
    queryFn: () => fetchClientBusiness(project.id),
    enabled: !!project?.id,
  });

  const upsertMutation = useMutation({
    mutationFn: upsertClientBusiness,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-business'] });
      setEditing(false);
    },
  });

  const scrapeMutation = useMutation({
    mutationFn: startScrape,
    onSuccess: (res) => navigate(`/monitor/${res.job_id}`),
  });

  if (!project) return <EmptyState icon={FolderKanban} title="No project selected" message="Select a project first." ctaLabel="Go to Projects" ctaTo="/projects" />;
  if (isLoading) return <div className="animate-pulse h-48 bg-[#141416] rounded-xl border border-[#27272A]" />;

  const registered = data?.registered;
  const client = data?.client;
  const showForm = !registered || editing;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#FAFAFA]">My Business</h1>
        <p className="text-sm text-[#A1A1AA] mt-1">Your own Google Maps presence</p>
      </div>

      {showForm ? (
        <BusinessForm
          project={project}
          defaults={client || { name: project.client_name || '', maps_url: project.client_maps_url || '' }}
          mutation={upsertMutation}
          isEdit={!!registered}
          onCancel={registered ? () => setEditing(false) : undefined}
        />
      ) : (
        <div className="bg-[#141416] border border-[#27272A] rounded-xl p-6 flex flex-col gap-4 max-w-lg">
          <div className="flex items-center gap-3">
            <div className="bg-[#6366F1]/10 rounded-full p-2.5">
              <Building2 size={22} className="text-[#6366F1]" />
            </div>
            <div>
              <h3 className="text-[#FAFAFA] font-medium">{client.name}</h3>
              <div className="flex items-center gap-2 text-xs text-[#A1A1AA]">
                <span className="font-mono">{client.posts_count ?? 0} posts</span>
                <span className="text-[#27272A]">·</span>
                <Clock size={12} />
                <span>{client.last_scraped_at ? new Date(client.last_scraped_at).toLocaleDateString() : 'Never scraped'}</span>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => setEditing(true)}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] transition-colors">
              <Pencil size={14} /> Edit
            </button>
            <button
              onClick={() => scrapeMutation.mutate({ competitor_id: client.id, project_id: project.id })}
              disabled={scrapeMutation.isPending}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors disabled:opacity-50">
              <Play size={14} /> Scrape My Business
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function BusinessForm({ project, defaults, mutation, isEdit, onCancel }) {
  const [form, setForm] = useState({
    name: defaults?.name || '',
    maps_url: defaults?.maps_url || '',
  });

  const submit = (e) => {
    e.preventDefault();
    mutation.mutate({ project_id: project.id, ...form });
  };

  return (
    <form onSubmit={submit} className="bg-[#141416] border border-[#27272A] rounded-xl p-6 flex flex-col gap-4 max-w-lg">
      {!isEdit && (
        <div className="bg-[#6366F1]/5 border border-[#6366F1]/20 rounded-lg p-4 mb-2">
          <p className="text-sm text-[#818CF8]">Register your business to unlock gap analysis — see which topics your rivals cover that you don't.</p>
        </div>
      )}
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
      <div className="flex gap-3">
        <button type="submit" disabled={mutation.isPending}
          className="px-4 py-2.5 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors disabled:opacity-50">
          {mutation.isPending ? 'Saving…' : isEdit ? 'Update' : 'Register'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel}
            className="px-4 py-2.5 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] transition-colors">
            Cancel
          </button>
        )}
      </div>
      {mutation.isError && <p className="text-sm text-[#EF4444]">{mutation.error.message}</p>}
    </form>
  );
}
