const colors = {
  high: 'bg-red-500/15 text-red-400 border-red-500/30',
  medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  low: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
};

export default function PriorityPill({ priority }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[priority] || colors.low}`}>
      {priority}
    </span>
  );
}
