"""
混合真实歌曲的转换人声与伴奏（带 RMS 音量匹配）

用法：
  python poc/sound-repalce-experiments/mix_real.py \
    --converted <seed_vc输出.wav> \
    --orig-vocals <原始人声.wav> \
    --accompaniment <伴奏.wav> \
    --output <输出.mp3>

示例（exp-03）：
  EXP02=poc/sound-repalce-experiments/exp-02-real-vc-no-vol-fix
  EXP03=poc/sound-repalce-experiments/exp-03-real-vc-rms-fix
  python poc/sound-repalce-experiments/mix_real.py \\
    --converted   $EXP02/intermediate/seed_vc/vc_output.wav \\
    --orig-vocals $EXP02/intermediate/demucs/source_vocals.wav \\
    --accompaniment $EXP02/intermediate/demucs/source_no_vocals.wav \\
    --output $EXP03/output/final_voice_replace_v2.mp3
"""
import argparse
from pydub import AudioSegment
from pathlib import Path


def match_rms(source: AudioSegment, reference: AudioSegment) -> AudioSegment:
    """将 source 的音量调整至与 reference 相同的 RMS 电平"""
    diff_db = reference.dBFS - source.dBFS
    print(f"   音量补偿: {diff_db:+.1f} dB（转换人声 {source.dBFS:.1f} dBFS → 目标 {reference.dBFS:.1f} dBFS）")
    return source + diff_db


def main():
    parser = argparse.ArgumentParser(description="混合转换人声与伴奏（带 RMS 音量匹配）")
    parser.add_argument("--converted",      required=True, help="seed-vc 转换输出人声 (.wav)")
    parser.add_argument("--orig-vocals",    required=True, help="原始人声（用于 RMS 参考）(.wav)")
    parser.add_argument("--accompaniment",  required=True, help="原始伴奏 (.wav)")
    parser.add_argument("--output",         required=True, help="输出文件路径 (.mp3)")
    args = parser.parse_args()

    converted   = Path(args.converted)
    orig_vocals = Path(args.orig_vocals)
    accompaniment = Path(args.accompaniment)
    output = Path(args.output)

    print(f"转换人声:       {converted}")
    print(f"原始人声（参考）: {orig_vocals}")
    print(f"原伴奏:          {accompaniment}")

    vocals = AudioSegment.from_wav(str(converted))
    orig_v = AudioSegment.from_wav(str(orig_vocals))
    accomp = AudioSegment.from_wav(str(accompaniment))

    print(f"\n混合前音量:")
    print(f"  转换后人声: {vocals.dBFS:.1f} dBFS")
    print(f"  原始人声:   {orig_v.dBFS:.1f} dBFS")
    print(f"  伴奏:       {accomp.dBFS:.1f} dBFS")

    # RMS 音量匹配：把转换人声的响度对齐到原始人声
    vocals = match_rms(vocals, orig_v)

    # 对齐时长（以伴奏为准）
    target_len = len(accomp)
    if len(vocals) < target_len:
        vocals = vocals + AudioSegment.silent(duration=target_len - len(vocals))
    else:
        vocals = vocals[:target_len]

    mixed = accomp.overlay(vocals)
    output.parent.mkdir(parents=True, exist_ok=True)
    mixed.export(str(output), format="mp3", bitrate="320k")
    print(f"\n✅ 完成！输出: {output}")
    print(f"   最终时长: {len(mixed)/1000:.1f}s")


if __name__ == "__main__":
    main()
