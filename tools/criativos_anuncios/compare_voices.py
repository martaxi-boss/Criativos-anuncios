#!/usr/bin/env python3
"""A/B audio-only evaluation of European Portuguese TTS, private preview.

One factual script, two separately licensed synthetic voices. Never describe
either as recorded human speech or automatically publish advertising.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave

import numpy as np
import soundfile as sf

def validate(request: dict) -> list[str]:
    if request.get("publish") is not False or request.get("commercial_release") is not False:
        raise ValueError("A/B comparisons must be unpublished private previews")
    lines=request.get("sample_sentences")
    if not isinstance(lines,list) or not 2<=len(lines)<=5:
        raise ValueError("Provide 2-5 pt-PT sentences")
    if any(not isinstance(x,str) or not 8<=len(x.strip())<=210 for x in lines):
        raise ValueError("Invalid sample sentence")
    if sum(len(x.split()) for x in lines)>75:
        raise ValueError("Sample should remain under 75 words")
    return lines

def wav_metadata(path:Path) -> dict:
    x,sr=sf.read(path,dtype="float32")
    if x.ndim>1: x=x.mean(axis=1)
    peak=float(np.max(np.abs(x)))
    rms=float(np.sqrt(np.mean(x.astype(np.float64)**2)))
    duration=len(x)/sr
    if not (3<=duration<=65) or not (.002<=rms<=.6) or peak>1.0:
        raise ValueError(f"Invalid generated speech: {duration:.2f}s RMS {rms:.5f} peak {peak:.3f}")
    return {"sample_rate":sr,"duration_seconds":round(duration,3),
            "peak":round(peak,4),"rms":round(rms,4),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

def normalize_mp3(source:Path,target:Path):
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                    "-i",str(source),"-af","loudnorm=I=-18:TP=-2:LRA=11",
                    "-ar","44100","-ac","2","-c:a","libmp3lame","-q:a","3",str(target)],
                   check=True,timeout=85)
    if not target.is_file() or target.stat().st_size<8000:
        raise ValueError("MP3 output failed")

def kokoro_audio(lines:list[str],path:Path) -> None:
    from tts_eu_pt import TTS
    speaker=TTS()
    rate=24000
    chunks=[np.zeros(int(.28*rate),dtype=np.float32)]
    for i,sentence in enumerate(lines):
        samples=np.asarray(speaker.say(sentence),dtype=np.float32).reshape(-1)
        if samples.size<rate//3 or not np.isfinite(samples).all():
            raise ValueError("Kokoro produced empty/invalid speech")
        chunks.append(samples)
        chunks.append(np.zeros(int((.52 if i<len(lines)-1 else .52)*rate),
                               dtype=np.float32))
        print(f"KOKORO_PT_PT_PART={i+1}/{len(lines)} {len(samples)/rate:.2f}s",flush=True)
    sf.write(path,np.concatenate(chunks),rate,subtype="PCM_16")

def piper_audio(lines:list[str],work:Path,path:Path) -> None:
    from render import synthesize_voice
    work.mkdir(parents=True,exist_ok=True)
    data={"voice":{"model":"pt_PT-tugao-medium","sentences":lines,
                   "length_scale":1.17,"intro_pause_s":.28,
                   "between_pause_s":.52,"outro_pause_s":.52}}
    wav,_,_,duration=synthesize_voice(data,work,supplied=None)
    if duration<3: raise ValueError("Piper produced insufficient speech")
    shutil.copyfile(wav,path)

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--request",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    data=json.loads(args.request.read_text(encoding="utf-8"))
    lines=validate(data)
    output=args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    a=output/"A_Kokoro_PT_PT.wav"
    b=output/"B_Piper_PT_PT.wav"
    kokoro_audio(lines,a)
    piper_audio(lines,output/"piper_work",b)
    normalize_mp3(a,output/"A_Kokoro_PT_PT.mp3")
    normalize_mp3(b,output/"B_Piper_PT_PT.mp3")
    results={
        "status":"preview_only","source":"same original Lowcost Europa script",
        "voice_labels":{
            "A":{"model":"logus2k/kokoro_tts_eu_pt","kind":"synthetic",
                 "license":"Apache-2.0","audio":wav_metadata(a)},
            "B":{"model":"Piper pt_PT-tugao-medium","kind":"synthetic",
                 "license":"voice-specific review required","audio":wav_metadata(b)}
        },
        "sample_sentences":lines,"spoken_words":sum(len(x.split()) for x in lines),
        "published":False,"user_approval_pending":True,
        "comparison_note":"Same words; different model and natural phrase length. Listen for naturalness, pt-PT diction, emotional warmth and pacing.",
    }
    (output/"report.json").write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("VOICE_AB_SUCCESS",results["spoken_words"],
          results["voice_labels"]["A"]["audio"]["duration_seconds"],
          results["voice_labels"]["B"]["audio"]["duration_seconds"],flush=True)
if __name__=="__main__":
    main()
