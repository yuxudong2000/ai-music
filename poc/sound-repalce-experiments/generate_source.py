"""生成 PoC-A 测试用源音频（source，模拟歌声）"""
import asyncio
import edge_tts

async def generate():
    # 用另一个声音生成 source，模拟"被替换的原唱"
    text = (
        "离人愁，流水绕孤舟，凉风起，心如浮萍走。"
        "长相思，在长安，络纬秋啼金井阑。"
        "微微风簇浪，散作满河星。"
        "月出惊山鸟，时鸣春涧中。"
    )
    # 用不同声音（女声）模拟原唱
    communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save("poc/audio/source_voice.wav")
    print("✅ 源音频（模拟人声）已生成: poc/audio/source_voice.wav")

asyncio.run(generate())
