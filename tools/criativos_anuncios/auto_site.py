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
    """Produce a factual, conversational preview; source headings remain immutable."""
    raw = [meta.get("h1"), meta.get("lead"), meta.get("h2"), meta.get("description")]
    if not any(sentence(x, 12) for x in raw):
        raise RuntimeError("Public page lacks genuine promotional copy")
    brand = sentence(meta.get("brand") or meta.get("title") or "", 6).rstrip(".")
    if not brand:
        raise RuntimeError("Brand name missing from public page")
    real = []
    for part in raw:
        value = sentence(part, 14)
        if value and value.casefold() not in {a.casefold() for a in real}:
            real.append(value)
    if len(real) < 2:
        raise RuntimeError("Not enough independent website statements")
    lines = [f"Descobre {brand} e explora as opções disponíveis no site."]
    lines += [sentence(x,9) for x in real[:3]]
    lines.append(f"Visita {brand} e conhece a seleção.")
    return lines[:5]


def captured_request(meta: dict, count: int, stem: str, voice_sentences: list[str] | None = None, target_seconds: int = 20) -> dict:
    lines = make_voice_lines(meta) if voice_sentences is None else voice_sentences
    if (not isinstance(lines, list) or not 2 <= len(lines) <= 18
            or not all(isinstance(t, str) and 4 <= len(t.strip()) <= 170 for t in lines)):
        raise ValueError("Requested voice sentences must be 2-18 short natural pt-PT phrases")
    if type(target_seconds) is not int or not 10 <= target_seconds <= 75:
        raise ValueError("Target ad duration must be 10-75 seconds")
    lines = lines[:count]
    if len(" ".join(lines).split()) > round(target_seconds*2.65):
        raise ValueError("Voice script too dense for relaxed speech at requested duration")
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
            "pace": "relaxed",
        },
        "voice": {"model": "pt_PT-tugao-medium", "sentences": lines,
                  "intro_pause_s": 0.35, "between_pause_s": 0.46, "outro_pause_s": 1.15,
                  "length_scale": 1.17},
        "scenes": [{"capture_index": i+1, "voice_range": [i, i+1]}
                   for i in range(count)],
        # Voice-only preview until music rights and the owner approve the soundtrack.
        "music": None,
    }


