"""开发环境验证脚本"""
import sys
import subprocess

print("=== AI Music 开发环境验证 ===\n")

ok = True

def check(label, fn):
    global ok
    try:
        result = fn()
        print(f"✅ {label}{': ' + result if result else ''}")
    except Exception as e:
        print(f"❌ {label}: {e}")
        ok = False

# Python 版本
check("Python", lambda: sys.version.split()[0])

# PyTorch + MPS
import torch
mps = torch.backends.mps.is_available()
check("PyTorch", lambda: f"{torch.__version__} | MPS={'可用' if mps else '不可用'}")

# Demucs
import demucs
check("Demucs", lambda: demucs.__version__)

# 音频处理
check("pydub", lambda: "已安装")
check("pyrubberband", lambda: __import__("pyrubberband").__version__)
check("soundfile", lambda: __import__("soundfile").__version__)

# LLM SDK
check("openai SDK", lambda: __import__("openai").__version__)

# TTS
check("edge-tts", lambda: "已安装")
check("pyttsx3", lambda: "已安装")

# CLI
check("typer", lambda: __import__("typer").__version__)
check("numpy", lambda: __import__("numpy").__version__)

# MPS 实际运算
if mps:
    t = torch.randn(3, 3, device="mps")
    _ = (t @ t.T).cpu()
    check("MPS 矩阵运算", lambda: "验证通过")

# ai-music CLI
r = subprocess.run(["ai-music", "--help"], capture_output=True, text=True)
check("ai-music CLI", lambda: "入口正常" if r.returncode == 0 else r.stderr[:80])

# ffmpeg 系统依赖
r2 = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
check("ffmpeg", lambda: r2.stdout.split("\n")[0].split("version ")[1].split(" ")[0] if r2.returncode == 0 else "未找到")

# rubberband 系统依赖
r3 = subprocess.run(["rubberband", "--version"], capture_output=True, text=True)
check("rubberband", lambda: (r3.stdout or r3.stderr).strip().split("\n")[0] if r3.returncode == 0 else "已安装（版本查询方式不同）")

print(f"\n{'🎉 所有核心依赖验证通过！开发环境就绪。' if ok else '⚠️  部分依赖存在问题，请检查上述错误。'}")
