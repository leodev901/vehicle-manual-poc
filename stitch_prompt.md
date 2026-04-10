# Stitch Design Prompt: Vehicle Manual RAG Chatbot

## ⚙️ Tech Stack & Architecture Rules
- **Framework**: Next.js App Router (`layout.tsx`, `page.tsx`) 기반 + React (TypeScript). 
- **Styling**: Tailwind CSS (최신 유행하는 모던한 컴포넌트 설계 방식 적용).
- **SEO & Meta**: SEO 최적화가 필수적. 검색 엔진 봇(Googlebot 등)이 페이지 구조를 잘 파악할 수 있도록 직관적인 레이아웃 구조와 시맨틱 태그(Semantic HTML)를 활용할 것.
- **Icons**: `lucide-react` 사용.
- **Component Pattern**: 인터랙션(채팅, 상태 관리)이 일어나는 핵심 영역은 Client Component(`'use client'`)로 분리 가능하도록 구조화해서 짜주세요.


## 🎯 Device Target & Layout
- **Mobile-First / App-Like UI**: 데스크톱의 꽉 찬 화면보다는 모바일 폰과 태블릿 환경에 최적화된 앱 스타일의 UI.
- PC 화면에서 볼 때도 모바일 화면 비율(max-width: 550px ~ 750px)의 컨테이너가 중앙에 배치되어, 네이티브 앱을 쓰는 듯한 몰입감을 주어야 합니다.

## 🎨 Aesthetic & Brand Identity
- **Modern & Premium Automotive**: 최신 전기차/스마트카의 인포테인먼트 시스템을 연상시키는 미래지향적이고 고급스러운 디자인.
- **Color Palette**: 깊이 있는 다크 모드(Deep Charcoal/Midnight Black 배경)를 기본으로 하고, AI가 동작하는 느낌을 주는 은은한 네온 블루(Neon Blue)나 에메랄드 그린(Emerald Green)을 포인트 컬러(Accent)로 사용.
- **UI Elements**: 부드러운 곡선(Rounded Corners), Glassmorphism(반투명 유리 효과) 패널, 플로팅 섀도우를 사용하여 세련된 느낌 강조.

## 📱 필수 화면 구성 요소 및 유저 스토리 적용

### 1. App Header (상단 고정)
- 중앙: "Auto-Guide AI" 또는 "차량 매뉴얼 AI" 타이틀.
- 좌측: 심플한 자동차 로고.
- 우측 설정 영역: 
  - ⚙️ **LLM 모델 선택기 (중요 기능)**: OpenAI (GPT)와 Google GenAI (Gemini) 중 원하는 AI 뇌를 선택할 수 있는 작고 세련된 토글 라디오 버튼 또는 셀렉트 박스 필수.
  - 내 정보 메뉴 아이콘.

### 2. Vehicle Context Selector (차량 선택 위젯 - 핵심 기능)
- **목적**: 유저가 자신의 차량 컨텍스트를 설정하는 공간.
- **디자인 방식**: 항상 펼쳐져 공간을 차지하지 않도록, 평소에는 **"현재 선택된 차량: 현대 투싼 하이브리드"** 형태로 작고 예쁜 칩(Chip)이나 카드 형태로 상단(헤더 바로 아래)에 플로팅.
- **인터랙션**: 칩을 탭(클릭)하면 부드럽게 아래로 확장(Accordion)되거나 Bottom Sheet가 올라오며 3개의 선택 옵션 제공:
  1. **브랜드 (Brand)**: (예: 현대, 기아, 제네시스)
  2. **라인업 (Lineup)**: (예: SUV, 세단)
  3. **모델 (Model)**: (예: 투싼 하이브리드 2024)
- 직관적인 드롭다운이나 둥근 버튼(Pill button) 형태의 선택기 적용.

