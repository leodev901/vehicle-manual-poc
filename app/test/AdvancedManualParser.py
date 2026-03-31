import fitz
import pandas as pd

class AdvancedManualParser:
    def __init__(self, pdf_path):
        self.doc = fitz.open(pdf_path)
        self.parsed_data = []
        
        # [설정] 분석 단계(Step 1)에서 파악한 기준값들을 여기에 입력하세요!
        # (아래는 일반적인 차량 매뉴얼 기준 임시값입니다)
        self.HEADING_MIN_SIZE = 11.0   # 이 크기 이상이면 제목으로 간주
        
        # [설정] 헤더/푸터 제거를 위한 Y축 좌표 (페이지 위아래 잘라낼 영역)
        self.MARGIN_TOP = 50     # 상단 50px 무시 (챕터명 등)
        self.MARGIN_BOTTOM = 50  # 하단 50px 무시 (페이지 번호 등)

    def extract_tables_to_markdown(self, page):
        """표(Table) 영역을 감지하고 Markdown으로 변환 + 좌표 반환"""
        tables = page.find_tables()
        table_areas = []
        markdown_tables = []
        
        if tables:
            for table in tables:
                # 표 영역 좌표 저장 (텍스트 중복 추출 방지용)
                table_areas.append(table.bbox)
                
                # 표 내용을 Pandas -> Markdown 변환
                df = table.to_pandas()
                # 빈 데이터나 헤더만 있는 경우 제외
                if not df.empty and len(df) > 1:
                    # 빈 컬럼 이름 정리
                    df.columns = [c if c else f"Col_{i}" for i, c in enumerate(df.columns)]
                    md_text = df.to_markdown(index=False)
                    markdown_tables.append(md_text)
                    
        return markdown_tables, table_areas

    def parse_page(self, page_num):
        page = self.doc[page_num]
        width, height = page.rect.width, page.rect.height
        
        # 1. 표(Table) 처리
        md_tables, table_bboxes = self.extract_tables_to_markdown(page)
        
        # 2. 텍스트 블록 추출 (위치 정렬)
        blocks = page.get_text("dict", sort=True)["blocks"]
        
        current_chunk = {"page": page_num + 1, "heading": "Intro/General", "content": [], "tables": []}
        
        for block in blocks:
            # (A) 이미지 블록 패스
            if "image" in block: continue
            
            block_bbox = fitz.Rect(block["bbox"])
            
            # (B) 헤더/푸터 영역 필터링 (Y좌표 기반)
            # 블록의 중심 Y좌표가 상단 마진보다 작거나, 하단 마진 영역에 있으면 무시
            if block_bbox.y1 < self.MARGIN_TOP or block_bbox.y0 > (height - self.MARGIN_BOTTOM):
                continue

            # (C) 표 영역 중복 방지
            # 현재 텍스트 블록이 이미 추출한 표 영역 안에 포함되면 무시
            if any(block_bbox.intersects(tb) for tb in table_bboxes):
                continue
            
            # (D) 텍스트 라인 분석
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        size = span["size"]
                        # 굵기 정보 (flags & 2의 2진수가 1이면 Bold) -> 필요시 사용
                        is_bold = bool(span["flags"] & 2) 

                        if not text: continue
                        
                        # [Logic] 제목 vs 본문 판단
                        if size >= self.HEADING_MIN_SIZE:
                            # 1. 기존 Chunk 저장 (내용이 있을 때만)
                            if current_chunk["content"] or current_chunk["tables"]:
                                self.parsed_data.append(current_chunk)
                            
                            # 2. 새 Chunk 시작
                            current_chunk = {
                                "page": page_num + 1,
                                "heading": text, # 감지된 제목
                                "content": [],
                                "tables": [] 
                            }
                        else:
                            # 본문 누적
                            current_chunk["content"].append(text)
        
        # 페이지가 끝날 때, 추출해둔 표가 있다면 현재 Chunk에 연결
        # (더 정확하게 하려면 표의 Y좌표와 제목의 Y좌표를 비교해야 함)
        if md_tables:
            current_chunk["tables"].extend(md_tables)
            
        # 마지막 Chunk 저장
        if current_chunk["content"] or current_chunk["tables"]:
            self.parsed_data.append(current_chunk)

    def run(self):
        print(f"🚀 차량 매뉴얼 고도화 파싱 시작... (Margin Top:{self.MARGIN_TOP}, Bottom:{self.MARGIN_BOTTOM})")
        for page_num in range(len(self.doc)):
            # 진행상황 표시 (10페이지마다)
            if (page_num + 1) % 10 == 0:
                print(f" - {page_num + 1} 페이지 처리 중...")
            self.parse_page(page_num)
            
        print(f"✅ 파싱 완료! 총 {len(self.parsed_data)}개의 의미 단위(Chunk) 추출")
        return self.parsed_data
