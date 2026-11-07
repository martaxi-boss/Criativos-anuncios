#!/usr/bin/env python3
"""Capture real public website scenes for a private vertical ad preview.

Independent Criativos-anuncios runner, not a service or dependency on the Ferrari VPS.
Never logs in, clicks purchase controls, downloads private content or publishes ads.
"""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import re
import socket
from pathlib import Path
from urllib.parse import urlsplit, urljoin

ALLOWED_SCHEMES = {"http", "https"}
BLOCKED_HOST_SUFFIXES = (".local", ".internal", ".localhost", ".onion")
SOCIAL_HOSTS = ("instagram.com", "facebook.com", "tiktok.com")


def public_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048 or any(c in url for c in "\r\n\t"):
        raise ValueError("Invalid public URL")
    p = urlsplit(url)
    host = (p.hostname or "").lower().rstrip(".")
    if (p.scheme not in ALLOWED_SCHEMES or not host or p.username or p.password
            or p.port not in (None, 80, 443) or host == "localhost"
            or host.endswith(BLOCKED_HOST_SUFFIXES)):
        raise ValueError("Only public websites without credentials or custom ports are supported")
    answers = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
        raise ValueError("URL resolves to a private/non-public address")
    return url


def sentence(text: str, max_words: int = 15) -> str:
    clean = " ".join(str(text or "").split())
    clean = re.sub(r"[\x00-\x1f]", "", clean)
    clean = " ".join(clean.split()[:max_words]).strip(" ,;:.-")
    if len(clean) < 4:
        return ""
    return clean if clean.endswith((".", "!", "?")) else clean + "."


def make_voice_lines(meta: dict) -> list[str]:
    """Use only words demonstrably found on the page, plus a fixed source-neutral CTA."""
    raw = [meta.get("h1"), meta.get("lead"), meta.get("h2"), meta.get("description")]
    raw = [sentence(t, 13) for t in raw if sentence(t, 13)]
    dedup = []
    for s in raw:
        if s.casefold() not in {x.casefold() for x in dedup}:
            dedup.append(s)
    brand = sentence(meta.get("brand") or meta.get("title") or "Explora", 6).strip(".")
    cta = sentence(meta.get("cta") or "Conheça as opções", 8)
    lines = ([brand + "."] if brand.casefold() not in {x.strip(".").casefold() for x in dedup} else [])
    lines += dedup[:3]
    lines += [cta]
    # At least 2 genuine distinct spoken statements must be present.
    if len(lines) < 2:
        raise RuntimeError("Not enough public page copy for a truthful voice script")
    return lines[:5]


def captured_request(meta: dict, count: int, stem: str) -> dict:
    lines = make_voice_lines(meta)
    # Each scene is tied to one sentence, with no synthetic imagery.
    lines = lines[:count]
    count = len(lines)
    if count < 2:
        raise RuntimeError("Insufficient scenes for automatic narration")
    return {
        "id": stem,
        "title": meta.get("title") or "Anuncio de site",
        "publish": False,
        "commercial_release": False,
        "source_capture": {
            "url": meta["url"], "kind": "public_website",
            "captured_at": meta["captured_at"],
            "source_verified": True, "editorial_approval": "pending",
            "visuals": "public-page-viewport-screenshots", "voice_style": "approved-piper-pt-PT",
        },
        "voice": {"model": "pt_PT-tugao-medium", "sentences": lines,
                  "intro_pause_s": 0.2, "between_pause_s": 0.15, "outro_pause_s": 0.35},
        "scenes": [{"capture_index": i+1, "voice_range": [i, i+1]}
                   for i in range(count)],
        # Voice-only preview until music rights and the owner approve the soundtrack.
        "music": None,
    }


