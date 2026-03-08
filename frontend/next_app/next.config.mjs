/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["react-markdown", "remark-gfm", "remark-parse", "unified", "vfile", "unist-util-visit", "mdast-util-to-hast", "hast-util-to-jsx-runtime", "@radix-ui/react-select", "@radix-ui/react-dialog", "remark-math", "rehype-katex", "katex"],
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '6305',
        pathname: '/api/**',
      },
    ],
  },
};

export default nextConfig;
