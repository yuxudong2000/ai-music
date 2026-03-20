"""poc/audio/process_vocals.py

一个可复用的本地脚本：
1) 人声分离（Demucs htdemucs，输出 vocals.wav / no_vocals.wav）
2) 去混响/回声去除（audio-separator 的 dereverb 模型，输出 vocals_dereverb.wav）

特点：
- 保留每一步产物，便于排查与复用
- 目录结构固定且可预测

用法示例：
  conda activate ai-music
  python poc/audio/process_vocals.py \
    --input "poc/audio/zhengzhihua/郑智化 - 水手.mp3" \
    --out-dir poc/audio/processed

输出示例：
  poc/audio/processed/郑智化 - 水手/
    demucs/htdemucs/<stem>/vocals.wav
    demucs/htdemucs/<stem>/no_vocals.wav
    dereverb/vocals_dereverb.wav

依赖：
- ffmpeg（pydub 与 demucs 读写常用）：brew install ffmpeg
- pip requirements: demucs==4.0.1, audio-separator[cpu]==0.42.1

"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import torch


def _safe_stem(name: str) -> str:
    # 保留中文/字母/数字/空格/常见连接符，其余替换为下划线
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff _\-\.]", "_", name)
    return s.strip().strip(".")


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "\n".join(
                [
                    "Command failed:",
                    "  " + " ".join(cmd),
                    "--- stdout ---",
                    p.stdout[-2000:],
                    "--- stderr ---",
                    p.stderr[-2000:],
                ]
            )
        )


def demucs_separate(input_audio: Path, out_dir: Path) -> tuple[Path, Path]:
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    t0 = time.time()

    demucs_out = out_dir / "demucs"
    demucs_out.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        "htdemucs",
        "--two-stems",
        "vocals",
        "-d",
        device,
        "-o",
        str(demucs_out),
        str(input_audio),
    ]
    run(cmd)

    stem = input_audio.stem
    demucs_dir = demucs_out / "htdemucs" / stem
    vocals = demucs_dir / "vocals.wav"
    no_vocals = demucs_dir / "no_vocals.wav"

    if not vocals.exists() or not no_vocals.exists():
        raise FileNotFoundError(
            f"Demucs 输出不存在，期望: {vocals} 与 {no_vocals}。实际目录: {demucs_dir}"
        )

    dt = time.time() - t0
    print(f"✅ Demucs 完成，用时 {dt:.1f}s")
    print(f"   vocals:    {vocals}")
    print(f"   no_vocals: {no_vocals}")
    return vocals, no_vocals


def dereverb_vocals(vocals_wav: Path, out_dir: Path, model: str) -> Path:
    """使用 audio-separator 做去混响。

    audio-separator 会按模型输出一个 wav，这里我们统一重命名为 vocals_dereverb.wav。
    """

    t0 = time.time()
    dereverb_out = out_dir / "dereverb"
    dereverb_out.mkdir(parents=True, exist_ok=True)

    # audio-separator CLI
    # 说明：不同版本参数略有差异，仓库当前已固定到 0.42.1
    # 常用：audio-separator -m <model> -i <input> -o <outdir>
    cmd = [
        "audio-separator",
        "-m",
        model,
        "-i",
        str(vocals_wav),
        "-o",
        str(dereverb_out),
    ]
    run(cmd)

    # 寻找最新输出 wav
    wavs = sorted(dereverb_out.glob("*.wav"), key=lambda p: p.stat().st_mtime)
    if not wavs:
        raise FileNotFoundError(f"audio-separator 未在 {dereverb_out} 产出 wav")

    out_wav = dereverb_out / "vocals_dereverb.wav"
    # audio-separator 可能产出多个 stem（如 vocals/instrumental），这里优先挑文件名包含 vocal 的
    preferred = [p for p in wavs if "vocal" in p.name.lower()]
    src = preferred[-1] if preferred else wavs[-1]
    if src.resolve() != out_wav.resolve():
        out_wav.write_bytes(src.read_bytes())

    dt = time.time() - t0
    print(f"✅ 去混响完成，用时 {dt:.1f}s")
    print(f"   input:  {vocals_wav}")
    print(f"   output: {out_wav}")
    return out_wav


def main() -> None:
    parser = argparse.ArgumentParser(description="人声分离 + 去混响（保留中间产物）")
    parser.add_argument("--input", required=True, help="输入音频（mp3/wav）")
    parser.add_argument(
        "--out-dir",
        default=str(Path("poc/audio/processed")),
        help="输出目录根路径（默认：poc/audio/processed）",
    )
    parser.add_argument(
        "--dereverb-model",
        default="dereverb_mel_band_roformer",
        help="audio-separator 去混响模型名（默认：dereverb_mel_band_roformer）",
    )

    args = parser.parse_args()

    input_audio = Path(args.input).expanduser().resolve()
    if not input_audio.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_audio}")

    out_root = Path(args.out_dir).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    job_dir = out_root / _safe_stem(input_audio.stem)
    job_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎛️  Vocal Processing Pipeline")
    print(f"input: {input_audio}")
    print(f"out:   {job_dir}")
    print("=" * 60)

    vocals, _no_vocals = demucs_separate(input_audio, job_dir)
    _ = dereverb_vocals(vocals, job_dir, model=args.dereverb_model)


if __name__ == "__main__":
    main()
