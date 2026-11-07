"""Offline regression tests for professional product visuals and relaxed voice."""
from io import BytesIO
from pathlib import Path
import importlib.util
import unittest
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
def load(filename,label):
    spec=importlib.util.spec_from_file_location(label,ROOT/"tools/criativos_anuncios"/filename)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
p=load("premium_scene.py","premium_scene")
a=load("auto_site.py","premium_capture")

def photo_bytes(size=(900,650),bare=False):
    im=Image.new("RGB",size,"white")
    d=ImageDraw.Draw(im)
    if not bare:
        d.rounded_rectangle((250,70,670,570),radius=70,fill="#4f7f88")
        d.ellipse((310,270,590,470),fill="#d2ab6d")
        for i in range(6):
            d.rectangle((200+i*90,570,230+i*90,625),fill="#293e42")
    b=BytesIO()
    im.save(b,"PNG")
    return b.getvalue()

def logo_bytes():
    im=Image.new("RGB",(520,95),"white")
    d=ImageDraw.Draw(im)
    d.text((40,32),"LOWCOST EUROPA",fill="#103c32")
    b=BytesIO()
    im.save(b,"PNG")
    return b.getvalue()

class PremiumScenes(unittest.TestCase):
    def test_real_photo_layout_and_original_logo(self):
        image=photo_bytes()
        logo=logo_bytes()
        pal={"bg":"#f7f7f2","accent":"#164f42","dark":"#103128"}
        for data in (p.intro_slide([image]*3,logo,pal),
                     p.product_slide(image,logo,"Equipamentos profissionais de estética",pal,2),
                     p.end_slide(logo,pal,"lowcost-europa.duckdns.org")):
            with Image.open(BytesIO(data)) as out:
                self.assertEqual(out.size,(864,1536))
                self.assertEqual(out.format,"PNG")
            self.assertGreater(len(data),8000)

    def test_low_quality_is_rejected_by_screening(self):
        self.assertFalse(p.quality_metrics(photo_bytes(bare=True),900,650)["passes"])
        self.assertFalse(p.quality_metrics(photo_bytes(),180,140)["passes"])
        good=p.quality_metrics(photo_bytes(),900,650)
        self.assertTrue(good["passes"],good)

    def test_detected_embedded_website_footer_is_trimmed(self):
        import PIL.ImageDraw as ImageDraw
        im=Image.new("RGB",(800,800),"#747879")
        d=ImageDraw.Draw(im)
        d.rectangle((10,80,790,570),fill="#505f69")
        d.rectangle((0,590,800,800),fill="#fafaf8")
        d.text((40,625),"Seleção em avaliação",fill="#103c32")
        b=BytesIO()
        im.save(b,"PNG")
        crop=p.clean_photo(b.getvalue())
        self.assertLess(crop.height,im.height*.8)
        clean=p.clean_photo(photo_bytes(size=(900,650)))
        self.assertEqual(clean.size,(900,650))

    def test_actual_brand_and_cta_are_parameters_not_lowcost_constants(self):
        photo=photo_bytes()
        logo=logo_bytes()
        pal={"bg":"#f7f7f2","accent":"#164f42","dark":"#103128"}
        for data in (p.intro_slide([photo]*3,logo,pal,"Tecnologia especial para profissionais"),
                     p.product_slide(photo,logo,"Equipamento teste",pal,1,brand="Marca Exemplo"),
                     p.end_slide(logo,pal,"marca-exemplo.pt","Tecnologia especial","VER CATÁLOGO")):
            with Image.open(BytesIO(data)) as im:
                self.assertEqual(im.size,(864,1536))

    def test_source_selection_excludes_full_website_cards(self):
        source=(ROOT/"tools/criativos_anuncios/auto_site.py").read_text(encoding="utf-8")
        self.assertIn('main .product-card__image',source)
        self.assertIn('premium_product_photography',source)
        self.assertNotIn('from editorial_scene import compose_product',source)

    def test_does_not_allow_missing_source_photo(self):
        with self.assertRaises(ValueError):
            p.product_slide(b"bad",logo_bytes(),"Real equipment",{},1)
        with self.assertRaises(ValueError):
            p.product_slide(photo_bytes(),logo_bytes(),"",{},1)

    def test_relaxed_voice_settings_preserve_user_model(self):
        meta={"brand":"Exemplo","title":"Exemplo","url":"https://example.org/",
              "captured_at":"2026-11-07T03:00:00Z","h1":"Equipamentos para profissionais",
              "h2":"Conheça as opções de qualidade","lead":"Veja os equipamentos disponíveis",
              "description":"Consulte informações úteis sobre serviços e produtos"}
        req=a.captured_request(meta,5,"adtest")
        self.assertEqual(req["voice"]["model"],"pt_PT-tugao-medium")
        self.assertGreater(req["voice"]["length_scale"],1.0)
        self.assertGreaterEqual(req["voice"]["between_pause_s"],.35)
        self.assertLessEqual(sum(len(s.split()) for s in req["voice"]["sentences"]),52)
        self.assertFalse(req["publish"])
        self.assertFalse(req["commercial_release"])

    def test_dense_voice_rejected_instead_of_accelerated(self):
        meta={"brand":"Exemplo","title":"Exemplo","url":"https://example.org/",
              "captured_at":"2026-11-07T03:00:00Z","h1":"Equipamentos"}
        huge=["palavra "*25]*5
        with self.assertRaises(ValueError):
            a.captured_request(meta,5,"adtest",huge)

if __name__=="__main__":
    unittest.main()
