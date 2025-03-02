/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  images: {
    domains: ["images.pexels.com", "i.ytimg.com"],
  },
  env: {
    BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
  },
};

module.exports = nextConfig;
