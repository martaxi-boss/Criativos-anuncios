"""Generate a private sample via Microsoft Edge Read Aloud's public demo endpoint.

This is not the Azure commercial API and no commercial-use license is implied.
Use exclusively for user's personal audition of the named Portuguese voice.
"""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import subprocess

TEXT="Bem-vindo à Low Cost Europa. Descobre equipamentos de estética profissional, compara as ofertas disponíveis e faz a compra diretamente ao vendedor parceiro."

async def main():
    import edge_tts
    directory=Path("edge-voice-previews")
    directory.mkdir(exist_ok=True)
    voices=await edge_tts.list_voices()
    portuguese=[{"name":v.get("ShortName"),"gender":v.get("Gender")}
                for v in voices if str(v.get("Locale","")).lower()=="pt-pt"]
    result={"purpose":"personal-preview-only","voice_catalog":portuguese,"samples":[],
            "commercial_use_license":"not-established"}
    voice="pt-PT-RaquelNeural"
    if any(x["name"]==voice for x in portuguese):
        file=directory/"Raquel_Neural_ptPT_Exemplo_LowCost.mp3"
        await edge_tts.Communicate(TEXT,voice,rate="-8%",pitch="+0Hz").save(str(file))
        from mutagen.mp3 import MP3
        if not file.exists() or file.stat().st_size<8000:
            raise ValueError("Invalid Raquel voice sample")
        seconds=float(MP3(file).info.length)
        if not 3<seconds<120:
            raise ValueError("Unexpected Raquel sample duration")
        result["samples"].append({"model":voice,"file":file.name,
                                  "duration":round(seconds,2),"bytes":file.stat().st_size})
        print("RAQUEL_REAL_MP3_PASS",file.stat().st_size,flush=True)
    else:
        print("RAQUEL_NOT_IN_EDGE_CATALOG",flush=True)
    result["rui_hd_on_edge_available"]=any("Rui" in str(x["name"]) for x in portuguese)
    (directory/"voice_sample_report.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("AVAILABLE_PTPT_VOICES",portuguese,flush=True)

if __name__=="__main__":
    asyncio.run(main())
