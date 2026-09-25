import { useQuery } from '@tanstack/react-query';
import { fetchPosts, fetchPost, fetchCompetitors, fetchTopics } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { PostCard, PostLightbox } from '../components/PostCard';
import EmptyState from '../components/EmptyState';
import { Search, Archive, FolderKanban, ChevronLeft, ChevronRight } from 'lucide-react';

function useDebounce(fn, delay) {
  const [timer, setTimer] = useState(null);
  return useCallback((...args) => {
    if (timer) clearTimeout(timer);
    setTimer(setTimeout(() => fn(...args), delay));
  }, [fn, delay, timer]);
}

export default function Repository() {
  const { project } = useProject();
  const [searchParams] = useSearchParams();

  const [filters, setFilters] = useState({
    search: '',
    competitor_id: searchParams.get('competitor_id') || '',
    topic: '',
    date_from: '',
    date_to: '',
    page: 0,
  });
  const [searchInput, setSearchInput] = useState('');
  const [selectedPostId, setSelectedPostId] = useState(null);

  const debouncedSearch = useDebounce((val) => setFilters((f) => ({ ...f, search: val, page: 0 })), 400);

  const { data: competitors = [] } = useQuery({
    queryKey: ['competitors-all', project?.id],
    queryFn: () => fetchCompetitors(project.id, true),
    enabled: !!project?.id,
  });

  const { data: topics = [] } = useQuery({
    queryKey: ['topics', project?.id],
    queryFn: () => fetchTopics(project.id),
    enabled: !!project?.id,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['posts', project?.id, filters],
    queryFn: () => fetchPosts({ project_id: project.id, limit: 20, ...filters }),
    enabled: !!project?.id,
  });

  const { data: selectedPost } = useQuery({
    queryKey: ['post-detail', selectedPostId],
    queryFn: () => fetchPost(selectedPostId),
    enabled: !!selectedPostId,
  });

  if (!project) return <EmptyState icon={FolderKanban} title="No project selected" message="Select a project first." ctaLabel="Go to Projects" ctaTo="/projects" />;

  const results = data?.results || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#FAFAFA]">Repository</h1>
        <p className="text-sm text-[#A1A1AA] mt-1">{total} posts collected</p>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A1A1AA]" />
          <input
            placeholder="Search posts…"
            value={searchInput}
            onChange={(e) => { setSearchInput(e.target.value); debouncedSearch(e.target.value); }}
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors"
          />
        </div>

        <select
          value={filters.competitor_id}
          onChange={(e) => setFilters({ ...filters, competitor_id: e.target.value, page: 0 })}
          className="px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors"
        >
          <option value="">All businesses</option>
          {competitors.find((c) => c.is_client) && (
            <optgroup label="My Business">
              <option value={competitors.find((c) => c.is_client).id}>
                ⭐ {competitors.find((c) => c.is_client).name} (You)
              </option>
            </optgroup>
          )}
          {competitors.some((c) => !c.is_client) && (
            <optgroup label="Rivals">
              {competitors.filter((c) => !c.is_client).map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </optgroup>
          )}
        </select>

        <select
          value={filters.topic}
          onChange={(e) => setFilters({ ...filters, topic: e.target.value, page: 0 })}
          className="px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors"
        >
          <option value="">All topics</option>
          {topics.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>

        <input type="date" value={filters.date_from}
          onChange={(e) => setFilters({ ...filters, date_from: e.target.value, page: 0 })}
          className="px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors"
        />
        <input type="date" value={filters.date_to}
          onChange={(e) => setFilters({ ...filters, date_to: e.target.value, page: 0 })}
          className="px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] focus:outline-none focus:border-[#6366F1] transition-colors"
        />
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => <div key={i} className="h-52 bg-[#141416] rounded-xl border border-[#27272A] animate-pulse" />)}
        </div>
      ) : results.length === 0 ? (
        <EmptyState icon={Archive} title="No posts found" message="Try adjusting your filters or scrape more competitors." />
      ) : (
        <>
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {results.map((post) => (
              <PostCard key={post.id} post={post} onClick={() => setSelectedPostId(post.id)} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
                disabled={filters.page === 0}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] disabled:opacity-30 transition-colors"
              >
                <ChevronLeft size={16} /> Prev
              </button>
              <span className="text-sm text-[#A1A1AA] font-mono">
                {filters.page + 1} / {totalPages}
              </span>
              <button
                onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
                disabled={filters.page >= totalPages - 1}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-[#141416] border border-[#27272A] text-sm text-[#FAFAFA] hover:bg-[#1C1C1F] disabled:opacity-30 transition-colors"
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}

      {/* Post lightbox */}
      {selectedPost && (
        <PostLightbox post={selectedPost} onClose={() => setSelectedPostId(null)} />
      )}
    </div>
  );
}
