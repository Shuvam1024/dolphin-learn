import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Public demo tunnels hit the dev server with a foreign Host.
  allowedDevOrigins: ["*.trycloudflare.com", "*.loca.lt"],
};

export default nextConfig;
