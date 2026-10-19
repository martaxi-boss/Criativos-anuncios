#!/usr/bin/env python3
"""Capture public website screenshots for ad production with local Chromium + Playwright.

Runtime prerequisite: `pip install playwright` and a Chromium binary usable on the
same CPU/OS (`playwright install chromium` or `--browser /path/to/chromium`).
Never authenticates, uses credentials, or bypasses access controls.
"""
import argparse
import asyncio
import ipaddress
import json
import socket
from pathlib import Path
from urllib.parse import urlparse, urljoin


def check_url(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError('Use a public http(s) URL without credentials')
    if p.port not in (None, 80, 443):
        raise ValueError('Nonstandard ports are not supported')
    for _, _, _, _, address in socket.getaddrinfo(p.hostname, None, proto=socket.IPPROTO_TCP):
        ip = ipaddress.ip_address(address[0])
        if not ip.is_global:
            raise ValueError('Private, loopback, or non-public hosts are blocked')
    return url


async def capture(args):
    from playwright.async_api import async_playwright
    urls = [check_url(args.url)]
    for path in args.path:
        if path.startswith(('http:', 'https:')):
            raise ValueError('Additional pages must be relative paths on same host')
        candidate = urljoin(args.url.rstrip('/') + '/', path.lstrip('/'))
        if urlparse(candidate).hostname != urlparse(args.url).hostname:
            raise ValueError('External page is not allowed')
        urls.append(check_url(candidate))
    args.output.mkdir(parents=True, exist_ok=True)
    result = []
    async with async_playwright() as p:
        opts = {'headless': True, 'args': ['--no-sandbox', '--disable-dev-shm-usage']}
        if args.browser:
            opts['executable_path'] = args.browser
        browser = await p.chromium.launch(**opts)
        try:
            for layout, size in [('mobile', {'width': 390, 'height': 844}),
                                 ('desktop', {'width': 1440, 'height': 900})]:
                context = await browser.new_context(viewport=size, device_scale_factor=1,
                                                    java_script_enabled=True, accept_downloads=False)
                await context.route('**/*', lambda route: route.continue_() if
                                    urlparse(route.request.url).scheme in ('http','https') and
                                    (urlparse(route.request.url).hostname == urlparse(args.url).hostname or
                                     urlparse(route.request.url).hostname in args.assets_host)
                                    else route.abort())
                for idx, url in enumerate(urls):
                    page = await context.new_page()
                    resp = await page.goto(url, wait_until='domcontentloaded', timeout=25000)
                    await page.evaluate("document.fonts.ready")
                    await page.wait_for_timeout(850)
                    # Do not capture authenticated/private state, browser bars or cookie overlays.
                    if resp is None or resp.status >= 400:
                        raise RuntimeError(f'Page failed: {url}, status={resp.status if resp else "none"}')
                    dest = args.output / f'{idx:02d}_{layout}.png'
                    await page.screenshot(path=str(dest), full_page=args.full_page, animations='disabled')
                    result.append({'url': url, 'viewport': layout, 'path': str(dest),
                                   'title': await page.title(), 'http_status': resp.status})
                    await page.close()
                await context.close()
        finally:
            await browser.close()
    (args.output / 'capture_manifest.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), 'utf-8')
    print(json.dumps({'captured': len(result), 'files': result}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description='Capture public site pages for audiovisual creatives')
    p.add_argument('--url', required=True, help='Public website URL')
    p.add_argument('--path', action='append', default=[], help='Other public relative page')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--browser', help='Installed Chromium executable path')
    p.add_argument('--assets-host', action='append', default=[], help='Allowlisted public image CDN hostname')
    p.add_argument('--full-page', action='store_true')
    args = p.parse_args()
    asyncio.run(capture(args))


if __name__ == '__main__':
    main()
