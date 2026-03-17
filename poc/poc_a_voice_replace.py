"""
PoC-A 脚本：Demucs 人声分离 + seed-vc 声音替换
完整流程：source 歌曲 → 分离人声 → seed-vc 转换音色 → 混合伴奏 → 输出

运行方式：
  conda activate ai-music
  python poc/poc_a_voice_replace.py --source poc/audio/source.mp3 --target poc/audio/target.wav
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import torch
from pydub import AudioSegment


def step1_separate_vocals(source_path: Path, output_dir: Path) -> tuple[Path, Path]:
    """Step 1: 用 Demucs 分离人声和伴奏"""
    print("\n" + "="*50)
    print("📌 Step 1: Demucs 人声分离")
    print("="*50)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"   使用设备: {device}")

    t0 = time.time()
    cmd = [
        sys.executable, "-m", "demucs",
        "--two-stems", "vocals",
        "-d", device,
        "-o", str(output_dir / "demucs_output"),
        str(source_path)
    ]
    print(f"   命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Demucs 分离失败:\n{result.stderr}")
        sys.exit(1)

    elapsed = time.time() - t0
    # Demucs 输出目录: output_dir/demucs_output/htdemucs/{stem}/
    stem = source_path.stem
    demucs_dir = output_dir / "demucs_output" / "htdemucs" / stem
    vocals_path = demucs_dir / "vocals.wav"
    accompaniment_path = demucs_dir / "no_vocals.wav"

    if not vocals_path.exists():
        print(f"❌ 未找到分离结果: {vocals_path}")
        print(f"   Demucs stdout: {result.stdout[-500:]}")
        sys.exit(1)

    print(f"✅ 人声分离完成 ({elapsed:.1f}s)")
    print(f"   人声: {vocals_path}")
    print(f"   伴奏: {accompaniment_path}")
    return vocals_path, accompaniment_path


def step2_voice_conversion(
    vocals_path: Path,
    target_path: Path,
    output_dir: Path,
    seed_vc_dir: Path,
    diffusion_steps: int = 10,
) -> Path:
    """Step 2: 用 seed-vc 进行声音转换"""
    print("\n" + "="*50)
    print("📌 Step 2: seed-vc 声音转换")
    print("="*50)

    converted_dir = output_dir / "seed_vc_output"
    converted_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    # 注意：国内网络可能需要设置 HF 镜像
    env_prefix = "HF_ENDPOINT=https://hf-mirror.com "
    cmd = [
        sys.executable,
        str(seed_vc_dir / "inference.py"),
        "--source", str(vocals_path),
        "--target", str(target_path),
        "--output", str(converted_dir),
        "--diffusion-steps", str(diffusion_steps),
        "--length-adjust", "1.0",
        "--inference-cfg-rate", "0.7",
        "--f0-condition", "False",   # False = 普通声音转换（非歌唱模式）
        "--fp16", "True",
    ]
    print(f"   diffusion steps: {diffusion_steps}")
    print(f"   命令: {' '.join(cmd)}")
    print("   ⏳ 首次运行会从 HuggingFace 下载模型（约 200-400MB）...")

    env = {"HF_ENDPOINT": "https://hf-mirror.com"}
    import os
    full_env = {**os.environ, **env}
    result = subprocess.run(cmd, capture_output=True, text=True, env=full_env)

    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"❌ seed-vc 转换失败:\n{result.stderr[-1000:]}")
        print(f"   stdout: {result.stdout[-500:]}")
        sys.exit(1)

    # seed-vc 输出文件名规则：{source_stem}_{target_stem}_vc.wav
    converted_files = list(converted_dir.glob("*_vc.wav"))
    if not converted_files:
        converted_files = list(converted_dir.glob("*.wav"))

    if not converted_files:
        print(f"❌ 未找到转换输出文件，目录内容: {list(converted_dir.iterdir())}")
        print(f"   stdout: {result.stdout[-500:]}")
        sys.exit(1)

    converted_path = converted_files[0]
    print(f"✅ 声音转换完成 ({elapsed:.1f}s)")
    print(f"   转换后人声: {converted_path}")
    return converted_path


def step3_mix_audio(
    converted_vocals: Path,
    accompaniment: Path,
    output_path: Path,
    vocals_gain_db: float = 0.0,
) -> Path:
    """Step 3: 混合转换后的人声与原伴奏"""
    print("\n" + "="*50)
    print("📌 Step 3: 音频混合")
    print("="*50)

    vocals_audio = AudioSegment.from_wav(str(converted_vocals))
    accompaniment_audio = AudioSegment.from_wav(str(accompaniment))

    # 对齐时长
    target_len = len(accompaniment_audio)
    if len(vocals_audio) < target_len:
        # 人声较短，用静音补齐
        silence = AudioSegment.silent(duration=target_len - len(vocals_audio))
        vocals_audio = vocals_audio + silence
    else:
        vocals_audio = vocals_audio[:target_len]

    # 音量调整
    if vocals_gain_db != 0:
        vocals_audio = vocals_audio + vocals_gain_db

    # 混合
    mixed = accompaniment_audio.overlay(vocals_audio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    mixed.export(str(output_path), format="mp3", bitrate="320k")

    print(f"✅ 混合完成")
    print(f"   输出文件: {output_path}")
    print(f"   时长: {len(mixed)/1000:.1f}s")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="PoC-A: 声音替换完整流程")
    parser.add_argument("--source", required=True, help="源歌曲路径（MP3/WAV）")
    parser.add_argument("--target", required=True, help="目标参考音频路径（WAV）")
    parser.add_argument("--output", default="poc/output/result.mp3", help="输出文件路径")
    parser.add_argument("--seed-vc-dir", default="/Users/yuxudong/Documents/seed-vc", help="seed-vc 目录")
    parser.add_argument("--diffusion-steps", type=int, default=10, help="扩散步数（10=快速，30=高质量）")
    args = parser.parse_args()

    source_path = Path(args.source)
    target_path = Path(args.target)
    output_path = Path(args.output)
    seed_vc_dir = Path(args.seed_vc_dir)
    work_dir = output_path.parent

    print("🎵 PoC-A: Demucs + seed-vc 声音替换")
    print(f"   source: {source_path}")
    print(f"   target: {target_path}")
    print(f"   output: {output_path}")

    # Step 1: 人声分离
    vocals, accompaniment = step1_separate_vocals(source_path, work_dir)

    # Step 2: 声音转换
    converted = step2_voice_conversion(
        vocals, target_path, work_dir, seed_vc_dir,
        diffusion_steps=args.diffusion_steps
    )

    # Step 3: 混合输出
    step3_mix_audio(converted, accompaniment, output_path)

    print("\n" + "="*50)
    print(f"🎉 PoC-A 完成！输出: {output_path}")
    print("="*50)


if __name__ == "__main__":
    main()
