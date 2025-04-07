import os
import sys
import glob
import subprocess
import logging
from PIL import Image


logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

# Potrace 명령어 설정
POTRACE_COMMAND = "potrace"

def create_directory_if_not_exists(directory):
    """지정된 디렉토리가 없으면 생성합니다."""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logging.info(f"디렉토리 생성: {directory}")
        except Exception as e:
            logging.error(f"디렉토리 생성 실패: {e}")
            sys.exit(1)

def convert_to_bmp(input_path, temp_path):
    try:
        logging.debug(f"이미지 로드 시작: {input_path}")
        with Image.open(input_path) as img:
            # 원본 이미지 정보 기록
            width, height = img.size
            mode = img.mode
            logging.debug(f"원본 이미지 크기: {width}x{height}, 모드: {mode}")
            
            # 흑백으로 변환
            logging.debug(f"흑백(L) 모드로 변환 중")
            img = img.convert('L')
            
            # 임계값 적용 (128)하여 이진화
            logging.debug(f"이진화 처리 시작 (임계값: 128)")
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            
            # BMP로 저장
            logging.debug(f"BMP 파일 저장: {temp_path}")
            img.save(temp_path, 'BMP')
            
            # 저장된 파일 크기 확인
            bmp_size = os.path.getsize(temp_path)
            logging.debug(f"BMP 파일 생성 완료: {bmp_size:,} 바이트, 크기: {width}x{height}")
        return True
    except Exception as e:
        logging.error(f"'{input_path}' BMP 변환 실패: {e}")
        return False

