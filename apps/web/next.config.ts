import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Public demo tunnel (trycloudflare) hits the dev server with a foreign Host.
  allowedDevOrigins: ["*.trycloudflare.com"],
};

export default nextConfig;
