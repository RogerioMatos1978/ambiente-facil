/** @type {import('next').NextConfig} */
const nextConfig = {
  // "standalone" gera um bundle enxuto para produção (usado no Dockerfile.prod).
  output: "standalone",
};

export default nextConfig;
