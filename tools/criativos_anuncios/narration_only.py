#!/usr/bin/env python3
"""Render approved Piper pt-PT narration independently of visual scene selection.

The host writes the site-specific copy. This action only voices it and returns
measured segment times, so real website footage can be edited to the speech.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from render import synthesize_voice

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--request",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    data=json.loads(args.request.read_text(encoding="utf-8"))
    slug=data.get("id")
    lines=data.get("voice_sentences")
    if not isinstance(slug,str) or not re.fullmatch(r"[a-zA-Z0-9_-]{5,70}",slug):
        raise ValueError("Safe narration ID required")
    if not isinstance(lines,list) or not 3<=len(lines)<=12:
        raise ValueError("Provide 3-12 verified Portuguese explanatory paragraphs")
    if any(not isinstance(x,str) or not 10<=len(x.strip())<=280 for x in lines):
        raise ValueError("Narration paragraph malformed")
    if sum(len(x.split()) for x in lines)>180:
        raise ValueError("Excessive script; use concise site-specific narration")
    if data.get("commercial_release") is not False or data.get("publish") is not False:
        raise ValueError("Only private preview, never automatically publish")
    voice_settings=data.get("voice_settings") or {}
    length_scale=float(voice_settings.get("length_scale",1.20))
    between=float(voice_settings.get("between_pause_s",.58))
    intro=float(voice_settings.get("intro_pause_s",.42))
    outro=float(voice_settings.get("outro_pause_s",1.05))
    for value,low,high in [(length_scale,1.0,1.30),(between,.3,.95),(intro,.2,1.2),(outro,.4,2.5)]:
        if not math.isfinite(value) or not low<=value<=high:
            raise ValueError("Piper pace/pauses outside approved range")
    output=args.output_dir
    work=output/"work"
    work.mkdir(parents=True,exist_ok=True)
    request={"voice":{"sentences":lines,"length_scale":length_scale,
                     "between_pause_s":between,"intro_pause_s":intro,
                     "outro_pause_s":outro}}
    wav,starts,parts,seconds=synthesize_voice(request,work,supplied=None)
    if not 30<=seconds<=85:
        raise ValueError(f"Explainer duration must be at least 30s and at most 85s: {seconds}")
    target=output/"narracao_ptpt.wav"
    shutil.copyfile(wav,target)
    manifest={
        "id":slug,"status":"preview_only","source_url":data.get("source_url"),
        "narrator":"Piper pt_PT-tugao-medium (synthetic voice)",
        "voice_length_scale":length_scale,"duration_seconds":round(seconds,3),
        "spoken_words":sum(len(x.split()) for x in lines),
        "paragraphs":[{"index":i,"text":x,"start_seconds":round(starts[i],3),
                       "duration_seconds":round(parts[i]["duration"],3) if isinstance(parts[i],dict) and "duration" in parts[i] else None}
                      for i,x in enumerate(lines)],
        "wav_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
        "approved_for_ads":False,"published":False
    }
    (output/"report.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PT_PT_NARRATION_PASS",slug,round(seconds,2),"s",manifest["spoken_words"],"words")
if __name__=="__main__":
    main()
