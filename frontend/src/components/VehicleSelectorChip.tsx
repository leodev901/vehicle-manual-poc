'use client'

import { useState, useEffect } from 'react'
import { Car, ChevronDown, ChevronRight, Check, X } from 'lucide-react'
import type { Brand, Lineup, CarModel, VehicleContext } from '@/types'
import { fetchBrands, fetchLineups, fetchModels } from '@/lib/api'

interface VehicleSelectorChipProps {
  /** 현재 선택된 차량 컨텍스트 */
  context: VehicleContext
  /** 차량 확정 시 호출 (model_id 저장용) */
  onConfirm: (ctx: VehicleContext) => void
}

/**
 * 차량 선택 위젯
 * - 평소엔 작은 칩(Chip) 형태로 선택된 차량 표시
 * - 클릭 시 확장(Accordion) → 브랜드/라인업/모델 3단 Cascade 선택
 * - 백엔드 API Cascade: brands → lineups?brand_id → models?lineup_id
 */
export default function VehicleSelectorChip({ context, onConfirm }: VehicleSelectorChipProps) {
  const [isOpen, setIsOpen] = useState(false)

  // ── 로딩된 목록 상태 ──
  const [brands, setBrands]   = useState<Brand[]>([])
  const [lineups, setLineups] = useState<Lineup[]>([])
  const [models, setModels]   = useState<CarModel[]>([])

  // ── 임시 선택 상태 (확정 전까지 컨텍스트에 반영 안 함) ──
  const [tmpBrand,  setTmpBrand]  = useState<Brand | null>(context.brand)
  const [tmpLineup, setTmpLineup] = useState<Lineup | null>(context.lineup)
  const [tmpModel,  setTmpModel]  = useState<CarModel | null>(context.model)

  const [loading, setLoading] = useState<'brand' | 'lineup' | 'model' | null>(null)
  const [error, setError]     = useState<string | null>(null)

  /* 드롭다운 열릴 때 브랜드 목록 로드 */
  useEffect(() => {
    if (!isOpen) return
    setLoading('brand')
    fetchBrands()
      .then(setBrands)
      .catch(() => setError('브랜드 목록을 불러오지 못했습니다.'))
      .finally(() => setLoading(null))
  }, [isOpen])

  /* 브랜드 선택 시 라인업 로드 */
  const handleSelectBrand = async (brand: Brand) => {
    setTmpBrand(brand)
    setTmpLineup(null)
    setTmpModel(null)
    setLineups([])
    setModels([])
    setLoading('lineup')
    try {
      const data = await fetchLineups(brand.brand_id)
      setLineups(data)
    } catch {
      setError('라인업 목록을 불러오지 못했습니다.')
    } finally {
      setLoading(null)
    }
  }

  /* 라인업 선택 시 모델 로드 */
  const handleSelectLineup = async (lineup: Lineup) => {
    setTmpLineup(lineup)
    setTmpModel(null)
    setModels([])
    setLoading('model')
    try {
      const data = await fetchModels(lineup.lineup_id)
      setModels(data)
    } catch {
      setError('모델 목록을 불러오지 못했습니다.')
    } finally {
      setLoading(null)
    }
  }

  /* 차량 확정 */
  const handleConfirm = () => {
    onConfirm({ brand: tmpBrand, lineup: tmpLineup, model: tmpModel })
    setIsOpen(false)
  }

  /* 닫기 */
  const handleClose = () => {
    // 임시 상태를 현재 컨텍스트로 되돌림
    setTmpBrand(context.brand)
    setTmpLineup(context.lineup)
    setTmpModel(context.model)
    setIsOpen(false)
    setError(null)
  }

  /* 현재 선택된 차량의 라벨 문자열 */
  const chipLabel = context.model
    ? `${context.brand?.brand_nm ?? ''} ${context.model.model_nm}`
    : '차량을 선택해 주세요'

  return (
    <div className="px-5 pt-4">
      {/* ── 평상시 칩 (Chip) ── */}
      <button
        id="btn-vehicle-chip"
        onClick={() => setIsOpen(true)}
        className="group flex items-center gap-2 px-4 py-2.5 bg-secondary-container text-on-secondary-container rounded-full text-sm font-semibold shadow-card hover:shadow-md transition-all active:scale-95"
      >
        <Car className="w-4 h-4" strokeWidth={1.5} />
        <span>{chipLabel}</span>
        <ChevronDown className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" strokeWidth={1.5} />
      </button>

      {/* ── 확장 패널 (아코디언) ── */}
      {isOpen && (
        <div className="absolute inset-0 z-40 bg-surface/95 backdrop-blur-sm flex flex-col">
          {/* 패널 헤더 */}
          <div className="flex items-center justify-between px-6 py-5 border-b border-outline-variant/10">
            <h2 className="font-headline font-bold text-lg text-on-surface">차량 선택</h2>
            <button id="btn-close-vehicle-panel" onClick={handleClose} className="p-1 text-on-surface-variant hover:text-on-surface transition-colors">
              <X className="w-5 h-5" strokeWidth={1.5} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-hidden px-6 py-6 space-y-8">
            {/* 에러 메시지 */}
            {error && (
              <p className="text-sm text-error bg-error-container px-4 py-2 rounded-DEFAULT">{error}</p>
            )}

            {/* ── STEP 1: 브랜드 ── */}
            <section>
              <p className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-3">01 브랜드</p>
              {loading === 'brand' ? (
                <div className="flex gap-2">
                  {[1,2,3].map(i => (
                    <div key={i} className="h-10 w-20 bg-surface-container-low rounded-full animate-pulse" />
                  ))}
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {brands.map((b) => (
                    <button
                      key={b.brand_id}
                      id={`brand-${b.brand_id}`}
                      onClick={() => handleSelectBrand(b)}
                      className={`px-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-1.5 transition-all active:scale-95 ${
                        tmpBrand?.brand_id === b.brand_id
                          ? 'bg-primary text-on-primary shadow-lg shadow-primary/20'
                          : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                      }`}
                    >
                      {b.brand_nm}
                      {tmpBrand?.brand_id === b.brand_id && <Check className="w-3.5 h-3.5" strokeWidth={2.5} />}
                    </button>
                  ))}
                </div>
              )}
            </section>

            {/* ── STEP 2: 라인업 (브랜드 선택 후 표시) ── */}
            {tmpBrand && (
              <section>
                <p className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-3">02 라인업</p>
                {loading === 'lineup' ? (
                  <div className="flex gap-2">
                    {[1,2,3].map(i => (
                      <div key={i} className="h-10 w-20 bg-surface-container-low rounded-full animate-pulse" />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {lineups.map((l) => (
                      <button
                        key={l.lineup_id}
                        id={`lineup-${l.lineup_id}`}
                        onClick={() => handleSelectLineup(l)}
                        className={`px-5 py-2.5 rounded-full text-sm font-semibold flex items-center gap-1.5 transition-all active:scale-95 ${
                          tmpLineup?.lineup_id === l.lineup_id
                            ? 'bg-primary text-on-primary shadow-lg shadow-primary/20'
                            : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                        }`}
                      >
                        {l.lineup_nm}
                        {tmpLineup?.lineup_id === l.lineup_id && <Check className="w-3.5 h-3.5" strokeWidth={2.5} />}
                      </button>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* ── STEP 3: 모델 (라인업 선택 후 표시) ── */}
            {tmpLineup && (
              <section>
                <p className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-3">03 모델</p>
                {loading === 'model' ? (
                  <div className="grid grid-cols-2 gap-2">
                    {[1,2,3,4].map(i => (
                      <div key={i} className="h-16 bg-surface-container-low rounded-DEFAULT animate-pulse" />
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {models.map((m) => (
                      <button
                        key={m.model_id}
                        id={`model-${m.model_id}`}
                        onClick={() => setTmpModel(m)}
                        className={`p-4 rounded-DEFAULT text-left transition-all active:scale-95 ${
                          tmpModel?.model_id === m.model_id
                            ? 'bg-primary text-on-primary shadow-lg shadow-primary/20'
                            : 'bg-surface-container-low text-on-surface hover:bg-surface-container-high'
                        }`}
                      >
                        <span className="block text-sm font-bold">{m.model_nm}</span>
                        <span className="block text-[10px] uppercase tracking-tight opacity-60 mt-0.5">
                          {m.fuel_type} · {m.gen_no}세대
                        </span>
                        {tmpModel?.model_id === m.model_id && (
                          <Check className="w-3.5 h-3.5 mt-1" strokeWidth={2.5} />
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>

          {/* 확정 버튼 */}
          <div className="px-6 py-5 bg-surface border-t border-outline-variant/10">
            <button
              id="btn-confirm-vehicle"
              onClick={handleConfirm}
              disabled={!tmpModel}
              className="w-full py-4 signature-gradient text-on-primary font-bold rounded-full shadow-xl shadow-primary/25 disabled:opacity-40 disabled:cursor-not-allowed active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              차량 확정 및 AI 업데이트
              <ChevronRight className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
