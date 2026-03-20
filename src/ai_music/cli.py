"""AI Music CLI - 入口文件"""

import typer

app = typer.Typer(
    name="ai-music",
    help="🎵 AI 音乐处理 CLI 工具",
    no_args_is_help=True,
)

# --- 子命令组 ---
lrc_app = typer.Typer(help="LRC 歌词时间轴管理")
voice_app = typer.Typer(help="声音模型管理")
app.add_typer(lrc_app, name="lrc")
app.add_typer(voice_app, name="voice")


# --- LRC 命令 ---
@lrc_app.command("extract")
def lrc_extract(
    input: str = typer.Option(..., "--input", help="输入音频文件路径"),
    output: str = typer.Option("output.lrc", "--output", help="输出 LRC 文件路径"),
):
    """从音频文件自动提取 LRC 歌词时间轴"""
    typer.echo(f"🎤 正在从 {input} 提取 LRC...")
    typer.echo("⚠️  功能开发中")


@lrc_app.command("import")
def lrc_import(
    lrc: str = typer.Option(..., "--lrc", help="已有 LRC 文件路径"),
    output: str = typer.Option("output.lrc", "--output", help="输出 LRC 文件路径"),
):
    """导入并校验已有 LRC 文件"""
    typer.echo(f"📄 正在校验 {lrc}...")
    typer.echo("⚠️  功能开发中")


@lrc_app.command("preview")
def lrc_preview(
    lrc: str = typer.Option(..., "--lrc", help="LRC 文件路径"),
):
    """预览 LRC 文件内容"""
    typer.echo(f"👀 预览 {lrc}...")
    typer.echo("⚠️  功能开发中")


# --- Voice 命令 ---
@voice_app.command("preprocess")
def voice_preprocess(
    input: str = typer.Option(..., "--input", help="输入音频（mp3/wav）"),
    out_dir: str = typer.Option("poc/audio/processed", "--out-dir", help="输出目录根路径"),
    dereverb_model: str = typer.Option(
        "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt",
        "--dereverb-model",
        help=(
            "audio-separator 的 model_filename（默认：dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt，用于去混响/去回声；"
            "可用 audio-separator -l --list_filter dereverb 查看更多模型）"
        ),
    ),
):
    """人声预处理：Demucs 分离 + 去混响（保留中间产物）"""
    import subprocess
    import sys

    cmd = [
        sys.executable,
        "poc/audio/process_vocals.py",
        "--input",
        input,
        "--out-dir",
        out_dir,
        "--dereverb-model",
        dereverb_model,
    ]
    typer.echo(f"🎛️  运行：{' '.join(cmd)}")
    subprocess.check_call(cmd)


@voice_app.command("learn")
def voice_learn(
    name: str = typer.Option(..., "--name", help="声音模型名称"),
    ref: list[str] = typer.Option(..., "--ref", help="参考音频文件路径"),
):
    """学习并保存声音模型"""
    typer.echo(f"🎙️ 正在学习声音 '{name}'，参考音频: {ref}")
    typer.echo("⚠️  功能开发中")


@voice_app.command("list")
def voice_list():
    """列出所有已保存的声音模型"""
    typer.echo("📋 已保存的声音模型:")
    typer.echo("⚠️  功能开发中")


# --- 顶层命令 ---
@app.command("voice-replace")
def voice_replace(
    input: str = typer.Option(..., "--input", help="输入歌曲音频"),
    voice: str = typer.Option(..., "--voice", help="目标声音名称"),
    output: str = typer.Option("output.mp3", "--output", help="输出文件路径"),
):
    """替换歌曲中的人声音色"""
    typer.echo(f"🔄 声音替换: {input} → 使用声音 '{voice}'")
    typer.echo("⚠️  功能开发中")


@app.command("lyrics-generate")
def lyrics_generate(
    lyrics: str = typer.Option(..., "--lyrics", help="原歌词文件路径"),
    prompt: str = typer.Option(..., "--prompt", help="创作提示词"),
    output: str = typer.Option("new_lyrics.txt", "--output", help="输出歌词文件路径"),
):
    """基于原歌词结构生成新歌词"""
    typer.echo(f"✍️ 生成歌词: 结构来源={lyrics}, 主题={prompt}")
    typer.echo("⚠️  功能开发中")


@app.command("lyrics-replace")
def lyrics_replace(
    input: str = typer.Option(..., "--input", help="输入歌曲音频"),
    lyrics: str = typer.Option(..., "--lyrics", help="新歌词文件路径"),
    lrc: str = typer.Option(..., "--lrc", help="LRC 时间轴文件路径（必须）"),
    output: str = typer.Option("output.mp3", "--output", help="输出文件路径"),
):
    """替换歌曲歌词并重新合成"""
    typer.echo(f"🎵 歌词替换: {input} + {lyrics} + {lrc}")
    typer.echo("⚠️  功能开发中")


if __name__ == "__main__":
    app()
