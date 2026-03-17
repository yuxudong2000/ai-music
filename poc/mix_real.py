"""混合真实歌曲的转换人声与伴奏（带 RMS 音量匹配）"""
from pydub import AudioSegment
from pathlib import Path


def match_rms(source: AudioSegment, reference: AudioSegment) -> AudioSegment:
    """将 source 的音量调整至与 reference 相同的 RMS 电平"""
    diff_db = reference.dBFS - source.dBFS
    print(f"   音量补偿: {diff_db:+.1f} dB（转换人声 {source.dBFS:.1f} dB → 目标 {reference.dBFS:.1f} dB）")
    return source + diff_db


converted   = Path("poc/output/real/seed_vc/vc_vocals_vocals_1.0_30_0.7.wav")
orig_vocals = Path("poc/output/real/htdemucs/source/vocals.wav")   # 用于 RMS 参考
accompaniment = Path("poc/output/real/htdemucs/source/no_vocals.wav")
output = Path("poc/output/real/final_voice_replace_v2.mp3")

print(f"转换人声: {converted}")
print(f"原始人声（RMS参考）: {orig_vocals}")
print(f"原伴奏: {accompaniment}")

vocals     = AudioSegment.from_wav(str(converted))
orig_v     = AudioSegment.from_wav(str(orig_vocals))
accomp     = AudioSegment.from_wav(str(accompaniment))

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
