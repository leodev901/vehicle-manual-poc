/**
 * 백엔드 API 호출 함수 모음
 * 
 * 기본 URL은 환경 변수 NEXT_PUBLIC_API_BASE_URL 을 따르며,
 * next.config.js 의 rewrites 설정으로 로컬 개발 시 CORS 없이 백엔드 호출 가능.
 */

import type { Brand, Lineup, CarModel, CommonResponse } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || ''

/**
 * 공통 fetch 래퍼
 * 에러 발생 시 raw exception 대신 친화적인 에러 메시지로 변환
 */
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API 오류 (${res.status}): ${text}`)
  }
  return res.json() as Promise<T>
}

/** 차량 브랜드 목록 조회 */
export async function fetchBrands(): Promise<Brand[]> {
  const resp = await apiFetch<CommonResponse<Brand[]>>('/api/v1/manual/brands')
  return resp.data
}

/** 브랜드별 라인업 목록 조회 */
export async function fetchLineups(brandId: string): Promise<Lineup[]> {
  const resp = await apiFetch<CommonResponse<Lineup[]>>(
    `/api/v1/manual/lineups?brand_id=${encodeURIComponent(brandId)}`
  )
  return resp.data
}

/** 라인업별 모델 목록 조회 */
export async function fetchModels(lineupId: string): Promise<CarModel[]> {
  const resp = await apiFetch<CommonResponse<CarModel[]>>(
    `/api/v1/manual/models?lineup_id=${encodeURIComponent(lineupId)}`
  )
  return resp.data
}

/**
 * SSE 스트리밍 채팅 요청
 * 
 * 백엔드의 StreamingResponse(text/event-stream)를 파싱하여
 * 토큰이 올 때마다 onChunk 콜백을 호출함.
 * 스트리밍이 끝나면 onDone을 호출.
 */
export async function streamChat({
  sessionId,
  modelId,
  message,
  llmProvider,
  llmModel,
  onStatusUpdate,
  onChunk,
  onDone,
  onError,
}: {
  sessionId: string
  modelId: string | null
  message: string
  llmProvider: string
  llmModel: string
  onStatusUpdate?: (status: string) => void
  onChunk: (token: string) => void
  onDone: () => void
  onError: (err: string) => void
}) {
  try {
    const resp = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        model_id: modelId,
        llm_config: { provider: llmProvider, model: llmModel },
        message,
      }),
    })

    if (!resp.ok || !resp.body) {
      onError(`서버 오류 (${resp.status})`)
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      // SSE 포맷 파싱: "data: {...}\n\n"
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (!raw || raw === '[DONE]') continue

        try {
          const parsed = JSON.parse(raw)
          // 백엔드가 보내는 status 이벤트 (예: 키워드 추출 중...)
          if (parsed.status && onStatusUpdate) {
            onStatusUpdate(parsed.message ?? '')
          } else if (parsed.token) {
            // 실제 LLM 토큰
            onChunk(parsed.token)
          } else if (typeof parsed === 'string') {
            onChunk(parsed)
          }
        } catch {
          // JSON 파싱 실패 시 raw 텍스트를 직접 사용
          onChunk(raw)
        }
      }
    }
    onDone()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
    onError(msg)
  }
}