async def capture(url: str, output: Path, stem: str, max_scenes: int = 5) -> dict:
    from datetime import datetime, timezone
    from PIL import Image, ImageChops, ImageStat
    from playwright.async_api import async_playwright

    url = public_url(url)
    output.mkdir(parents=True, exist_ok=True)
    work = output / "work"
    work.mkdir(parents=True, exist_ok=True)
    source_host = (urlsplit(url).hostname or "").lower()

    async with async_playwright() as browser_api:
        browser = await browser_api.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        try:
            context = await browser.new_context(
                viewport={"width": 432, "height": 768},
                device_scale_factor=2, service_workers="block",
                accept_downloads=False, is_mobile=True, has_touch=True,
            )
            validated_hosts = {source_host}
            async def on_route(route):
                target = route.request.url
                p = urlsplit(target)
                try:
                    if p.scheme not in ALLOWED_SCHEMES:
                        await route.abort()
                        return
                    host = (p.hostname or "").lower()
                    if host not in validated_hosts:
                        public_url(target)
                        validated_hosts.add(host)
                    await route.continue_()
                except (ValueError, OSError, socket.gaierror):
                    await route.abort()

            await context.route("**/*", on_route)
            page = await context.new_page()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if response is None or response.status >= 400:
                raise RuntimeError("Public page did not return a successful HTTP response")
            if (urlsplit(page.url).hostname or "").lower() != source_host:
                raise RuntimeError("Website redirected to a different host")
            await page.evaluate("document.fonts.ready")
            await page.wait_for_timeout(1200)
            body = await page.locator("body").inner_text(timeout=10000)
            is_social = any(source_host == h or source_host.endswith("." + h) for h in SOCIAL_HOSTS)
            if is_social:
                raise RuntimeError(
                    "Social/Reel pages require accessible authorized media; "
                    "browser screenshots alone are not a verified original Reel. "
                    "Use an authorized public media file/source or connected account."
                )
            if len(body.strip()) < 75:
                raise RuntimeError("Public page content is empty or access-limited")
            meta = await page.evaluate("""() => {
                const text = el => (el?.innerText || el?.textContent || '').trim();
                const val = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
                const first = selector => text(document.querySelector(selector));
                const link = [...document.querySelectorAll('main a, main button')]
                    .find(el => /ver|explorar|conhecer|comprar|consultar|pesquisar|preços|opções/i.test(text(el)));
                return {
                  title: document.title.slice(0,160),
                  brand: first('header .brand, header .logo, header [class*=brand], header img[alt]') ||
                      document.title.split(/[|–-]/)[0].trim(),
                  h1: first('main h1') || first('h1'),
                  lead: first('main .hero-lead p, main .hero p, main p'),
                  h2: first('main h2'),
                  description: first('meta[name=description]') || first('main section p:nth-of-type(2)'),
                  cta: text(link),
                  palette: {bg: val('--bg'), accent: val('--accent'), dark: val('--dark')},
                  height: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
                };
            }""")
            meta.update({"url": url, "captured_at": datetime.now(timezone.utc).isoformat()})
            if not meta["h1"] and not meta["h2"]:
                raise RuntimeError("No real headings found: cannot claim the site's visual identity")
            # Scroll five positions along the real page. If necessary, visit actual
            # same-host links from the page to obtain distinct sections.
            full_height = int(meta["height"])
            viewport_height = 768
            offsets = [round((full_height-viewport_height)*i/max(1,max_scenes-1))
                       for i in range(max_scenes)]
            candidates = []
            for pos in offsets:
                await page.evaluate("(y) => window.scrollTo(0,y)", pos)
                await page.wait_for_timeout(350)
                png = await page.screenshot(animations="disabled")
                im = Image.open(__import__("io").BytesIO(png)).convert("RGB")
                thumb = im.resize((90, 160))
                if candidates:
                    differences = []
                    for prev, _, _ in candidates:
                        delta = ImageStat.Stat(ImageChops.difference(prev,thumb)).mean
                        differences.append(sum(delta)/3)
                    if min(differences) < 8:
                        continue
                candidates.append((thumb,png,pos))
            if len(candidates)<2:
                raise RuntimeError("The site did not expose enough distinct real visual scenes")
            lines = make_voice_lines(meta)
            number = min(len(lines),len(candidates))
            for i,(_,png,_) in enumerate(candidates[:number],start=1):
                dest=work/f"scene_{i:02d}.png"
                dest.write_bytes(png)
                with Image.open(dest) as im:
                    im.verify()
            request = captured_request(meta,number,stem)
            (output/"auto_request.json").write_text(
                json.dumps(request,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
            )
            manifest = {
                "source_url":url, "captured_at":meta["captured_at"],
                "title":meta["title"],"brand":meta["brand"],"h1":meta["h1"],
                "palette":meta["palette"],"cta":meta["cta"],
                "screenshots":[{"name":f"scene_{i+1:02d}.png","scroll_y":pos}
                               for i,(_,__,pos) in enumerate(candidates[:number])],
                "source_rights":"owner review required",
                "narration":"existing approved pt_PT-tugao-medium model; generated text requires approval",
                "approval_state":"preview_only"
            }
            (output/"site_capture.json").write_text(
                json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
            )
            return manifest
        finally:
            await browser.close()


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--id",default="site-automatic-preview")
    parser.add_argument("--max-scenes",type=int,default=5,choices=range(2,7),metavar="2..6")
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,60}",args.id):
        parser.error("Invalid identifier")
    result=asyncio.run(capture(args.url,args.output_dir,args.id,args.max_scenes))
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":
    main()
