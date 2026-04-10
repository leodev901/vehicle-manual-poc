'use client'

import { useEffect, useRef } from 'react'
import { BookOpen, Zap, AlertTriangle, Bluetooth, Sparkles } from 'lucide-react'
import type { ChatMessage } from '@/types'

/* ── 퀵 액션 카드 정의 ── */
const QUICK_ACTIONS = [
  { id: 'qa-battery',   icon: Zap,          label: '스마트키 배터리 교체' },
  { id: 'qa-airfilter', icon: Sparkles,     label: '에어컨 필터 교체' },
  { id: 'qa-warning',   icon: AlertTriangle, label: '계기판 경고등 의미' },
  { id: 'qa-bluetooth', icon: Bluetooth,    label: '블루투스 페어링' },
]

interface ChatInterfaceProps {
  messages: ChatMessage[]
  /** 퀵 액션 클릭 시 해당 질문을 입력창에 바로 전송 */
  onQuickAction: (text: string) => void
}

/**
 * 채팅 메시지 스크롤 영역
 * - Empty State: 인사말 + 퀵 액션 카드
 * - 유저 메시지 버블 (우측 정렬, signature-gradient)
 * - AI 메시지 버블 (좌측 정렬, surface-container-highest)
 * - 스트리밍 중 로딩 점 애니메이션
 * - 출처 뱃지 (Reference Tag)
 */
export default function ChatInterface({ messages, onQuickAction }: ChatInterfaceProps) {
  /* 새 메시지 추가 시 자동으로 맨 아래로 스크롤 */
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="h-full overflow-y-auto scrollbar-hidden py-4">
      {messages.length === 0 ? (
        /* ── Empty State ── */
        <div className="flex flex-col items-center text-center px-8 mt-16">
          {/* 아이콘 */}
          <div className="w-20 h-20 bg-primary-container/20 rounded-full flex items-center justify-center mb-6">
            <Sparkles className="w-9 h-9 text-primary" strokeWidth={1.2} />
          </div>

          <h1 className="font-headline text-3xl font-extrabold text-on-surface tracking-tight mb-3 leading-tight">
            무엇을 도와드릴까요?
          </h1>
          <p className="text-on-surface-variant text-sm mb-10 leading-relaxed">
            전체 차량 매뉴얼을 AI가 학습했습니다.<br />
            경고등, 유지보수, 기능 사용법 무엇이든 물어보세요.
          </p>

          {/* 퀵 액션 카드 그리드 */}
          <div className="grid grid-cols-2 gap-3 w-full">
            {QUICK_ACTIONS.map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                id={id}
                onClick={() => onQuickAction(label)}
                className="bg-surface-container-lowest border border-outline-variant/15 px-4 py-4 rounded-DEFAULT text-xs font-semibold text-left hover:bg-surface-container-low transition-colors flex flex-col gap-2 shadow-card active:scale-95"
              >
                <Icon className="w-5 h-5 text-primary" strokeWidth={1.5} />
                {label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* ── 메시지 목록 ── */
        <div className="flex flex-col gap-6 px-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col animate-fade-up ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              {msg.role === 'user' ? (
                /* 유저 메시지 버블 */
                <>
                  <div className="user-bubble signature-gradient text-on-primary px-5 py-3.5 max-w-[85%] shadow-lg shadow-primary/10">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  <span className="text-[10px] uppercase tracking-widest text-on-surface-variant mt-1.5 mr-2 opacity-50">
                    {formatTime(msg.timestamp)}
                  </span>
                </>
              ) : (
                /* AI 메시지 버블 */
                <>
                  {/* 스트리밍 로딩 상태 표시 */}
                  {msg.isStreaming && msg.statusMessage && (
                    <div className="flex items-center gap-2 px-4 py-1.5 mb-1 text-xs text-on-surface-variant italic">
                      <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-pulse-dot dot-delay-1" />
                      <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-pulse-dot dot-delay-2" />
                      <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-pulse-dot dot-delay-3" />
                      <span>{msg.statusMessage}</span>
                    </div>
                  )}

                  {/* 스트리밍 점 (내용 없을 때) */}
                  {msg.isStreaming && !msg.content ? (
                    <div className="ai-bubble bg-surface-container-low px-5 py-4 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-pulse-dot dot-delay-1" />
                      <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-pulse-dot dot-delay-2" />
                      <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-pulse-dot dot-delay-3" />
                    </div>
                  ) : (
                    <div className="ai-bubble bg-surface-container-highest text-on-surface px-5 py-4 max-w-[90%] shadow-card">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      {/* 스트리밍 커서 */}
                      {msg.isStreaming && (
                        <span className="inline-block w-0.5 h-4 bg-primary ml-0.5 animate-pulse rounded-full" />
                      )}
                    </div>
                  )}

                  {/* 출처 뱃지 (스트리밍 완료 후 표시) */}
                  {!msg.isStreaming && msg.content && (
                    <div className="mt-2 ml-1">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-surface-container-low text-primary text-[11px] font-semibold rounded-full border border-outline-variant/15 hover:bg-primary-container/10 cursor-pointer transition-colors">
                        <BookOpen className="w-3 h-3" strokeWidth={1.5} />
                        매뉴얼 기반 답변
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}
