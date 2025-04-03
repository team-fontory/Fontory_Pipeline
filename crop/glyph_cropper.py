#!/usr/bin/env python3
"""
Fontory용 글리프 크로퍼 (단일 템플릿 버전)
입력 이미지 해상도(2480x3508)를 확인하고, 템플릿 설정에 따라 정확한 빈 영역을 잘라내며,
목표 크기(128x128)로 리사이즈합니다.
글리프를 입력 파일 이름의 하위 디렉토리에 저장합니다.
(정밀 크롭은 비활성화됨)
"""

import os
import sys
import glob
import re
import traceback
import logging
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
import importlib.util

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 기본/대체 설정 --- 
EXPECTED_TEMPLATE_WIDTH = 2480 # 예상 템플릿 너비
EXPECTED_TEMPLATE_HEIGHT = 3508 # 예상 템플릿 높이
MARGIN=150; BLANK_SIZE=280; CHAR_SECTION_HEIGHT=80; GRID_SIZE_WIDTH=350 # 여백, 쓰기 영역 크기, 글자 영역 높이, 그리드 셀 너비
GRID_SIZE_HEIGHT=CHAR_SECTION_HEIGHT+BLANK_SIZE+20; CHARS_PER_ROW=6; ROWS_PER_PAGE=8 # 그리드 셀 높이, 행당 글자 수, 페이지당 행 수
HEADER_SPACING=50; FONT_PATH="/app/NanumGothic.ttf"; FONT_SIZE=60 # 헤더 간격, 폰트 경로, 폰트 크기
TITLE_FONT_SIZE=FONT_SIZE*1.5; TITLE_Y=MARGIN//2; TITLE_HEIGHT=TITLE_FONT_SIZE # 제목 폰트 크기, 제목 Y 위치, 제목 높이
GRID_START_Y=TITLE_Y+TITLE_HEIGHT+HEADER_SPACING; korean_chars=None # 그리드 시작 Y 위치, 한글 목록 (초기화)
TEMPLATE_BLANK_PADDING = 10 # 템플릿 구분선 아래 패딩
DIVIDER_LINE_THICKNESS = 2 # 템플릿 구분선 두께
REFERENCE_DIVIDER_Y_ROW0 = 291 # <<< 마지막 생성기 실행 로그에서 업데이트된 값 (첫 행 구분선 Y 기준)

# --- 경로 (컨테이너 내부) --- 
# Dockerfile이 파일을 배치하는 위치를 반영하는 경로
TEMPLATE_GENERATOR_PATH = "/app/make_template/template_generator.py"
KOREAN_CHARS_PATH = "/app/korean_reference_chars.py"
# 컨테이너 내부 폰트 경로는 /app/
FONT_PATH = "/app/NanumGothic.ttf"
DEBUG_MODE = True # 크롭 영역 디버그 이미지 생성 여부 (기본값 True로 변경)
TARGET_SIZE = 128 # 최종 글리프 크기

# --- 폰트 로딩 함수 --- 
def get_text_dimensions_internal(text, font_path, font_size):
    # 폰트 경로는 이제 컨테이너 내부 절대 경로
    try:
        font = ImageFont.truetype(font_path, int(font_size))
        bbox = font.getbbox(text); width = bbox[2] - bbox[0]; height = bbox[3] - bbox[1]
        ascent, descent = font.getmetrics(); total_height = ascent + descent
        return width, max(height, total_height)
    except Exception as e: 
        logging.warning(f"폰트 로딩 경고 {font_path}: {e}")
        return 50, 20

# --- 전역 변수 덮어쓰기 전에 함수 정의 --- 
def create_directory_if_not_exists(directory):
    """디렉토리가 없으면 오류 보고와 함께 생성합니다."""
    if not os.path.exists(directory):
        logging.info(f"디렉토리 생성 시도: {directory}")
        try:
            os.makedirs(directory)
            logging.info(f"디렉토리 생성 성공: {directory}")
        except OSError as e:
            logging.error(f"오류: 디렉토리 생성 실패 {directory}: {e}")
        except Exception as e:
            logging.error(f"오류: 디렉토리 생성 중 예기치 않은 오류 발생 {directory}: {e}")
    # else:
    #     logging.debug(f"디렉토리가 이미 존재함: {directory}") # 선택 사항: 더 자세한 로깅을 위해 DEBUG 레벨로 변경

def calculate_crop_coordinates(row, col):
    """템플플릿 생성기의 로직과 유사하게 잘라낼 좌표를 계산합니다."""
    # MARGIN 및 GRID_SIZE_WIDTH를 기반으로 X 계산 (신뢰성 높음)
    cell_x_start = MARGIN + col * GRID_SIZE_WIDTH
    blank_x_offset = (GRID_SIZE_WIDTH - BLANK_SIZE) // 2
    left = cell_x_start + blank_x_offset
    right = left + BLANK_SIZE

    # --- Y 계산 수정: 셀 상단 Y를 먼저 계산 ---
    # 전역 변수로 로드된 GRID_START_Y 및 GRID_SIZE_HEIGHT 사용
    cell_y_start = GRID_START_Y + row * GRID_SIZE_HEIGHT
    # 구분선 Y는 셀 상단 + 문자 영역 높이
    divider_y = cell_y_start + CHAR_SECTION_HEIGHT
    
    # 크롭 상단은 구분선 아래 (1픽셀 위로 이동)
    top = divider_y + DIVIDER_LINE_THICKNESS + TEMPLATE_BLANK_PADDING - 1
    bottom = top + BLANK_SIZE

    # 첫 번째 셀 계산 디버그
    if row == 0 and col == 0: 
        logging.debug("--- 첫 셀 계산 디버그 (동적 계산 사용) ---")
        logging.debug(f"사용된 값: MARGIN={MARGIN}, GRID_SIZE_WIDTH={GRID_SIZE_WIDTH}, BLANK_SIZE={BLANK_SIZE}")
        logging.debug(f"사용된 값: GRID_START_Y={GRID_START_Y}, GRID_SIZE_HEIGHT={GRID_SIZE_HEIGHT}, CHAR_SECTION_HEIGHT={CHAR_SECTION_HEIGHT}")
        logging.debug(f"사용된 값: TEMPLATE_BLANK_PADDING={TEMPLATE_BLANK_PADDING}")
        logging.debug(f"행: {row}, 열: {col}")
        logging.debug(f"계산된 셀 상단 Y (cell_y_start): {cell_y_start}")
        logging.debug(f"계산된 구분선 Y (divider_y = cell_y_start + CHAR_SECTION_HEIGHT): {divider_y}")
        logging.debug(f"계산된 크롭 상단 (top = divider_y + padding - 1): {top}")
        logging.debug(f"크롭 상자: L={left}, T={top}, R={right}, B={bottom}")
        logging.debug("-----------------------------------------------------------------")

    return (left, top, right, bottom)

def get_character_for_position(row, col):
    """행과 열 위치에 해당하는 문자를 반환합니다."""
    global korean_chars # 전역 변수 사용 명시
    if korean_chars is None:
        logging.error("오류: 한글 문자 목록(korean_chars)이 로드되지 않았습니다.")
        return f"nolist_{row}_{col}"
        
    index = row * CHARS_PER_ROW + col
    if 0 <= index < len(korean_chars): return korean_chars[index]
    else:
        # 잘못된 행/열 조합에 대해 경고를 한 번만 출력하여 로그 스팸 줄이기
        # 이 기본 확인은 완벽하지 않지만 도움이 됨
        if not hasattr(get_character_for_position, 'warned_indices'):
            get_character_for_position.warned_indices = set()
        if (row, col) not in get_character_for_position.warned_indices:
             logging.warning(f"경고: 인덱스 {index}가 범위를 벗어남 (크기 {len(korean_chars)}). 행={row}, 열={col}")
             get_character_for_position.warned_indices.add((row, col))
        return f"unknown_{index+1}" # 알 수 없는 문자 반환

def create_debug_image(img, debug_save_path):
    """지정된 경로에 오버레이가 있는 디버그 이미지를 저장합니다."""
    if not DEBUG_MODE: return # 디버그 모드가 아니면 반환
    # 디렉토리 생성은 이 함수 호출 전에 이루어져야 함
    # create_directory_if_not_exists(os.path.dirname(debug_save_path))
    debug_img = img.copy(); draw = ImageDraw.Draw(debug_img)
    try: font = ImageFont.load_default() # 기본 폰트 로드
    except IOError: font = None
    for row in range(ROWS_PER_PAGE):
        for col in range(CHARS_PER_ROW):
            char = get_character_for_position(row, col)
            left, top, right, bottom = calculate_crop_coordinates(row, col)
            divider_y_vis = REFERENCE_DIVIDER_Y_ROW0 + row * GRID_SIZE_HEIGHT # 시각화용 구분선 Y
            cell_x = MARGIN + col * GRID_SIZE_WIDTH # 선 그리기에 cell_x 필요
            draw.line([cell_x, divider_y_vis, cell_x + GRID_SIZE_WIDTH, divider_y_vis], fill=(0, 255, 255), width=2) # 구분선 시각화
            draw.rectangle([left, top, right, bottom], outline=(255, 0, 0), width=5) # 크롭 영역 표시
            label_text = f"{char}\n({row},{col})\nT:{top} L:{left}" # 레이블 텍스트
            if font: draw.text((left + 5, top + 5), label_text, fill=(255, 0, 0), font=font)
            else: draw.text((left + 5, top + 5), label_text, fill=(255, 0, 0))
            
    try: 
        debug_img.save(debug_save_path)
        logging.info(f"디버그 이미지 저장됨: {debug_save_path}")
    except Exception as save_err: 
        logging.error(f"디버그 이미지 저장 오류 {debug_save_path}: {save_err}")

# --- 정밀 크롭 함수 (정의는 유지하되 아래 호출 비활성화) ---
def find_ink_bbox(img, threshold, padding):
    """잉크 영역의 경계 상자를 찾습니다."""
    gray_img = img.convert('L'); binary_img = gray_img.point(lambda p: 255 if p < threshold else 0) # 그레이스케일 변환 및 이진화
    bbox = binary_img.getbbox() # 경계 상자 얻기
    if bbox:
        x1, y1, x2, y2 = bbox
        x1 = max(0, x1 - padding); y1 = max(0, y1 - padding)
        x2 = min(img.width, x2 + padding); y2 = min(img.height, y2 + padding) # 패딩 적용
        if x2 > x1 and y2 > y1: return (x1, y1, x2, y2) # 유효한 경계 상자 반환
        else: 
            logging.warning(" 경고: 정밀 크롭 경계 상자 유효하지 않음.")
            return None
    return None

def crop_glyph(image, bbox, padding=5):
    """주어진 이미지에서 글리프를 자르고 패딩을 추가합니다."""
    try:
        # bbox에서 좌표 추출
        left, top, right, bottom = bbox
        
        # 패딩 적용 (하단 패딩은 더 작게 설정)
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(image.width, right + padding)
        bottom = min(image.height, bottom + 2)  # 하단 패딩을 2로 줄임
        
        # 자르기
        cropped = image.crop((left, top, right, bottom))
        
        # 새로운 이미지 생성 (흰색 배경)
        new_image = Image.new('RGB', (cropped.width, cropped.height), 'white')
        new_image.paste(cropped, (0, 0))
        
        return new_image
    except Exception as e:
        logging.error(f"글리프 자르기 실패: {e}")
        return None

def crop_glyphs_from_image(image_path, base_output_dir, verbose=True):
    """단일 템플릿 이미지를 처리하여 글리프와 디버그 이미지를 구조화된 하위 디렉토리에 저장합니다."""
    try:
        img = Image.open(image_path)
        actual_width, actual_height = img.size # 실제 이미지 크기
        filename_base = os.path.splitext(os.path.basename(image_path))[0] # 파일 이름 (확장자 제외)
        
        if verbose: logging.info(f"\n처리 중: {filename_base} (실제 크기: {actual_width}x{actual_height})")
        
        # 이미지 크기 확인
        if actual_width != EXPECTED_TEMPLATE_WIDTH or actual_height != EXPECTED_TEMPLATE_HEIGHT:
            logging.error(f"  오류: 이미지 크기 ({actual_width}x{actual_height})가 예상({EXPECTED_TEMPLATE_WIDTH}x{EXPECTED_TEMPLATE_HEIGHT})과 다릅니다. 건너뜁니다.")
            return 0, 1 # 처리 실패 (건너뜀 수 증가)
            
        # --- 출력 디렉토리 정의 ---
        glyph_output_dir = base_output_dir # 기본 출력 디렉토리에 직접 저장
        debug_output_dir = "/app/debug_output" # 컨테이너 내 디버그 출력 경로 지정
        
        # --- 출력 디렉토리 생성 --- 
        create_directory_if_not_exists(glyph_output_dir)  # 주 출력 디렉토리 존재 확인
        if DEBUG_MODE:
            create_directory_if_not_exists(debug_output_dir) # 필요시 디버그 디렉토리 생성 (경로 수정)
            
        if verbose: 
            logging.info(f"  글리프를 저장할 경로: {glyph_output_dir}") # 업데이트된 메시지
            if DEBUG_MODE:
                 logging.info(f"  디버그 이미지를 저장할 경로: {debug_output_dir}")

        # --- 디버그 이미지 생성 및 저장 (활성화된 경우) --- 
        if DEBUG_MODE:
             debug_save_path = os.path.join(debug_output_dir, f"debug_{os.path.basename(image_path)}") # 경로 수정
             create_debug_image(img, debug_save_path)
        
        num_glyphs = 0 # 처리된 글리프 수 초기화
        # 페이지 내 각 셀 순회
        for row in range(ROWS_PER_PAGE):
            for col in range(CHARS_PER_ROW):
                char = get_character_for_position(row, col) # 현재 위치의 문자 가져오기
                if char.startswith("unknown_") or char.startswith("nolist_"): # 알 수 없는 문자인 경우 (리스트 미로드 포함)
                    # 경고 출력은 get_character_for_position에서 처리
                    if col == 0: # 행당 한 번만 중단 메시지 출력
                         logging.info(f"알려진 문자 목록 끝에 도달 또는 문자 목록 로드 실패 (행 {row}). 이 이미지의 크롭 중단.")
                    break # 내부 루프(열) 중단
                    
                glyph_index = row * CHARS_PER_ROW + col + 1 # 글리프 인덱스 (1부터 시작)
                left, top, right, bottom = calculate_crop_coordinates(row, col) # 크롭 좌표 계산
                
                # 좌표 유효성 검사
                if 0 <= left < right <= actual_width and 0 <= top < bottom <= actual_height:
                    direct_crop = img.crop((left, top, right, bottom)) # 직접 크롭
                    final_glyph = direct_crop # 최종 글리프 (정밀 크롭 비활성화)
                    final_glyph = final_glyph.convert('L') # 그레이스케일 변환
                    final_glyph = final_glyph.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS) # 목표 크기로 리사이즈
                    
                    # 유니코드 값 가져와서 U+XXXX 형식으로 변환
                    unicode_val = ord(char)
                    unicode_hex = f"U+{unicode_val:04X}" 
                    # 새 파일 이름 구성
                    char_filename = f"{char}.jpg"
                    # 'characters' 하위 디렉토리에 저장 (이제 기본 출력 디렉토리)
                    char_path = os.path.join(glyph_output_dir, char_filename) # 업데이트된 glyph_output_dir 사용
                    try: 
                        final_glyph.save(char_path, "JPEG", quality=95) # JPEG으로 저장
                        if verbose: logging.info(f"    저장됨: {char_filename} (문자 '{char}' | 행={row}, 열={col}) -> ./{os.path.relpath(glyph_output_dir)}")
                        num_glyphs += 1 # 처리된 글리프 수 증가
                    except Exception as save_err: 
                        logging.error(f"    글리프 저장 오류 {char_path}: {save_err}")
                else: 
                    logging.warning(f"  크롭 건너뜀: 좌표 범위 벗어남 ({left},{top})-({right},{bottom}) for char '{char}'")
            else: continue # 내부 루프가 정상적으로 완료된 경우에만 계속
            break # 내부 루프가 중단된 경우 외부 루프(행) 중단
            
        logging.info(f"  {filename_base} 처리 완료. {num_glyphs}개 글리프 추출됨.")
        return num_glyphs, 0 # 성공
        
    except Exception as e:
        logging.critical(f"치명적 오류: {image_path} 처리 중 오류: {e}", exc_info=True)
        return 0, 1 # 실패

def process_all_templates(input_dir, output_dir, verbose=True):
    """입력 디렉토리에 있는 모든 템플릿 이미지를 처리합니다."""
    logging.info(f"\n템플릿 처리 시작...") 
    logging.info(f"디버그 모드 현재 설정: {DEBUG_MODE}") 
    # 기본 출력 디렉토리는 이제 crop_glyphs_from_image 내부에서 파일별로 생성됨
    # create_directory_if_not_exists(output_dir) # 여기서 더 이상 필요 없음
    # 디버그 디렉토리도 파일별로 생성됨
    # if DEBUG_MODE: create_directory_if_not_exists(DEBUG_OUTPUT_DIR)
        
    # 입력 디렉토리에서 이미지 파일 찾기
    template_paths = glob.glob(os.path.join(input_dir, "*.jpg"))
    template_paths.extend(glob.glob(os.path.join(input_dir, "*.jpeg")))
    template_paths.extend(glob.glob(os.path.join(input_dir, "*.png")))
    if not template_paths: 
        logging.warning(f"{input_dir}에서 템플릿 이미지를 찾을 수 없습니다.")
        return
    template_paths.sort() # 파일 정렬
    total_glyphs_processed = 0; total_files_skipped = 0; processed_files_count = 0 # 카운터 초기화
    # 각 템플릿 파일 처리
    for template_path in template_paths:
        processed_files_count += 1
        num_glyphs, skipped = crop_glyphs_from_image(template_path, output_dir, verbose)
        total_glyphs_processed += num_glyphs; total_files_skipped += skipped
    # 최종 결과 출력
    logging.info(f"\n--- 처리 완료 ---")
    logging.info(f"처리된 파일 수: {processed_files_count}")
    if total_files_skipped > 0: 
        logging.warning(f"잘못된 해상도 또는 오류로 인해 {total_files_skipped}개 파일 건너뜀.")
    logging.info(f"추출된 총 글리프 수: {total_glyphs_processed}")
    if korean_chars:
        logging.info(f"문자 매핑 ({len(korean_chars)}): {korean_chars[:5]}...{korean_chars[-5:]}")
    else:
        logging.warning("처리 완료 요약 시 한글 문자 목록을 사용할 수 없습니다.")
        
    if DEBUG_MODE: 
        # 경로 수정: /app/debug_output 사용
        logging.info(f"디버그 이미지가 '/app/debug_output' (컨테이너 내부)에 저장됨") 
    logging.info("---------------------------")

def load_korean_chars():
    """지정된 파이썬 파일에서 korean_chars 목록을 로드합니다."""
    global korean_chars # 전역 변수 수정 명시
    logging.info(f"한글 문자 로드 시도: {KOREAN_CHARS_PATH}")
    if not os.path.exists(KOREAN_CHARS_PATH):
        logging.error(f"오류: 한글 참조 문자 파일을 {KOREAN_CHARS_PATH}에서 찾을 수 없습니다.")
        return # 로드 실패

    try:
        module_name = "korean_reference_chars_loaded"
        spec = importlib.util.spec_from_file_location(module_name, KOREAN_CHARS_PATH)
        if spec is None: raise ImportError(f"{KOREAN_CHARS_PATH} spec 생성 불가")
        korean_module = importlib.util.module_from_spec(spec)
        if korean_module is None: raise ImportError(f"{KOREAN_CHARS_PATH} spec에서 모듈 생성 불가")
        sys.modules[module_name] = korean_module
        spec.loader.exec_module(korean_module)
        
        if hasattr(korean_module, 'korean_chars') and isinstance(korean_module.korean_chars, list):
            korean_chars = korean_module.korean_chars # 전역 변수 설정
            logging.info(f"파일에서 한글 문자 {len(korean_chars)}개를 성공적으로 로드했습니다.")
        else:
            logging.error(f"오류: {KOREAN_CHARS_PATH}에 'korean_chars' 목록이 없거나 목록이 아닙니다.")
            korean_chars = None # 오류 발생 시 None으로 설정
            
    except Exception as e:
        logging.error(f"{KOREAN_CHARS_PATH} 로딩 오류: {e}", exc_info=True)
        korean_chars = None # 오류 발생 시 None으로 설정

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python glyph_cropper.py <입력_템플릿_디렉토리> <출력_글리프_디렉토리> [--no-verbose] [--debug]")
        sys.exit(1)
        
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    verbose_mode = True
    # --- 명령줄 인자 구문 분석 추가 ---
    if len(sys.argv) > 3:
        for arg in sys.argv[3:]:
            if arg == '--no-verbose':
                verbose_mode = False
                logging.getLogger().setLevel(logging.WARNING) # 로깅 레벨 조정
                logging.info("상세 모드 비활성화됨. 경고 이상만 표시.") # 이건 여전히 INFO 레벨
            elif arg == '--debug':
                DEBUG_MODE = True
                logging.getLogger().setLevel(logging.DEBUG) # 디버그 레벨 활성화
                logging.info("디버그 모드 활성화됨.")
            else:
                 print(f"알 수 없는 인자: {arg}")
                 sys.exit(1)
                 
    logging.info(f"입력 디렉토리: {input_directory}")
    logging.info(f"출력 디렉토리: {output_directory}")
    logging.info(f"상세 모드: {verbose_mode}")
    logging.info(f"디버그 모드: {DEBUG_MODE}")
    
    config_loaded_successfully = False # 플래그 추가
    # --- 템플릿 값 로딩 시도 (덮어쓰기용) ---
    try:
        logging.info(f"템플릿 생성기에서 설정 로드 시도: {TEMPLATE_GENERATOR_PATH}")
        spec = importlib.util.spec_from_file_location("template_config", TEMPLATE_GENERATOR_PATH)
        if spec is None: raise ImportError("spec 생성 불가")
        template_config = importlib.util.module_from_spec(spec)
        if template_config is None: raise ImportError("spec에서 모듈 생성 불가")
        spec.loader.exec_module(template_config)
        # 덮어쓸 변수 목록
        vars_to_override = ['MARGIN', 'BLANK_SIZE', 'CHAR_SECTION_HEIGHT', 'GRID_SIZE_WIDTH', 
                            'GRID_SIZE_HEIGHT', 'CHARS_PER_ROW', 'ROWS_PER_PAGE', 
                            'HEADER_SPACING', 'TEMPLATE_BLANK_PADDING', 'DIVIDER_LINE_THICKNESS',
                            'TITLE_TEXT', 'TITLE_FONT_SIZE', 'GRID_START_Y']
        overridden_count = 0
        
        # 제목 관련 값도 로드 시도
        if hasattr(template_config, 'TITLE_FONT_SIZE'):
             globals()['TITLE_FONT_SIZE'] = getattr(template_config, 'TITLE_FONT_SIZE')
        if hasattr(template_config, 'TITLE_TEXT'): # TITLE_TEXT 로드 추가
             globals()['TITLE_TEXT'] = getattr(template_config, 'TITLE_TEXT')
             
        for var_name in vars_to_override:
            if hasattr(template_config, var_name):
                value = getattr(template_config, var_name)
                globals()[var_name] = value # 전역 변수 덮어쓰기
                # 로깅은 유지하되, GRID_START_Y 로딩에 주목
                if var_name == 'GRID_START_Y':
                    logging.info(f"  >>> 템플릿에서 직접 로드됨: GRID_START_Y = {value}")
                else:
                    logging.info(f"  템플릿에서 덮어씀: {var_name} = {value}")
                overridden_count += 1
            else: 
                logging.warning(f"  템플릿 파일에서 변수 '{var_name}'을(를) 찾을 수 없음. 기본값 {globals().get(var_name, 'N/A')} 유지.") # 기본값 유지 명시
            
        if overridden_count > 0: 
            logging.info(f"{overridden_count}개 변수를 템플릿 생성기 파일에서 성공적으로 덮어썼거나 확인했습니다.")
            config_loaded_successfully = True # 성공 플래그 설정
            
            # --- 재계산 블록 제거 --- 
            # 아래 블록은 GRID_START_Y를 직접 로드하므로 제거됨
            # # --- 성공 시에만 GRID_START_Y 및 REFERENCE_DIVIDER_Y_ROW0 재계산 --- 
            # # 제목 Y 재계산 (MARGIN 필요)
            # ... (이전 재계산 로직 전체 주석 처리 또는 삭제) ...
            # # 첫 행 구분선 Y 참조값도 재계산 (GRID_START_Y, CHAR_SECTION_HEIGHT 필요)
            # # 참고: 이 값은 이제 주로 디버깅용
            # if 'GRID_START_Y' in globals() and 'CHAR_SECTION_HEIGHT' in globals():
            #     globals()['REFERENCE_DIVIDER_Y_ROW0'] = globals()['GRID_START_Y'] + globals()['CHAR_SECTION_HEIGHT']
            #     logging.info(f"참조/디버깅용 재계산된 REFERENCE_DIVIDER_Y_ROW0: {globals()['REFERENCE_DIVIDER_Y_ROW0']}")
            # else:
            #      logging.warning("REFERENCE_DIVIDER_Y_ROW0 재계산에 필요한 값을 찾을 수 없음.")
        else:
             logging.warning("템플릿 생성기 파일에서 어떤 변수도 덮어쓰지 못했습니다. 기본값 사용.")
             # 로딩 실패 시에도 기본 GRID_START_Y 계산 시도 -> 제거하고 기본값 사용 경고만 남김

    except Exception as e:
        logging.warning(f"템플릿 생성기 설정 로딩 중 오류 발생: {e}. 기본값 사용.", exc_info=True)
        # 실패 시 명시적으로 기본값 사용 로깅
        logging.warning(f"계산에 기본 GRID_START_Y={GRID_START_Y} 및 기타 기본값 사용 중.")
        
    # --- 최종 GRID_START_Y 로깅 ---
    logging.info(f"크롭 계산에 사용할 최종 GRID_START_Y: {GRID_START_Y}") # 여기서 사용될 값 명시
        
    # 로딩 성공 여부 로깅
    if not config_loaded_successfully:
         logging.error("템플릿 구성 로딩 실패! 크롭 좌표가 정확하지 않을 수 있습니다.")
        
    # 한글 목록 로드
    load_korean_chars()
    if korean_chars is None:
         logging.critical("한글 문자 목록을 로드할 수 없습니다. 크로핑을 계속할 수 없습니다.")
         sys.exit(1)
         
    # 주요 처리 함수 호출
    process_all_templates(input_directory, output_directory, verbose_mode) 