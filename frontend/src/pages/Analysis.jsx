import { useQuery } from '@tanstack/react-query';
import { fetchTrends, fetchGaps } from '../lib/api';
import { useProject } from '../context/ProjectContext';
import { Link } from 'react-router-dom';
import EmptyState from '../components/EmptyState';
import PriorityPill from '../components/PriorityPill';
import { BarChart3, FolderKanban, AlertTriangle, CheckCircle2, Star, Building2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function Analysis() {
  const { project } = useProject();

  if (!project) return <EmptyState icon={FolderKanban} title="No project selected" message="Select a project first." ctaLabel="Go to Projects" ctaTo="/projects" />;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-[#FAFAFA]">Trends & Analysis</h1>
        <p className="text-sm text-[#A1A1AA] mt-1">Competitor trends and gap analysis for {project.name}</p>
      </div>

      <TrendsSection projectId={project.id} />
      <GapSection projectId={project.id} />
    </div>
  );
}

function TrendsSection({ projectId }) {
  const { data: trends = [], isLoading } = useQuery({
    queryKey: ['trends', projectId],
    queryFn: () => fetchTrends(projectId),
  });

  if (isLoading) return <div className="h-64 bg-[#141416] rounded-xl border border-[#27272A] animate-pulse" />;
  if (trends.length === 0) return <EmptyState icon={BarChart3} title="No trends yet" message="Trends appear after posts are classified by the AI pipeline." />;

  const chartData = trends.map((t) => ({ name: t.topic, value: t.percentage }));

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-medium text-[#FAFAFA]">Topic Trends</h2>

      {/* Bar chart */}
      <div className="bg-[#141416] border border-[#27272A] rounded-xl p-6">
        <ResponsiveContainer width="100%" height={Math.max(200, trends.length * 44)}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
            <XAxis type="number" domain={[0, 100]} tick={{ fill: '#A1A1AA', fontSize: 12 }} tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#FAFAFA', fontSize: 13 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#141416', border: '1px solid #27272A', borderRadius: 8, fontSize: 13 }}
              labelStyle={{ color: '#FAFAFA' }}
              formatter={(v) => [`${v}%`, 'Share']}
            />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={28}>
              {chartData.map((_, i) => <Cell key={i} fill={i === 0 ? '#6366F1' : '#818CF8'} fillOpacity={1 - i * 0.08} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className="bg-[#141416] border border-[#27272A] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#27272A] text-[#A1A1AA]">
              <th className="text-left px-4 py-3 font-medium">Topic</th>
              <th className="text-right px-4 py-3 font-medium">Rivals</th>
              <th className="text-right px-4 py-3 font-medium">Posts</th>
              <th className="text-right px-4 py-3 font-medium">Share</th>
            </tr>
          </thead>
          <tbody>
            {trends.map((t) => (
              <tr key={t.id} className="border-b border-[#27272A] last:border-0 hover:bg-[#1C1C1F] transition-colors">
                <td className="px-4 py-3 text-[#FAFAFA]">{t.topic}</td>
                <td className="px-4 py-3 text-right font-mono text-[#A1A1AA]">{t.competitor_count}</td>
                <td className="px-4 py-3 text-right font-mono text-[#A1A1AA]">{t.occurrence_count}</td>
                <td className="px-4 py-3 text-right font-mono text-[#6366F1]">{t.percentage}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function GapSection({ projectId }) {
  const { data, isLoading } = useQuery({
    queryKey: ['gaps', projectId],
    queryFn: () => fetchGaps(projectId),
  });

  if (isLoading) return <div className="h-48 bg-[#141416] rounded-xl border border-[#27272A] animate-pulse" />;

  if (!data?.client_registered) {
    return (
      <section className="bg-[#141416] border border-[#27272A] rounded-xl p-6">
        <div className="flex items-center gap-3 mb-3">
          <Building2 size={20} className="text-[#F59E0B]" />
          <h2 className="text-lg font-medium text-[#FAFAFA]">Gap Analysis</h2>
        </div>
        <p className="text-sm text-[#A1A1AA] mb-4">Register your business on the My Business page to unlock gap analysis.</p>
        <Link to="/my-business" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#6366F1] text-sm text-white font-medium hover:bg-[#818CF8] transition-colors">
          Go to My Business →
        </Link>
      </section>
    );
  }

  const gaps = data.gaps || [];
  const covered = data.covered || [];
  const clientOnly = data.client_only_topics || [];

  return (
    <section className="flex flex-col gap-6">
      <h2 className="text-lg font-medium text-[#FAFAFA]">Gap Analysis</h2>

      {/* Opportunities (gaps) */}
      <div className="bg-[#141416] border border-[#27272A] rounded-xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[#27272A]">
          <AlertTriangle size={16} className="text-[#EF4444]" />
          <h3 className="text-sm font-medium text-[#FAFAFA]">Opportunities</h3>
          <span className="text-xs text-[#A1A1AA]">— Topics rivals cover that you don't</span>
        </div>
        {gaps.length === 0 ? (
          <p className="px-4 py-4 text-sm text-[#A1A1AA]">No gaps — you're covering all rival topics! 🎉</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#27272A] text-[#A1A1AA]">
                <th className="text-left px-4 py-2 font-medium">Topic</th>
                <th className="text-right px-4 py-2 font-medium">Rivals</th>
                <th className="text-right px-4 py-2 font-medium">Priority</th>
              </tr>
            </thead>
            <tbody>
              {gaps.map((g) => (
                <tr key={g.topic} className="border-b border-[#27272A] last:border-0 hover:bg-[#1C1C1F] transition-colors">
                  <td className="px-4 py-2.5 text-[#FAFAFA]">{g.topic}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[#A1A1AA]">{g.competitors_using}</td>
                  <td className="px-4 py-2.5 text-right"><PriorityPill priority={g.priority} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Already Covered */}
      <div className="bg-[#141416] border border-[#27272A] rounded-xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[#27272A]">
          <CheckCircle2 size={16} className="text-[#22C55E]" />
          <h3 className="text-sm font-medium text-[#FAFAFA]">Already Covered</h3>
        </div>
        {covered.length === 0 ? (
          <p className="px-4 py-4 text-sm text-[#A1A1AA]">No overlapping topics yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#27272A] text-[#A1A1AA]">
                <th className="text-left px-4 py-2 font-medium">Topic</th>
                <th className="text-right px-4 py-2 font-medium">Rivals</th>
                <th className="text-right px-4 py-2 font-medium">Posts</th>
              </tr>
            </thead>
            <tbody>
              {covered.map((c) => (
                <tr key={c.topic} className="border-b border-[#27272A] last:border-0 hover:bg-[#1C1C1F] transition-colors">
                  <td className="px-4 py-2.5 text-[#22C55E]">{c.topic}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[#A1A1AA]">{c.competitors_using}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[#A1A1AA]">{c.occurrence_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Your Unique Topics */}
      {clientOnly.length > 0 && (
        <div className="bg-[#141416] border border-[#27272A] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Star size={16} className="text-[#F59E0B]" />
            <h3 className="text-sm font-medium text-[#FAFAFA]">Your Unique Topics</h3>
            <span className="text-xs text-[#A1A1AA]">— Differentiators only you post about</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {clientOnly.map((t) => (
              <span key={t} className="px-3 py-1 rounded-full text-sm bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/30">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
