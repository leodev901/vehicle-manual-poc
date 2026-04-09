import fitz  # PyMuPDF
from collections import Counter

def analyze_pdf_style(pdf_path):
    doc = fitz.open(pdf_path)
    styles = Counter()
    
    print(f"📄 파일 분석 시작: {pdf_path}")
    print(f"📄 총 페이지 수: {len(doc)}페이지")
    
    # 앞쪽 5페이지만 샘플로 분석 (표지, 목차, 본문 초입 등 확인)
    # 0페이지부터 5페이지까지 확인
    for page_num, page in enumerate(doc[:30]): 
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
                            if styles[(size, font)] < 3: # 각 스타일별로 2개씩만 예시 출력
                                print(f"[Page {page_num+1}] Size: {size:>5} | Font: {font:<20} | Text: {text[:30]}...")

    print("\n" + "="*50)
    print("📊 [폰트 스타일 빈도 분석 결과 - 상위 10개]")
    print("="*50)
    for (size, font), count in styles.most_common(10):
        print(f"Size: {size:<5} | Count: {count:<4} | Font: {font}")

# 실행
# analyze_pdf_style("app/docs/LX3HEV_2026_ko_KR.pdf")
analyze_pdf_style("app/docs/ME_2025_ko_KR.pdf")