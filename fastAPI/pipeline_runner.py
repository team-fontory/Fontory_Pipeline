import os
from fastAPI.script_utils import run_script

def run_font_pipeline(font_name: str, font_eng_name:str, request_id: str, logger):
    logger.info(f"폰트 생성 파이프라인 시작...")
    
    crop_script = os.path.join(os.getcwd(), "scripts", "1_crop_glyphs.sh")
    logger.info("글리프 크롭 스크립트 실행 중...")
    success, error = run_script(crop_script, [font_name], logger, "CROP")
    if not success:
        logger.error(f"글리프 크롭 실패: {error}")
        raise Exception(f"글리프 크롭 실패: {error}")
    
    inference_script = os.path.join(os.getcwd(), "scripts", "2_run_inference.sh")
    logger.info("추론 스크립트 실행 중...")
    success, error = run_script(inference_script, [font_name], logger, "INFERENCE")
    if not success:
        logger.error(f"추론 실패: {error}")
        raise Exception(f"추론 실패: {error}")
    
    jpg2svg_script = os.path.join(os.getcwd(), "scripts", "3_run_jpg2svg.sh")
    logger.info("JPG에서 SVG 변환 스크립트 실행 중...")
    success, error = run_script(jpg2svg_script, [font_name], logger, "SVG")
    if not success:
        logger.error(f"JPG에서 SVG 변환 실패: {error}")
        raise Exception(f"JPG에서 SVG 변환 실패: {error}")
    
    svg2ttf_script = os.path.join(os.getcwd(), "scripts", "4_run_svg2ttf.sh")
    logger.info("SVG에서 TTF/WOFF 변환 스크립트 실행 중...")
    success, error = run_script(svg2ttf_script, ["-f", font_name, "-e", font_eng_name], logger, "TTF/WOFF")
    if not success:
        logger.error(f"SVG에서 TTF/WOFF 변환 실패: {error}")
        raise Exception(f"SVG에서 TTF/WOFF 변환 실패: {error}")
    
    logger.info(f"폰트 '{font_name}' 생성 파이프라인이 성공적으로 완료되었습니다.")
    result_ttf_path = os.path.join(os.getcwd(), "result", "4_fonts", f"{font_name}.ttf")
    result_woff_path = os.path.join(os.getcwd(), "result", "4_fonts", f"{font_name}.woff2")
    return result_ttf_path, result_woff_path