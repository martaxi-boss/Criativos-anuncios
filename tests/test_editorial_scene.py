"""Validate branded editorial frames made exclusively from captured website assets."""
from io import BytesIO
from pathlib import Path
import importlib.util
from unittest import TestCase
from PIL import Image

SCRIPT=Path(__file__).resolve().parents[1]/"tools/criativos_anuncios/editorial_scene.py"
spec=importlib.util.spec_from_file_location("creative_frames", SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def image_bytes(color,size=(400,600)):
    b=BytesIO()
    Image.new("RGB",size,color).save(b,"PNG")
    return b.getvalue()

class EditorialFrames(TestCase):
    def test_images_keep_real_screenshots_and_export_vertical_frames(self):
        card=image_bytes("#ede3dd")
        logo=image_bytes("#ffffff",(500,130))
        cta=image_bytes("#e4bd7a",(550,100))
        palette={"bg":"#f7f7f2","accent":"#164f42","dark":"#103128"}
        for result in (mod.compose_product(card,logo,cta,palette),
                       mod.compose_end(logo,card,cta,palette)):
            with Image.open(BytesIO(result)) as im:
                self.assertEqual(im.format,"PNG")
                self.assertEqual(im.size,(864,1536))
            self.assertGreater(len(result),4000)
    def test_invalid_media_or_css_palette_rejected(self):
        logo=image_bytes("#ffffff",(500,130))
        cta=image_bytes("#e4bd7a",(550,100))
        with self.assertRaises(Exception):
            mod.compose_product(b"not an image",logo,cta,{})
        self.assertEqual(mod.palette_color("transparent;injected","#fff"),"#fff")
