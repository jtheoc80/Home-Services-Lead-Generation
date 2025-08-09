/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  eslint: {
    ignoreDuringBuilds: process.env.DISABLE_ESLINT === 'true',
  },
}

module.exports = nextConfig