def make_media_contact_sheet(pool: list[dict], output: Path) -> None:
    """Export a visual shortlist so the ChatGPT host can reject ugly partner posters."""
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageOps, ImageFont
    from premium_scene import clean_photo
    width,cell_w,cell_h=1120,280,235
    rows=(min(len(pool),32)+3)//4
    canvas=Image.new("RGB",(width,75+rows*cell_h),"#f7f7f2")
    draw=ImageDraw.Draw(canvas)
    label_font=ImageFont.truetype("DejaVuSans.ttf",16)
    header_font=ImageFont.truetype("DejaVuSans-Bold.ttf",24)
    draw.text((19,16),"CANDIDATOS REAIS - REVER ANTES DO ANUNCIO",fill="#103c32",font=header_font)
    meta=[]
    for n,item in enumerate(pool):
        ident=f"F{item['family_index']:02d}-C{item['card_index']:02d}-{item['source'][0]}"
        meta.append({"id":ident,"family_index":item["family_index"],
                     "card_index":item["card_index"],"source":item["source"],
                     "category":item["name"],"image_sha256":item["digest"],
                     "quality":item["metrics"]})
        if n>=32:
            continue
        x=(n%4)*cell_w+10
        y=75+(n//4)*cell_h
        photo=clean_photo(item["image"])
        photo=ImageOps.contain(photo,(256,170),Image.Resampling.LANCZOS)
        canvas.paste(photo,(x+(256-photo.width)//2,y+(173-photo.height)//2))
        draw.text((x+5,y+177),ident+"  "+str(item["metrics"]["quality_score"]),
                  font=label_font,fill="#103c32")
        label=item["name"].strip()[:34]
        draw.text((x+5,y+200),label,font=label_font,fill="#4d6058")
    output.mkdir(parents=True,exist_ok=True)
    canvas.save(output/"media_candidates.jpg",quality=88)
    (output/"media_candidates.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )


async def capture(url: str, output: Path, stem: str, max_scenes: int = 5, voice_sentences: list[str] | None = None, preferred_photos: list[dict] | None = None, target_seconds: int = 20) -> dict:
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
            # Hide floating chat UI only in advertisement captures; do not edit the site.
            # It otherwise obscures the actual product image/observed price.
            await page.add_style_tag(content=".whatsapp-float { visibility: hidden !important; }")
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
                const anchors = [...document.querySelectorAll('main a, main button')];
                const link = anchors.find(el => /ver equipamentos|ver produtos|ver opções|ver precos|ver preços/i.test(text(el))) ||
                    anchors.find(el => /explorar|conhecer|comprar|consultar|pesquisar|preços|opções/i.test(text(el)));
                const paragraphs = [...document.querySelectorAll('main p')].map(text)
                    .filter(t => t.length >= 40 && t.length < 700);
                return {
                  title: document.title.slice(0,160),
                  brand: first('header .brand, header .logo, header [class*=brand], header img[alt]') ||
                      document.title.split(/[|–-]/)[0].trim(),
                  h1: first('main h1') || first('h1'),
                  lead: paragraphs[0] || first('main .hero p'),
                  h2: first('main h2'),
                  description: paragraphs.find(t => t !== paragraphs[0]) || first('main section p:nth-of-type(2)'),
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
            # Prioritize hero, categories and product areas. Avoid the footer.
            offsets = [round(max(0, full_height-viewport_height)*(.64*i/max(1,max_scenes-1)))
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
            # End with the genuine website CTA rather than its footer, where possible.
            if len(candidates) >= 4:
                try:
                    target = page.locator("main a, main button").filter(
                        has_text=re.compile(r"ver equipamentos|ver produtos|ver preços|explorar|conhecer",re.I)
                    ).first
                    if await target.count():
                        await target.scroll_into_view_if_needed(timeout=5000)
                        await page.evaluate("window.scrollBy(0,160)")
                        await page.wait_for_timeout(350)
                        cta_png = await page.screenshot(animations="disabled")
                        cta_thumb = Image.open(__import__("io").BytesIO(cta_png)).convert("RGB").resize((90,160))
                        distinct = all(
                            sum(ImageStat.Stat(ImageChops.difference(prev,cta_thumb)).mean)/3 > 8
                            for prev,_,_ in candidates[:-1]
                        )
                        if distinct:
                            candidates[-1] = (cta_thumb, cta_png, -1)
                except Exception:
                    pass  # Retain genuine product page capture on CTA failure.
            # PREMIUM: image-only extraction, no product-card screenshots.
            # Fail closed when real, reasonably sharp product photographs are absent.
            from premium_scene import (
                quality_metrics, product_slide, intro_slide, end_slide
            )
            import hashlib
            cards = page.locator("main .product-card")
            logo_el = page.locator("header img.brand-logo").first
            if not await logo_el.count():
                raise RuntimeError("Premium creative rejected: original brand logo missing")
            logo_png = await logo_el.screenshot(timeout=12000,animations="disabled")
            pool = []
            rejected = []
            digests = set()
            for n in range(min(await cards.count(), 24)):
                card = cards.nth(n)
                image = card.locator("img.product-card__image").first
                if not await image.count():
                    rejected.append({"card_index":n,"reason":"no-original-photo"})
                    continue
                try:
                    await image.scroll_into_view_if_needed(timeout=8000)
                    await page.wait_for_timeout(180)
                    dims = await image.evaluate(
                        "(el) => ({w:el.naturalWidth,h:el.naturalHeight,loaded:el.complete})"
                    )
                    if not dims.get("loaded"):
                        await page.wait_for_timeout(650)
                        dims = await image.evaluate(
                            "(el) => ({w:el.naturalWidth,h:el.naturalHeight,loaded:el.complete})"
                        )
                    raw = await image.screenshot(timeout=12000,animations="disabled")
                    metrics = quality_metrics(raw,int(dims["w"]),int(dims["h"]))
                    name = " ".join((await card.locator("h3").first.inner_text()).split())
                    digest = hashlib.sha256(raw).hexdigest()
                    if not metrics["passes"] or digest in digests or not name:
                        rejected.append({"card_index":n,"reason":"quality-or-duplicate",
                                         "metrics":metrics})
                        continue
                    digests.add(digest)
                    pool.append({"card_index":n,"family_index":n,"image":raw,"name":name,
                                 "digest":digest,"metrics":metrics,"source":"homepage"})
                except Exception as exc:
                    rejected.append({"card_index":n,"reason":str(exc)[:170]})
            # Discover better product originals via the website's own public
            # detail/gallery pages before deciding which media are advert-ready.
            links=await cards.evaluate_all("""els => els.slice(0,5).map(e => {
                const link=e.querySelector('a.product-card__media-link');
                return link ? link.href : '';
            }).filter(Boolean)""")
            visited=set()
            for family_index,link in enumerate(links[:5]):
                parsed=urlsplit(link)
                if (parsed.scheme!="https" or parsed.hostname != source_host or
                        link in visited):
                    continue
                visited.add(link)
                try:
                    detail=await page.goto(link,wait_until="domcontentloaded",timeout=22000)
                    if detail is None or detail.status>=400:
                        raise RuntimeError("detail page unavailable")
                    await page.wait_for_timeout(380)
                    offers=page.locator("article.offer-card")
                    for offer_index in range(min(await offers.count(),6)):
                        offer=offers.nth(offer_index)
                        image=offer.locator("img.offer-card__image").first
                        if not await image.count():
                            continue
                        try:
                            await image.scroll_into_view_if_needed(timeout=7000)
                            await page.wait_for_timeout(140)
                            dims=await image.evaluate(
                                "(el)=>({w:el.naturalWidth,h:el.naturalHeight,loaded:el.complete})"
                            )
                            if not dims.get("loaded"):
                                await page.wait_for_timeout(450)
                                dims=await image.evaluate(
                                    "(el)=>({w:el.naturalWidth,h:el.naturalHeight,loaded:el.complete})"
                                )
                            raw=await image.screenshot(timeout=11000,animations="disabled")
                            metrics=quality_metrics(raw,int(dims["w"]),int(dims["h"]))
                            title=" ".join((await offer.locator("h3.offer-title").first.inner_text()).split())
                            digest=hashlib.sha256(raw).hexdigest()
                            if not metrics["passes"] or digest in digests or not title:
                                rejected.append({"detail_family":family_index,
                                                 "offer_index":offer_index,
                                                 "reason":"gallery-photo-quality-or-duplicate",
                                                 "metrics":metrics})
                                continue
                            pool.append({"card_index":offer_index,
                                         "family_index":family_index,
                                         "image":raw,"name":title,
                                         "digest":digest,"metrics":metrics,
                                         "source":"public-detail-page"})
                            digests.add(digest)
                        except Exception as ex:
                            rejected.append({"detail_family":family_index,
                                             "offer_index":offer_index,
                                             "reason":str(ex)[:140]})
                except Exception as ex:
                    rejected.append({"detail_family":family_index,
                                     "reason":"detail-unavailable: "+str(ex)[:160]})
            pool.sort(key=lambda x:(
                x["metrics"]["quality_score"]+
                (0.04 if x["source"]=="public-detail-page" else 0)),
                reverse=True)
            make_media_contact_sheet(pool,output)
            from storyboard import build_storyboard
            copy, shots, alignment=build_storyboard(
                pool, meta, target_seconds, voice_sentences, preferred_photos
            )
            chosen=[shot["photo"] for shot in shots if shot["kind"]=="product"]
            if len(chosen)<2:
                raise RuntimeError("No authentic product photos aligned with spoken claims")
            palette=meta["palette"]
            domain=(urlsplit(url).hostname or "")
            intro_images=[x["image"] for x in chosen[:3]]
            visual=[]
            for shot in shots:
                if shot["kind"]=="intro":
                    png=intro_slide(intro_images,logo_png,palette,
                        meta.get("h1") or meta["title"])
                elif shot["kind"]=="product":
                    png=product_slide(
                        shot["photo"]["image"],logo_png,shot["caption"],palette,
                        len(visual)+1,meta.get("brand") or meta["title"]
                    )
                elif shot["kind"]=="end":
                    png=end_slide(logo_png,palette,domain,
                        meta.get("h1") or meta["title"],meta.get("cta") or "")
                else:
                    raise RuntimeError("Unknown editorial shot")
                visual.append(png)
            candidates=[]
            alignment_rows=[]
            for n,(shot,png) in enumerate(zip(shots,visual),start=1):
                im=Image.open(__import__("io").BytesIO(png)).convert("RGB")
                candidates.append((im.resize((90,160)),png,-100-n))
                alignment_rows.append({
                    "shot":n,"kind":shot["kind"],
                    "voice_index":shot["voice_index"],
                    "spoken_text":copy[shot["voice_index"]],
                    "visual_caption":shot["caption"],
                    "image_sha256":shot.get("photo",{}).get("digest"),
                    "image_source":shot.get("photo",{}).get("source"),
                    "category":shot.get("photo",{}).get("name"),
                    "semantic_match_score":shot.get("matching"),
                })
            for i,(_,png,_) in enumerate(candidates,start=1):
                dest=work/f"scene_{i:02d}.png"
                dest.write_bytes(png)
                with Image.open(dest) as im:
                    im.verify()
            request=captured_request(meta,len(copy),stem,copy,target_seconds)
            request["scenes"]=[
                {"capture_index":n+1,
                 "voice_index":shot["voice_index"],
                 "visual_caption":shot["caption"]}
                for n,shot in enumerate(shots)
            ]
            request["source_capture"]["visuals"]="premium_product_photography"
            request["source_capture"]["scene_timing"]="voice_aligned"
            request["source_capture"]["requested_seconds"]=target_seconds
            editorial={
                "mode":"premium_product_photography",
                "source_elements":["header img.brand-logo",
                    "main .product-card__image", "main img.offer-card__image",
                    "main .product-card h3", "main a.hero-primary-cta"],
                "selected":[
                    {"shot":entry["shot"],"category":entry["category"],
                     "source":entry["image_source"],"image_sha256":entry["image_sha256"]}
                    for entry in alignment_rows if entry["kind"]=="product"
                ],
                "screening_rejections":rejected,
                "candidate_count":len(pool),
                "detail_pages_visited":len(visited),
                "storyboard":alignment,
                "alignment":alignment_rows,
                "selection_method":"source-grounded-script-alignment",
                "quality_gate":"technical_screening_pass_editorial_review_pending",
            }
            (output/"storyboard.json").write_text(
                json.dumps({"voice_sentences":copy,"alignment":alignment_rows,
                            "metrics":alignment},ensure_ascii=False,indent=2)+"\n",
                encoding="utf-8"
            )
            (output/"auto_request.json").write_text(
                json.dumps(request,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
            )
            manifest = {
                "source_url":url, "captured_at":meta["captured_at"],
                "title":meta["title"],"brand":meta["brand"],"h1":meta["h1"],
                "lead":meta.get("lead"),"h2":meta.get("h2"),"description":meta.get("description"),
                "palette":meta["palette"],"cta":meta["cta"],
                "editorial":editorial,
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
    parser.add_argument("--source-request",type=Path,
                        help="Optional public JSON request with ChatGPT-authored verified voice_sentences")
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,60}",args.id):
        parser.error("Invalid identifier")
    sentences=None
    preferred=None
    target_seconds=20
    if args.source_request:
        data=json.loads(args.source_request.read_text(encoding="utf-8"))
        if data.get("source_url") != args.url:
            raise ValueError("Original request URL does not match captured URL")
        sentences=data.get("voice_sentences")
        preferred=data.get("preferred_photos")
        target_seconds=data.get("target_duration_seconds",20)
    result=asyncio.run(capture(
        args.url,args.output_dir,args.id,args.max_scenes,
        sentences,preferred,target_seconds
    ))
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":
    main()
