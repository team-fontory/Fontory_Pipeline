import os
import sys
import glob
import subprocess
import logging
from PIL import Image

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 설정
POTRACE_COMMAND = "potrace"  # potrace 실행 파일 경로

def create_directory_if_not_exists(directory):
    """지정된 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logging.info(f"출력 디렉토리 생성됨: {directory}")
        except OSError as e:
            logging.error(f"오류: 디렉토리 생성 실패 '{directory}': {e}")
            sys.exit(1)
        except Exception as e:
            logging.critical(f"치명적 오류: 디렉토리 생성 중 예기치 않은 오류 '{directory}': {e}", exc_info=True)
            sys.exit(1)

def convert_to_bmp(input_path, temp_path):
    """이미지를 흑백 BMP로 변환합니다."""
    try:
        with Image.open(input_path) as img:
            # 흑백으로 변환
            img = img.convert('L')
            # 임계값 처리로 이진화 (threshold = 128)
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            img.save(temp_path, 'BMP')
        return True
    except Exception as e:
        logging.error(f"이미지 변환 실패 '{input_path}': {e}")
        return False

def convert_image(input_path, output_path):
    """단일 이미지를 SVG로 변환합니다."""
    # 임시 BMP 파일 경로
    temp_bmp = os.path.splitext(output_path)[0] + '.bmp'
    
    try:
        # 1. 먼저 이미지를 흑백 BMP로 변환
        if not convert_to_bmp(input_path, temp_bmp):
            return False

        # 2. potrace로 BMP를 SVG로 변환
        command = [
            POTRACE_COMMAND,
            '-s',  # SVG 출력
            '-o', output_path,  # 출력 파일
            temp_bmp  # 입력 파일
        ]
        
        logging.info(f"실행 중: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        if result.stderr:
            logging.warning(f"Potrace 경고:\n{result.stderr}")
        
        # 성공 확인
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            logging.error(f"변환된 파일이 생성되지 않았거나 비어 있습니다: {output_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Potrace 실행 실패: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"변환 중 오류 발생: {e}")
        return False
    finally:
        # 임시 BMP 파일 삭제
        try:
            if os.path.exists(temp_bmp):
                os.remove(temp_bmp)
        except Exception as e:
            logging.warning(f"임시 파일 삭제 실패 {temp_bmp}: {e}")

def process_images(input_dir, output_dir):
    """입력 디렉토리의 모든 이미지를 처리하여 출력 디렉토리에 SVG로 저장합니다."""
    create_directory_if_not_exists(output_dir)
    
    image_paths = glob.glob(os.path.join(input_dir, '*.jpg'))
    image_paths.extend(glob.glob(os.path.join(input_dir, '*.jpeg')))
    image_paths.extend(glob.glob(os.path.join(input_dir, '*.png')))

    if not image_paths:
        logging.warning(f"입력 디렉토리 '{input_dir}'에서 처리할 이미지 파일을 찾을 수 없습니다.")
        return
        
    image_paths.sort()
    logging.info(f"총 {len(image_paths)}개의 이미지 파일을 변환합니다.")
    
    processed_count = 0
    failed_count = 0

    for img_path in image_paths:
        base_filename = os.path.splitext(os.path.basename(img_path))[0]
        output_path = os.path.join(output_dir, f"{base_filename}.svg")
        
        logging.info(f"변환 중: '{os.path.basename(img_path)}' -> '{os.path.basename(output_path)}'")
        if convert_image(img_path, output_path):
            processed_count += 1
        else:
            failed_count += 1

    logging.info("\n--- 변환 완료 ---")
    logging.info(f"성공적으로 변환된 파일: {processed_count}")
    if failed_count > 0:
        logging.warning(f"변환 실패 파일: {failed_count}")
    logging.info("--------------------------")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.critical("사용법: python jpg_to_svg_converter.py <입력_이미지_디렉토리> <출력_svg_디렉토리>")
        sys.exit(1)
        
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    
    logging.info(f"입력 디렉토리: {input_directory}")
    logging.info(f"출력 디렉토리: {output_directory}")
    
    process_images(input_directory, output_directory) 