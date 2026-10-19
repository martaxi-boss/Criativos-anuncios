#!/usr/bin/env python3
"""Remux approved narration and licensed music into an existing MP4.

Requires ffmpeg/ffprobe. Optionally requires Piper TTS CLI and an ONNX voice.
No remote services, tokens, cookies, web requests, or paid API calls.
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command, input_text=None):
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    return float(run(cmd).stdout.strip())


def video_hash(path):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-c:v", "copy", "-f", "hash", "-hash", "SHA256", "-"]
    return run(cmd).stdout.strip()


def must_exist(path, label):
    p = Path(path).resolve()
    if not p.is_file():
        raise ValueError(f"Falta {label}: {p}")
    return p


def main():
    ap = argparse.ArgumentParser(description="Adicionar locucao e musica a um MP4, sem alterar as imagens.")
    ap.add_argument("--video", required=True, help="MP4 existente")
    ap.add_argument("--music", required=True, help="Faixa de musica licenciada, ficheiro local")
    ap.add_argument("--license-note", required=True, help="Origem/licenca comprovada da musica, ex: 'Mixkit, titulo, URL, data'")
    ap.add_argument("--voice-wav", help="Narracao gravada/aprovada, WAV")
    ap.add_argument("--text-file", help="Texto UTF-8 para gerar locucao com Piper")
    ap.add_argument("--piper-model", help="Modelo Piper .onnx de pt-PT")
    ap.add_argument("--output", required=True, help="MP4 de saida")
    ap.add_argument("--voice-delay-ms", type=int, default=600)
    ap.add_argument("--voice-end-padding", type=float, default=0.7)
    ap.add_argument("--music-gain", type=float, default=0.16, help="Amplitude linear da musica (0..1), padrao aprox -16 dB")
    args = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        ap.error("Sao necessarios ffmpeg e ffprobe no runtime.")
    if bool(args.voice_wav) == bool(args.text_file):
        ap.error("Indica OU --voice-wav OU --text-file (apenas um).")
    if args.text_file and not args.piper_model:
        ap.error("--text-file requer --piper-model.")
    if args.voice_delay_ms < 0 or args.voice_end_padding < 0:
        ap.error("Pausa e margem nao podem ser negativas.")
    if not 0.0 <= args.music_gain <= 1.0:
        ap.error("--music-gain deve estar entre 0 e 1.")
    if not args.license_note.strip():
        ap.error("Indica a origem e prova da licenca da faixa de musica.")

    video = must_exist(args.video, "video")
    music = must_exist(args.music, "musica")
    output = Path(args.output).resolve()
    if output in (video, music):
        ap.error("O ficheiro de saida deve ser diferente dos de entrada.")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="viral_ugc_audio_") as tmp:
        if args.voice_wav:
            voice = must_exist(args.voice_wav, "WAV da locucao")
        else:
            if not shutil.which("piper"):
                ap.error("Piper TTS nao esta instalado; instala piper-tts num ambiente isolado.")
            model = must_exist(args.piper_model, "modelo Piper")
            content = must_exist(args.text_file, "ficheiro de texto").read_text(encoding="utf-8").strip()
            if not content:
                ap.error("O texto para locucao esta vazio.")
            voice = Path(tmp) / "voice.wav"
            run(["piper", "--model", str(model), "--output_file", str(voice)], input_text=content + "\n")
            must_exist(voice, "WAV gerado por Piper")

        vd = duration(video)
        ad = duration(voice)
        available = vd - args.voice_delay_ms / 1000 - args.voice_end_padding
        if ad > available:
            ap.error(
                f"Narracao demasiado longa ({ad:.1f}s) para o video ({vd:.1f}s). "
                f"Disponivel: {available:.1f}s. Resumir texto, nao acelerar fala."
            )
        if vd <= 2.5:
            ap.error("Video demasiado curto para mistura sonora segura.")

        # Preserve exact encoded video bytes, change only audio. No infinite generators or paid calls.
        fade_at = max(0.0, vd - 1.2)
        filt = (
            f"[1:a:0]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={args.voice_delay_ms}:all=1,volume=1.0[vo];"
            f"[2:a:0]aresample=48000,aformat=channel_layouts=stereo,"
            f"volume={args.music_gain:.3f},atrim=duration={vd:.4f},"
            f"afade=t=in:st=0:d=0.5,afade=t=out:st={fade_at:.4f}:d=1.2[mu];"
            "[vo][mu]amix=inputs=2:duration=longest:normalize=0,"
            "loudnorm=I=-16:TP=-1.5:LRA=10[a]"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video), "-i", str(voice), "-stream_loop", "-1", "-i", str(music),
            "-filter_complex", filt,
            "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-t", f"{vd:.4f}", "-movflags", "+faststart", str(output),
        ]
        try:
            run(cmd)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Falhou ffmpeg: {e.stderr[-1200:]}") from e

        od = duration(output)
        if abs(od - vd) > 0.6:
            raise RuntimeError(f"Duracao errada: entrada {vd:.2f}s, saida {od:.2f}s")
        if video_hash(video) != video_hash(output):
            raise RuntimeError("A faixa de video foi alterada! Rejeitar resultado")
        print(f"MP4 verificado: {output} | {vd:.2f}s | video preservado (SHA256)")
        print("Licenca da musica declarada:", args.license_note)
        print("AVISO: verificacao tecnica nao substitui avaliacao auditiva nem valida licenca comercial")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("ERRO:", exc, file=sys.stderr)
        sys.exit(2)
