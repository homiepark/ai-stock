/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static-friendly: data lives in ./data/*.json, read at build time.
  // No serverless functions needed for the dashboard.
  trailingSlash: false,
  // Avoid noisy ESLint failures on initial Vercel deploys; we still run
  // lint locally and in CI.
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
