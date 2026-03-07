/** @type {import('next').NextConfig} */
const nextConfig = {
  // API Rewrites - Proxy /api/v1/* to backend
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/v1/:path*`,
      },
    ];
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'JobScale',
  },

  // Image optimization
  images: {
    domains: ['media.licdn.com', 'logos-world.net', 'images.crunchbase.com'],
  },

  // TypeScript
  typescript: {
    ignoreBuildErrors: true, // Allow build even with TS errors during development
  },

  // ESLint
  eslint: {
    ignoreDuringBuilds: true, // Allow build even with ESLint errors during development
  },

  // React strict mode (disable in production for performance)
  reactStrictMode: process.env.NODE_ENV !== 'production',

  // Output configuration
  output: 'standalone', // Optimize for Docker deployment

  // Compression
  compress: true,

  // Power header
  poweredByHeader: false,
};

module.exports = nextConfig;
