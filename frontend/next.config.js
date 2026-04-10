/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  /* 
   * 백엔드 API 프록시 설정
   * 로컬 개발 시 CORS 문제 없이 백엔드를 호출하기 위한 rewrites
   */
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8009'}/api/v1/:path*`,
      },
      {
        source: '/api/manual/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/v1/manual/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
