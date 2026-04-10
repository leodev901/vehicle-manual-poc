import fitz  # PyMuPDF
from collections import Counter

"""
[데이터 기반 매뉴얼 분석 가이드]
1. 결과 해석 방법:
   - 빈도수(Count)가 가장 높은 스타일: 매뉴얼의 '본문'입니다. (보통 8~9pt, Light/Regular)
   - 본문보다 크면서(Size ↑) 굵은(Bold) 스타일: '소제목' 또는 '섹션 제목'입니다.
   - 빈도수가 매우 적으면서(1~10회) 큰 폰트: '표지'나 '대단원 제목'입니다.

2. 헤더 사이즈(HEADING_MIN_SIZE) 결정 기준:
   - RAG의 검색 단위(Chunk)를 나누고 싶다면 '소제목' 사이즈를 기준으로 삼아야 합니다.
   - 본문 사이즈(예: 8.8)와 소제목 사이즈(예: 9.8) 사이의 중간값(예: 9.5)을 임계값으로 설정하세요.
   - 본문 내의 강조 텍스트와 섞이지 않으려면 'Bold' 조건을 함께 사용하는 것이 가장 정확합니다.
"""

def analyze_pdf_style(pdf_path):
    doc = fitz.open(pdf_path)
    styles = Counter()
    
    print(f"📄 파일 분석 시작: {pdf_path}")
    print(f"📄 총 페이지 수: {len(doc)}페이지")
    
    # 앞쪽 5페이지만 샘플로 분석 (표지, 목차, 본문 초입 등 확인)
    # 0페이지부터 5페이지까지 확인
    for page_num, page in enumerate(doc[:80]): 
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # 폰트 크기를 소수점 첫째 자리까지 반올림
                        size = round(span["size"], 1)
                        font = span["font"]
                        text = span["text"].strip()
                        
                        if text and len(text) > 1: # 의미 있는 텍스트만
                            styles[(size, font)] += 1
                            # 샘플 텍스트 출력 (스타일 판단용)
                            if styles[(size, font)] < 5: # 각 스타일별로 2개씩만 예시 출력
                                print(f"[Page {page_num+1}] Size: {size:>5} | Font: {font:<20} | Text: {text[:250]}...")

    print("\n" + "="*50)
    print("📊 [폰트 스타일 빈도 분석 결과 - 상위 10개]")
    print("="*50)
    for (size, font), count in styles.most_common(10):
        print(f"Size: {size:<5} | Count: {count:<4} | Font: {font}")

# 실행
# analyze_pdf_style("app/docs/LX3HEV_2026_ko_KR.pdf")
# analyze_pdf_style("app/docs/ME_2025_ko_KR.pdf")
analyze_pdf_style("./docs/NQ5HEV_2025_KR.pdf")