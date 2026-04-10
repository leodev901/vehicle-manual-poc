/* ──────────────────────────────────────────────────────
 * 백엔드의 Pydantic 스키마와 매핑되는 TypeScript 타입 정의
 * ────────────────────────────────────────────────────── */

/** 브랜드 (예: 현대, 기아) */
export interface Brand {
  brand_id: string
  brand_nm: string
}

/** 라인업 (예: SUV, 세단) */
export interface Lineup {
  lineup_id: string
  lineup_nm: string
  brand_id: string
  type: string | null
}

/** 차량 모델 (예: 투싼 하이브리드 2024) */
export interface CarModel {
  model_id: string
  model_nm: string
  lineup_id: string
  fuel_type: string
  gen_no: number
}

/** 공통 API 응답 래퍼 (CommonResponse) */
export interface CommonResponse<T> {
  status_code: number
  message: string
  data: T
}

/** LLM 설정: chat/stream 요청에 포함 */
export interface LlmConfig {
  provider: 'openai' | 'google'
  model: string
}

/** 채팅 요청 (POST /api/v1/chat/stream) */
export interface ChatRequest {
  session_id: string
  model_id: string | null
  llm_config: LlmConfig
  message: string
}

/** 현재 선택된 차량 컨텍스트 (프론트엔드 상태 관리용) */
export interface VehicleContext {
  brand: Brand | null
  lineup: Lineup | null
  model: CarModel | null
}

/** 채팅 메시지 (UI 렌더링용) */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  /** SSE 스트리밍 상태 정보 (예: "키워드 추출 중...") */
  statusMessage?: string
  isStreaming?: boolean
}

/** LLM 모델 설정 선택지 */
export const LLM_OPTIONS = [
  { label: 'GPT-5', provider: 'openai', model: 'gpt-5-mini' },
  { label: 'Gemini', provider: 'google', model: 'gemini-2.5-flash' },
] as const

export type LlmOptionKey = (typeof LLM_OPTIONS)[number]['label']
