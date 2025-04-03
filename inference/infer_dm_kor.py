import argparse
import os
import sys
from sconf import Config

from DM.models import Generator # /app/inference/resources/DM/...
from base.utils import load_reference # /app/inference/resources/base/...
from inference import infer_DM # /app/inference/resources/inference.py

try:
    from korean_reference_chars import korean_chars as KOREAN_REF_CHARS
except ImportError as e:
    print(f"Error importing from korean_reference_chars.py (expected in /app/resource): {e}")
    sys.exit(1)

import json
import torch
import subprocess
import time

def inference(args):
    app_base_path = "/app"
    resources_base_path = os.path.join(app_base_path, "inference", "resources")

    weight_path = os.path.join(resources_base_path, "checkpoints", "last.pth")
    decomposition_path = os.path.join(resources_base_path, "decomposition_DM.json")
    # config_path = os.path.join(resources_base_path, "cfgs", "DM", "default.yaml")
    gen_chars_path = os.path.join(resources_base_path, "gen_all_chars.json")

    n_heads = 3
    n_comps = 68
    ###############################################################
    print(f"Output directory (container): {args.output_dir}")
    print(f"Reference directory (container): {args.reference_dir}")
    print(f"Using weight path: {weight_path}")
    # print(f"Using config path: {config_path}")
    print(f"Using decomposition path: {decomposition_path}")
    print(f"Using gen_chars path: {gen_chars_path}")

    # 모델 로딩
    # if not os.path.exists(config_path):
    #     raise FileNotFoundError(f"Config file not found at {config_path}. Check cfgs directory and filename.")
    # cfg = Config(config_path)

    if not os.path.exists(decomposition_path):
        raise FileNotFoundError(f"Decomposition file not found at {decomposition_path}")
    decomposition = json.load(open(decomposition_path))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    gen = Generator(n_heads=n_heads, n_comps=n_comps).to(device).eval()

    if not os.path.exists(weight_path):
        raise FileNotFoundError(f"Weight file not found at {weight_path}")
    weight = torch.load(weight_path, map_location=device)
    
    gen.load_state_dict(weight["generator_ema"])
    print("Warning: Could not find standard keys ('generator_ema', 'state_dict') in weight file. Attempting to load directly.")
    # gen.load_state_dict(weight)

    ###############################################################
    extension = "jpg"
    ref_chars = KOREAN_REF_CHARS
    ###############################################################
    print(f"Loading references from (container): {args.reference_dir}")
    ref_dict, load_img = load_reference(args.reference_dir, extension, ref_chars)
    print(f"Loaded ref_dict keys: {ref_dict.keys() if isinstance(ref_dict, dict) else 'Not a dict'}")

    ###############################################################
    if not os.path.exists(gen_chars_path):
        raise FileNotFoundError(f"Generate characters file not found at {gen_chars_path}")
    gen_chars = json.load(open(gen_chars_path))
    print(f"Characters to generate (first 50): {gen_chars[:50] if isinstance(gen_chars, (list, str)) else 'Invalid type'}")
    print(f"Total characters to generate: {len(gen_chars)}")

    batch_size = 32 # 
    print(f"Using minimum batch_size: {batch_size}")
    ###############################################################

    print(f"Starting inference with filtered characters. Output will be saved to (container): {args.output_dir}")
    start_time = time.time() # <<< 시간 측정 시작
    infer_DM(gen, args.output_dir, gen_chars, ref_dict, load_img, decomposition, batch_size) # Pass filtered gen_chars
    end_time = time.time() # <<< 시간 측정 종료
    print(f"infer_DM function execution time: {end_time - start_time:.2f} seconds") # <<< 실행 시간 출력

    print(f"Inference finished. Output saved to (container) {args.output_dir}")
    return args.output_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DM inference.")
    parser.add_argument('--reference_dir', type=str, required=True, help='Directory containing reference images (e.g., /app/result/1_cropped).')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save generated images (e.g., /app/result/2_inference).')

    args = parser.parse_args()
    inference(args)