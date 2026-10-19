#!/usr/bin/env python3
"""Automated no-credit pt-PT Piper narration over an existing video's soundtrack.

First run downloads official Piper 1.2.0 Linux binary and pt_PT-tugao-medium model.
No authentication, API credits or browser cookies. All original video packets retained.
Commercial publication requires validation of model, music, and visual licenses.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import tempfile
import urllib.request

VOICE_BASE = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_PT/tug%C3%A3o/medium/'
MODEL_NAME = 'pt_PT-tug%C3%A3o-medium.onnx'
MODEL_SHA256 = '223a7aaca69a155c61897e8ada7c3b13bc306e16c72dbb9c2fed733e2b0927d4'
PIPER_RELEASE = 'https://github.com/rhasspy/piper/releases/download/v1.2.0/'


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'viral-ugc-chatgpt/0.1.4'})
        with urllib.request.urlopen(req, timeout=90) as inp, tmp.open('wb') as out:
            while chunk := inp.read(1024 * 1024):
                out.write(chunk)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def execute(command, **kwargs):
    return subprocess.run(command, check=True, capture_output=True, text=True, **kwargs)


def video_md5(ffmpeg, source):
    return execute([ffmpeg, '-v', 'error', '-i', str(source), '-map', '0:v:0',
                    '-c:v', 'copy', '-f', 'md5', '-']).stdout.strip()


def main():
    p = argparse.ArgumentParser(description='Gera locucao neural pt-PT e monta video mantendo as imagens')
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--text', type=Path, required=True, help='Texto narrado UTF-8')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cache', type=Path, default=Path.home() / '.cache/viral-ugc-piper')
    p.add_argument('--piper-path', type=Path, help='Opcional: executavel Piper ja instalado')
    p.add_argument('--ffmpeg', default='ffmpeg')
    p.add_argument('--voice-delay-ms', type=int, default=1000)
    p.add_argument('--music-gain', type=float, default=0.18)
    a = p.parse_args()
    if not a.video.is_file() or not a.text.is_file():
        p.error('Video ou texto em falta')
    if not (0 <= a.voice_delay_ms <= 15000 and 0 <= a.music_gain <= 1):
        p.error('Valores de atraso/volume invalidos')
    a.cache.mkdir(parents=True, exist_ok=True)
    arch = {'x86_64': 'piper_amd64.tar.gz', 'aarch64': 'piper_arm64.tar.gz'}.get(platform.machine())
    if not arch and not a.piper_path:
        p.error('Arquitetura nao suportada: instalar Piper manualmente e usar --piper-path')
    binary = a.piper_path or a.cache / 'piper/piper'
    if not binary.is_file():
        archive = a.cache / arch
        if not archive.is_file():
            download(PIPER_RELEASE + arch, archive)
        with tarfile.open(archive) as tar:
            for item in tar.getmembers():
                path = (a.cache / item.name).resolve()
                if not path.is_relative_to(a.cache.resolve()) or item.issym() or item.islnk():
                    raise RuntimeError('Arquivo do Piper com caminhos nao permitidos')
            tar.extractall(a.cache, filter='data')
    model = a.cache / 'pt_PT-tugao-medium.onnx'
    config = a.cache / 'pt_PT-tugao-medium.onnx.json'
    if not model.is_file() or sha256_file(model) != MODEL_SHA256:
        download(VOICE_BASE + MODEL_NAME, model)
    if sha256_file(model) != MODEL_SHA256:
        raise RuntimeError('O hash SHA256 do modelo nao coincide')
    if not config.is_file():
        download(VOICE_BASE + MODEL_NAME + '.json', config)
    if not json.loads(config.read_text('utf-8')).get('audio'):
        raise RuntimeError('Configuracao de voz invalida')
    text = a.text.read_text('utf-8').strip()
    if not text:
        p.error('Texto vazio')
    with tempfile.TemporaryDirectory(prefix='ugc-piper-') as td:
        voice = Path(td) / 'voice.wav'
        env = os.environ.copy()
        if not a.piper_path:
            env['LD_LIBRARY_PATH'] = str(binary.parent) + ':' + env.get('LD_LIBRARY_PATH', '')
        subprocess.run([str(binary), '--model', str(model), '--config', str(config),
                        '--output_file', str(voice)], input=text + '\n', text=True,
                       env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        probe = execute(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'default=noprint_wrappers=1:nokey=1', str(a.video)]).stdout
        total = float(probe.strip())
        vlen = execute(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', str(voice)]).stdout
        if float(vlen.strip()) + a.voice_delay_ms/1000 > total - .7:
            raise RuntimeError('Locucao demasiado longa: resumir texto; nao acelerar voz')
        filt = (f'[0:a:0]volume={a.music_gain},afade=t=out:st={max(0,total-1.4):.3f}:d=1.3[m];'
                f'[1:a:0]aresample=44100,aformat=channel_layouts=stereo,'
                f'adelay={a.voice_delay_ms}:all=1,volume=1.3[v];'
                '[m][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.94[a]')
        a.output.parent.mkdir(parents=True, exist_ok=True)
        execute([a.ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(a.video),
                 '-i', str(voice), '-filter_complex', filt, '-map', '0:v:0', '-map', '[a]',
                 '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(total),
                 '-movflags', '+faststart', str(a.output)])
    if video_md5(a.ffmpeg, a.video) != video_md5(a.ffmpeg, a.output):
        raise RuntimeError('Falha: pacotes de video foram alterados')
    print(f'OK: {a.output}; {total:.2f}s; video original preservado; voz pt-PT gerada')
    print('TESTE: validar naturalidade ao ouvir e direitos musicais antes de publicar publicidade')


if __name__ == '__main__':
    main()
