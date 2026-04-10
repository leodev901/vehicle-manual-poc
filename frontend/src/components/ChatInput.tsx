'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { ArrowUp, Paperclip } from 'lucide-react'

interface ChatInputProps {
  /** 메시지 전송 가능 여부 (스트리밍 중에는 비활성화) */
  disabled?: boolean
  /** 전송 핸들러 */
  onSend: (text: string) => void
}

/**
 * 하단 고정 채팅 입력창
 * - Glassmorphism 적용 floating 인풋
 * - Enter로 전송, Shift+Enter로 줄바꿈
 * - 전송 버튼: signature-gradient 원형 버튼
 */
export default function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    // textarea 높이 초기화
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  /* Enter: 전송 / Shift+Enter: 줄바꿈 */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  /* textarea 높이를 내용에 맞게 자동 조절 (최대 5줄) */
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
    setText(el.value)
  }

  const canSend = text.trim().length > 0 && !disabled

  return (
    /* 하단 글래스 바 */
    <div className="absolute bottom-0 left-0 w-full glass px-4 pt-3 pb-5 border-t border-outline-variant/10">
      <div className="flex items-end gap-2">
        {/* 첨부 버튼 */}
        <button
          id="btn-attach"
          title="첨부"
          className="p-2.5 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low flex-shrink-0 mb-0.5"
        >
          <Paperclip className="w-5 h-5" strokeWidth={1.5} />
        </button>

        {/* 텍스트 입력 필드 */}
        <div className="flex-1 bg-surface-container-lowest rounded-full px-5 py-3 shadow-card border border-outline-variant/10 flex items-end">
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={text}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="차량에 대해 무엇이든 물어보세요..."
            rows={1}
            className="w-full bg-transparent resize-none border-none outline-none text-sm font-medium text-on-surface placeholder:text-on-surface-variant/40 leading-relaxed"
            style={{ maxHeight: '120px', overflowY: 'auto' }}
          />
        </div>

        {/* 전송 버튼 */}
        <button
          id="btn-send"
          onClick={handleSend}
          disabled={!canSend}
          className={`w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0 mb-0.5 transition-all duration-200 ${
            canSend
              ? 'signature-gradient text-on-primary shadow-lg shadow-primary/20 active:scale-90 hover:shadow-xl'
              : 'bg-surface-container-high text-on-surface-variant cursor-not-allowed'
          }`}
        >
          <ArrowUp className="w-5 h-5" strokeWidth={2.5} />
        </button>
      </div>
    </div>
  )
}
