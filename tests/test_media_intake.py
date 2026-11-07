"""Smoke tests for private multimodal media intake, without paid AI or publishing."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/criativos_anuncios"))

def load(filename,name):
    path=ROOT/"tools/criativos_anuncios"/filename
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

intake=load("media_intake.py","ad_media_intake")
render=load("render.py","ad_render_verify")

def make_photo(path:Path,shade:str)->None:
    im=Image.new("RGB",(1200,900),shade)
    d=ImageDraw.Draw(im)
    d.ellipse((310,160,890,740),fill="#ae9973")
    im.save(path,format="PNG")

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"ffmpeg not available")
class MixedMediaIntake(unittest.TestCase):
    def test_photos_and_video_yield_verified_storyboard_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            make_photo(p/"produto-a.png","#1b5545")
            make_photo(p/"produto-b.png","#ccdccf")
            video=p/"video-demonstracao.mp4"
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","testsrc2=size=640x360:rate=10",
                "-t","4","-c:v","mpeg4","-q:v","8",str(video)],
                timeout=30,check=True)
            output=p/"private"
            manifest=intake.inspect_media([p/"produto-a.png",video,p/"produto-b.png"],
                                          output,max_frames_per_video=4)
            self.assertEqual(manifest["source_types"],["photo","video"])
            self.assertEqual(len(manifest["inputs"]),3)
            self.assertEqual(len(manifest["candidates"]),6)
            self.assertFalse(manifest["upload_to_public_github"])
            self.assertTrue(manifest["media_private"])
            self.assertTrue((output/"media_candidates.jpg").is_file())
            self.assertTrue((output/"intake_manifest.json").is_file())
            choices=manifest["candidates"]
            self.assertTrue(any(x["frame_time_seconds"] is not None for x in choices))
            self.assertTrue(all((output/"work"/x["staged_image"]).exists() for x in choices))
            story={
                "id":"foto-video-20s","target_duration_seconds":20,
                "voice_sentences":["Conhece os materiais apresentados.",
                                   "Neste vídeo vemos diferentes detalhes.",
                                   "Explora a seleção e pede informações."],
                "shots":[{"candidate_id":x["candidate_id"],"voice_index":i,
                          "visual_caption":f"Imagem verificada {i}"}
                         for i,x in enumerate([choices[0],choices[2],choices[5]])],
                "intake_dir":str(output)
            }
            request=intake.render_request(manifest,story,output)
            self.assertEqual(len(request["scenes"]),3)
            self.assertEqual(request["voice"]["model"],"pt_PT-tugao-medium")
            self.assertEqual(request["source_capture"]["scene_timing"],"voice_aligned")
            self.assertEqual(render.validate_request(request)[2],"foto-video-20s")
            for n in range(1,4):
                with Image.open(output/"work"/f"scene_{n:02d}.png") as im:
                    self.assertEqual(im.size,(864,1536))
            self.assertTrue((output/"render_request.json").exists())

    def test_rejects_unsupported_and_duplicate_private_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            make_photo(root/"imagem.png","#223344")
            with self.assertRaises(ValueError):
                intake.inspect_media([root/"imagem.png",root/"imagem.png"],root/"duplicates")
            bad=root/"secret.txt"
            bad.write_text("nothing here")
            with self.assertRaises(ValueError):
                intake.inspect_media([bad],root/"untrusted")
            ln=root/"symlink.png"
            ln.symlink_to(root/"imagem.png")
            with self.assertRaises(ValueError):
                intake.inspect_media([ln],root/"links")

    def test_refuses_unverified_photos_and_unsynchronized_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            make_photo(root/"real.png","#123456")
            manifest=intake.inspect_media([root/"real.png"],root/"output")
            base={"id":"private-test","intake_dir":str(root/"output"),
                  "voice_sentences":["Um plano real.","Um segundo plano."]}
            bad={**base,"shots":[{"candidate_id":"inventado","voice_index":0,
                                   "visual_caption":"Imagem inexistente"},
                                  {"candidate_id":"media-01","voice_index":1,
                                   "visual_caption":"Imagem autorizada"}]}
            with self.assertRaises(ValueError):
                intake.render_request(manifest,bad,root/"output")
            bad["shots"][0]["candidate_id"]="media-01"
            bad["shots"][1]["voice_index"]=0
            with self.assertRaises(ValueError):
                intake.render_request(manifest,bad,root/"output")

if __name__=="__main__":
    unittest.main()
