"""混合转换后人声与伴奏"""
from pydub import AudioSegment
from pathlib import Path

converted = Path("poc/output/seed_vc/vc_vocals_target_reference_1.0_10_0.7.wav")
accompaniment = Path("poc/output/demucs/htdemucs/source_voice/no_vocals.wav")
output = Path("poc/output/final_poc_a.mp3")

vocals = AudioSegment.from_wav(str(converted))
accomp = AudioSegment.from_wav(str(accompaniment))

# 对齐时长
target_len = max(len(vocals), len(accomp))
if len(accomp) < target_len:
    accomp = accomp + AudioSegment.silent(duration=target_len - len(accomp))
if len(vocals) < target_len:
    vocals = vocals + AudioSegment.silent(duration=target_len - len(vocals))

mixed = accomp.overlay(vocals)
output.parent.mkdir(parents=True, exist_ok=True)
mixed.export(str(output), format="mp3", bitrate="320k")
print(f"✅ 混合完成: {output} (时长: {len(mixed)/1000:.1f}s)")
