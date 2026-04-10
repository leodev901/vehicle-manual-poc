import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Auto-Guide AI | 차량 매뉴얼 AI 챗봇',
  description: '차량 매뉴얼을 AI가 읽고, 사용자의 질문에 정확하게 답변하는 RAG 기반 인텔리전트 챗봇 서비스입니다.',
  keywords: ['차량 매뉴얼', 'AI 챗봇', 'RAG', '현대', '기아', '제네시스'],
  openGraph: {
    title: 'Auto-Guide AI',
    description: '차량 매뉴얼 AI 가이드',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
