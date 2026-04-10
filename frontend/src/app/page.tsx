'use client'

import { useState, useCallback } from 'react'
import TopAppBar from '@/components/TopAppBar'
import VehicleSelectorChip from '@/components/VehicleSelectorChip'
import ChatInterface from '@/components/ChatInterface'
import ChatInput from '@/components/ChatInput'
import type { ChatMessage, VehicleContext, LlmOptionKey } from '@/types'
import { LLM_OPTIONS } from '@/types'
import { streamChat } from '@/lib/api'

/**
 * 메인 페이지
 * 
 * 상태 관리:
 * - sessionId:    대화 세션 UUID (새 대화 시작 시 재생성)
 * - vehicleCtx:  선택된 차량 컨텍스트 (브랜드/라인업/모델)
 * - messages:    채팅 메시지 배열
 * - selectedLlm: 현재 선택된 LLM 라벨 ('GPT-5' | 'Gemini')
 * - isStreaming:  SSE 스트리밍 진행 중 여부
 */
export default function HomePage() {
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID())
  const [vehicleCtx, setVehicleCtx] = useState<VehicleContext>({ brand: null, lineup: null, model: null })
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [selectedLlm, setSelectedLlm] = useState<LlmOptionKey>('GPT-5')
  const [isStreaming, setIsStreaming] = useState(false)

  /** 선택된 LLM의 provider/model 정보 */
  const currentLlm = LLM_OPTIONS.find(o => o.label === selectedLlm) ?? LLM_OPTIONS[0]

  /** 새 대화 시작: 세션 ID 재생성 + 메시지 초기화 */
  const handleNewSession = useCallback(() => {
    setSessionId(crypto.randomUUID())
    setMessages([])
  }, [])

  /** 차량 확정 */
  const handleVehicleConfirm = useCallback((ctx: VehicleContext) => {
    setVehicleCtx(ctx)
    // 차량이 바뀌면 세션도 초기화
    setSessionId(crypto.randomUUID())
    setMessages([])
  }, [])

  /**
   * 메시지 전송 + SSE 스트리밍 응답 처리
   * 
   * 동작 순서:
   * 1. 유저 메시지를 messages에 추가
   * 2. 빈 AI 메시지(isStreaming: true)를 생성
   * 3. streamChat()으로 SSE 스트리밍 시작
   * 4. onChunk: AI 메시지 content에 토큰 누적
   * 5. onDone/onError: 스트리밍 종료 처리
   */
  const handleSend = useCallback(async (text: string) => {
    if (isStreaming) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }

    // AI 응답 자리를 미리 만들어 스트리밍 상태 표시
    const aiMsgId = crypto.randomUUID()
    const aiPlaceholder: ChatMessage = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      statusMessage: '답변을 생성하는 중...',
    }

    setMessages(prev => [...prev, userMsg, aiPlaceholder])
    setIsStreaming(true)

    await streamChat({
      sessionId,
      modelId: vehicleCtx.model?.model_id ?? null,
      message: text,
      llmProvider: currentLlm.provider,
      llmModel: currentLlm.model,

      // 상태 메시지(키워드 추출 중, RAG 검색 중 등)
      onStatusUpdate: (status) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === aiMsgId ? { ...m, statusMessage: status } : m
          )
        )
      },
      // 토큰을 AI 메시지에 누적
      onChunk: (token) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === aiMsgId
              ? { ...m, content: m.content + token, statusMessage: undefined }
              : m
          )
        )
      },
      // 스트리밍 완료
      onDone: () => {
        setMessages(prev =>
          prev.map(m =>
            m.id === aiMsgId ? { ...m, isStreaming: false, statusMessage: undefined } : m
          )
        )
        setIsStreaming(false)
      },
      // 에러 처리
      onError: (err) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === aiMsgId
              ? { ...m, content: `오류가 발생했습니다: ${err}`, isStreaming: false }
              : m
          )
        )
        setIsStreaming(false)
      },
    })
  }, [isStreaming, sessionId, vehicleCtx, currentLlm])

  /** 퀵 액션 클릭 시 바로 전송 */
  const handleQuickAction = useCallback((text: string) => {
    handleSend(text)
  }, [handleSend])

  return (
    /*
     * 풀 브라우저 높이 레이아웃
     * 가로: max-w-[1150px] (기존 대비 2.5배), 세로: h-screen (브라우저 전체)
     */
    <main className="h-screen flex items-stretch justify-center bg-[#eef0f0]">
      {/* 배경 장식 (주변 글로우) */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute bottom-[-5%] left-[-5%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-[100px]" />
      </div>

      {/* 확장 컨테이너: 가로 max-w-[748px], 세로 h-screen */}
      <div className="relative w-full max-w-[748px] h-screen bg-surface flex flex-col shadow-floating border-x border-outline-variant/10">
        {/* ── 헤더 ── */}
        <TopAppBar
          selectedLlm={selectedLlm}
          onLlmChange={(label) => setSelectedLlm(label as LlmOptionKey)}
          onNewSession={handleNewSession}
        />

        {/* ── 스크롤 콘텐츠 영역: 헤더(60px) + 인풋(72px) 제외한 나머지 전부 ── */}
        <div className="flex flex-col" style={{ height: 'calc(100vh - 60px - 72px)', marginTop: '60px' }}>
          {/* 차량 선택 칩 */}
          <div className="flex-shrink-0">
            <VehicleSelectorChip context={vehicleCtx} onConfirm={handleVehicleConfirm} />
          </div>

          {/* 채팅 메시지 영역: 남은 공간을 차지하며 내부 스크롤 */}
          <div className="flex-1 min-h-0">
            <ChatInterface messages={messages} onQuickAction={handleQuickAction} />
          </div>
        </div>

        {/* ── 하단 입력창 ── */}
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </main>
  )
}
