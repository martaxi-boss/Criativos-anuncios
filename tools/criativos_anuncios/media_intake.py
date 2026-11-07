#!/usr/bin/env python3
"""Offline intake of user-supplied photo/video media for professional ads.

Runs only with user-authorized local files in the current private workspace.
Not a remote URL fetcher, social downloader, automatic classifier or publisher.
Video files are sampled into authentic candidate frames; motion editing is a
separate operation. The ChatGPT creative director examines the contact sheet,
writes source-grounded copy, and selects frames before an MP4 is rendered.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont

IMAGES={".png",".jpg",".jpeg",".webp"}
VIDEOS={".mp4",".mov",".m4v",".webm"}
MAX_INPUT=24
MAX_IMAGE_SIZE=30*1024*1024
MAX_VIDEO_SIZE=350*1024*1024
MAX_DURATION_SECONDS=1800
FRAME_SIZE=(864,1536)

def _command(command: list[str],timeout:int=90) -> bytes:
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=timeout,check=False)
    if result.returncode:
        raise ValueError("Media probe/extraction failed: "+result.stderr.decode("utf-8","replace")[-700:])
    return result.stdout

def sha256(path:Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def _image(path:Path) -> Image.Image:
    with Image.open(path) as raw:
        if raw.width<320 or raw.height<240 or raw.width*raw.height>70_000_000:
            raise ValueError("Image dimensions unsuitable for an advertisement")
        raw.verify()
    with Image.open(path) as raw:
        return ImageOps.exif_transpose(raw).convert("RGB")

def _frame_image(source:Image.Image) -> Image.Image:
    fitted=ImageOps.contain(source,FRAME_SIZE,method=Image.Resampling.LANCZOS)
    canvas=Image.new("RGB",FRAME_SIZE,(239,243,240))
    canvas.paste(fitted,((FRAME_SIZE[0]-fitted.width)//2,
                         (FRAME_SIZE[1]-fitted.height)//2))
    return canvas

def _probe_video(path:Path) -> dict:
    data=json.loads(_command([
        "ffprobe","-v","error","-show_streams","-show_format","-of","json",
        str(path)
    ]))
    streams=[s for s in data.get("streams",[]) if s.get("codec_type")=="video"]
    if not streams:
        raise ValueError("Video has no video stream")
    video=streams[0]
    duration=float(data.get("format",{}).get("duration") or video.get("duration") or 0)
    width=int(video.get("width") or 0)
    height=int(video.get("height") or 0)
    if (not math.isfinite(duration) or not 0.3<=duration<=MAX_DURATION_SECONDS
            or not 320<=width<=7680 or not 240<=height<=4320):
        raise ValueError("Video duration/resolution outside intake limits")
    return {"duration_seconds":round(duration,3),"width":width,"height":height,
            "codec":video.get("codec_name","unknown"),
            "has_audio":any(s.get("codec_type")=="audio" for s in data.get("streams",[]))}

def _safe_file(path:Path) -> tuple[Path,str]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Input must be a regular, non-symlink local file")
    ext=path.suffix.lower()
    if ext not in IMAGES|VIDEOS:
        raise ValueError("Only PNG/JPG/WEBP photos and MP4/MOV/WEBM videos are supported")
    max_bytes=MAX_IMAGE_SIZE if ext in IMAGES else MAX_VIDEO_SIZE
    if not 500<=path.stat().st_size<=max_bytes:
        raise ValueError("Input size outside supported limits")
    return path,("photo" if ext in IMAGES else "video")

def inspect_media(paths:list[Path],output:Path,max_frames_per_video:int=4) -> dict:
    if not paths or len(paths)>MAX_INPUT:
        raise ValueError("Supply 1-24 local photos/videos")
    if not 2<=max_frames_per_video<=8:
        raise ValueError("Extract 2-8 source frames per video")
    if output.is_symlink():
        raise ValueError("Output cannot be a symlink")
    output.mkdir(parents=True,exist_ok=True)
    work=output/"work"
    work.mkdir(exist_ok=True)
    candidates=[]
    inputs=[]
    fingerprints=set()
    for source_index,item in enumerate(paths):
        file,kind=_safe_file(Path(item))
        fingerprint=sha256(file)
        if fingerprint in fingerprints:
            raise ValueError("Duplicated source media")
        fingerprints.add(fingerprint)
        probe=None
        if kind=="photo":
            originals=[(_image(file),None)]
            with Image.open(file) as raw:
                probe={"width":raw.width,"height":raw.height}
        else:
            probe=_probe_video(file)
            originals=[]
            for frame_index in range(max_frames_per_video):
                pos=probe["duration_seconds"]*(frame_index+1)/(max_frames_per_video+1)
                frame=_command([
                    "ffmpeg","-hide_banner","-loglevel","error","-ss",f"{pos:.3f}",
                    "-i",str(file),"-frames:v","1","-f","image2pipe","-vcodec","png","-"
                ],timeout=70)
                with Image.open(io.BytesIO(frame)) as still:
                    originals.append((still.convert("RGB"),round(pos,3)))
        inputs.append({"source_index":source_index,"source_type":kind,
                       "name":file.name,"sha256":fingerprint,
                       "bytes":file.stat().st_size,"technical":probe})
        for im,at in originals:
            asset_number=len(candidates)+1
            picture=_frame_image(im)
            name=f"scene_{asset_number:02d}.png"
            picture.save(work/name,optimize=True)
            candidates.append({
                "candidate_id":f"media-{asset_number:02d}",
                "capture_index":asset_number,
                "source_index":source_index,
                "source_type":kind,
                "origin_name":file.name,
                "origin_sha256":fingerprint,
                "frame_time_seconds":at,
                "staged_image":name,
                "staged_sha256":sha256(work/name),
                "rights":"owner_review_required",
                "description":None,
                "speech_claim_supported":None
            })
    if len(candidates)>80:
        raise ValueError("Too many candidate images in one intake")
    columns=min(4,len(candidates))
    thumb_w,thumb_h=192,342
    rows=math.ceil(len(candidates)/columns)
    sheet=Image.new("RGB",(columns*thumb_w,rows*(thumb_h+38)),(246,246,243))
    draw=ImageDraw.Draw(sheet)
    for i,candidate in enumerate(candidates):
        x=(i%columns)*thumb_w
        y=(i//columns)*(thumb_h+38)
        with Image.open(work/candidate["staged_image"]) as picture:
            thumb=ImageOps.fit(picture.convert("RGB"),(thumb_w,thumb_h),
                               method=Image.Resampling.BICUBIC)
        sheet.paste(thumb,(x,y))
        draw.text((x+8,y+thumb_h+8),candidate["candidate_id"],fill=(20,65,56))
    sheet.save(output/"media_candidates.jpg",quality=85)
    status={
      "intake_version":1,
      "mode":"local_authorized_media",
      "source_types":sorted({x["source_type"] for x in inputs}),
      "inputs":inputs,"candidates":candidates,
      "media_private":True,"upload_to_public_github":False,
      "rights_status":"owner_review_required",
      "editorial_stage":"AI_analysis_and_storyboard_required",
      "preview_extraction":"video candidate frames are not continuous video clips",
      "suggested_workflow":"AI analyzes photos/video frames -> writes script -> maps scene indices to spoken phrases -> renders a preview -> reviews"
    }
    (output/"intake_manifest.json").write_text(
        json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return status

def render_request(intake:dict, storyboard:dict, output:Path) -> dict:
    """Convert AI-authored copy/selected candidate IDs to the existing renderer.

    The intake itself does NOT invent advertising claims or pretend to know a
    photographed product. The AI host must inspect the evidence and write copy.
    """
    if intake.get("mode")!="local_authorized_media":
        raise ValueError("Only verified local intake manifests are allowed")
    lines=storyboard.get("voice_sentences")
    shots=storyboard.get("shots")
    if not isinstance(lines,list) or not 2<=len(lines)<=18 or not all(
         isinstance(s,str) and 4<=len(s.strip())<=170 for s in lines):
        raise ValueError("AI-authored pt-PT voice script required")
    if not isinstance(shots,list) or not 2<=len(shots)<=18:
        raise ValueError("2-18 verified shots required")
    catalog={x["candidate_id"]:x for x in intake["candidates"]}
    shots_out=[]
    actual=[]
    for i,shot in enumerate(shots,start=1):
        if not isinstance(shot,dict) or shot.get("candidate_id") not in catalog:
            raise ValueError("Unverified shot reference")
        idx=shot.get("voice_index")
        if type(idx) is not int or not 0<=idx<len(lines):
            raise ValueError("Every shot must point to a spoken phrase")
        caption=shot.get("visual_caption")
        if not isinstance(caption,str) or not caption.strip():
            raise ValueError("Every shot must describe the pictured content")
        origin=catalog[shot["candidate_id"]]
        actual.append((i,origin))
        shots_out.append({"capture_index":i,"voice_index":idx,
                          "visual_caption":caption.strip()})
    indices=[x["voice_index"] for x in shots_out]
    if indices!=sorted(indices) or indices[0]!=0 or indices[-1]!=len(lines)-1 or set(indices)!=set(range(len(lines))):
        raise ValueError("Every spoken phrase needs matching visuals in order")
    slug=storyboard.get("id")
    if not isinstance(slug,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,60}",slug):
        raise ValueError("Unsafe creative ID")
    length=storyboard.get("target_duration_seconds",20)
    if type(length) is not int or not 10<=length<=75:
        raise ValueError("Invalid target duration")
    if sum(len(t.split()) for t in lines)>round(length*2.65):
        raise ValueError("Copy too dense for relaxed speech")
    output.mkdir(parents=True,exist_ok=True)
    work=output/"work"
    work.mkdir(exist_ok=True)
    source=Path(storyboard["intake_dir"]).resolve()
    # Verify and snapshot all originals BEFORE writing scene files. Otherwise
    # a reordered selection (scene_02 before scene_01) can overwrite its input.
    snapshots=[]
    for pos,asset in actual:
        previous=source/"work"/asset["staged_image"]
        if previous.is_symlink() or not previous.is_file() or sha256(previous)!=asset["staged_sha256"]:
            raise ValueError("Staged source mismatch")
        snapshots.append((pos,previous.read_bytes()))
    for pos,contents in snapshots:
        (work/f"scene_{pos:02d}.png").write_bytes(contents)
    request={
        "id":slug,"title":storyboard.get("title","Criativo"),
        "publish":False,"commercial_release":False,
        "source_capture":{"kind":"local_authorized_media","scene_timing":"voice_aligned",
                          "visuals":"authorized_uploaded_photos_and_video_frames",
                          "requested_seconds":length,
                          "human_editorial_review":"pending"},
        "voice":{"model":"pt_PT-tugao-medium","sentences":lines,
                 "length_scale":1.17,"intro_pause_s":0.35,
                 "between_pause_s":0.46,"outro_pause_s":1.15},
        "scenes":shots_out,"music":None
    }
    (output/"render_request.json").write_text(
        json.dumps(request,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return request

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",action="append",type=Path,default=[],
                        help="Local authorized image/video; can repeat")
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--frames-per-video",type=int,default=4)
    parser.add_argument("--storyboard",type=Path,
                        help="Optional AI-authored JSON to create a render request after intake")
    args=parser.parse_args()
    if args.storyboard:
        intake=json.loads((args.output_dir/"intake_manifest.json").read_text(encoding="utf-8"))
        story=json.loads(args.storyboard.read_text(encoding="utf-8"))
        story["intake_dir"]=str(args.output_dir)
        print(json.dumps(render_request(intake,story,args.output_dir),ensure_ascii=False))
    else:
        print(json.dumps(inspect_media(args.input,args.output_dir,args.frames_per_video),
                         ensure_ascii=False))
if __name__=="__main__":
    main()
