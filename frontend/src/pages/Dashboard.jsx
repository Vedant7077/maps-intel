import { useQuery } from '@tanstack/react-query';
import { useProject } from '../context/ProjectContext';
import { fetchDashboard } from '../lib/api';
import { Link } from 'react-router-dom';
import StatCard from '../components/StatCard';
import EmptyState from '../components/EmptyState';
import { FileText, Swords, Zap, Lightbulb, Archive, Sparkles, BarChart3, FolderKanban } from 'lucide-react';

export default function Dashboard() {
  const { project } = useProject();

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', project?.id],
    queryFn: () => fetchDashboard(project.id),
    enabled: !!project?.id,
    refetchInterval: 30000,
  });

  if (!project) {
    return <EmptyState icon={FolderKanban} title="No project selected" message="Select or create a project to get started." ctaLabel="Go to Projects" ctaTo="/projects" />;
  }

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorRetry error={error} />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#FAFAFA]">Dashboard</h1>
        <p className="text-sm text-[#A1A1AA] mt-1">Overview for {project.name}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText} label="Total Posts" value={data?.total_posts ?? 0} />
        <StatCard icon={Swords} label="Rival Businesses" value={data?.competitors_count ?? 0} />
        <StatCard icon={Zap} label="New This Week" value={data?.new_this_week ?? 0} />
        <StatCard icon={Lightbulb} label="Ideas Generated" value={data?.ideas_generated ?? 0} />
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-sm font-medium text-[#A1A1AA] uppercase tracking-wider mb-3">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/repository" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] hover:border-[#6366F1]/40 transition-all">
            <Archive size={16} /> View Repository
          </Link>
          <Link to="/generator" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors">
            <Sparkles size={16} /> Generate Ideas
          </Link>
          <Link to="/analysis" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] hover:border-[#6366F1]/40 transition-all">
            <BarChart3 size={16} /> Check Gaps
          </Link>
        </div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="flex items-center gap-2 text-sm text-[#A1A1AA]">
        <div className="w-2 h-2 rounded-full bg-[#6366F1] animate-ping" />
        <span>Loading intelligence overview...</span>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-28 bg-[#141416] rounded-xl border border-[#27272A]" />)}
      </div>
    </div>
  );
}

function ErrorRetry({ error }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <p className="text-sm text-[#EF4444] mb-4">Failed to load: {error.message}</p>
      <button onClick={() => window.location.reload()} className="px-4 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F]">
        Retry
      </button>
    </div>
  );
}
