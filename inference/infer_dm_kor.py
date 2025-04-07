import argparse
import os
import sys
import logging
from sconf import Config

from DM.models import Generator
from base.utils import load_reference
from inference import infer_DM

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

try:
    from korean_reference_chars import korean_chars as KOREAN_REF_CHARS
except ImportError as e:
    logging.error(f"한글 참조 문자 가져오기 오류: {e}")
    sys.exit(1)

import json
import torch
import time

def inference(args):
    try:
        # 리소스 경로 설정
        app_base_path = "/app"
        resources_base_path = os.path.join(app_base_path, "inference", "resources")
        weight_path = os.path.join(resources_base_path, "checkpoints", "last.pth")
        decomposition_path = os.path.join(resources_base_path, "decomposition_DM.json")
        gen_chars_path = os.path.join(resources_base_path, "gen_all_chars.json")
        actual_reference_dir = os.path.join(args.reference_dir, args.font_name)
        
        # 모델 하이퍼파라미터
        n_heads = 3
        n_comps = 68
        
        logging.info(f"추론 시작 - 폰트: {args.font_name}")
        logging.info(f"출력 디렉토리: {args.output_dir}")
        logging.info(f"참조 이미지 디렉토리: {actual_reference_dir}")

        # 분해 정보 로드
        if not os.path.exists(decomposition_path):
            logging.error(f"분해 정보 파일을 찾을 수 없음: {decomposition_path}")
            raise FileNotFoundError(f"분해 정보 파일을 찾을 수 없음: {decomposition_path}")
        
        logging.debug(f"분해 정보 파일 로드: {decomposition_path}")
        decomposition = json.load(open(decomposition_path))
        logging.debug(f"분해 정보 로드 완료: {len(decomposition)} 항목")

        # 장치 설정 및 모델 초기화
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logging.info(f"사용 장치: {device}")
        
        logging.debug(f"모델 초기화 - n_heads: {n_heads}, n_comps: {n_comps}")
        gen = Generator(n_heads=n_heads, n_comps=n_comps).to(device).eval()
        logging.debug("모델 초기화 완료")

        # 가중치 로드
        if not os.path.exists(weight_path):
            logging.error(f"가중치 파일을 찾을 수 없음: {weight_path}")
            raise FileNotFoundError(f"가중치 파일을 찾을 수 없음: {weight_path}")
        
        logging.debug(f"가중치 로드 시작: {weight_path}")
        weight = torch.load(weight_path, map_location=device, weights_only=False)
        
        # 상태 사전 키에 따라 가중치 로드
        if "generator_ema" in weight:
            gen.load_state_dict(weight["generator_ema"])
            logging.debug("'generator_ema' 키에서 가중치 로드 완료")
        elif "state_dict" in weight:
            gen.load_state_dict(weight["state_dict"])
            logging.debug("'state_dict' 키에서 가중치 로드 완료")
        else:
            try:
                gen.load_state_dict(weight)
                logging.debug("직접 가중치 로드 완료")
            except RuntimeError as load_err:
                logging.error(f"가중치 로드 실패. 발견된 키: {weight.keys()}")
                raise load_err
        
        logging.debug("모델 가중치 로드 완료")

        # 참조 이미지 로드 설정
        extension = "jpg"
        ref_chars = KOREAN_REF_CHARS
        
        logging.info(f"참조 이미지 로드: {actual_reference_dir}")

        # 참조 이미지 로드
        ref_dict, load_img = load_reference(args.reference_dir, extension, ref_chars)
        
        if not ref_dict:
            logging.error(f"참조 이미지를 로드할 수 없음. 참조 디렉토리 확인 필요.")
            raise ValueError(f"참조 이미지를 로드할 수 없음. 참조 디렉토리 확인 필요.")
        
        logging.info(f"참조 이미지 로드 완료: {len(ref_dict[args.font_name])}개 문자")

        # 생성할 문자 목록 로드
        if not os.path.exists(gen_chars_path):
            logging.error(f"생성할 문자 목록 파일을 찾을 수 없음: {gen_chars_path}")
            raise FileNotFoundError(f"생성할 문자 목록 파일을 찾을 수 없음: {gen_chars_path}")
        
        logging.debug(f"생성할 문자 목록 로드: {gen_chars_path}")
        gen_chars = json.load(open(gen_chars_path))
        logging.info(f"생성할 문자 총 개수: {len(gen_chars)}개")

        # 추론 실행 설정
        batch_size = 32
        logging.debug(f"배치 크기: {batch_size}")
        
        # 추론 실행
        logging.info(f"추론 시작. 출력 경로: {args.output_dir}")
        start_time = time.time()
        infer_DM(gen, args.output_dir, gen_chars, ref_dict, load_img, decomposition, batch_size)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"추론 완료: {elapsed_time:.2f}초 소요")
        logging.info(f"생성된 이미지: {args.output_dir}/{args.font_name}/*.png")

        return args.output_dir

    except Exception as e:
        logging.error(f"추론 중 오류 발생: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="한글 폰트 DM 추론 실행")
    parser.add_argument('--reference_dir', type=str, required=True, help='참조 이미지가 포함된 기본 디렉토리')
    parser.add_argument('--output_dir', type=str, required=True, help='생성된 이미지를 저장할 디렉토리')
    parser.add_argument('--font_name', type=str, required=True, help='처리할 폰트 이름')
    
    args = parser.parse_args()
    inference(args)