### 3. Main Chat Interface (중앙 스크롤 영역)
- **초기 화면 (Empty State)**: AI의 인사말과 함께 퀵-액션(Quick Action) 추천 질문 칩 제공 (예: "스마트키가 방전됬어요", "에어컨 필터 교체 방법", "계기판 경고등 의미", "블루투스 페어링").
- **User Message Bubble (우측 정렬)**: 유저가 보낸 질문. 포인트 컬러(예: 차분한 파란색) 배경.
- **AI Message Bubble (좌측 정렬)**: AI 답변. 짙은 회색 계열의 우아한 카드 배경.
- **Streaming State UX**: AI가 답을 찾는 중(RAG 검색 중)임을 나타내는 고급스러운 로딩 애니메이션 (펄스 효과 또는 빛이 흐르는 효과) 및 상태 텍스트("매뉴얼 검색 중...").
- **Reference Tag (출처 뱃지)**: AI 답변 하단에 "출처: 매뉴얼 124페이지" 같은 작고 세련된 태그가 붙을 수 있는 디자인 반영.

### 4. Input Area (하단 고정)
- 아이메시지(iMessage)나 카카오톡처럼 친숙하고 깔끔한 하단 입력창.
- **Placeholder**: "차량에 대해 무엇이든 물어보세요..."
- **요소**: 둥근 텍스트 입력 필드, 첨부/메뉴 아이콘(우측 또는 좌측), 눈에 띄는 전송(Send) 버튼(위쪽 화살표 모양).

## 💫 디테일 & 애니메이션 요구사항
- 모바일 환경에서의 터치 친화적인 큼직한 터치 영역(Touch Target).
- 메시지가 추가될 때 위로 부드럽게 밀려 올라가는(Slide-up & Fade-in) 효과.
- 다크 모드 특성상 텍스트 가독성을 위한 명확한 화이트/밝은 그레이 폰트 컨트라스트 유지.

## 🔌 프론트엔드 연동(API) 스키마 및 상태(State) 관리 요구사항
UI를 구성하는 컴포넌트를 설계할 때, 실제 백엔드 API와의 연동을 염두에 둔 뼈대(Mock logic)를 반영해 주세요.

### 1. 계층형 차량 선택 로직 (Cascade API)
- **동작 방식**: 3단 Select(또는 Bottom Sheet 리스트) 구조이며, 상위 항목을 선택해야 하위 API를 호출하는 연쇄(Cascade) 구조입니다.
  - 1단계: `/api/v1/manual/brands` 호출 결과로 렌더링
  - 2단계: `/api/v1/manual/lineups?brand_id={선택한 브랜드}` 
  - 3단계: `/api/v1/manual/models?lineup_id={선택한 라인업}`
- 선택 결과는 최종적으로 `model_id` 상태(State)로 저장되어 채팅 API 호출 시 함께 전송됩니다.

### 2. 챗봇 API 및 세션(Context) 관리
- **엔드포인트**: `POST /api/v1/chat/stream`
- **Request Payload (스키마)**: 
  ```json
  {
    "session_id": "브라우저에서 임의 생성된 UUID",
    "model_id": "선택된 차량의 ID (예: LX3HEV)",
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4o-mini"
    },
    "message": "스마트키 배터리가 방전되면 어떻게 하나요?"
  }
  ```
- **세션(Session) 관리**: 대화의 흐름(문맥)을 기억하기 위해 `session_id`를 유지합니다. 헤더나 채팅창 상단에 **"새 대화 시작(초기화/휴지통)" 아이콘**을 배치해 주세요. 이 버튼을 탭하면 `session_id`가 새로 생성(refresh)되며 대화창이 빈 화면(초기 상태)으로 돌아가는 UI 컴포넌트를 포함합니다.
- **스트리밍 반응**: 일반적인 JSON 응답 대신 SSE(Server-Sent Events)를 통해 토큰 단위로 스트리밍 되는 것을 파싱하는 구조를 가정한 리액트(혹은 바닐라) 상태 처리 코드가 뼈대로 들어가면 좋습니다.
