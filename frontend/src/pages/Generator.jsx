import { useQuery, useMutation } from '@tanstack/react-query';
import { generateIdeas, fetchGeneratedIdeas } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { useState, useEffect, useRef } from 'react';
import EmptyState from '../components/EmptyState';
import { parseList } from '../components/PostCard';
import { Sparkles, FolderKanban, Copy, Check, ChevronLeft, ChevronRight } from 'lucide-react';

const loadingMessages = [
  'Analyzing competitor trends…',
  'Identifying content gaps…',
  'Drafting your posts…',
  'Adding creative touches…',
  'Almost done…',
];

export default function Generator() {
  const { project } = useProject();
  const [count, setCount] = useState(5);
  const [ideas, setIdeas] = useState(null);
  const [historyPage, setHistoryPage] = useState(0);

  const mutation = useMutation({
    mutationFn: generateIdeas,
    onSuccess: (data) => setIdeas(data.ideas || []),
  });

  const { data: history } = useQuery({
    queryKey: ['generated-ideas', project?.id, historyPage],
    queryFn: () => fetchGeneratedIdeas({ project_id: project.id, page: historyPage }),
    enabled: !!project?.id,
  });

  if (!project) return <EmptyState icon={FolderKanban} title="No project selected" ctaLabel="Go to Projects" ctaTo="/projects" />;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-[#FAFAFA]">Content Generator</h1>
        <p className="text-sm text-[#A1A1AA] mt-1">AI-powered content ideas based on competitor analysis</p>
      </div>

      {/* Generator controls */}
      <div className="bg-[#141416] border border-[#27272A] rounded-xl p-6 flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm text-[#A1A1AA]">Number of ideas</span>
          <input
            type="number" min={1} max={10} value={count}
            onChange={(e) => setCount(Math.max(1, Math.min(10, Number(e.target.value))))}
            className="w-24 px-3 py-2 rounded-lg bg-[#0A0A0B] border border-[#27272A] text-sm text-[#FAFAFA] font-mono focus:outline-none focus:border-[#6366F1] transition-colors"
          />
        </label>
        <button
          onClick={() => { setIdeas(null); mutation.mutate({ project_id: project.id, count }); }}
          disabled={mutation.isPending}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors disabled:opacity-50"
        >
          <Sparkles size={16} />
          {mutation.isPending ? 'Generating…' : 'Generate'}
        </button>
      </div>

      {/* Loading state */}
      {mutation.isPending && <GeneratingLoader />}

      {/* Error */}
      {mutation.isError && (
        <div className="bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl p-4 text-sm text-[#EF4444]">
          {mutation.error.message}
        </div>
      )}

      {/* Results */}
      {ideas && (
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-medium text-[#FAFAFA]">Generated Ideas</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {ideas.map((idea, i) => <IdeaCard key={i} idea={idea} />)}
          </div>
        </div>
      )}

      {/* History */}
      {history && history.results?.length > 0 && (
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-medium text-[#FAFAFA]">History</h2>
          <div className="grid gap-3">
            {history.results.map((idea) => (
              <div key={idea.id} className="bg-[#141416] border border-[#27272A] rounded-xl p-4 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-[#FAFAFA]">{idea.topic_title}</h4>
                  <span className="text-xs text-[#A1A1AA] font-mono">{new Date(idea.generated_at).toLocaleDateString()}</span>
                </div>
                <p className="text-sm text-[#A1A1AA] line-clamp-2">{idea.post_copy}</p>
              </div>
            ))}
          </div>

          {/* History pagination */}
          {history.total > 20 && (
            <div className="flex items-center justify-center gap-4">
              <button onClick={() => setHistoryPage((p) => Math.max(0, p - 1))} disabled={historyPage === 0}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] disabled:opacity-30 transition-colors">
                <ChevronLeft size={16} /> Prev
              </button>
              <span className="text-sm text-[#A1A1AA] font-mono">{historyPage + 1} / {Math.ceil(history.total / 20)}</span>
              <button onClick={() => setHistoryPage((p) => p + 1)} disabled={(historyPage + 1) * 20 >= history.total}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] disabled:opacity-30 transition-colors">
                Next <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function GeneratingLoader() {
  const [msgIdx, setMsgIdx] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setMsgIdx((i) => (i + 1) % loadingMessages.length);
    }, 8000);
    return () => clearInterval(intervalRef.current);
  }, []);

  return (
    <div className="bg-[#141416] border border-[#6366F1]/30 rounded-xl p-8 flex flex-col items-center gap-4">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-[#6366F1]/20" />
        <div className="absolute inset-0 rounded-full border-2 border-t-[#6366F1] animate-spin" />
        <Sparkles size={20} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[#6366F1]" />
      </div>
      <p className="text-sm text-[#818CF8] animate-pulse">{loadingMessages[msgIdx]}</p>
      <p className="text-xs text-[#A1A1AA]">This may take up to 45 seconds</p>
    </div>
  );
}

function IdeaCard({ idea }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(idea.post_copy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#141416] border border-[#27272A] rounded-xl p-5 flex flex-col gap-3 hover:border-[#6366F1]/30 transition-colors">
      <div className="flex items-center justify-between">
        <h4 className="text-[#FAFAFA] font-medium">{idea.topic_title}</h4>
        <button onClick={copy} className="text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors" title="Copy post text">
          {copied ? <Check size={16} className="text-[#22C55E]" /> : <Copy size={16} />}
        </button>
      </div>

      <p className="text-sm text-[#A1A1AA] leading-relaxed">{idea.post_copy}</p>

      {parseList(idea?.keywords).length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {parseList(idea?.keywords).map((kw, i) => (
            <span key={i} className="px-2 py-0.5 rounded-md text-xs bg-[#1C1C1F] text-[#A1A1AA] border border-[#27272A]">{kw}</span>
          ))}
        </div>
      )}

      {(idea.cta_type || idea.cta_text) && (
        <div className="text-sm">
          <span className="text-[#6366F1]">
            {idea.cta_type === 'call' ? '📞' : idea.cta_type === 'visit' ? '📍' : idea.cta_type === 'book' ? '📅' : idea.cta_type === 'buy' ? '🛒' : '📎'}{' '}
          </span>
          <span className="text-[#FAFAFA]">{idea.cta_text || idea.cta_type}</span>
        </div>
      )}

      {idea.image_concept && (
        <p className="text-xs text-[#A1A1AA] italic border-t border-[#27272A] pt-2 mt-1">
          📸 {idea.image_concept}
        </p>
      )}
    </div>
  );
}
