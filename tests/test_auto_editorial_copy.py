"""Automatic advertising copy must be written from observed website facts."""
from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"tools/criativos_anuncios/storyboard.py"
spec=importlib.util.spec_from_file_location("creative_storyboard_contract",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def photo(name,i):
    return {"name":name,"family_index":i,"card_index":0,
            "source":"public-detail-page","digest":f"hash{i}",
            "image":b"not-needed-for-script-test",
            "metrics":{"quality_score":.89-i*.01}}

class AutoEditorialCopyTests(unittest.TestCase):
    def test_creates_site_specific_narration_without_user_text(self):
        meta={"url":"https://estetica.example/","brand":"Estética Europa",
              "title":"Estética Europa","h1":"Tecnologia para a estética",
              "lead":"Produtos e equipamentos com preços observados",
              "cta":"Ver equipamentos e preços"}
        names=["Laser de depilação","HIFU profissional",
               "Radiofrequência multipolar","Criolipólise para estética"]
        text=module.auto_script(meta,names,20)
        joined=" ".join(text)
        self.assertIn("Tecnologia para a estética",joined)
        self.assertIn("Estética Europa",joined)
        self.assertIn("Laser de depilação",joined)
        self.assertIn("HIFU profissional",joined)
        self.assertNotIn("25% desconto",joined)
        self.assertLessEqual(len(joined.split()),53)

    def test_neutral_service_site_is_not_automatically_called_equipment_seller(self):
        meta={"url":"https://barber.example/","brand":"Barbearia Local",
              "title":"Barbearia Local","h1":"Cortes masculinos e barba",
              "cta":"Marcar reserva"}
        text=module.auto_script(meta,["Corte clássico","Aparar barba",
                        "Tratamento de cabelo"],20)
        self.assertIn("Cortes masculinos e barba"," ".join(text))
        self.assertNotIn("seleção de equipamentos"," ".join(text))

    def test_brief_only_includes_verified_website_information(self):
        meta={"url":"https://estetica.example/","brand":"Estética Europa",
              "title":"Estética Europa","h1":"Tecnologia para a estética",
              "lead":"Equipamentos para profissionais",
              "description":"Comparar preços por categoria",
              "cta":"VER EQUIPAMENTOS E PREÇOS",
              "palette":{"accent":"#164f42"}}
        brief=module.business_brief(meta,[photo("Laser",0),photo("HIFU",1)],20)
        self.assertEqual(brief["brand"],meta["brand"])
        self.assertEqual(brief["real_cta"],meta["cta"])
        self.assertEqual(len(brief["verified_product_photographs"]),2)
        self.assertEqual(brief["target_seconds"],20)
        self.assertNotIn("shipping_guarantee",brief)

    def test_unsupported_spoken_product_requires_matching_real_photo(self):
        meta={"url":"https://estetica.example/","brand":"Estética Europa","title":"Estética Europa"}
        media=[photo("Laser de depilação",0),photo("HIFU profissional",1),photo("Radiofrequência",2)]
        with self.assertRaisesRegex(ValueError,"No genuine"):
            module.build_storyboard(media,meta,20,[
                "Conhece a Estética Europa.","Veja um ultrassom de estética.",
                "Visita a nossa página."
            ])
    def test_no_manual_text_is_necessary_for_an_automatic_storyboard(self):
        meta={"url":"https://estetica.example/","brand":"Estética Europa",
              "title":"Estética Europa","h1":"Tecnologia para a estética",
              "cta":"VER EQUIPAMENTOS E PREÇOS"}
        media=[photo(x,i) for i,x in enumerate(
            ["Laser de depilação","HIFU profissional","Radiofrequência","Criolipólise","Cavitacão"])]
        lines,shots,report=module.build_storyboard(media,meta,20)
        self.assertEqual(report["script_origin"],"verified_site_template_preview")
        self.assertTrue(any("Laser de depilação" in l for l in lines))
        self.assertTrue(all(s["kind"]!="product" or
            module.words(lines[s["voice_index"]]).intersection(module.words(s["caption"]))
            for s in shots))
        self.assertGreaterEqual(len(shots),5)
if __name__=="__main__":
    unittest.main()
