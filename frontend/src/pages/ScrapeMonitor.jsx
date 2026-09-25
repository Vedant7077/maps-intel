import { useParams, Link } from 'react-router-dom';
import { usePolling } from '../hooks/usePolling';
import { resumeJob } from '../lib/api';
import { useMutation } from '@tanstack/react-query';
import { Loader, CheckCircle2, XCircle, AlertTriangle, FileText, PlusCircle, Copy, ImageIcon } from 'lucide-react';
import StatCard from '../components/StatCard';

const statusConfig = {
  queued: { color: 'bg-zinc-500', text: 'text-zinc-400', label: 'Queued', icon: null },
  running: { color: 'bg-[#6366F1]', text: 'text-[#818CF8]', label: 'Scraping…', icon: Loader },
  completed: { color: 'bg-[#22C55E]', text: 'text-[#22C55E]', label: 'Completed', icon: CheckCircle2 },
  failed: { color: 'bg-[#EF4444]', text: 'text-[#EF4444]', label: 'Failed', icon: XCircle },
};

export default function ScrapeMonitor() {
  const { jobId } = useParams();
  const { job, error } = usePolling(jobId);

  const resumeMutation = useMutation({
    mutationFn: () => resumeJob(jobId),
  });

  if (error) {
    return (
      <div className="flex flex-col items-center py-16">
        <p className="text-sm text-[#EF4444] mb-4">Failed to load job: {error.message}</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader className="animate-spin text-[#6366F1]" size={24} />
      </div>
    );
  }

  const cfg = statusConfig[job.status] || statusConfig.queued;
  const StatusIcon = cfg.icon;
  const isCaptcha = job.captcha_required && job.status === 'running';

  return (
    <div className="flex flex-col gap-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-semibold text-[#FAFAFA]">Scrape Monitor</h1>
        <p className="text-xs text-[#A1A1AA] font-mono mt-1">Job {jobId?.slice(0, 8)}…</p>
      </div>

      {/* Status badge */}
      <div className="bg-[#141416] border border-[#27272A] rounded-xl p-6 flex flex-col items-center gap-4">
        {isCaptcha ? (
          <>
            <div className="bg-amber-500/10 rounded-full p-4">
              <AlertTriangle size={32} className="text-[#F59E0B]" />
            </div>
            <h2 className="text-lg font-medium text-[#F59E0B]">Verification Needed</h2>
            <p className="text-sm text-[#A1A1AA] text-center">Please solve the CAPTCHA in the browser, then click resume.</p>
            <button
              onClick={() => resumeMutation.mutate()}
              disabled={resumeMutation.isPending}
              className="px-4 py-2 rounded-lg bg-[#F59E0B] text-black text-sm font-medium hover:bg-amber-400 transition-colors disabled:opacity-50"
            >
              {resumeMutation.isPending ? 'Resuming…' : 'Resume'}
            </button>
          </>
        ) : (
          <>
            <div className={`${cfg.color}/10 rounded-full p-4`}>
              {StatusIcon ? (
                <StatusIcon size={32} className={`${cfg.text} ${job.status === 'running' ? 'animate-spin' : ''}`} />
              ) : (
                <div className={`w-8 h-8 rounded-full ${cfg.color}`} />
              )}
            </div>
            <h2 className={`text-lg font-medium ${cfg.text}`}>{cfg.label}</h2>
          </>
        )}
      </div>

      {/* Counters */}
      <div className="grid grid-cols-2 gap-4">
        <StatCard icon={FileText} label="Posts Found" value={job.posts_found ?? 0} />
        <StatCard icon={PlusCircle} label="New Added" value={job.new_added ?? 0} />
        <StatCard icon={Copy} label="Duplicates Skipped" value={job.duplicates_skipped ?? 0} />
        <StatCard icon={ImageIcon} label="Images Downloaded" value={job.images_downloaded ?? 0} />
      </div>

      {/* Post-completion CTA */}
      {job.status === 'completed' && (
        <Link
          to={`/repository?competitor_id=${job.competitor_id}`}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors"
        >
          View New Posts →
        </Link>
      )}
    </div>
  );
}
