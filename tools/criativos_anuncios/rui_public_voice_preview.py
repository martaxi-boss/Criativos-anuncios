#!/usr/bin/env python3
"""Inspect publicly playable Rui MAI-Voice-2 voice demos, no account or paid synthesis.

Download only audio exposed by the site's *normal public Play control*.
Do not bypass login, payment, usage limits, CSP or other site restrictions.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import re
from pathlib import Path
import subprocess

SOURCES=[
    ("Nepvox","https://nepvox.com/text-to-speech/portuguese"),
    ("Leelo","https://leelo-ai.com/pt"),
    ("TTS.audio","https://tts.audio/voices"),
]

def is_mp3(data:bytes)->bool:
    return len(data)>=6000 and (data.startswith(b"ID3") or data[:2] in (b"\xff\xfb",b"\xff\xf3",b"\xff\xf2"))

def duration(path:Path)->float:
    proc=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of",
                         "default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True)
    if proc.returncode: raise ValueError(proc.stderr[-300:])
    t=float(proc.stdout.strip())
    if not 1.0<t<120.0: raise ValueError("Demo duration outside expected range")
    return round(t,2)

async def visit(name:str,url:str,folder:Path,log:list) -> bool:
    from playwright.async_api import async_playwright
    async with async_playwright() as engine:
        browser=await engine.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            page=await browser.new_page(viewport={"width":1200,"height":950},
                                        accept_downloads=True,service_workers="block")
            audio_packets=[]
            async def inspect_response(resp):
                try:
                    typ=resp.headers.get("content-type","").lower()
                    if resp.status==200 and ("audio/" in typ or ".mp3" in resp.url):
                        buf=await resp.body()
                        if is_mp3(buf) and len(buf)<8_000_000:
                            audio_packets.append((resp.url,buf))
                except Exception:
                    pass
            page.on("response",inspect_response)
            response=await page.goto(url,wait_until="domcontentloaded",timeout=30000)
            await page.wait_for_timeout(1800)
            html=await page.content()
            matched=list(re.finditer(r"Rui.{0,65}(MAI[- ]?Voice[- ]?2)",html,re.I))
            preview=[html[max(0,m.start()-280):m.end()+520] for m in matched[:3]]
            log.append({"provider":name,"status":response.status if response else None,
                        "title":await page.title(),
                        "snippets":preview,"audio_elements":await page.locator("audio, source").count()})
            print("RUI_PREVIEW_SOURCE",name,"status",response.status if response else 0,
                  "matches",len(matched),flush=True)
            if response is None or response.status>=400 or not matched:
                return False
            # UI only: click an exact card's visible "Play" button if accessible.
            containers=page.locator("div, article, li").filter(
                has_text=re.compile(r"Rui MAI[- ]Voice[- ]2",re.I)
            )
            target=None
            for i in range(min(await containers.count(),60)):
                item=containers.nth(i)
                size=len((await item.inner_text())[:1500])
                if size>500: continue
                controls=item.get_by_role("button",name=re.compile(r"play|ouvir",re.I))
                if await controls.count():
                    target=controls.first
                    break
            if target is not None:
                await target.click(timeout=7000)
                await page.wait_for_timeout(2400)
            for link,data in audio_packets:
                if is_mp3(data):
                    output=folder/("Rui_HD_MAI_Voice_2_Demo_"+name.replace(".","_")+".mp3")
                    output.write_bytes(data)
                    d=duration(output)
                    log[-1]["downloaded_audio"]={"file":output.name,"bytes":len(data),
                                                  "duration_seconds":d,"response_url":link}
                    print("RUI_PREVIEW_MP3_PASS",output.name,len(data),d,flush=True)
                    return True
            print("RUI_NO_PUBLIC_MP3",name,flush=True)
            return False
        except Exception as exc:
            log.append({"provider":name,"error":str(exc)[:400]})
            print("RUI_SITE_UNAVAILABLE",name,str(exc)[:180],flush=True)
            return False
        finally:
            await browser.close()

async def main():
    folder=Path("rui-public-preview")
    folder.mkdir(exist_ok=True)
    log=[]
    success=False
    for name,url in SOURCES:
        if await visit(name,url,folder,log):
            success=True
            break
    (folder/"rui_preview_report.json").write_text(
        json.dumps({"source_voice":"Rui MAI-Voice-2","status":"verified_demo" if success else "unavailable",
                    "rights":"personal_audition_only_not_for_ads",
                    "sources":log},ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__":
    asyncio.run(main())
