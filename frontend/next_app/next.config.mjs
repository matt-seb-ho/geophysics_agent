/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["react-markdown", "remark-gfm", "remark-parse", "unified", "vfile", "unist-util-visit", "mdast-util-to-hast", "hast-util-to-jsx-runtime"],
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/**',
      },
    ],
  },
};

export default nextConfig;
