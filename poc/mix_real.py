"""混合真实歌曲的转换人声与伴奏"""
from pydub import AudioSegment
from pathlib import Path

converted = Path("poc/output/real/seed_vc/vc_vocals_vocals_1.0_30_0.7.wav")
accompaniment = Path("poc/output/real/htdemucs/source/no_vocals.wav")
output = Path("poc/output/real/final_voice_replace.mp3")

print(f"转换人声: {converted}")
print(f"原伴奏: {accompaniment}")

vocals = AudioSegment.from_wav(str(converted))
accomp = AudioSegment.from_wav(str(accompaniment))

print(f"转换人声时长: {len(vocals)/1000:.1f}s")
print(f"伴奏时长: {len(accomp)/1000:.1f}s")

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
