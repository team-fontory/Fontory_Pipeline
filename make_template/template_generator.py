#!/usr/bin/env python3
"""
한글 폰트 스타일용 템플릿 생성기
이 스크립트는 한글 글자 쓰기를 위한 인쇄용 템플릿 페이지를 생성합니다.
템플릿은 한글 글자의 손글씨 샘플 수집에 사용되도록 설계되었습니다.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
import importlib.util
import traceback
import logging

# --- 설정 값 --- 
FONT_PATH = "/app/resource/NanumGothic.ttf" # 폰트 경로 (컨테이너 내부)
PAGE_WIDTH = 2480  # 페이지 너비 (A4, 300dpi)
PAGE_HEIGHT = 3508 # 페이지 높이 (A4, 300dpi)
MARGIN = 150  # 여백
BLANK_SIZE = 280  # 글자 쓰는 영역 크기
TARGET_SIZE = 128  # 최종 크롭 후 목표 크기
CHAR_SECTION_HEIGHT = 80  # 상단 글자 표시 영역 높이
GRID_SIZE_WIDTH = 350  # 전체 그리드 셀 너비
GRID_SIZE_HEIGHT = CHAR_SECTION_HEIGHT + BLANK_SIZE + 20  # 그리드 셀 높이
CHARS_PER_ROW = 6  # 한 줄당 글자 수
ROWS_PER_PAGE = 8  # 페이지당 줄 수
FONT_SIZE = 60  # 폰트 크기
HEADER_SPACING = 50  # 헤더와 그리드 사이 추가 공간
OUTPUT_DIR = "/app/output_templates" # 출력 디렉토리 (컨테이너 내부)
DEBUG_MODE = False  # True로 설정하면 확인을 위해 빈 영역 경계 표시
TITLE_TEXT = "Fontory - 한글 글자 연습 용지"
TITLE_FONT_SIZE = FONT_SIZE * 1.5 # 제목 폰트 크기
KOREAN_CHARS_PATH = "/app/resource/korean_reference_chars.py" # 한글 목록 파일 경로 (컨테이너 내부)

# --- 로깅 설정 --- 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 유틸리티 함수 --- 
def create_directory_if_not_exists(directory):
    """디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory):
        logging.info(f"출력 디렉토리 생성 중: {directory}")
        os.makedirs(directory)

def get_text_dimensions(draw, text, font):
    """최신 PIL API를 사용하여 텍스트 너비와 높이를 가져옵니다."""
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return draw.textsize(text, font=font)

# --- 그리기 함수 --- 
def draw_grid_cell(draw, x, y, character=None, row=0, col=0):
    """상단에 글자를, 하단에 빈 쓰기 영역을 포함하는 그리드 셀을 그립니다."""
    # 전체 셀 테두리
    draw.rectangle([x, y, x + GRID_SIZE_WIDTH, y + GRID_SIZE_HEIGHT], outline="black", width=2)
    
    # 상단 글자 영역
    if character:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        char_width, char_height = get_text_dimensions(draw, character, font)
        char_x = x + (GRID_SIZE_WIDTH - char_width) // 2
        char_y = y + (CHAR_SECTION_HEIGHT - char_height) // 2
        draw.text((char_x, char_y), character, fill="black", font=font)
    
    # 구분선
    divider_y = y + CHAR_SECTION_HEIGHT
    draw.line(
        [x, divider_y, x + GRID_SIZE_WIDTH, divider_y],
        fill="black",
        width=2
    )
    
    # 빈 쓰기 영역
    blank_x = x + (GRID_SIZE_WIDTH - BLANK_SIZE) // 2
    blank_y = divider_y + 10
    
    if DEBUG_MODE:
        draw.rectangle(
            [blank_x, blank_y, blank_x + BLANK_SIZE, blank_y + BLANK_SIZE],
            outline=(200, 200, 200),
            width=2
        )
        draw.line(
            [blank_x, blank_y, blank_x + BLANK_SIZE, blank_y + BLANK_SIZE],
            fill=(220, 220, 220),
            width=1
        )
        draw.line(
            [blank_x + BLANK_SIZE, blank_y, blank_x, blank_y + BLANK_SIZE],
            fill=(220, 220, 220),
            width=1
        )

