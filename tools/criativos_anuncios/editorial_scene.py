"""Compose branded vertical frames from screenshots of real website elements.

The photographs, card text, CTA and logo are screenshots captured from the
user-provided public site. An editorial composition is not a website screenshot.
"""
from __future__ import annotations

from io import BytesIO
import re
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont

CANVAS=(864,1536)

def palette_color(value: str | None, default: str) -> str:
    raw=(value or '').strip().lower()
    return raw if re.fullmatch(r'#[0-9a-f]{6}',raw) else default

def _img(raw: bytes) -> Image.Image:
    if len(raw) > 12_000_000:
        raise ValueError('Element image exceeds capture limit')
    with Image.open(BytesIO(raw)) as im:
        if im.width < 30 or im.height < 18 or im.width * im.height > 18_000_000:
            raise ValueError('Invalid product/brand element screenshot')
        return im.convert('RGB')

def _fit(raw: bytes, region: tuple[int,int]) -> Image.Image:
    return ImageOps.contain(_img(raw),region,method=Image.Resampling.LANCZOS)

def _card(canvas: Image.Image, box: tuple[int,int,int,int], radius: int=24, fill: str='#ffffff'):
    overlay=Image.new('RGBA',canvas.size,(0,0,0,0))
    shadow=ImageDraw.Draw(overlay)
    x1,y1,x2,y2=box
    shadow.rounded_rectangle((x1+2,y1+10,x2+2,y2+12),radius=radius,fill=(16,60,50,24))
    overlay=overlay.filter(ImageFilter.GaussianBlur(17))
    canvas.paste(overlay,(0,0),overlay)
    ImageDraw.Draw(canvas).rounded_rectangle(box,radius=radius,fill=fill)

def _paste_center(canvas: Image.Image, raw: bytes, box: tuple[int,int,int,int]):
    x1,y1,x2,y2=box
    im=_fit(raw,(x2-x1,y2-y1))
    canvas.paste(im,(x1+(x2-x1-im.width)//2,y1+(y2-y1-im.height)//2))

def compose_product(card_png: bytes, logo_png: bytes, cta_png: bytes, palette: dict) -> bytes:
    """Feature a REAL product-card screenshot, original logo and original CTA."""
    bg=palette_color(palette.get('bg'),'#f7f7f2')
    accent=palette_color(palette.get('accent'),'#164f42')
    dark=palette_color(palette.get('dark'),'#103128')
    cv=Image.new('RGB',CANVAS,bg)
    d=ImageDraw.Draw(cv)
    d.rectangle((0,0,864,176),fill='#ffffff')
    _paste_center(cv,logo_png,(80,24,784,158))
    d.rectangle((0,176,864,281),fill=dark)
    font=ImageFont.truetype('DejaVuSans-Bold.ttf',30)
    label='PRODUTOS EM DESTAQUE'
    bb=d.textbbox((0,0),label,font=font)
    d.text(((864-(bb[2]-bb[0]))//2,212),label,font=font,fill='#ffffff')
    _card(cv,(46,321,818,1343),radius=26)
    _paste_center(cv,card_png,(77,340,787,1312))
    d.rectangle((0,1378,864,1536),fill=accent)
    _paste_center(cv,cta_png,(132,1400,732,1504))
    out=BytesIO()
    cv.save(out,format='PNG',optimize=True)
    return out.getvalue()

def compose_end(logo_png: bytes, hero_png: bytes, cta_png: bytes, palette: dict) -> bytes:
    """End card uses original logo, headline and CTA from the captured website."""
    dark=palette_color(palette.get('dark'),'#103128')
    accent=palette_color(palette.get('accent'),'#164f42')
    bg=palette_color(palette.get('bg'),'#f7f7f2')
    cv=Image.new('RGB',CANVAS,dark)
    d=ImageDraw.Draw(cv)
    _card(cv,(69,245,795,470),radius=25,fill='#ffffff')
    _paste_center(cv,logo_png,(110,267,754,441))
    _card(cv,(55,588,809,1085),radius=24,fill=bg)
    _paste_center(cv,hero_png,(83,610,781,1055))
    _card(cv,(88,1177,776,1356),radius=22,fill='#ffffff')
    _paste_center(cv,cta_png,(105,1198,759,1332))
    d.rectangle((0,1478,864,1536),fill=accent)
    out=BytesIO()
    cv.save(out,format='PNG',optimize=True)
    return out.getvalue()
