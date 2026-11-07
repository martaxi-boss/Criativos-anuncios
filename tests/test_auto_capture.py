"""Offline contract tests for automatic public website ad capture."""
import copy
import importlib.util
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def load(file,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools/criativos_anuncios"/file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

auto=load("auto_site.py","auto_site")
render=load("render.py","creative_render")

class AutoCaptureTests(TestCase):
    def test_public_url_rejects_private_urls_and_credentials(self):
        for bad in ("file:///etc/passwd","http://localhost","http://127.0.0.1",
                    "https://example.com:1234","https://person:pass@example.com",
                    "http://169.254.169.254/latest/meta-data","https://example.com\nbad"):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError,OSError)):
                    auto.public_url(bad)
        with patch.object(auto.socket,"getaddrinfo",return_value=[(2,1,6,"",("93.184.216.34",443))]):
            self.assertEqual(auto.public_url("https://www.example.com/path"),"https://www.example.com/path")
        with patch.object(auto.socket,"getaddrinfo",return_value=[(2,1,6,"",("10.1.0.10",443))]):
            with self.assertRaises(ValueError):
                auto.public_url("https://example.com")
    def test_site_text_is_source_bound_not_synthetic_upsell(self):
        meta={"url":"https://example.com","captured_at":"2026-11-07T03:00:00Z",
              "title":"Empresa Exemplo", "brand":"Empresa Exemplo",
              "h1":"Serviços de design em Portugal",
              "lead":"Soluções de design para negócios locais",
              "h2":"Explore as categorias", "cta":"Conhecer serviços",
              "palette":{"accent":"#164f42"}}
        data=auto.captured_request(meta,5,"site-demo-001")
        self.assertEqual(data["music"],None)
        self.assertFalse(data["publish"])
        self.assertFalse(data["commercial_release"])
        self.assertEqual(data["voice"]["model"],"pt_PT-tugao-medium")
        self.assertGreaterEqual(len(data["scenes"]),2)
        self.assertEqual(data["scenes"][0]["capture_index"],1)
        self.assertEqual(data["scenes"][-1]["voice_range"][1],len(data["voice"]["sentences"]))
        render.validate_request(data)
    def test_manual_photos_still_supported(self):
        data=json.loads((ROOT/"ads/requests/lowcost-europa-cinco-fotos.json").read_text(encoding="utf-8"))
        self.assertEqual(len(render.validate_request(data)[0]),5)
    def test_missing_captured_screenshots_are_not_fabricated(self):
        meta={"url":"https://example.com","captured_at":"2026-11-07T03:00:00Z",
              "title":"Demo","h1":"Produtos genuínos", "h2":"Destaques", "lead":"Informação disponível"}
        data=auto.captured_request(meta,4,"site-001")
        with __import__("tempfile").TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                render.prepare_assets(data,Path(d),cached=True)
    def test_capture_refs_cannot_be_reused_as_arbitrary_local_paths(self):
        meta={"url":"https://example.com","captured_at":"2026-11-07T03:00:00Z",
              "title":"Demo","h1":"Produtos genuínos","h2":"Destaques","lead":"Informação disponível"}
        data=auto.captured_request(meta,4,"site-001")
        bad=copy.deepcopy(data);bad["scenes"][0]["capture_index"]=99
        with self.assertRaises(ValueError):render.validate_request(bad)
        bad=copy.deepcopy(data);bad["scenes"][0]["image_url"]="https://example.com/fake.jpg"
        with self.assertRaises(ValueError):render.validate_request(bad)
        bad=copy.deepcopy(data);del bad["source_capture"]
        with self.assertRaises(ValueError):render.validate_request(bad)
    def test_no_fabrication_for_empty_site_copy(self):
        with self.assertRaises(RuntimeError):
            auto.captured_request({"url":"https://example.com","captured_at":"2026-11-07T03:00:00Z"},5,"site-001")
