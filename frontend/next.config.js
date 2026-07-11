/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production';

const nextConfig = {
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'JobScale',
  },

  // Image optimization — domains we may load company logos from
  images: {
    domains: ['media.licdn.com', 'logos-world.net', 'images.crunchbase.com'],
    // Static export doesn't support the default loader — disable optimization
    unoptimized: true,
  },

  // TypeScript — fail the build on type errors in production.
  // In dev we let it slide so the dev server stays fast.
  typescript: {
    ignoreBuildErrors: !isProd,
  },

  // ESLint — fail the build on lint errors in production.
  eslint: {
    ignoreDuringBuilds: !isProd,
  },

  // React strict mode in dev only (perf in prod)
  reactStrictMode: !isProd,

  // Output: static export for Cloudflare Pages. With this enabled, rewrites()
  // are NOT supported (Next.js warns about this). The frontend uses getApiBase()
  // (lib/apiBase.ts) which reads NEXT_PUBLIC_BACKEND_URL at build time to point
  // directly at the API — no proxy needed.
  output: 'export',
  distDir: 'out',

  // Compression (handled by the CDN in prod, but fine to enable)
  compress: true,

  // Don't expose the Next.js brand
  poweredByHeader: false,
};

module.exports = nextConfig;
