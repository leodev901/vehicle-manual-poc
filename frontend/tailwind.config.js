/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      /* ──────────────────────────────────────────────────────────────────
       * Stitch Design System 에서 추출한 색상 토큰 (DESIGN.md 기반)
       * "Mint Breeze" 포인트 컬러 적용
       * ────────────────────────────────────────────────────────────────── */
      colors: {
        // 메인 포인트 컬러 (민트 계열)
        'primary':                 '#006b5b',
        'on-primary':              '#ffffff',
        'primary-container':       '#4fdbc0',
        'on-primary-container':    '#005d4f',
        'primary-fixed':           '#71f9dd',
        'primary-fixed-dim':       '#50dcc1',
        'on-primary-fixed':        '#00201a',
        'on-primary-fixed-variant':'#005144',
        'inverse-primary':         '#50dcc1',

        // 세컨더리 컬러
        'secondary':               '#38675c',
        'on-secondary':            '#ffffff',
        'secondary-container':     '#bbeddf',
        'on-secondary-container':  '#3e6d62',
        'secondary-fixed':         '#bbeddf',
        'secondary-fixed-dim':     '#a0d0c3',
        'on-secondary-fixed':      '#00201a',
        'on-secondary-fixed-variant':'#1f4f45',

        // 서피스 계층 (DESIGN.md "Surface Hierarchy" 원칙)
        'background':              '#f8f9fa',
        'on-background':           '#191c1d',
        'surface':                 '#f8f9fa',
        'surface-bright':          '#f8f9fa',
        'surface-dim':             '#d9dadb',
        'surface-variant':         '#e1e3e4',
        'surface-tint':            '#006b5b',
        'surface-container-lowest':'#ffffff',   // Level 2: 카드 팝업
        'surface-container-low':   '#f3f4f5',   // Level 1: 섹션 배경
        'surface-container':       '#edeeef',
        'surface-container-high':  '#e7e8e9',
        'surface-container-highest':'#e1e3e4',
        'on-surface':              '#191c1d',
        'on-surface-variant':      '#3c4a46',
        'inverse-surface':         '#2e3132',
        'inverse-on-surface':      '#f0f1f2',

        // 아웃라인 (DESIGNMD "No-Line Rule" → outline-variant 15% 적용)
        'outline':                 '#6c7a75',
        'outline-variant':         '#bbcac4',

        // 에러
        'error':                   '#ba1a1a',
        'on-error':                '#ffffff',
        'error-container':         '#ffdad6',
        'on-error-container':      '#93000a',

        // 터셔리
        'tertiary':                '#885204',
        'on-tertiary':             '#ffffff',
        'tertiary-container':      '#ffb766',
        'on-tertiary-container':   '#774700',
        'tertiary-fixed':          '#ffdcbb',
        'tertiary-fixed-dim':      '#ffb869',
        'on-tertiary-fixed':       '#2c1700',
        'on-tertiary-fixed-variant':'#673d00',
      },

      /* ──────────────────────────────────────────────────────────────────
       * borderRadius: xl(3rem) = 대형 컨테이너, DEFAULT(1rem) = 컴포넌트
       * ────────────────────────────────────────────────────────────────── */
      borderRadius: {
        DEFAULT: '1rem',
        lg:      '2rem',
        xl:      '3rem',
        full:    '9999px',
      },

      /* ──────────────────────────────────────────────────────────────────
       * 폰트: Manrope(헤드라인 에디토리얼) + Inter(본문 기능성)
       * ────────────────────────────────────────────────────────────────── */
      fontFamily: {
        headline: ['Manrope', 'sans-serif'],
        body:     ['Inter', 'sans-serif'],
        label:    ['Inter', 'sans-serif'],
      },

      /* ──────────────────────────────────────────────────────────────────
       * 애니메이션: 메시지 등장 효과
       * ────────────────────────────────────────────────────────────────── */
      keyframes: {
        'fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-dot': {
          '0%, 100%': { opacity: '0.3', transform: 'scale(0.8)' },
          '50%':      { opacity: '1',   transform: 'scale(1.2)' },
        },
      },
      animation: {
        'fade-up':   'fade-up 0.35s ease-out',
        'pulse-dot': 'pulse-dot 1.4s ease-in-out infinite',
      },

      /* ──────────────────────────────────────────────────────────────────
       * 박스 그림자: DESIGN.md "Ambient Occlusion" 원칙
       * ────────────────────────────────────────────────────────────────── */
      boxShadow: {
        'ambient':  '0 20px 40px rgba(25, 28, 29, 0.05)',
        'card':     '0 4px 20px rgba(25, 28, 29, 0.03)',
        'floating': '0 10px 30px rgba(0, 0, 0, 0.08)',
      },
    },
  },
  plugins: [],
}
