import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ugc_engine", ROOT / "tools" / "criativos_anuncios" / "render.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "ads/requests/lowcost-europa-cinco-fotos.json").read_text(encoding="utf-8"))

    def test_five_images_and_voice(self):
        scenes, texts, ident = MOD.validate_request(self.data)
        self.assertEqual(len(scenes), 5)
        self.assertEqual(len(texts), 7)
        self.assertEqual(scenes[-1]["voice_range"][1], 7)
        self.assertFalse(self.data["publish"])
        self.assertFalse(self.data["commercial_release"])

    def test_missing_scene_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["scenes"].pop()
        with self.assertRaises(ValueError):
            MOD.validate_request(bad)

    def test_duplicate_image_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["scenes"][1]["image_url"] = bad["scenes"][0]["image_url"]
        with self.assertRaises(ValueError):
            MOD.validate_request(bad)

    def test_publication_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["publish"] = True
        with self.assertRaises(ValueError):
            MOD.validate_request(bad)

if __name__ == "__main__": unittest.main()
