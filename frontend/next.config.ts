import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["10.196.242.15"],
  async rewrites() {
    return [
      {
        source: "/backend-api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
