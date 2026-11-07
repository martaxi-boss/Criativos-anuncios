"""Regression checks: use the two audio references explicitly approved by the owner."""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("approved_voice_renderer",ROOT/"tools/criativos_anuncios/render.py")
RENDER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDER)

class ApprovedVoiceTests(unittest.TestCase):
    def test_default_is_original_male_not_rui(self):
        self.assertEqual(RENDER.voice_profile({"voice":{"sentences":["Olá, Portugal."]}}),"piper-original-ptpt")
        self.assertEqual(RENDER.APPROVED_VOICES["piper-original-ptpt"],"pt_PT-tugao-medium")

    def test_raquel_selection_explicit(self):
        choice={"voice":{"profile":"raquel-neural-ptpt","model":"pt-PT-RaquelNeural","sentences":["Bem-vindo à Lowcost Europa."]}}
        self.assertEqual(RENDER.voice_profile(choice),"raquel-neural-ptpt")

    def test_disallow_unapproved_or_mismatched_model(self):
        for profile,model in [("rui-hd","pt-PT-RuiNeural"),("raquel-neural-ptpt","pt_PT-tugao-medium"),("piper-original-ptpt","pt-PT-RaquelNeural")]:
            with self.subTest(profile=profile,model=model):
                with self.assertRaises(ValueError):
                    RENDER.voice_profile({"voice":{"profile":profile,"model":model}})

    def test_invalid_voice_fields_fail_closed(self):
        for value in [None,[],{}, "Raquel"]:
            if value=={}: continue
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    RENDER.voice_profile({"voice":value})

if __name__=="__main__":
    unittest.main()
