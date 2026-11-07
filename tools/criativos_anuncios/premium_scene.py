"""Professional product-led vertical compositions from verified website photos.

Every featured photograph and the logo must come from the given public website.
No full product-card/browser screenshot, fabricated product, price, or logo.
"""
from __future__ import annotations

import io
import math
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat, ImageFilter

SIZE = (864, 1536)
BG = "#F7F7F2"
GREEN = "#103C32"
SOFT = "#EDF3EF"
GOLD = "#D7B778"

def _color(raw: str | None, fallback: str) -> str:
    value = (raw or "").strip()
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback

def image_from_bytes(source: bytes) -> Image.Image:
    if not isinstance(source, bytes) or len(source) < 100 or len(source) > 12_000_000:
        raise ValueError("Invalid or oversized source photograph")
    with Image.open(io.BytesIO(source)) as image:
        if image.width < 300 or image.height < 210 or image.width*image.height > 15_000_000:
            raise ValueError("Source photograph too small or too large for advertisement")
        return ImageOps.exif_transpose(image).convert("RGB")

def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)

def quality_metrics(source: bytes, natural_width: int = 0, natural_height: int = 0) -> dict:
    """Conservative, explainable screening; quality scoring is not editorial approval."""
    im = image_from_bytes(source).resize((240, 180), Image.Resampling.LANCZOS)
    stat = ImageStat.Stat(im)
    variance = round(sum(stat.stddev)/3, 2)
    edge = round(ImageStat.Stat(im.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0], 2)
    pixels = list(im.getdata())
    # Approximate non-white image content to reject mostly empty catalogue placeholders.
    occupancy = sum(1 for r,g,b in pixels if min(r,g,b) < 232 or max(r,g,b)-min(r,g,b)>18)/len(pixels)
    occupancy = round(occupancy, 3)
    return {
        "natural_width": natural_width, "natural_height": natural_height,
        "color_stddev": variance, "edge_score": edge,
        "content_ratio": occupancy,
        "quality_score": round(
            0.48*min(variance, 85)/85 +
            0.26*min(edge, 17)/17 +
            0.26*min(occupancy, .6)/.6, 4),
        "passes": natural_width >= 500 and natural_height >= 350 and
                  variance >= 18 and edge >= 2.8 and occupancy >= .095
    }

def _logo(canvas: Image.Image, raw: bytes, box=(66,48,798,168)):
    logo = image_from_bytes(raw)
    logo = ImageOps.contain(logo, (box[2]-box[0],box[3]-box[1]), Image.Resampling.LANCZOS)
    x = box[0]+(box[2]-box[0]-logo.width)//2
    y = box[1]+(box[3]-box[1]-logo.height)//2
    canvas.paste(logo,(x,y))

def _text_lines(draw, text: str, font, max_width: int, max_lines=2) -> list[str]:
    words = " ".join((text or "").split()).split(" ")
    lines, line = [], ""
    for word in words:
        candidate = (line+" "+word).strip()
        if draw.textbbox((0,0), candidate, font=font)[2] <= max_width:
            line = candidate
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while draw.textbbox((0,0),lines[-1]+"…",font=font)[2] > max_width and len(lines[-1])>1:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines

def _product_image(canvas: Image.Image, raw: bytes, rect: tuple[int,int,int,int]):
    product = image_from_bytes(raw)
    w,h=rect[2]-rect[0],rect[3]-rect[1]
    product=ImageOps.contain(product,(w,h),Image.Resampling.LANCZOS)
    x=rect[0]+(w-product.width)//2
    y=rect[1]+(h-product.height)//2
    canvas.paste(product,(x,y))

def _save(im: Image.Image) -> bytes:
    buf=io.BytesIO()
    im.save(buf,"PNG",optimize=True)
    return buf.getvalue()

