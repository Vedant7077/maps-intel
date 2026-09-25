import { Inbox } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function EmptyState({ icon: Icon = Inbox, title, message, ctaLabel, ctaTo }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="bg-[#141416] border border-[#27272A] rounded-full p-4 mb-4">
        <Icon size={32} className="text-[#A1A1AA]" />
      </div>
      <h3 className="text-lg font-medium text-[#FAFAFA] mb-1">{title}</h3>
      {message && <p className="text-sm text-[#A1A1AA] max-w-md mb-4">{message}</p>}
      {ctaLabel && ctaTo && (
        <Link
          to={ctaTo}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#6366F1] text-white text-sm font-medium hover:bg-[#818CF8] transition-colors"
        >
          {ctaLabel}
        </Link>
      )}
    </div>
  );
}
