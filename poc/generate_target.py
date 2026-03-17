"""生成 PoC-A 测试用参考音频（target）"""
import asyncio
import edge_tts

async def generate():
    # 用一段中文语音作为目标音色参考（约 15 秒）
    text = (
        "春风又绿江南岸，明月何时照我还。"
        "床前明月光，疑是地上霜，举头望明月，低头思故乡。"
        "白日依山尽，黄河入海流，欲穷千里目，更上一层楼。"
    )
    communicate = edge_tts.Communicate(text, voice="zh-CN-YunxiNeural")
    await communicate.save("poc/audio/target_reference.wav")
    print("✅ 参考音频已生成: poc/audio/target_reference.wav")

asyncio.run(generate())