def product_slide(photo: bytes, logo: bytes, title: str, palette: dict, index: int = 1) -> bytes:
    """Feature the original photograph at nearly full width; minimal brand overlay."""
    if not title or not title.strip() or len(title)>220:
        raise ValueError("Product title absent or excessive; no fabricated labels")
    dark=_color(palette.get("dark"),GREEN)
    base=_color(palette.get("bg"),BG)
    accent=_color(palette.get("accent"),"#164F42")
    canvas=Image.new("RGB", SIZE, base)
    d=ImageDraw.Draw(canvas)
    d.rectangle((0,0,864,204),fill="#FFFFFF")
    _logo(canvas,logo,(88,24,776,178))
    d.rectangle((0,208,864,218),fill=GOLD)
    label="EQUIPAMENTOS DE ESTÉTICA"
    d.text((76,274),label,font=_font(28,True),fill=accent,stroke_width=0)
    # Large single product image, no baked website card chrome or buttons.
    d.rounded_rectangle((50,352,814,1132),radius=32,fill="#FFFFFF")
    _product_image(canvas,photo,(72,369,792,1114))
    # Keep product names clear and bounded; no unverified prices.
    fontsize=38 if len(title)<=52 else 33
    lines=_text_lines(d,title,_font(fontsize,True),730,2)
    y=1178
    for line in lines:
        d.text((67,y),line,font=_font(fontsize,True),fill=dark)
        y+=fontsize+13
    d.rectangle((0,1450,864,1536),fill=accent)
    d.text((70,1473),"LOWCOST EUROPA",font=_font(28,True),fill="#FFFFFF")
    return _save(canvas)

def intro_slide(images: list[bytes], logo: bytes, palette: dict) -> bytes:
    """Clean opening that presents a three-product selection, never a mobile screenshot."""
    if len(images)<2:
        raise ValueError("At least two real product photos required for an intro")
    dark=_color(palette.get("dark"),GREEN)
    bg=_color(palette.get("bg"),BG)
    cv=Image.new("RGB",SIZE,bg)
    d=ImageDraw.Draw(cv)
    d.rectangle((0,0,864,192),fill="#FFFFFF")
    _logo(cv,logo,(80,27,784,168))
    d.text((61,258),"TECNOLOGIA",font=_font(65,True),fill=dark)
    d.text((61,342),"PARA A ESTÉTICA",font=_font(51,True),fill=dark)
    d.rounded_rectangle((55,476,808,1252),radius=30,fill="#FFFFFF")
    # Unlike repeating a slide, this layout is a curated product collage.
    boxes=[(79,496,784,896),(82,918,418,1227),(437,918,781,1227)]
    products=images[:3] if len(images)>=3 else [images[0],images[1],images[0]]
    for source,box in zip(products,boxes):
        _product_image(cv,source,box)
    d.rectangle((0,1345,864,1536),fill=dark)
    d.text((68,1394),"ESCOLHAS COM CRITÉRIO",font=_font(34,True),fill="#FFFFFF")
    return _save(cv)

def end_slide(logo: bytes, palette: dict, domain: str) -> bytes:
    """End frame: verified original logo and actual brand CTA."""
    dark=_color(palette.get("dark"),GREEN)
    bg=_color(palette.get("bg"),BG)
    accent=_color(palette.get("accent"),"#164F42")
    cv=Image.new("RGB",SIZE,dark)
    d=ImageDraw.Draw(cv)
    d.rounded_rectangle((58,348,806,630),radius=26,fill="#FFFFFF")
    _logo(cv,logo,(86,392,778,588))
    d.text((81,724),"ESCOLHAS COM",font=_font(56,True),fill="#FFFFFF")
    d.text((81,808),"CRITÉRIO.",font=_font(73,True),fill=GOLD)
    d.rounded_rectangle((85,1017,779,1146),radius=24,fill="#F0D3A4")
    d.text((124,1057),"VER EQUIPAMENTOS",font=_font(37,True),fill=dark)
    if domain and len(domain)<=54 and re.fullmatch(r"[a-zA-Z0-9.-]+",domain):
        d.text((111,1310),domain,font=_font(32),fill="#FFFFFF")
    return _save(cv)
