/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
  // Reduce memory usage
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.optimization = {
        ...config.optimization,
        minimize: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig
