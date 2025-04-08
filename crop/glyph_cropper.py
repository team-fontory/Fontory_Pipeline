#!/usr/bin/env python3
"""
Fontory용 글리프 크로퍼
입력 이미지를 확인하고 템플릿 설정에 따라 글자 영역을 추출한 후 목표 크기(128x128)로 리사이즈.
"""

import os
import sys
import glob
import logging
from PIL import Image, ImageDraw, ImageFont
import importlib.util

logging.basicConfig(
    level=logging.DEBUG,  
    format='%(message)s',  
    handlers=[logging.StreamHandler()]
)

# --- 템플릿 설정 --- 
EXPECTED_TEMPLATE_WIDTH = 2480  # 예상 템플릿 너비
EXPECTED_TEMPLATE_HEIGHT = 3508  # 예상 템플릿 높이
MARGIN = 150                    # 템플릿 여백
BLANK_SIZE = 280                # 쓰기 영역 크기 
CHAR_SECTION_HEIGHT = 80        # 글자 영역 높이
GRID_SIZE_WIDTH = 350           # 그리드 셀 너비
GRID_SIZE_HEIGHT = CHAR_SECTION_HEIGHT + BLANK_SIZE + 20  # 그리드 셀 높이
CHARS_PER_ROW = 6               # 행당 글자 수
ROWS_PER_PAGE = 8               # 페이지당 행 수
HEADER_SPACING = 50             # 헤더 간격
FONT_PATH = "/app/NanumGothic.ttf"  # 폰트 경로
FONT_SIZE = 60                  # 폰트 크기
TITLE_FONT_SIZE = FONT_SIZE * 1.5  # 제목 폰트 크기
TITLE_Y = MARGIN // 2           # 제목 Y 위치
TITLE_HEIGHT = TITLE_FONT_SIZE  # 제목 높이
GRID_START_Y = TITLE_Y + TITLE_HEIGHT + HEADER_SPACING  # 그리드 시작 Y 위치
korean_chars = None             # 한글 문자 목록 (초기화)
TEMPLATE_BLANK_PADDING = 10     # 템플릿 구분선 아래 패딩
DIVIDER_LINE_THICKNESS = 2      # 템플릿 구분선 두께
DEBUG_MODE = True               # 디버그 이미지 생성 여부
TARGET_SIZE = 128               # 최종 글리프 크기

# --- 경로 (컨테이너 내부) --- 
TEMPLATE_GENERATOR_PATH = "/app/make_template/template_generator.py"
KOREAN_CHARS_PATH = "/app/korean_reference_chars.py"

def create_directory_if_not_exists(directory):
    """디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory):
        logging.info(f"디렉토리 생성: {directory}")
        try:
            os.makedirs(directory)
        except Exception as e:
            logging.error(f"디렉토리 생성 실패 {directory}: {e}")
            sys.exit(1)

def calculate_crop_coordinates(row, col):
    """템플릿 내 글자 영역의 좌표를 계산합니다."""
    # X 좌표 계산
    cell_x_start = MARGIN + col * GRID_SIZE_WIDTH
    blank_x_offset = (GRID_SIZE_WIDTH - BLANK_SIZE) // 2
    left = cell_x_start + blank_x_offset
    right = left + BLANK_SIZE

    # Y 좌표 계산
    cell_y_start = GRID_START_Y + row * GRID_SIZE_HEIGHT
    divider_y = cell_y_start + CHAR_SECTION_HEIGHT
    
    top = divider_y + TEMPLATE_BLANK_PADDING 
    bottom = top + BLANK_SIZE

    return (left, top, right, bottom)

def get_character_for_position(row, col):
    """행과 열 위치에 해당하는 문자를 반환합니다."""
    global korean_chars
    if korean_chars is None:
        logging.error("한글 문자 목록이 로드되지 않았습니다.")
        sys.exit(1)
        
    index = row * CHARS_PER_ROW + col
    if 0 <= index < len(korean_chars):
        return korean_chars[index]
    else:
        if not hasattr(get_character_for_position, 'warned_indices'):
            get_character_for_position.warned_indices = set()
        if (row, col) not in get_character_for_position.warned_indices:
            logging.error(f"인덱스 {index}가 범위를 벗어남 (크기 {len(korean_chars)}). 행={row}, 열={col}")
            sys.exit(1)
        return f"unknown_{index+1}"

def create_debug_image(img, debug_save_path):
    """크롭 영역이 표시된 디버그 이미지를 생성합니다."""
    if not DEBUG_MODE: return
    
    debug_img = img.copy()
    draw = ImageDraw.Draw(debug_img)
    
    try: 
        font = ImageFont.load_default()
    except IOError: 
        font = None
        
    for row in range(ROWS_PER_PAGE):
        for col in range(CHARS_PER_ROW):
            char = get_character_for_position(row, col)
            left, top, right, bottom = calculate_crop_coordinates(row, col)
            
            # 계산된 값으로 구분선 표시
            cell_y_start = GRID_START_Y + row * GRID_SIZE_HEIGHT
            divider_y_vis = cell_y_start + CHAR_SECTION_HEIGHT
            cell_x = MARGIN + col * GRID_SIZE_WIDTH
            
            # 시각적 표시
            draw.line([cell_x, divider_y_vis, cell_x + GRID_SIZE_WIDTH, divider_y_vis], 
                     fill=(0, 255, 255), width=2)
            draw.rectangle([left, top, right, bottom], outline=(255, 0, 0), width=5)
            
            # 레이블 텍스트
            label_text = f"{char}\n({row},{col})\nT:{top} L:{left}"
            if font: 
                draw.text((left + 5, top + 5), label_text, fill=(255, 0, 0), font=font)
            else: 
                draw.text((left + 5, top + 5), label_text, fill=(255, 0, 0))
            
    try: 
        debug_img.save(debug_save_path)
        logging.info(f"디버그 이미지 저장: {debug_save_path}")
    except Exception as save_err: 
        logging.error(f"디버그 이미지 저장 오류: {save_err}")
        sys.exit(1)

def crop_glyphs_from_image(image_path, base_output_dir, verbose=True):
    """이미지에서 글리프를 추출하고 저장합니다."""
    try:
        # 이미지 로드 및 기본 정보 획득
        img = Image.open(image_path)
        actual_width, actual_height = img.size
        filename_base = os.path.splitext(os.path.basename(image_path))[0]
        
        logging.info(f"\n처리 중: {filename_base} (크기: {actual_width}x{actual_height})")
        
        # 출력 디렉토리 설정
        glyph_output_dir = base_output_dir
        debug_output_dir = "/app/debug_output"
        create_directory_if_not_exists(glyph_output_dir)
        if DEBUG_MODE:
            create_directory_if_not_exists(debug_output_dir)

        logging.info(f"  글리프 저장 경로: {glyph_output_dir}")
        if DEBUG_MODE:
            logging.info(f"  디버그 이미지 경로: {debug_output_dir}")

        # 이미지 크기 확인 및 조정
        if actual_width != EXPECTED_TEMPLATE_WIDTH or actual_height != EXPECTED_TEMPLATE_HEIGHT:
            logging.warning(f"  이미지 크기 ({actual_width}x{actual_height})가 예상({EXPECTED_TEMPLATE_WIDTH}x{EXPECTED_TEMPLATE_HEIGHT})과 다릅니다. 리사이징합니다.")
            try:
                img = img.resize((EXPECTED_TEMPLATE_WIDTH, EXPECTED_TEMPLATE_HEIGHT), Image.Resampling.LANCZOS)
                actual_width, actual_height = img.size
                logging.info(f"  리사이징 완료: {actual_width}x{actual_height}")
                
                # 디버그용 리사이징 이미지 저장
                if DEBUG_MODE:
                    resized_save_path = os.path.join(debug_output_dir, f"resized_{os.path.basename(image_path)}")
                    try:
                        img.save(resized_save_path)
                        logging.info(f"  리사이징 이미지 저장: {resized_save_path}")
                    except Exception as save_err:
                        logging.error(f"  리사이징 이미지 저장 실패: {save_err}")
            except Exception as e:
                logging.error(f"  이미지 리사이징 실패: {e}")
                sys.exit(1)
            
        # 디버그 이미지 생성
        if DEBUG_MODE:
            debug_save_path = os.path.join(debug_output_dir, f"debug_{os.path.basename(image_path)}")
            create_debug_image(img, debug_save_path)
        
        # 글리프 추출 및 저장
        num_glyphs = 0
        for row in range(ROWS_PER_PAGE):
            for col in range(CHARS_PER_ROW):
                char = get_character_for_position(row, col)
                
                # 알 수 없는 문자인 경우 처리 중단
                if char.startswith("unknown_") or char.startswith("nolist_"):
                    if col == 0:
                        logging.info(f"문자 목록 끝에 도달 (행 {row}). 크롭 중단.")
                    break
                    
                # 크롭 좌표 계산 및 유효성 검사
                left, top, right, bottom = calculate_crop_coordinates(row, col)
                if 0 <= left < right <= actual_width and 0 <= top < bottom <= actual_height:
                    # 글리프 크롭 및 변환
                    direct_crop = img.crop((left, top, right, bottom))
                    final_glyph = direct_crop
                    final_glyph = final_glyph.convert('L')  # 그레이스케일 변환
                    final_glyph = final_glyph.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
                    
                    # 파일 저장
                    char_filename = f"{char}.jpg"
                    char_path = os.path.join(glyph_output_dir, char_filename)
                    try: 
                        final_glyph.save(char_path, "JPEG", quality=95)
                        logging.info(f"저장: {char_filename} (문자 '{char}' | 행={row}, 열={col})")
                        num_glyphs += 1
                    except Exception as save_err: 
                        logging.error(f"글리프 저장 오류: {save_err}")
                        sys.exit(1)
                else: 
                    logging.warning(f"  크롭 건너뜀: 범위 벗어남 ({left},{top})-({right},{bottom}) for '{char}'")
            else:
                continue  # 내부 루프가 정상적으로 완료된 경우
            break  # 내부 루프가 중단된 경우 외부 루프도 중단
            
        logging.info(f"  {filename_base} 처리 완료. {num_glyphs}개 글리프 추출.")
        return num_glyphs, 0
        
    except Exception as e:
        logging.critical(f"치명적 오류: {image_path} 처리 중 {e}", exc_info=True)
        return 0, 1

def process_all_templates(input_dir, output_dir, verbose=True):
    """입력 디렉토리의 모든 템플릿 이미지를 처리합니다."""
    logging.info("\n템플릿 처리 시작...")
    logging.info(f"디버그 모드: {DEBUG_MODE}")
        
    # 입력 디렉토리에서 이미지 파일 찾기
    template_paths = glob.glob(os.path.join(input_dir, "*.jpg"))
    template_paths.extend(glob.glob(os.path.join(input_dir, "*.jpeg")))
    template_paths.extend(glob.glob(os.path.join(input_dir, "*.png")))
    
    if not template_paths: 
        logging.error(f"{input_dir}에서 이미지를 찾을 수 없습니다.")
        sys.exit(1)
    
    template_paths.sort()
    
    # 통계 카운터 초기화
    total_glyphs_processed = 0
    total_files_skipped = 0
    processed_files_count = 0
    
    # 각 템플릿 파일 처리
    for template_path in template_paths:
        processed_files_count += 1
        num_glyphs, skipped = crop_glyphs_from_image(template_path, output_dir, verbose)
        total_glyphs_processed += num_glyphs
        total_files_skipped += skipped
    
    # 최종 결과 출력
    logging.info(f"\n--- 처리 완료 ---")
    logging.info(f"처리된 파일 수: {processed_files_count}")
    if total_files_skipped > 0: 
        logging.warning(f"건너뛴 파일 수: {total_files_skipped}")
    logging.info(f"추출된 총 글리프 수: {total_glyphs_processed}")
    
    if korean_chars:
        logging.info(f"문자 매핑 ({len(korean_chars)}): {korean_chars[:5]}...{korean_chars[-5:]}")
    else:
        logging.warning("한글 문자 목록을 사용할 수 없습니다.")
        
    if DEBUG_MODE: 
        logging.info(f"디버그 이미지: '/app/debug_output'")
    logging.info("---------------------------")

def load_korean_chars():
    """한글 문자 목록을 로드합니다."""
    global korean_chars
    logging.info(f"한글 문자 로드: {KOREAN_CHARS_PATH}")
    
    if not os.path.exists(KOREAN_CHARS_PATH):
        logging.error(f"한글 참조 문자 파일을 찾을 수 없습니다.")
        sys.exit(1)

    try:
        # 파이썬 모듈로 로드
        module_name = "korean_reference_chars_loaded"
        spec = importlib.util.spec_from_file_location(module_name, KOREAN_CHARS_PATH)
        if spec is None:
            raise ImportError(f"{KOREAN_CHARS_PATH} spec 생성 불가")
            
        korean_module = importlib.util.module_from_spec(spec)
        if korean_module is None:
            raise ImportError(f"{KOREAN_CHARS_PATH} 모듈 생성 불가")
            
        sys.modules[module_name] = korean_module
        spec.loader.exec_module(korean_module)
        
        # 모듈에서 korean_chars 리스트 추출
        if hasattr(korean_module, 'korean_chars') and isinstance(korean_module.korean_chars, list):
            korean_chars = korean_module.korean_chars
            logging.info(f"한글 문자 {len(korean_chars)}개 로드 완료")
        else:
            logging.error(f"'korean_chars' 목록이 없거나 형식이 잘못됨")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"문자 목록 로딩 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python glyph_cropper.py <입력_템플릿_디렉토리> <출력_글리프_디렉토리> [--no-verbose] [--debug]")
        sys.exit(1)
        
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    verbose_mode = True
    
    # 명령줄 인자 처리
    if len(sys.argv) > 3:
        for arg in sys.argv[3:]:
            if arg == '--no-verbose':
                verbose_mode = False
                logging.getLogger().setLevel(logging.WARNING)
            elif arg == '--debug':
                DEBUG_MODE = True
                logging.getLogger().setLevel(logging.DEBUG)
            else:
                print(f"알 수 없는 인자: {arg}")
                sys.exit(1)
                 
    logging.info(f"입력 디렉토리: {input_directory}")
    logging.info(f"출력 디렉토리: {output_directory}")
    
    # 설정 로드 시도
    try:
        logging.info(f"템플릿 생성기 설정 로드: {TEMPLATE_GENERATOR_PATH}")
        spec = importlib.util.spec_from_file_location("template_config", TEMPLATE_GENERATOR_PATH)
        if spec is None:
            raise ImportError("spec 생성 불가")
            
        template_config = importlib.util.module_from_spec(spec)
        if template_config is None:
            raise ImportError("모듈 생성 불가")
            
        spec.loader.exec_module(template_config)
        
        # 덮어쓸 변수 목록
        vars_to_override = ['MARGIN', 'BLANK_SIZE', 'CHAR_SECTION_HEIGHT', 'GRID_SIZE_WIDTH', 
                          'GRID_SIZE_HEIGHT', 'CHARS_PER_ROW', 'ROWS_PER_PAGE', 
                          'HEADER_SPACING', 'TEMPLATE_BLANK_PADDING', 'DIVIDER_LINE_THICKNESS',
                          'TITLE_FONT_SIZE', 'GRID_START_Y']
        
        # 각 변수 로드 및 설정
        for var_name in vars_to_override:
            if hasattr(template_config, var_name):
                globals()[var_name] = getattr(template_config, var_name)
                if var_name == 'GRID_START_Y':
                    logging.info(f"  GRID_START_Y = {globals()[var_name]}")
                    
    except Exception as e:
        logging.warning(f"템플릿 설정 로드 실패: {e}. 기본값 사용.")
        
    # 최종 설정 로깅
    logging.info(f"GRID_START_Y: {GRID_START_Y}")
        
    # 한글 목록 로드
    load_korean_chars()
    if korean_chars is None:
        logging.critical("한글 문자 목록을 로드할 수 없습니다.")
        sys.exit(1)
         
    # 처리 시작
    process_all_templates(input_directory, output_directory, verbose_mode) 