"""Script/photo/voice sync: 20, 45 and 60 seconds, no fixed shot count."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(filename,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tools/criativos_anuncios"/filename)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

story=load("storyboard.py","ad_storyboard")
render=load("render.py","ad_render")
auto=load("auto_site.py","ad_capture")

def photos(amount=30):
    p=[]
    families=["Laser","Radiofrequência","HIFU","Depilação","Criolipólise"]
    for i in range(amount):
        category=families[i%len(families)]
        p.append({
            "family_index":i%5,"card_index":i//5,
            "source":"public-detail-page","digest":f"hash-{i}",
            "name":f"{category} equipamento modelo {i:02d}",
            "metrics":{"quality_score":round(.90-i*.01,3)},
            "image":b"source-photograph-"+bytes(str(i),"ascii")
        })
    return p

META={"brand":"Loja real","title":"Loja real","h1":"Equipamentos de estética",
      "cta":"VER EQUIPAMENTOS E PREÇOS","url":"https://loja.example/",
      "captured_at":"2026-11-07T04:00:00Z"}

class NarrativePhotoSync(unittest.TestCase):
    def _check(self,duration,minimum,maximum):
        lines,shots,report=story.build_storyboard(photos(),META,duration)
        self.assertGreaterEqual(len(shots),minimum)
        self.assertLessEqual(len(shots),maximum)
        self.assertEqual(shots[0]["kind"],"intro")
        self.assertEqual(shots[-1]["kind"],"end")
        self.assertEqual([s["voice_index"] for s in shots],
                         sorted(s["voice_index"] for s in shots))
        products=[s for s in shots if s["kind"]=="product"]
        self.assertTrue(products)
        self.assertEqual(len({s["photo"]["digest"] for s in products}),len(products))
        for shot in products:
            # Generated speech names the precise category of the selected image.
            line=lines[shot["voice_index"]]
            self.assertTrue(story.words(line).intersection(story.words(shot["caption"])),
                            (line,shot["caption"]))
        req=auto.captured_request(META,len(lines),f"story-{duration}",lines,duration)
        req["source_capture"]["scene_timing"]="voice_aligned"
        req["scenes"]=[{"capture_index":i+1,"voice_index":s["voice_index"],
                       "visual_caption":s["caption"]} for i,s in enumerate(shots)]
        render.validate_request(req)
        starts=[.35+i*duration/len(lines) for i in range(len(lines))]
        boundaries=render.scene_boundaries_for_speech(req,starts,duration,len(shots))
        self.assertEqual(len(boundaries),len(shots)+1)
        self.assertEqual(boundaries[0],0)
        self.assertEqual(boundaries[-1],duration)
        self.assertTrue(all(b>a+.6 for a,b in zip(boundaries,boundaries[1:])))
        for shot,start in zip(shots,boundaries):
            index=shot["voice_index"]
            lower=0 if index==0 else starts[index]
            upper=starts[index+1] if index+1<len(starts) else duration
            self.assertGreaterEqual(start,lower-.001)
            self.assertLess(start,upper+.001)
        self.assertEqual(report["visual_shots"],len(shots))
        return report
    def test_20_second_ad_can_show_more_than_three_photos(self):
        report=self._check(20,5,8)
        self.assertGreaterEqual(report["paired_product_photos"],3)
    def test_45_second_reel_has_more_shots(self):
        report=self._check(45,10,15)
        self.assertGreater(report["paired_product_photos"],5)
    def test_60_second_long_reel(self):
        report=self._check(60,13,18)
        self.assertGreater(report["paired_product_photos"],9)
    def test_user_mentions_laser_and_only_real_laser_photo_is_accepted(self):
        lines=["Conhece esta loja.","Conhece laser para estética.","Visita o site."]
        _,shots,_=story.build_storyboard(photos(),META,15,lines)
        matched=[s for s in shots if s["kind"]=="product"]
        self.assertTrue(all("Laser" in s["caption"] for s in matched))
        lines=["Conhece esta loja.","Descobre microagulhamento profissional.","Visita o site."]
        with self.assertRaises(ValueError):
            story.build_storyboard(photos(),META,15,lines)
    def test_invalid_narration_photo_order_is_rejected(self):
        req=auto.captured_request(META,3,"story-order",
                                  ["Conhece a loja.","Explora Laser.","Visita o site."])
        req["source_capture"]["scene_timing"]="voice_aligned"
        req["scenes"]=[{"capture_index":i+1,"voice_index":n}
                       for i,n in enumerate([0,2,1])]
        with self.assertRaises(ValueError):
            render.validate_request(req)
    def test_visuals_follow_actual_voice_intervals_not_equal_video_slices(self):
        req=auto.captured_request(META,3,"story-voice",
                                  ["Conhece a loja.","Explora Laser.","Visita o site."])
        req["source_capture"]["scene_timing"]="voice_aligned"
        req["scenes"]=[{"capture_index":i+1,"voice_index":n}
                       for i,n in enumerate([0,1,1,2])]
        times=render.scene_boundaries_for_speech(req,[.35,3.7,13.1],19,4)
        self.assertAlmostEqual(times[0],0)
        self.assertAlmostEqual(times[1],3.7)
        self.assertAlmostEqual(times[2],(3.7+13.1)/2)
        self.assertAlmostEqual(times[3],13.1)
        self.assertAlmostEqual(times[4],19)
if __name__=="__main__":
    unittest.main()
