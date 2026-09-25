export default function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="bg-[#141416] border border-[#27272A] rounded-xl p-5 flex flex-col gap-2 hover:bg-[#1C1C1F] transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-[#A1A1AA] text-sm">{label}</span>
        {Icon && <Icon size={18} className="text-[#A1A1AA]" />}
      </div>
      <span className="text-3xl font-semibold font-mono text-[#FAFAFA]">{value}</span>
      {sub && <span className="text-xs text-[#A1A1AA]">{sub}</span>}
    </div>
  );
}
