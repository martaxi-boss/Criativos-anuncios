#!/usr/bin/env python3
"""Capture the real public Lowcost website's shopper journey, without checkout."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from playwright.async_api import async_playwright
from auto_site import public_url

async def capture(url: str, dest: Path) -> dict:
    public_url(url)
    dest.mkdir(parents=True, exist_ok=True)
    frames=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        context=await browser.new_context(viewport={"width":432,"height":768},
                                          device_scale_factor=2,is_mobile=True,has_touch=True,
                                          accept_downloads=False,service_workers="block")
        page=await context.new_page()
        origin_host=urlsplit(url).hostname
        async def visit(path,label):
            target=urljoin(url,path)
            public_url(target)
            if urlsplit(target).hostname != origin_host:
                raise ValueError("Cannot follow to an external domain")
            response=await page.goto(target,wait_until="domcontentloaded",timeout=35000)
            if response is None or response.status>=400:
                raise RuntimeError("Public webpage unavailable "+target)
            if urlsplit(page.url).hostname != origin_host:
                raise RuntimeError("Website unexpectedly redirects elsewhere")
            await page.evaluate("document.fonts.ready")
            await page.add_style_tag(content=".whatsapp-float{visibility:hidden!important}")
            await page.wait_for_timeout(950)
            return page.url
        async def save(name,meaning):
            path=dest/(name+".png")
            await page.screenshot(path=str(path),animations="disabled")
            if path.stat().st_size<9000: raise RuntimeError("Screenshot empty")
            frames.append({"name":path.name,"url":page.url,"meaning":meaning,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        try:
            await visit("/","pagina_inicial")
            await save("01_inicio","Página inicial: marca, pesquisa e indicação de compra externa")
            await page.locator("#home-equipment-search").fill("laser")
            await save("02_pesquisa","Pesquisa real pelo equipamento, antes de submeter")
            await page.locator("form.search-form--hero button[type=submit]").click(timeout=10000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(850)
            await save("03_resultados","Resultados efetivos da pesquisa de equipamentos")
            await visit("/#familias","categorias")
            try: await page.locator("#familias").scroll_into_view_if_needed(timeout=10000)
            except Exception: pass
            await save("04_categorias","Lista real de categorias do site")
            family=await page.locator(".family-index a").first.get_attribute("href")
            if not family: raise RuntimeError("Category link unavailable")
            await visit(family,"categoria_escolhida")
            await save("05_categoria","Página de categoria: seleção e informação do parceiro")
            offers=page.locator("article.offer-card")
            if await offers.count():
                await offers.first.scroll_into_view_if_needed(timeout=10000)
                await page.wait_for_timeout(600)
                await save("06_oferta","Oferta real: preço observado e dados do parceiro")
                go=page.locator("article.offer-card a.button")
                if await go.count():
                    await go.first.scroll_into_view_if_needed(timeout=10000)
                    await page.wait_for_timeout(350)
                    await save("07_saida_parceiro","Botão de encaminhamento para o vendedor externo (sem clicar)")
            else:
                raise RuntimeError("No public offers available in selected category")
            # Open only pages hosted by Lowcost Europa. No external purchase clicks.
            how=await page.locator("a[href*='como-funciona']").first.get_attribute("href")
            if how:
                await visit(how,"como_funciona")
                await save("08_como_funciona","Explicação publicada de como funciona e quem vende")
                await page.evaluate("window.scrollTo(0,550)")
                await page.wait_for_timeout(250)
                await save("09_como_funciona_passos","Passos efetivos do comprador")
            await visit("/","regressar")
            await page.evaluate("window.scrollTo(0,document.documentElement.scrollHeight)")
            await page.wait_for_timeout(350)
            await save("10_rodape_transparencia","Rodapé com aviso da compra externa e parceiros")
        finally:
            await browser.close()
    result={"status":"captured_public_website_only","source":url,"frames":frames,
            "external_purchase_clicked":False,"logged_in":False}
    (dest/"capture_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--request",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    config=json.loads(args.request.read_text(encoding="utf-8"))
    url=config["source_url"]
    result=asyncio.run(capture(url,args.output_dir))
    print("REAL_SITE_FLOW_PASS",len(result["frames"]),result["source"])
if __name__=="__main__":
    main()
