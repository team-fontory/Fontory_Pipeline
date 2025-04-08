import os
import subprocess
import shlex
import shutil
from fastAPI.config import PROJECT_ROOT, RESULT_DIR, WRITTEN_DIR

def run_script(script_path, args, logger, step_name):
    try:
        cmd = [script_path]
        if args:
            cmd.extend(args)
        cmd_str = ' '.join(shlex.quote(arg) for arg in cmd)
        logger.info(f"명령어 실행: {cmd_str}")
        
        if not os.access(script_path, os.X_OK):
            logger.warning(f"스크립트 {script_path}에 실행 권한이 없습니다. 권한을 부여합니다.")
            os.chmod(script_path, 0o755)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=PROJECT_ROOT
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                logger.info(f"[{step_name}] {line}")
        
        process.wait()
        exit_code = process.returncode
        
        if exit_code != 0:
            logger.error(f"스크립트 실행 실패 (종료 코드: {exit_code})")
            return False, f"스크립트 {os.path.basename(script_path)} 실행 실패 (종료 코드: {exit_code})"
        
        logger.info(f"스크립트 성공적으로 실행됨 (종료 코드: {exit_code})")
        return True, None
    except Exception as e:
        error_msg = f"스크립트 실행 중 예외 발생: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def cleanup_intermediate_results(font_name: str, logger):
    dirs_to_delete = [
        WRITTEN_DIR,
        os.path.join(RESULT_DIR, "1_cropped", font_name),
        os.path.join(RESULT_DIR, "2_inference", font_name),
        os.path.join(RESULT_DIR, "3_svg", font_name)
    ]
    logger.info(f"'{font_name}'에 대한 중간 결과물 정리 시작...")
    for dir_path in dirs_to_delete:
        if os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path)
                logger.info(f"삭제 완료: {dir_path}")
            except Exception as e:
                logger.error(f"삭제 실패: {dir_path} - {e}")
        else:
            logger.info(f"  삭제 건너뜀 (존재하지 않음): {dir_path}")
    logger.info("중간 결과물 정리 완료.")