"""Script-led advertising storyboard: what is said determines what is shown.

The only source of product claims and images is the public website. This module
is intentionally pure and tested offline; an LLM can improve copy separately,
but it cannot invent a product or pair an unrelated product with a specific claim.
"""
from __future__ import annotations

import re
import unicodedata

_STOP={"a","as","o","os","um","uns","uma","umas","de","da","do","das","dos",
       "e","em","no","na","nos","nas","para","por","com","sem","que","como",
       "mais","ao","aos","as","se","sua","seu","suas","seus","esta","este",
       "estao","ser","compara","consultar","consulta","conhece","explora",
       "descobre","disponivel","disponiveis","produtos","equipamentos","produto",
       "equipamento","site","marca","opcoes","categoria","categorias","novo",
       "novos","nossos","tecnologia","profissional","profissionais","estetica"}
_CATEGORY_WORDS={"laser","hifu","radiofrequencia","ultrassom","criolipolise",
                 "depilacao","led","ipl","microneedling","cavitacao","ems",
                 "pressoterapia","lifting","microagulhamento"}
_GENERIC={"produto","equipamento","categoria","tecnologia","opcoes","escolhas","precos"}

def words(text: str) -> set[str]:
    normal=unicodedata.normalize("NFKD",str(text or "").lower())
    clean="".join(char for char in normal if not unicodedata.combining(char))
    return {x for x in re.findall(r"[a-z0-9]{3,}",clean) if x not in _STOP}

def relevance(voice_text: str, item_name: str) -> float:
    requested=words(voice_text)
    available=words(item_name)
    common=len(requested.intersection(available))
    return float(common) / max(1,len(requested)) + min(common,3)*.18

def _photo_identity(x:dict) -> tuple:
    return (x["family_index"],x["card_index"],x["source"],x["digest"])

def _choose(pool:list[dict], used:set[tuple], required_words:set[str] | None=None, voice_text:str="") -> dict:
    def rank(x):
        base=x["metrics"].get("quality_score",0)
        scope=.04 if x["source"]=="public-detail-page" else 0
        hit=len(required_words.intersection(words(x["name"]))) if required_words else 0
        semantic=len(words(voice_text).intersection(words(x["name"])))
        return 2.5*hit + 1.5*semantic + base + scope
    choices=[p for p in pool if _photo_identity(p) not in used]
    if required_words:
        choices=[p for p in choices if words(p["name"]).intersection(required_words)]
    if not choices:
        raise ValueError("No genuine, unused product photograph matches the spoken text")
    selected=max(choices,key=rank)
    used.add(_photo_identity(selected))
    return selected

def auto_script(brand:str, product_names:list[str], target_seconds:int) -> list[str]:
    """Copy is created *from verified product categories*, not generic stock claims."""
    if len(product_names)<2:
        raise ValueError("Need at least 2 real product categories")
    label=" ".join(str(brand or "").split())[:55]
    if not label:
        raise ValueError("Verified brand missing")
    # Longer ads describe more products. Voice stays relaxed, never force TTS speed.
    target_phrases=max(3,min(16,round(target_seconds/4)))
    product_slots=min(len(product_names),target_phrases-2)
    lines=[f"Conhece {label} e a sua seleção de equipamentos."]
    for title in product_names[:product_slots]:
        clean=" ".join(str(title).split()).strip(" ,;:.")[:75]
        if not clean:
            raise ValueError("A real product title is empty")
        lines.append(f"Descobre {clean}.")
    lines.append(f"Encontra mais informações em {label}.")
    return lines

