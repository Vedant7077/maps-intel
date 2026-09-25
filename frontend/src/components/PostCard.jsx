import { X, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { useState } from 'react';

export function parseList(val) {
  if (!val) return [];
  if (Array.isArray(val)) {
    if (val.length === 1 && typeof val[0] === 'string' && val[0].startsWith('[')) {
      try {
        const inner = JSON.parse(val[0]);
        if (Array.isArray(inner)) return inner;
      } catch {}
    }
    return val;
  }
  if (typeof val === 'string') {
    try {
      const parsed = JSON.parse(val);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      if (val.startsWith('{') && val.endsWith('}')) {
        return val.slice(1, -1).split(',').map((s) => s.trim().replace(/^"|"$/g, '')).filter(Boolean);
      }
      return val.split(',').map((s) => s.trim()).filter(Boolean);
    }
  }
  return [];
}

export function PostCard({ post, onClick }) {
  const imageUrls = parseList(post?.image_urls);
  const img = imageUrls[0];
  const text = post.post_text?.length > 120
    ? post.post_text.slice(0, 120) + '…'
    : post.post_text;

  return (
    <div
      onClick={onClick}
      className="bg-[#141416] border border-[#27272A] rounded-xl overflow-hidden cursor-pointer hover:bg-[#1C1C1F] hover:border-[#6366F1]/40 transition-all group"
    >
      {img && (
        <div className="h-40 bg-[#0A0A0B] overflow-hidden">
          <img src={img} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
        </div>
      )}
      <div className="p-4 flex flex-col gap-2">
        {post.main_topic && (
          <span className="inline-flex self-start px-2 py-0.5 rounded-full text-xs font-medium bg-[#6366F1]/15 text-[#818CF8] border border-[#6366F1]/30">
            {post.main_topic}
          </span>
        )}
        <p className="text-sm text-[#FAFAFA] leading-relaxed">{text}</p>
        {post.published_date && (
          <span className="text-xs text-[#A1A1AA] font-mono">
            {new Date(post.published_date).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}

export function PostLightbox({ post, onClose }) {
  const [imgIdx, setImgIdx] = useState(0);
  const images = parseList(post?.image_urls);
  const keywords = parseList(post?.keywords);

  if (!post) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={onClose}>
      <div
        className="bg-[#141416] border border-[#27272A] rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Image carousel */}
        {images.length > 0 && (
          <div className="relative h-64 bg-[#0A0A0B]">
            <img src={images[imgIdx]} alt="" className="w-full h-full object-contain" />
            {images.length > 1 && (
              <>
                <button onClick={() => setImgIdx((i) => (i - 1 + images.length) % images.length)}
                  className="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 rounded-full p-1 hover:bg-black/70">
                  <ChevronLeft size={20} />
                </button>
                <button onClick={() => setImgIdx((i) => (i + 1) % images.length)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 rounded-full p-1 hover:bg-black/70">
                  <ChevronRight size={20} />
                </button>
                <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                  {images.map((_, i) => (
                    <span key={i} className={`w-1.5 h-1.5 rounded-full ${i === imgIdx ? 'bg-white' : 'bg-white/40'}`} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        <div className="p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              {post.main_topic && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-[#6366F1]/15 text-[#818CF8] border border-[#6366F1]/30">
                  {post.main_topic}
                </span>
              )}
              {post.content_type && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30">
                  {post.content_type}
                </span>
              )}
            </div>
            <button onClick={onClose} className="text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors">
              <X size={20} />
            </button>
          </div>

          <p className="text-sm text-[#FAFAFA] leading-relaxed whitespace-pre-wrap">{post.post_text}</p>

          {post.cta_text && (
            <div className="text-sm text-[#A1A1AA]">
              <span className="font-medium text-[#FAFAFA]">CTA:</span> {post.cta_text}
              {post.cta_type && <span className="text-[#6366F1] ml-1">({post.cta_type})</span>}
            </div>
          )}

          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {keywords.map((kw, i) => (
                <span key={i} className="px-2 py-0.5 rounded-md text-xs bg-[#1C1C1F] text-[#A1A1AA] border border-[#27272A]">
                  {kw}
                </span>
              ))}
            </div>
          )}

          {post.post_url && (
            <a href={post.post_url} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-[#6366F1] hover:text-[#818CF8] transition-colors">
              <ExternalLink size={14} /> View original
            </a>
          )}

          <div className="flex items-center gap-3 text-xs text-[#A1A1AA] font-mono border-t border-[#27272A] pt-3 mt-1">
            {post.published_date && <span>Published: {new Date(post.published_date).toLocaleDateString()}</span>}
            {post.scraped_at && <span>Scraped: {new Date(post.scraped_at).toLocaleDateString()}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
