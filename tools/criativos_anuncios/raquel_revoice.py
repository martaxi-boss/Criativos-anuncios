#!/usr/bin/env python3
"""Revoice the approved Low Cost Europa explainer with Raquel pt-PT neural.

Strict private audition: original explanation, real word-level voice source,
no new promotional claims, no commercial distribution license implied.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

VOICE="pt-PT-RaquelNeural"
SAMPLE_RATE=44100

async def synthesize(request:dict,out:Path)->dict:
    import edge_tts
    lines=request.get("voice_sentences")
    if not isinstance(lines,list) or len(lines)!=6 or any(not isinstance(t,str) or len(t.strip())<15 for t in lines):
        raise ValueError("Six original explanatory paragraphs required")
    if request.get("publish") is not False or request.get("commercial_release") is not False:
        raise ValueError("Private preview only; commercial voice rights unconfirmed")
    out.mkdir(parents=True,exist_ok=True)
    slices=[]
    for i,line in enumerate(lines,1):
        raw=out/f"raquel_part_{i:02d}.mp3"
        await edge_tts.Communicate(line,VOICE,rate="-8%",pitch="+0Hz").save(str(raw))
        if not raw.is_file() or raw.stat().st_size<3500:
            raise RuntimeError(f"Raquel returned no audio for paragraph {i}")
        wav=out/f"raquel_part_{i:02d}.wav"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
                        "-ar",str(SAMPLE_RATE),"-ac","1","-c:a","pcm_s16le",str(wav)],
                       check=True,timeout=80)
        with wave.open(str(wav),"rb") as reader:
            if reader.getframerate()!=SAMPLE_RATE or reader.getnchannels()!=1 or reader.getsampwidth()!=2:
                raise RuntimeError("Unexpected Raquel audio format")
            chunks=reader.readframes(reader.getnframes())
            duration=reader.getnframes()/SAMPLE_RATE
        if not (1<=duration<=23):
            raise ValueError(f"Paragraph {i} duration out of range: {duration}")
        slices.append({"text":line,"data":chunks,"seconds":duration})
        print("RAQUEL_PARAGRAPH_PASS",i,round(duration,2),flush=True)
    intro=.42
    between=.55
    outro=1.08
    count=0
    paragraph_starts=[]
    full=out/"narracao_raquel_ptpt.wav"
    with wave.open(str(full),"wb") as writer:
        writer.setnchannels(1)
        writer.setframerate(SAMPLE_RATE)
        writer.setsampwidth(2)
        def silence(seconds:float):
            nonlocal count
            n=round(seconds*SAMPLE_RATE)
            writer.writeframes(b"\x00\x00"*n)
            count+=n
        silence(intro)
        for i,part in enumerate(slices):
            paragraph_starts.append(count/SAMPLE_RATE)
            writer.writeframes(part["data"])
            count+=len(part["data"])//2
            silence(between if i<len(slices)-1 else outro)
    total=count/SAMPLE_RATE
    if not 30<=total<=90:
        raise ValueError(f"Full Rui/Raquel explainer duration invalid {total}")
    mp3=out/"narracao_raquel_ptpt.mp3"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(full),
                    "-codec:a","libmp3lame","-b:a","192k",str(mp3)],
                   check=True,timeout=100)
    result={
        "id":request.get("id"),"status":"preview_only",
        "narrator":VOICE,"model_kind":"synthetic-neural",
        "voice_rate":"-8%","duration_seconds":round(total,3),
        "spoken_words":sum(len(t.split()) for t in lines),
        "paragraphs":[{"index":i,"text":part["text"],"start_seconds":round(paragraph_starts[i],3),
                       "speech_seconds":round(part["seconds"],3)}
                      for i,part in enumerate(slices)],
        "wav_sha256":hashlib.sha256(full.read_bytes()).hexdigest(),
        "mp3_sha256":hashlib.sha256(mp3.read_bytes()).hexdigest(),
        "published":False,"commercial_license_confirmed":False,
        "notes":"Raquel synthesis from Microsoft Edge Read Aloud; user-approved listening preview only."
    }
    (out/"raquel_timing.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("RAQUEL_FULL_EXPLAINER_PASS",total,"seconds",flush=True)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--request",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    args=p.parse_args()
    asyncio.run(synthesize(json.loads(args.request.read_text(encoding="utf-8")),args.output_dir))
if __name__=="__main__":
    main()
