"""验证 whisperx 和 seed-vc 依赖"""
print("=== 验证 whisperx & seed-vc 依赖 ===\n")

def check(name, fn):
    try:
        result = fn()
        print(f"✅ {name}{': ' + str(result) if result else ''}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

# whisperx
check("whisperx", lambda: __import__("whisperx") and "已安装")

# seed-vc 核心依赖
check("librosa", lambda: __import__("librosa").__version__)
check("transformers", lambda: __import__("transformers").__version__)
check("accelerate", lambda: __import__("accelerate").__version__)
check("hydra-core", lambda: __import__("hydra") and "已安装")
check("munch", lambda: __import__("munch").__version__)
check("scipy", lambda: __import__("scipy").__version__)
check("sounddevice", lambda: __import__("sounddevice").__version__)
check("resemblyzer", lambda: __import__("resemblyzer") and "已安装")
check("huggingface_hub", lambda: __import__("huggingface_hub").__version__)
check("descript_audio_codec", lambda: __import__("dac") and "已安装")

print("\n✅ 关键依赖验证完毕")
