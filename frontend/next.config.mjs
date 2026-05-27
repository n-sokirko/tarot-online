import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./i18n.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  // Allow the production domain to load /_next/* assets from the dev server
  allowedDevOrigins: ['sokirdon.com'],
};

export default withNextIntl(nextConfig);
