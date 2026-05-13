/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    // Production uses port 8132, development uses 8000
    const backendUrl = process.env.BACKEND_URL ||
      (process.env.NODE_ENV === 'production'
        ? 'http://127.0.0.1:8132'
        : 'http://localhost:8000')

    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
      {
        // Authentik OIDC login/callback/logout served by backend at /api/auth/*
        source: '/api/auth/:path*',
        destination: `${backendUrl}/api/auth/:path*`,
      },
    ]
  },
  async redirects() {
    return [
      {
        source: '/medicamentos',
        destination: '/editor/cif-medicamentos-workspace',
        permanent: true,
      },
    ]
  },
}

export default nextConfig
