const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

function qs(params) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') sp.set(k, v);
  });
  return sp.toString();
}

// ── Projects ──
export const fetchProjects = () => request('/api/projects');
export const createProject = ({ name, client_name, client_maps_url }) =>
  request(`/api/projects?${qs({ name, client_name, client_maps_url })}`, { method: 'POST' });

// ── Competitors ──
export const fetchCompetitors = (project_id, include_client = false) =>
  request(`/api/competitors?${qs({ project_id, include_client })}`);
export const createCompetitor = ({ project_id, name, maps_url }) =>
  request(`/api/competitors?${qs({ project_id, name, maps_url })}`, { method: 'POST' });

// ── Dashboard ──
export const fetchDashboard = (project_id) =>
  request(`/api/dashboard?${qs({ project_id })}`);

// ── Scrape ──
export const startScrape = ({ competitor_id, project_id }) =>
  request(`/api/scrape/start?${qs({ competitor_id, project_id })}`, { method: 'POST' });

// ── Jobs ──
export const fetchJob = (job_id) => request(`/api/jobs/${job_id}`);
export const resumeJob = (job_id) =>
  request(`/api/jobs/${job_id}/resume`, { method: 'POST' });

// ── Posts ──
export const fetchPosts = (params) => request(`/api/posts?${qs(params)}`);
export const fetchPost = (post_id) => request(`/api/posts/${post_id}`);

// ── Topics ──
export const fetchTopics = (project_id) =>
  request(`/api/topics?${qs({ project_id })}`);

// ── Trends ──
export const fetchTrends = (project_id) =>
  request(`/api/trends?${qs({ project_id })}`);

// ── Gaps ──
export const fetchGaps = (project_id) =>
  request(`/api/gaps?${qs({ project_id })}`);

// ── Client Business ──
export const fetchClientBusiness = (project_id) =>
  request(`/api/client-business?${qs({ project_id })}`);
export const upsertClientBusiness = ({ project_id, name, maps_url }) =>
  request(`/api/client-business?${qs({ project_id, name, maps_url })}`, { method: 'POST' });

// ── Ideas ──
export const generateIdeas = ({ project_id, count }) =>
  request(`/api/generate/ideas?${qs({ project_id, count })}`, { method: 'POST' });
export const fetchGeneratedIdeas = ({ project_id, page = 0, limit = 20 }) =>
  request(`/api/generated-ideas?${qs({ project_id, page, limit })}`);
