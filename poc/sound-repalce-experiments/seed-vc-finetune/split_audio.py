"""
把 clean-vocals 目录下的长音频切成 10-28 秒的短片段，
输出到同目录的 segments/ 子目录。

用法:
  python split_audio.py <clean_vocals_dir> [--segment-len 20] [--min-len 10]
"""

import argparse
import os
import sys
import math

def split_wav(input_path: str, output_dir: str, segment_len: float, min_len: float):
    """用 soundfile + numpy 切分，避免 pydub/librosa 额外依赖问题。"""
    try:
        import soundfile as sf
        import numpy as np
    except ImportError:
        # fallback: try librosa
        try:
            import librosa
            import soundfile as sf
            import numpy as np
        except ImportError:
            print("ERROR: 需要 soundfile 库，请运行: pip install soundfile")
            sys.exit(1)

    import soundfile as sf
    import numpy as np

    data, sr = sf.read(input_path)
    total_samples = len(data)
    seg_samples = int(segment_len * sr)
    min_samples = int(min_len * sr)

    basename = os.path.splitext(os.path.basename(input_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    count = 0
    start = 0
    while start < total_samples:
        end = start + seg_samples
        chunk = data[start:end]
        if len(chunk) < min_samples:
            print(f"  跳过尾部片段 (长度 {len(chunk)/sr:.1f}s < 最小 {min_len}s)")
            break
        out_path = os.path.join(output_dir, f"{basename}_seg{count:03d}.wav")
        sf.write(out_path, chunk, sr)
        print(f"  写入 {os.path.basename(out_path)}  ({len(chunk)/sr:.1f}s)")
        count += 1
        start = end

    print(f"  共产生 {count} 个片段  来自 {os.path.basename(input_path)}")
    return count


def main():
    parser = argparse.ArgumentParser(description="Split long vocals into short segments")
    parser.add_argument("input_dir", help="clean-vocals 目录")
    parser.add_argument("--segment-len", type=float, default=20.0, help="每段长度(秒), 默认20")
    parser.add_argument("--min-len", type=float, default=10.0, help="最小保留长度(秒), 默认10")
    parser.add_argument("--output-dir", type=str, default="", help="输出目录, 默认为 input_dir/segments")
    args = parser.parse_args()

    input_dir = args.input_dir.rstrip("/")
    output_dir = args.output_dir if args.output_dir else os.path.join(input_dir, "segments")

    wav_files = sorted([
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith(".wav") and not f.startswith(".")
    ])

    if not wav_files:
        print(f"ERROR: 在 {input_dir} 中没有找到 .wav 文件")
        sys.exit(1)

    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"每段长度: {args.segment_len}s  最小保留: {args.min_len}s")
    print(f"找到 {len(wav_files)} 个文件\n")

    total = 0
    for wav_path in wav_files:
        print(f"处理: {os.path.basename(wav_path)}")
        total += split_wav(wav_path, output_dir, args.segment_len, args.min_len)
        print()

    print(f"=== 完成！共产生 {total} 个训练片段 ===")
    print(f"片段保存在: {output_dir}")


if __name__ == "__main__":
    main()
