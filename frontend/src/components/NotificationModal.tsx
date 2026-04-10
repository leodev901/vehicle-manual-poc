import React from 'react';
import { AlertCircle } from 'lucide-react';

interface NotificationModalProps {
  /** 모달 표시 여부 */
  isOpen: boolean;
  /** 표시할 메시지 */
  message: string;
  /** 닫기 콜백 */
  onClose: () => void;
}

/**
 * Auto-Guide AI 전용 고품격 알림 모달
 * - Glassmorphism 배경 및 부드러운 스케일 업 애니메이션 적용
 * - Signature Mint 그라데이션 버튼 사용
 */
const NotificationModal: React.FC<NotificationModalProps> = ({ isOpen, message, onClose }) => {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/20 backdrop-blur-[4px] animate-in fade-in duration-300"
      onClick={onClose}
    >
      {/* 모달 카드: 클릭 이벤트 전파 방지 */}
      <div 
        className="w-full max-w-[340px] bg-white/90 backdrop-blur-xl rounded-[32px] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 border border-white/40"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-8 flex flex-col items-center text-center">
          {/* 아이콘 영역: 부드러운 배경과 함께 배치 */}
          <div className="w-16 h-16 rounded-full bg-[#006b5b]/10 flex items-center justify-center mb-5">
            <AlertCircle className="w-8 h-8 text-[#006b5b]" />
          </div>

          <h3 className="text-[20px] font-extrabold text-[#1a1c1e] mb-3 tracking-tight">
            안내 메시지
          </h3>
          
          <p className="text-[15px] font-medium text-[#44474e] leading-relaxed mb-8 break-keep">
            {message}
          </p>

          <button
            onClick={onClose}
            className="w-full py-4 rounded-2xl signature-gradient text-white font-bold text-[16px] shadow-lg shadow-[#006b5b]/20 hover:shadow-xl active:scale-[0.97] transition-all duration-200 hover:brightness-105"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationModal;
