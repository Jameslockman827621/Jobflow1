/**
 * Base URL for REST calls to the FastAPI backend (`.../api/v1`).
 *
 * - Static export (e.g. Cloudflare Pages): set `NEXT_PUBLIC_BACKEND_URL` at build time
 *   to your API origin, e.g. `https://api.yourdomain.com`, or set `NEXT_PUBLIC_API_URL`
 *   to the full API prefix, e.g. `https://api.yourdomain.com/api/v1`.
 * - Local Next dev with rewrites: omit both to use same-origin `/api/v1`.
 */
export function getApiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
  if (explicit) {
    return explicit;
  }
  const backend = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '');
  if (backend) {
    return `${backend}/api/v1`;
  }
  return '/api/v1';
}
