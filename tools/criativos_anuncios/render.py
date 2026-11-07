#!/usr/bin/env python3
"""Criativos-anuncios: safe, repeatable 9:16 advertisements using user-approved stills.

Purely local rendering except optional HTTPS fetches of publicly accessible media.
Every slide begins exactly at the start of a specified voice paragraph; visual
and audio QA fail closed. This tool NEVER publishes ads or changes a website.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import ipaddress
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageChops, ImageStat, ImageOps

MAX_MEDIA = 50 * 1024 * 1024
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_PT/tug%C3%A3o/medium/pt_PT-tug%C3%A3o-medium.onnx?download=true"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_PT/tug%C3%A3o/medium/pt_PT-tug%C3%A3o-medium.onnx.json"
MODEL_SHA256 = "223a7aaca69a155c61897e8ada7c3b13bc306e16c72dbb9c2fed733e2b0927d4"
BASE_DIR = Path(__file__).resolve().parents[2]


def run(cmd: list[str], *, input_text: str | None = None, timeout: int = 240, capture: bool = True) -> str:
    p = subprocess.run(cmd, input=input_text, text=True, capture_output=capture, timeout=timeout, check=False)
    if p.returncode:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd[0]}\n{(p.stderr or '')[-3500:]}")
    return p.stdout or ""


def checked_url(url: str) -> None:
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Only public HTTPS media URLs without credentials or custom ports are accepted")
    if any(c in url for c in "\r\n\t"):
        raise ValueError("Invalid media URL")
    host = p.hostname.rstrip(".")
    if host in {"localhost", "metadata.google.internal"} or host.endswith((".localhost", ".internal", ".local")):
        raise ValueError("Private host is not allowed")
    answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
        raise ValueError("Media URL resolves to a non-public address")


class CheckedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        checked_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def retrieve(url: str, dest: Path, max_bytes: int = MAX_MEDIA) -> None:
    checked_url(url)
    opener = urllib.request.build_opener(CheckedRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": "CriativosAnuncios/1.0 (media-asset-validation)"})
    with opener.open(request, timeout=65) as reply, dest.open("wb") as target:
        total = 0
        while True:
            chunk = reply.read(1024 * 256)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Asset exceeds {max_bytes} bytes")
            target.write(chunk)
    if dest.stat().st_size < 500:
        raise ValueError("Downloaded asset is unexpectedly small")


def validate_request(data: dict) -> tuple[list[dict], list[str], str]:
    if not isinstance(data, dict):
        raise ValueError("Request must be a JSON object")
    task_id = data.get("id", "")
    if not isinstance(task_id, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,60}", task_id):
        raise ValueError("id must be a safe short slug")
    if data.get("publish", False) is not False:
        raise ValueError("Publishing is not implemented; set publish=false")
    text = data.get("voice", {}).get("sentences", [])
    if not isinstance(text, list) or not (1 <= len(text) <= 24) or not all(isinstance(s, str) and 4 <= len(s.strip()) <= 700 for s in text):
        raise ValueError("Supply 1-24 approved voice sentences")
    scenes = data.get("scenes", [])
    evenly_timed = (data.get("source_capture") or {}).get("scene_timing") == "even"
    max_scenes = 18 if evenly_timed else 12
    if not isinstance(scenes, list) or not 2 <= len(scenes) <= max_scenes:
        raise ValueError(f"Supply 2-{max_scenes} scenes")
    consumed = 0
    sources = set()
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError(f"scene {index} is not an object")
        image_url = scene.get("image_url", "")
        captured = scene.get("capture_index")
        if captured is not None:
            if (not isinstance(data.get("source_capture"), dict) or
                    type(captured) is not int or captured != index+1 or image_url):
                raise ValueError(f"scene {index}: capture_index must match a generated site screenshot")
            source = ("capture", captured)
        else:
            if not isinstance(image_url, str) or not image_url.startswith("https://"):
                raise ValueError(f"scene {index} requires a HTTPS image_url or verified capture_index")
            source = ("url", image_url)
        if source in sources:
            raise ValueError(f"scene {index}: duplicated media")
        sources.add(source)
        if evenly_timed:
            if "voice_range" in scene:
                raise ValueError("Evenly timed auto-capture scenes must not assign voice ranges")
        else:
            indices = scene.get("voice_range")
            if not isinstance(indices, list) or len(indices) != 2 or any(type(v) is not int for v in indices):
                raise ValueError(f"scene {index}: voice_range must be [from, to]")
            start, end = indices
            if start != consumed or not start < end <= len(text):
                raise ValueError(f"scene {index}: voice ranges must be contiguous and cover the narration")
            consumed = end
    if not evenly_timed and consumed != len(text):
        raise ValueError("The final scene must cover the final voice sentence")
    music = data.get("music")
    if music is None:
        if not isinstance(data.get("source_capture"), dict):
            raise ValueError("Music source required for manually supplied adverts")
    else:
        if not isinstance(music, dict) or not isinstance(music.get("url"), str):
            raise ValueError("Valid music metadata required")
        if not music["url"].startswith("https://"):
            raise ValueError("A HTTPS music URL is required")
        if not isinstance(music.get("provenance", ""), str) or not music.get("provenance"):
            raise ValueError("Music provenance/licensing note required")
    if data.get("commercial_release") is not False:
        raise ValueError("Only private commercial_release=false test outputs are supported")
    return scenes, text, task_id


def verify_image(path: Path) -> None:
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        if im.width < 600 or im.height < 600:
            raise ValueError(f"Source photograph is too small: {path.name}, {im.size}")


def prepare_assets(data: dict, media: Path, *, cached: bool) -> list[Path]:
    scenes = data["scenes"]
    photos=[]
    for n,scene in enumerate(scenes, start=1):
        dest=media/f"scene_{n:02d}.png"
        if scene.get("capture_index") is not None:
            if not cached or not dest.is_file() or dest.is_symlink():
                raise ValueError("Missing verified site screenshot in private output folder")
        elif not cached or not dest.is_file():
            retrieve(scene["image_url"], dest, max_bytes=15 * 1024 * 1024)
        verify_image(dest)
        photos.append(dest)
    digests=[hashlib.sha256(p.read_bytes()).hexdigest() for p in photos]
    if len(set(digests)) != len(digests):
        raise ValueError("Source photographs must all be distinct")
    if data.get("music") is not None:
        music=media/"music_source.bin"
        if not cached or not music.is_file():
            retrieve(data["music"]["url"], music, max_bytes=MAX_MEDIA)
        probe=json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(music)]))
        if not any(s.get("codec_type")=="audio" for s in probe["streams"]):
            raise ValueError("Music source does not contain an audio stream")
    return photos


def voice_part(path: Path) -> tuple[bytes, int, float, float]:
    with wave.open(str(path), "rb") as source:
        sr=source.getframerate()
        channels=source.getnchannels()
        width=source.getsampwidth()
        n=source.getnframes()
        pcm=source.readframes(n)
    if channels!=1 or width!=2 or sr < 16000 or n < sr//3:
        raise ValueError(f"Invalid voice PCM {path.name}")
    samples=array.array("h")
    samples.frombytes(pcm)
    rms=math.sqrt(sum(v*v for v in samples) / max(1, len(samples)))
    if rms < 120:
        raise ValueError(f"Missing spoken voice in {path.name}: RMS={rms:.1f}")
    return pcm,sr,n/sr,rms


def synthesize_voice(data: dict, media: Path, *, supplied: Path | None) -> tuple[Path, list[float], list[dict], float]:
    voices=data["voice"]["sentences"]
    voice_dir=media/"voice_parts"
    voice_dir.mkdir(exist_ok=True)
    if supplied:
        for i in range(len(voices)):
            source=supplied/f"part_{i}.wav"
            if not source.is_file():
                raise ValueError(f"Missing pre-approved test voice part {i}")
            shutil.copyfile(source, voice_dir/f"part_{i}.wav")
    else:
        model=media/"pt_PT-tugao-medium.onnx"
        config=media/"pt_PT-tugao-medium.onnx.json"
        if not model.is_file():
            retrieve(MODEL_URL, model, max_bytes=125*1024*1024)
        if hashlib.sha256(model.read_bytes()).hexdigest()!=MODEL_SHA256:
            raise ValueError("Piper voice model checksum mismatch")
        if not config.is_file():
            retrieve(CONFIG_URL, config, max_bytes=10*1024*1024)
        if config.stat().st_size < 100:
            raise ValueError("Piper voice config invalid")
        length_scale=float(data.get("voice", {}).get("length_scale",1.0))
        if not (0.85 <= length_scale <= 1.3):
            raise ValueError("Piper length_scale must be between 0.85 and 1.30")
        piper=data.get("voice", {}).get("piper_bin") or str(Path(sys.executable).parent / "piper")
        for i,sentence in enumerate(voices):
            result=run([piper, "--model", str(model), "--config", str(config), "--length_scale", str(length_scale), "--output_file", str(voice_dir/f"part_{i}.wav")],input_text=sentence+"\n",timeout=90)
            print(f"Piper part {i+1}/{len(voices)}: {result[:90]}",flush=True)

    start_silence=float(data["voice"].get("intro_pause_s", .35))
    mid_silence=float(data["voice"].get("between_pause_s", .26))
    end_silence=float(data["voice"].get("outro_pause_s", .80))
    if not (0 <= start_silence <= 3 and .08 <= mid_silence <= 2 and 0 <= end_silence <= 3):
        raise ValueError("Narration pauses outside limits")
    pieces=[]
    rates=set()
    for i in range(len(voices)):
        piece=voice_part(voice_dir/f"part_{i}.wav")
        pieces.append(piece)
        rates.add(piece[1])
    if len(rates)!=1:
        raise ValueError("Narration segments have inconsistent sample rates")
    sr=pieces[0][1]
    speech_starts=[]
    voice_timing=[]
    cursor=start_silence
    wav_path=media/"voice_narration_ptpt.wav"
    with wave.open(str(wav_path),"wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sr)
        output.writeframes(b"\x00\x00"*round(sr*start_silence))
        for i,(pcm,_,duration,rms) in enumerate(pieces):
            speech_starts.append(cursor)
            output.writeframes(pcm)
            voice_timing.append({"segment":i,"start":round(cursor,4),"end":round(cursor+duration,4),"rms":round(rms,1),"text":voices[i]})
            cursor+=duration
            if i<len(voices)-1:
                output.writeframes(b"\x00\x00"*round(sr*mid_silence))
                cursor+=mid_silence
        output.writeframes(b"\x00\x00"*round(sr*end_silence))
        cursor+=end_silence
    with wave.open(str(wav_path),"rb") as result:
        full_duration=result.getnframes()/sr
    return wav_path,speech_starts,voice_timing,full_duration


def make_video(photos: list[Path], voices: list[dict], data: dict, voice_file: Path, starts: list[float], total: float, media: Path, output: Path, *, fps: int = 25) -> list[float]:
    # Automatic campaigns may have more visual shots than spoken phrases.
    # Legacy manually supplied ads retain paragraph-synced scene cuts.
    if (data.get("source_capture") or {}).get("scene_timing") == "even":
        scene_boundaries=[total*i/len(photos) for i in range(len(photos)+1)]
    else:
        scene_boundaries=[0.0]
        for scene in data["scenes"][1:]:
            scene_boundaries.append(starts[scene["voice_range"][0]])
        scene_boundaries.append(total)
    if not all(b>a+0.6 for a,b in zip(scene_boundaries,scene_boundaries[1:])):
        raise ValueError("Too many visual scenes for actual spoken clip duration")
    widths=[scene_boundaries[i+1]-scene_boundaries[i] for i in range(len(photos))]
    args=["ffmpeg", "-hide_banner", "-y", "-loglevel", "error", "-nostdin"]
    for image,sec in zip(photos,widths):
        args.extend(["-loop","1","-framerate",str(fps),"-t",f"{sec:.5f}","-i",str(image)])
    has_music=(media/"music_source.bin").is_file()
    if has_music:
        args.extend(["-stream_loop","-1","-i",str(media/"music_source.bin")])
    args.extend(["-i",str(voice_file)])
    f=[]
    editorial=(data.get("source_capture") or {}).get("visuals") == "authentic_editorial_composition"
    for i,duration in enumerate(widths):
        # Genuine product elements receive a restrained 3% motion treatment.
        # No aggressive zoom on the original site hero or final real-brand CTA.
        scale="scale=864:1536:force_original_aspect_ratio=decrease,pad=864:1536:(ow-iw)/2:(oh-ih)/2:color=0x103c32"
        speed="0.00026" if editorial and 1 <= i <= 3 else "0.000025"
        cap="1.033" if editorial and 1 <= i <= 3 else "1.011"
        zoom=f"zoompan=z='min(zoom+{speed},{cap})':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=864x1536:fps=25"
        f.append(f"[{i}:v]{scale},format=rgb24,{zoom},trim=duration={duration:.5f},setpts=PTS-STARTPTS,fps={fps},settb=AVTB,format=yuv420p[v{i}]")
    concatenated="".join(f"[v{i}]" for i in range(len(photos)))
    f.append(f"{concatenated}concat=n={len(photos)}:v=1:a=0[video]")
    voice_index=len(photos)+(1 if has_music else 0)
    if has_music:
        music_index=len(photos)
        f.append(f"[{music_index}:a:0]aresample=44100,aformat=channel_layouts=stereo,volume=0.18,atrim=duration={total:.5f},asetpts=PTS-STARTPTS[music]")
    f.append(f"[{voice_index}:a:0]aresample=44100,aformat=channel_layouts=stereo,volume=1.0,atrim=duration={total:.5f},asetpts=PTS-STARTPTS[voice]")
    if has_music:
        f.append("[music][voice]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[sound]")
    else:
        f.append("[voice]alimiter=limit=0.95[sound]")
    args.extend(["-filter_complex",";".join(f),"-map","[video]","-map","[sound]","-c:v","libx264","-preset","medium" if editorial else "veryfast","-crf","18" if editorial else "21","-pix_fmt","yuv420p","-r",str(fps),"-c:a","aac","-b:a","192k","-ar","44100","-t",f"{total:.5f}","-movflags","+faststart",str(output)])
    run(args,timeout=360)
    return scene_boundaries


def verify_output(video: Path, images: list[Path], cuts: list[float], media: Path) -> dict:
    meta=json.loads(run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height:format=duration,size","-of","json",str(video)]))
    streams=meta.get("streams",[])
    assert any(s.get("codec_type")=="audio" for s in streams), "Missing final audio"
    assert any(s.get("codec_type")=="video" and s.get("width")==864 and s.get("height")==1536 for s in streams), "Invalid final video resolution"
    video_length=float(meta["format"]["duration"])
    if abs(video_length-cuts[-1])>0.22:
        raise ValueError(f"Video/audio lengths out of sync: {video_length} vs {cuts[-1]}")
    previews=[]
    for i,img in enumerate(images):
        position=(cuts[i]+cuts[i+1])/2
        proof=media/f"proof_scene_{i+1:02d}.jpg"
        run(["ffmpeg","-hide_banner","-y","-loglevel","error","-ss",f"{position:.3f}","-i",str(video),"-frames:v","1","-q:v","3",str(proof)],timeout=35)
        with Image.open(proof) as im:
            sample=ImageOps.fit(im.convert("RGB"),(162,288))
        expected=[]
        for ref in images:
            with Image.open(ref) as original:
                expected.append(ImageOps.contain(original.convert("RGB"),(162,288),method=Image.Resampling.BICUBIC))
        # User-supplied 9:16 images should be the closest matches at their own midpoints.
        scores=[]
        for e in expected:
            if e.size!=(162,288):
                # Correct for source not matching video aspect; preserved without cropping.
                canvas=Image.new("RGB",(162,288),(16,60,50))
                canvas.paste(e,((162-e.width)//2,(288-e.height)//2))
                e=canvas
            d=ImageChops.difference(sample,e)
            scores.append(sum(ImageStat.Stat(d).mean)/3)
        if min(range(len(scores)),key=scores.__getitem__)!=i:
            raise ValueError(f"Scene {i+1} appears missing/misordered; scores={scores}")
        previews.append(sample)
    sheet=Image.new("RGB",(162*len(previews),288))
    for i,thumb in enumerate(previews):
        sheet.paste(thumb,(162*i,0))
    sheet.save(media/"qa_five_scenes.jpg",quality=90)
    return {"duration":video_length,"distinct_scenes_verified":len(images),"voice_segments_confirmed":True,"has_audio_stream":True,"frames_checked_at_midpoints":len(images),"video_resolution":"864x1536","artifact_bytes":video.stat().st_size}


def main() -> None:
    parser=argparse.ArgumentParser(description="Make a multi-photo PT-PT advertisement with automatic voice timing and QA")
    parser.add_argument("--request",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--cached-assets",action="store_true",help="Use preloaded scene_NN.png and music_source.bin, mainly for unit tests")
    parser.add_argument("--voice-parts-dir",type=Path,help="Reuse approved part_0.wav etc, mainly for QA without TTS download")
    args=parser.parse_args()
    data=json.loads(args.request.read_text(encoding="utf-8"))
    scenes,text,slug=validate_request(data)
    folder=args.output_dir.resolve()
    folder.mkdir(parents=True,exist_ok=True)
    media=folder/"work"
    media.mkdir(exist_ok=True)
    photos=prepare_assets(data,media,cached=args.cached_assets)
    voice,starts,details,seconds=synthesize_voice(data,media,supplied=args.voice_parts_dir)
    output=folder/f"{slug}.mp4"
    bounds=make_video(photos,details,data,voice,starts,seconds,media,output)
    report=verify_output(output,photos,bounds,media)
    timeline={"id":slug,"voice_model":"pt_PT-tugao-medium","voice_length_scale":float(data["voice"].get("length_scale",1.0)),"spoken_words":sum(len(s.split()) for s in data["voice"]["sentences"]),"source_capture":data.get("source_capture"),"approval_state":"preview_only" if data.get("source_capture") else "owner_review_required","scenes":[{"scene":i+1,"voice_range":x.get("voice_range"),"starts_at":round(bounds[i],3),"ends_at":round(bounds[i+1],3),"image_source":x.get("image_url") or f"captured_scene_{x.get('capture_index',0):02d}"}for i,x in enumerate(scenes)],"speech":details,"qa":report,"published":False,"commercial_rights_checked":False}
    (folder/"report.json").write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding="utf-8")
    shutil.copyfile(voice,folder/"voice_ptpt.wav")
    shutil.copyfile(media/"qa_five_scenes.jpg",folder/"preview_scenes.jpg")
    print("COMPLETE",str(output),"VOICE_VERIFIED",len(details),"SCENES_VERIFIED",len(photos),"DURATION",round(seconds,2),flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print(f"UGC_RENDER_FAILED: {error}",file=sys.stderr,flush=True)
        raise
