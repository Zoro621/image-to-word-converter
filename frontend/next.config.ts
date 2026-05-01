import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow cross-origin images for previews
  images: {
    remotePatterns: [],
  },
  // Transpile Three.js ecosystem
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
};

export default nextConfig;
