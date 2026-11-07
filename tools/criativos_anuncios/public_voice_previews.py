#!/usr/bin/env python3
"""Download genuine, publicly offered demo samples. Do not impersonate a voice.

Audio is for personal A/B listening only, never advertising reuse.
"""
import json
import os
import subprocess
import urllib.request
from pathlib import Path

RAQUEL_DEMO="https://media.play.ht/full_-MWglvx2PLLlQQbzk5Mc.mp3"

def fetch_demo(url: str, target: Path) -> dict:
    request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (voice preview only)"})
    with urllib.request.urlopen(request,timeout=45) as response:
        raw=response.read(12_000_001)
        ctype=response.headers.get("Content-Type","")
    if len(raw)<8000 or len(raw)>12_000_000 or not (raw.startswith(b"ID3") or raw[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2")):
        raise ValueError(f"Remote sample is not a valid MP3 (bytes={len(raw)}, mime={ctype})")
    target.write_bytes(raw)
    probe=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","default=noprint_wrappers=1:nokey=1",str(target)],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if probe.returncode:
        raise ValueError(probe.stderr[-300:])
    duration=float(probe.stdout.strip())
    if not 1<duration<180:
        raise ValueError("Unexpected sample duration")
    return {"file":target.name,"duration_s":round(duration,2),"bytes":len(raw),
            "source":url}

def main():
    folder=Path("public-voice-previews")
    folder.mkdir(exist_ok=True)
    report={"purpose":"personal-voice-listening-only","licensed_for_ads":False,"samples":[]}
    try:
        info=fetch_demo(RAQUEL_DEMO,folder/"Raquel_pt-PT_Neural_OfficialVoice_Preview.mp3")
        info["claimed_voice_id"]="pt-PT-RaquelNeural"
        info["origin"]="Public PlayHT voice demo listing (not Microsoft-hosted)"
        report["samples"].append(info)
        print("RAQUEL_PUBLIC_MP3_PASS",info["duration_s"],info["bytes"],flush=True)
    except Exception as exc:
        report["raquel_error"]=str(exc)
        print("RAQUEL_SAMPLE_UNAVAILABLE",str(exc),flush=True)
    # Site inspection of Rui without bypassing access restrictions.
    try:
        import asyncio
        from playwright.async_api import async_playwright
        async def inspect():
            async with async_playwright() as p:
                browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
                page=await browser.new_page(viewport={"width":1080,"height":950})
                resp=await page.goto("https://tts.audio/tts/pt-PT",
                                     wait_until="domcontentloaded",timeout=35000)
                await page.wait_for_timeout(1500)
                controls=await page.locator("input, textarea, button, audio, select").evaluate_all(
                    """els=>els.map(e=>({tag:e.tagName,outer:e.outerHTML.slice(0,420)})).slice(0,60)""")
                audios=await page.locator("audio, source").evaluate_all(
                    """els=>els.map(e=>e.src||e.getAttribute('src'))""")
                result={"response_status":resp.status if resp else None,
                        "page_title":await page.title(),
                        "form_controls":controls,"audio_urls":audios}
                (folder/"Rui_voice_preview_site_inspection.json").write_text(
                    json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
                print("RUI_PAGE_INSPECTED",resp.status if resp else 0,
                      "controls",len(controls),"audio_sources",len(audios),flush=True)
                await browser.close()
        asyncio.run(inspect())
    except Exception as exc:
        report["rui_page_error"]=str(exc)
        print("RUI_SITE_INSPECTION_UNAVAILABLE",str(exc),flush=True)
    (folder/"voice_demo_report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8"
    )

if __name__=="__main__":
    main()