def convert_image(input_path, output_path):
    # 임시 BMP 파일 경로
    temp_bmp = os.path.splitext(output_path)[0] + '.bmp'
    
    try:
        # 원본 파일 크기 기록
        input_size = os.path.getsize(input_path)
        logging.debug(f"변환 시작: '{os.path.basename(input_path)}' ({input_size:,} 바이트) → '{os.path.basename(output_path)}'")
        
        # 이미지를 흑백 BMP로 변환
        logging.debug(f"단계 1/3: BMP 변환 시작")
        if not convert_to_bmp(input_path, temp_bmp):
            logging.error(f"변환 실패: BMP 변환 단계에서 실패")
            return False
        
        # BMP 파일 크기 기록
        bmp_size = os.path.getsize(temp_bmp)
        logging.debug(f"BMP 변환 완료: {bmp_size:,} 바이트")

        # Potrace로 BMP를 SVG로 변환
        logging.debug(f"단계 2/3: Potrace SVG 변환 시작")
        command = [
            POTRACE_COMMAND,
            '-s',          # SVG 출력
            '-o', output_path,  # 출력 파일
            temp_bmp       # 입력 파일
        ]
        
        logging.debug(f"Potrace 명령어: {' '.join(command)}")
        
        # 시간 측정 시작
        import time
        start_time = time.time()
        
        # 명령 실행
        logging.debug(f"Potrace 실행 중...")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        # 실행 시간 계산
        elapsed_time = time.time() - start_time
        logging.debug(f"Potrace 실행 완료: {elapsed_time:.2f}초 소요")
        
        if result.stdout:
            logging.debug(f"Potrace 출력: {result.stdout}")
        
        if result.stderr:
            logging.warning(f"Potrace 경고: {result.stderr}")
        
        # 결과 확인
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            svg_size = os.path.getsize(output_path)
            compression_ratio = bmp_size / svg_size if svg_size > 0 else 0
            logging.debug(f"SVG 생성 완료: {svg_size:,} 바이트 (압축률: {compression_ratio:.2f}x)")
            
            # SVG 파일 분석
            try:
                with open(output_path, 'r') as f:
                    svg_content = f.read()
                    path_count = svg_content.count('<path')
                    logging.debug(f"SVG 분석: <path> 요소 {path_count}개 발견")
            except Exception as e:
                logging.debug(f"SVG 분석 중 오류: {e}")
            
            return True
        else:
            logging.error(f"SVG 파일 생성 실패: {output_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Potrace 실행 실패: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"변환 중 예외 발생: {e}")
        return False
    finally:
        # 임시 파일 정리
        logging.debug(f"단계 3/3: 임시 파일 정리")
        if os.path.exists(temp_bmp):
            try:
                bmp_size = os.path.getsize(temp_bmp)
                os.remove(temp_bmp)
                logging.debug(f"임시 BMP 파일 제거: {os.path.basename(temp_bmp)} ({bmp_size:,} 바이트)")
            except Exception as e:
                logging.warning(f"임시 파일 제거 실패: {e}")

def process_images(input_dir, output_dir):
    """입력 디렉토리의 모든 이미지를 SVG로 변환합니다.
    
    지원 형식: JPG, JPEG, PNG
    """
    # 시작 시간 기록
    import time
    start_time = time.time()
    
    # 출력 디렉토리 생성
    logging.info(f"변환 프로세스 시작")
    logging.info(f"출력 디렉토리 확인: {output_dir}")
    create_directory_if_not_exists(output_dir)
    
    # 이미지 파일 찾기
    logging.info(f"이미지 검색: '{input_dir}'에서 이미지 파일 검색 중")
    image_paths = glob.glob(os.path.join(input_dir, '*.jpg'))
    logging.info(f"JPG 파일 {len(image_paths)}개 발견")
    
    jpeg_files = glob.glob(os.path.join(input_dir, '*.jpeg'))
    logging.info(f"JPEG 파일 {len(jpeg_files)}개 발견")
    image_paths.extend(jpeg_files)
    
    png_files = glob.glob(os.path.join(input_dir, '*.png'))
    logging.info(f"PNG 파일 {len(png_files)}개 발견")
    image_paths.extend(png_files)

    if not image_paths:
        logging.warning(f"입력 디렉토리에 이미지가 없음: {input_dir}")
        return
        
    image_paths.sort()
    total_files = len(image_paths)
    logging.info(f"변환 준비: 총 {total_files}개 이미지 파일 발견")
    
    # 변환 통계
    processed_count = 0
    failed_count = 0
    total_input_size = 0
    total_output_size = 0

    # 각 이미지 처리
    for index, img_path in enumerate(image_paths, 1):
        base_filename = os.path.splitext(os.path.basename(img_path))[0]
        output_path = os.path.join(output_dir, f"{base_filename}.svg")
        
        # 파일 크기 기록
        input_size = os.path.getsize(img_path)
        total_input_size += input_size
        
        if index % 100 == 0:
                logging.info(f"이미지 처리 진행: {index}/{total_files}")
        logging.debug(f"이미지 처리 [{index}/{total_files}]: '{os.path.basename(img_path)}' ({input_size:,} 바이트)")
        
        if convert_image(img_path, output_path):
            output_size = os.path.getsize(output_path)
            total_output_size += output_size
            compression_ratio = (input_size / output_size) if output_size > 0 else 0
            
            logging.debug(f"변환 성공: '{os.path.basename(output_path)}' 생성 완료 ({output_size:,} 바이트, 압축비: {compression_ratio:.2f}x)")
            processed_count += 1
        else:
            logging.error(f"변환 실패: '{os.path.basename(img_path)}'")
            failed_count += 1

    # 실행 시간 계산
    elapsed_time = time.time() - start_time
    avg_time_per_file = elapsed_time / total_files if total_files > 0 else 0
    
    # 변환 결과 요약
    logging.info("\n--- 변환 결과 요약 ---")
    logging.info(f"결과: 성공: {processed_count}개 | 실패: {failed_count}개 | 총: {total_files}개")
    
    if processed_count > 0:
        avg_compression = (total_input_size / total_output_size) if total_output_size > 0 else 0
        logging.info(f"크기: 입력: {total_input_size:,} 바이트 | 출력: {total_output_size:,} 바이트 | 평균 압축비: {avg_compression:.2f}x")
    
    logging.info(f"시간: 총 {elapsed_time:.2f}초 | 평균 {avg_time_per_file:.2f}초/파일")
    logging.info("--------------------------")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("사용법: python jpg_to_svg_converter.py <입력_이미지_디렉토리> <출력_svg_디렉토리>")
        sys.exit(1)
        
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    
    logging.info(f"JPG/PNG → SVG 변환 시작")
    logging.info(f"입력 디렉토리: {input_directory}")
    logging.info(f"출력 디렉토리: {output_directory}")
    
    process_images(input_directory, output_directory) 