def build_storyboard(
    pool:list[dict],meta:dict,target_seconds:int,
    voice_sentences:list[str]|None=None,
    preferred_photos:list[dict]|None=None,
) -> tuple[list[str], list[dict], dict]:
    """Storyboard photo+script pairs, voice indices and source evidence.

    20s normally produces 5-7 shots; 45s 10-15, subject to the number of
    actual source photographs and spoken phrase count. No fixed 3-photo rule.
    """
    if type(target_seconds) is not int or not 10 <= target_seconds <= 75:
        raise ValueError("Advertising target duration must be 10-75 seconds")
    if not isinstance(pool,list) or len(pool)<2:
        raise ValueError("Insufficient original product photography")
    if preferred_photos is not None:
        if not isinstance(preferred_photos,list) or not 2<=len(preferred_photos)<=16:
            raise ValueError("Curated photos require 2-16 verified source references")
        resolved=[]
        for ref in preferred_photos:
            if not isinstance(ref,dict):
                raise ValueError("Invalid curator photo reference")
            matches=[p for p in pool if p["family_index"]==ref.get("family_index")
                     and p["card_index"]==ref.get("card_index")
                     and p["source"]==ref.get("source") and
                     p["digest"]==ref.get("image_sha256")]
            if len(matches)!=1:
                raise ValueError("Selected photo must match a real captured hash")
            resolved.append(matches[0])
        if len({_photo_identity(p) for p in resolved})!=len(resolved):
            raise ValueError("Curator repeated a photograph")
        source=resolved
    else:
        source=pool
    # One best photo per category to start; then additional views, never
    # repeating identical source bytes.
    sorted_photos=sorted(source,key=lambda p:p["metrics"]["quality_score"],reverse=True)
    unique=[]
    seen=set()
    for p in sorted_photos:
        if _photo_identity(p) not in seen:
            unique.append(p)
            seen.add(_photo_identity(p))
    distinct=[]
    families=set()
    for p in unique:
        if p["family_index"] not in families:
            distinct.append(p)
            families.add(p["family_index"])
    ordered=distinct+[p for p in unique if p not in distinct]
    if len(ordered)<2:
        raise ValueError("At least 2 genuine different photographs required")

    lines=list(voice_sentences) if voice_sentences is not None else auto_script(
        meta.get("brand") or meta.get("title"), [p["name"] for p in ordered],
        target_seconds)
    if not 3<=len(lines)<=18 or any(not isinstance(t,str) or not 4<=len(t.strip())<=170 for t in lines):
        raise ValueError("Narration must contain 3-18 natural short phrases")
    word_count=sum(len(x.split()) for x in lines)
    if word_count > round(target_seconds*2.65):
        raise ValueError("Narration too dense for calm Portuguese; shorten rather than accelerate")
    # Introduction and conclusion are source-branded; middle lines pair with
    # matching product images. If an explicit technical term is spoken, it
    # must occur in the corresponding verified product name.
    voice_shots=[{"kind":"intro","voice_index":0,"caption":lines[0],
                  "source":"verified-website-brand"}]
    used=set()
    for index,line in enumerate(lines[1:-1],start=1):
        requested=words(line)
        category_terms=requested.intersection(_CATEGORY_WORDS)
        # In full automation, first curate the real product photograph, then
        # write that exact category into the spoken line. If the user supplies
        # narration, match its wording to genuine source categories.
        if voice_sentences is None:
            photo=ordered[index-1]
            used.add(_photo_identity(photo))
        else:
            photo=_choose(ordered,used,category_terms or None,voice_text=line)
        shot={"kind":"product","voice_index":index,"caption":photo["name"],
              "spoken_text":line,"photo":photo,
              "matching":round(relevance(line,photo["name"]),3)}
        voice_shots.append(shot)
    voice_shots.append({"kind":"end","voice_index":len(lines)-1,
                        "caption":meta.get("cta") or meta.get("title"),
                        "source":"verified-website-cta"})

    # Shots are planned per spoken segment, then timecoded against the
    # actual WAV durations during render. Extra photos extend existing
    # spoken product segments rather than adding unrelated audio.
    base=len(voice_shots)
    target_shots=max(base,min(18,round(target_seconds/3.3)))
    surplus=min(max(0,target_shots-base),len(ordered)-len(used))
    cursor=1
    while surplus>0 and len(voice_shots)<18:
        product_positions=[i for i,s in enumerate(voice_shots)
                           if s["kind"]=="product"]
        if not product_positions:
            break
        pos=product_positions[(cursor-1)%len(product_positions)]
        primary=voice_shots[pos]
        # Prefer another authentic photo from the same category to continue
        # describing the SAME product without semantic drift.
        same=[x for x in ordered if x["family_index"]==primary["photo"]["family_index"]
              and _photo_identity(x) not in used]
        if not same:
            cursor+=1
            if cursor>len(product_positions)*2:
                break
            continue
        alt=max(same,key=lambda p:p["metrics"]["quality_score"])
        used.add(_photo_identity(alt))
        insert={**primary,"photo":alt,"caption":alt["name"],"alternate_view":True}
        voice_shots.insert(pos+1,insert)
        surplus-=1
        cursor+=1

    # Non-decreasing voice_index guarantees the visual is coupled with
    # the same spoken paragraph, even with 2+ photos within a paragraph.
    indices=[x["voice_index"] for x in voice_shots]
    if sorted(indices)!=indices:
        raise ValueError("Storyboard and speech lost chronological alignment")
    report={
        "requested_seconds":target_seconds,
        "voice_phrases":len(lines),"spoken_words":word_count,
        "visual_shots":len(voice_shots),
        "paired_product_photos":len([x for x in voice_shots if x["kind"]=="product"]),
        "alignment":"voice_segment_boundaries",
        "source":"verified-public-website",
        "approval_state":"editorial_pending",
    }
    return lines,voice_shots,report
