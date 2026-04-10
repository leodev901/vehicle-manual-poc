'use client'

import { Car, Settings, RotateCcw } from 'lucide-react'
import { LLM_OPTIONS } from '@/types'

interface TopAppBarProps {
  /** 현재 선택된 LLM 라벨 (예: 'GPT-5') */
  selectedLlm: string
  /** LLM 변경 시 호출 */
  onLlmChange: (label: string) => void
  /** 새 대화 시작(세션 초기화) 핸들러 */
  onNewSession: () => void
}

/**
 * 상단 앱바
 * - Auto-Guide AI 로고 (좌측)
 * - LLM 토글 버튼 + 새 대화 시작 아이콘 (우측)
 */
export default function TopAppBar({ selectedLlm, onLlmChange, onNewSession }: TopAppBarProps) {
  return (
    <header className="absolute top-0 w-full z-50 glass shadow-sm shadow-zinc-200/50 flex justify-between items-center px-5 py-3.5">
      {/* ── 로고 영역 ── */}
      <div className="flex items-center gap-2">
        <div className="w-9 h-9 rounded-full bg-primary-container/20 flex items-center justify-center">
          <Car className="w-5 h-5 text-primary" strokeWidth={1.5} />
        </div>
        <span className="font-headline font-bold text-lg tracking-tight text-primary">
          Auto-Guide AI
        </span>
      </div>

      {/* ── 우측 컨트롤 영역 ── */}
      <div className="flex items-center gap-2">
        {/* LLM 모델 토글 */}
        <div className="flex items-center bg-surface-container-high rounded-full p-1 border border-outline-variant/15">
          {LLM_OPTIONS.map((opt) => (
            <button
              key={opt.label}
              id={`llm-toggle-${opt.label.toLowerCase()}`}
              onClick={() => onLlmChange(opt.label)}
              className={`px-3 py-1 text-[11px] font-semibold rounded-full transition-all duration-200 ${selectedLlm === opt.label
                  ? 'bg-white text-on-surface shadow-sm'
                  : 'text-on-surface-variant hover:text-primary'
                }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* 새 대화 시작 버튼 */}
        <button
          id="btn-new-session"
          onClick={onNewSession}
          title="새 대화 시작"
          className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low"
        >
          <RotateCcw className="w-4 h-4" strokeWidth={1.5} />
        </button>

        {/* 설정 */}
        <button
          id="btn-settings"
          title="설정"
          className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low"
        >
          <Settings className="w-4 h-4" strokeWidth={1.5} />
        </button>
      </div>
    </header>
  )
}