# --- 페이지 생성 함수 --- 
def generate_template_page(chars_on_page, page_num):
    logging.info(f"--- 페이지 {page_num} 생성 시작 ---")
    try:
        img = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), color='white')
        draw = ImageDraw.Draw(img)

        # 폰트 로드
        try:
            font = ImageFont.truetype(FONT_PATH, int(FONT_SIZE))
            title_font = ImageFont.truetype(FONT_PATH, int(TITLE_FONT_SIZE))
        except IOError as font_err:
            logging.critical(f"치명적 오류: 폰트 로딩 오류: {font_err}. 페이지 {page_num}을(를) 진행할 수 없습니다.")
            return
        except Exception as font_err:
            logging.critical(f"치명적 오류: 예기치 않은 폰트 오류: {font_err}. 페이지 {page_num}을(를) 진행할 수 없습니다.", exc_info=True)
            return

        # 제목 그리기
        title = TITLE_TEXT
        title_width, title_height = get_text_dimensions(draw, title, title_font)
        title_y = MARGIN // 2
        draw.text((MARGIN, title_y), title + " Template", fill="black", font=title_font)
        
        # 페이지 번호 그리기
        page_text = f"Page {page_num}"
        page_text_font = ImageFont.truetype(FONT_PATH, FONT_SIZE // 2)
        page_width, _ = get_text_dimensions(draw, page_text, page_text_font)
        draw.text((PAGE_WIDTH - MARGIN - page_width, title_y + title_height//2), page_text, fill="black", font=page_text_font)

        GRID_START_Y = title_y + title_height + HEADER_SPACING

        # 그리드 및 셀 그리기
        char_index_on_page = 0
        for row in range(ROWS_PER_PAGE):
            for col in range(CHARS_PER_ROW):
                if char_index_on_page >= len(chars_on_page):
                    break 
                char = chars_on_page[char_index_on_page]
                cell_x = MARGIN + col * GRID_SIZE_WIDTH
                cell_y = GRID_START_Y + row * GRID_SIZE_HEIGHT
                
                try:
                    draw_grid_cell(draw, cell_x, cell_y, char, row=row, col=col)
                except Exception as cell_draw_err:
                    logging.critical(f"!!! 치명적 오류: 글자 '{char}' ({row},{col})의 draw_grid_cell 중 오류: {cell_draw_err}", exc_info=True)
                    logging.critical(f"!!! 셀 오류로 인해 페이지 {page_num}의 generate_template_page 종료.")
                    return
                    
                char_index_on_page += 1
            if char_index_on_page >= len(chars_on_page):
                 break
                 
        # 이미지 저장
        output_filename = os.path.join(OUTPUT_DIR, f"template_page_{page_num}.jpg")
        absolute_save_path = os.path.abspath(output_filename)
        logging.info(f"이미지를 절대 경로에 저장 시도: {absolute_save_path}")
        
        if not os.path.exists(OUTPUT_DIR):
             logging.error(f"오류: 출력 디렉토리 {OUTPUT_DIR}가 저장 전에 사라졌습니다!")
             return
             
        try:
            img.save(absolute_save_path, "JPEG", quality=95)
            logging.info(f"img.save() 명령 실행 완료: {absolute_save_path}.")
            if os.path.exists(absolute_save_path):
                logging.info(f"확인됨: 저장 후 파일이 {absolute_save_path}에 존재합니다.")
            else:
                logging.error(f"오류: 저장 시도 직후 파일이 {absolute_save_path}에 존재하지 않습니다!")
        except Exception as save_err:
            logging.critical(f"치명적 오류: img.save({absolute_save_path}) 중 오류: {save_err}", exc_info=True)
            
    except Exception as page_err:
        logging.critical(f"치명적 예기치 않은 오류: 페이지 {page_num}의 generate_template_page 중 오류: {page_err}", exc_info=True)
        
    logging.info(f"--- 페이지 {page_num} 생성 완료 ---")

# --- 데이터 로딩 함수 --- 
def load_korean_chars():
    """지정된 파이썬 파일에서 korean_chars 목록을 로드합니다."""
    logging.info(f"한글 문자 로드 시도: {KOREAN_CHARS_PATH}")
    if not os.path.exists(KOREAN_CHARS_PATH):
        logging.error(f"오류: 한글 참조 문자 파일을 {KOREAN_CHARS_PATH}에서 찾을 수 없습니다.")
        fallback_chars = ['가', '나', '다', '라']
        logging.warning(f"최소 대체 문자 목록 사용: {fallback_chars}")
        return fallback_chars

    try:
        module_name = "korean_reference_chars_loaded"
        spec = importlib.util.spec_from_file_location(module_name, KOREAN_CHARS_PATH)
        if spec is None:
             raise ImportError(f"{KOREAN_CHARS_PATH}에 대한 spec을 생성할 수 없습니다.")
        korean_module = importlib.util.module_from_spec(spec)
        if korean_module is None:
            raise ImportError(f"{KOREAN_CHARS_PATH}의 spec에서 모듈을 생성할 수 없습니다.")
        sys.modules[module_name] = korean_module
        spec.loader.exec_module(korean_module)
        logging.info("파일에서 한글 문자를 성공적으로 로드했습니다.")
        if hasattr(korean_module, 'korean_chars') and isinstance(korean_module.korean_chars, list):
             return korean_module.korean_chars
        else:
            logging.error(f"오류: {KOREAN_CHARS_PATH}에서 'korean_chars' 목록을 찾을 수 없거나 목록이 아닙니다.")
            fallback_chars = ['가', '나', '다', '라']
            logging.warning(f"최소 대체 문자 목록 사용: {fallback_chars}")
            return fallback_chars
    except Exception as e:
        logging.error(f"{KOREAN_CHARS_PATH}에서 한글 문자 로딩 오류: {e}", exc_info=True)
        fallback_chars = ['가', '나', '다', '라']
        logging.warning(f"최소 대체 문자 목록 사용: {fallback_chars}")
        return fallback_chars

# --- 메인 실행 로직 --- 
def generate_template_pages():
    """필요한 모든 템플릿 페이지를 생성합니다."""
    korean_chars = load_korean_chars()
    if not korean_chars:
        logging.error("오류: 로드된 문자가 없습니다. 템플릿을 생성할 수 없습니다.")
        return
        
    total_chars = len(korean_chars)
    logging.info(f"처리할 총 문자 수: {total_chars}")
    
    chars_per_full_page = CHARS_PER_ROW * ROWS_PER_PAGE
    num_pages = (total_chars + chars_per_full_page - 1) // chars_per_full_page
    logging.info(f"필요한 페이지 수 계산됨: {num_pages}")

    create_directory_if_not_exists(OUTPUT_DIR)

    for i in range(num_pages):
        page_num = i + 1
        start_index = i * chars_per_full_page
        end_index = start_index + chars_per_full_page
        chars_for_page = korean_chars[start_index:end_index]
        
        try:
            generate_template_page(chars_for_page, page_num)
        except Exception as e:
            logging.error(f"페이지 {page_num} 생성 중 오류 발생: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        generate_template_pages()
        logging.info("템플릿 생성 스크립트 완료.")
    except Exception as e:
        logging.critical(f"최상위 레벨에서 처리되지 않은 오류 발생: {e}", exc_info=True)
        sys.exit(1)
