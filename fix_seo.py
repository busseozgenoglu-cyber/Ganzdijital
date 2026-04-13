#!/usr/bin/env python3
"""SEO maintenance and repair utility for the Ganz Dijital site."""

from __future__ import annotations

import argparse
import os
import re
import struct
import zlib
from datetime import UTC, datetime
from pathlib import Path

BASE_URL = "https://ganzz.digital"
ROOT = Path(__file__).resolve().parent
BLOG_DIR = ROOT / "blog"
OG_IMAGE_NAME = "og-image.png"
OG_IMAGE_URL = f"{BASE_URL}/{OG_IMAGE_NAME}"
BROKEN_ARTICLE_MARKER = "</html<!-- BLOG HERO -->"

DUPLICATE_SLUGS = {
    "tarım-ciftlik-dijital-pazarlama.html": "tarim-ciftlik-dijital-pazarlama.html",
    "danismanlik-koçluk-dijital-pazarlama.html": "danismanlik-kocluk-dijital-pazarlama.html",
}

TITLE_SUFFIXES = (
    " | Türkiye | Ganz Dijital - Dijital Pazarlama Ajansı",
    " | Ganz Dijital - Dijital Pazarlama Ajansı",
    " | Ganz Dijital Blog",
    " | Ganz Dijital",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> bool:
    if not content.endswith("\n"):
        content += "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def replace_og_refs(content: str) -> str:
    content = content.replace("og-image.jpg", OG_IMAGE_NAME)
    content = content.replace(f"{BASE_URL}/og-image.jpg", OG_IMAGE_URL)
    if 'property="og:image"' in content and 'property="og:image:type"' not in content:
        content = content.replace(
            '<meta property="og:image:height" content="630">',
            '<meta property="og:image:height" content="630">\n<meta property="og:image:type" content="image/png">',
            1,
        )
    return content


def remove_jsonld_block(content: str, type_name: str) -> str:
    pattern = re.compile(
        rf'<script type="application/ld\+json">\s*\{{.*?"@type":\s*"{re.escape(type_name)}".*?</script>\s*',
        re.DOTALL,
    )
    return pattern.sub("", content, count=1)


def replace_jsonld_block(content: str, type_name: str, new_block: str) -> str:
    pattern = re.compile(
        rf'<script type="application/ld\+json">\s*\{{.*?"@type":\s*"{re.escape(type_name)}".*?</script>\s*',
        re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub(new_block + "\n", content, count=1)
    return content


def replace_first_jsonld_field(content: str, type_name: str, field_name: str, value: str) -> str:
    pattern = re.compile(
        rf'(<script type="application/ld\+json">\s*\{{.*?"@type":\s*"{re.escape(type_name)}".*?"{re.escape(field_name)}":\s*")[^"]*(")',
        re.DOTALL,
    )
    return pattern.sub(lambda match: match.group(1) + value + match.group(2), content, count=1)


def extract(pattern: str, content: str) -> str | None:
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else None


def clean_title(raw_title: str) -> str:
    title = raw_title.strip()
    for suffix in TITLE_SUFFIXES:
        if title.endswith(suffix):
            return title[: -len(suffix)].strip()
    return title


def extract_blog_footer() -> str:
    marker = '<a href="https://wa.me/905078805608" class="waf" target="_blank">'
    for path in sorted(BLOG_DIR.glob("*.html")):
        content = read_text(path)
        if marker in content and "</body>" in content and "</html>" in content:
            start = content.index(marker)
            return content[start:].strip()
    return (
        '<a href="https://wa.me/905078805608" class="waf" target="_blank">\n'
        '  <svg viewBox="0 0 32 32" fill="white"><path d="M16 0C7.163 0 0 7.163 0 16c0 2.82.735 5.47 2.02 7.77L0 32l8.43-2.01A15.94 15.94 0 0016 32c8.837 0 16-7.163 16-16S24.837 0 16 0zm8.13 22.27c-.34.96-1.67 1.76-2.75 1.99-.73.16-1.68.28-4.88-.99-4.1-1.61-6.74-5.77-6.95-6.04-.2-.27-1.66-2.2-1.66-4.2s1.05-2.98 1.43-3.39c.34-.37.9-.54 1.44-.54.17 0 .33.01.47.01.42.02.63.05.9.7.34.82 1.17 2.82 1.27 3.02.1.2.2.47.06.74-.13.28-.2.45-.4.69-.2.24-.39.42-.59.68-.18.23-.39.47-.16.87.23.4.98 1.61 2.1 2.61 1.44 1.27 2.65 1.67 3.04 1.85.39.18.62.15.85-.09.24-.24.96-1.12 1.22-1.5.25-.38.5-.32.85-.19.35.13 2.2 1.04 2.58 1.23.38.19.63.28.72.43.09.15.09.89-.25 1.85z"/></svg>\n'
        '</a>\n\n'
        '<script>\n'
        'function toggleFaq(i) {\n'
        "  const el = document.getElementById('faq-'+i);\n"
        "  if (el) {\n"
        "    el.classList.toggle('open');\n"
        "  }\n"
        '}\n'
        '</script>\n'
        '</body>\n'
        '</html>'
    )


def ensure_complete_blog_document(content: str, footer: str) -> str:
    content = re.sub(r"\n>\s*$", "\n", content)
    if "</article>" not in content:
        content = content.rstrip() + "\n</article>\n\n"
    if '<a href="https://wa.me/905078805608" class="waf" target="_blank">' not in content:
        content = content.rstrip() + "\n" + footer.strip() + "\n"
    elif "</body>" not in content or "</html>" not in content:
        head, _, _ = content.partition('<a href="https://wa.me/905078805608" class="waf" target="_blank">')
        content = head.rstrip() + "\n" + footer.strip() + "\n"
    return content


def create_og_image() -> bool:
    path = ROOT / OG_IMAGE_NAME
    width = 1200
    height = 630

    bg_top = (2, 4, 8)
    bg_bottom = (10, 17, 34)
    cyan = (0, 245, 255)
    purple = (123, 47, 255)
    pink = (255, 0, 110)
    white = (240, 246, 255)

    pixels = [[list(bg_top) for _ in range(width)] for _ in range(height)]

    def blend(base: tuple[int, int, int], overlay: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
        return tuple(
            max(0, min(255, int(base[i] * (1 - alpha) + overlay[i] * alpha))) for i in range(3)
        )

    for y in range(height):
        vertical_alpha = y / (height - 1)
        row_color = blend(bg_top, bg_bottom, vertical_alpha)
        for x in range(width):
            horizontal_glow = 0.08 * (x / (width - 1))
            pixels[y][x] = list(blend(row_color, purple, horizontal_glow))

    def add_glow(center_x: int, center_y: int, radius: int, color: tuple[int, int, int], strength: float) -> None:
        radius_sq = radius * radius
        y_start = max(0, center_y - radius)
        y_end = min(height, center_y + radius)
        x_start = max(0, center_x - radius)
        x_end = min(width, center_x + radius)
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                dx = x - center_x
                dy = y - center_y
                dist_sq = dx * dx + dy * dy
                if dist_sq >= radius_sq:
                    continue
                intensity = (1 - (dist_sq / radius_sq)) * strength
                pixels[y][x] = list(blend(tuple(pixels[y][x]), color, intensity))

    add_glow(950, 120, 260, purple, 0.30)
    add_glow(250, 510, 220, cyan, 0.22)
    add_glow(760, 320, 180, pink, 0.18)

    for y in range(70, 560):
        for x in range(72, 74):
            pixels[y][x] = list(cyan)

    for y in range(500, 504):
        for x in range(72, 1128):
            pixels[y][x] = list(blend(tuple(pixels[y][x]), cyan, 0.55))

    font = {
        "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
        "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
        "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
        "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
        "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
        "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
        "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
        "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
        "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
        "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
        "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
        " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    }

    def draw_char(char: str, origin_x: int, origin_y: int, scale: int, color: tuple[int, int, int]) -> int:
        pattern = font[char]
        for row_index, row in enumerate(pattern):
            for col_index, pixel in enumerate(row):
                if pixel != "1":
                    continue
                for dy in range(scale):
                    py = origin_y + row_index * scale + dy
                    if py >= height:
                        continue
                    for dx in range(scale):
                        px = origin_x + col_index * scale + dx
                        if px < width:
                            pixels[py][px] = list(color)
        return len(pattern[0]) * scale

    def draw_text(text: str, origin_x: int, origin_y: int, scale: int, color: tuple[int, int, int], spacing: int) -> None:
        cursor_x = origin_x
        for char in text:
            cursor_x += draw_char(char, cursor_x, origin_y, scale, color) + spacing

    draw_text("GANZ", 90, 138, 20, white, 16)
    draw_text("DIJITAL", 90, 296, 20, cyan, 16)
    draw_text("GOOGLE ADS", 92, 430, 9, white, 8)
    draw_text("SEO", 520, 430, 9, purple, 8)

    for y in range(height):
        for x in range(width):
            if (x + y) % 62 == 0:
                pixels[y][x] = list(blend(tuple(pixels[y][x]), cyan, 0.18))

    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(
        chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
        )
    )
    png.extend(chunk(b"IDAT", zlib.compress(bytes(raw), level=9)))
    png.extend(chunk(b"IEND", b""))

    existing = path.read_bytes() if path.exists() else None
    if existing == bytes(png):
        return False
    path.write_bytes(bytes(png))
    return True


def fix_index_html() -> bool:
    path = ROOT / "index.html"
    content = read_text(path)
    original = content

    content = replace_og_refs(content)
    content = content.replace("<!-- Schema.org - WebSite + SearchAction -->\n", "", 1)
    organization_block = """<!-- Schema.org - Organization -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MarketingAgency",
  "@id": "https://ganzz.digital/#organization",
  "name": "Ganz Dijital",
  "alternateName": "Ganz Dijital Reklam Ajansı",
  "url": "https://ganzz.digital/",
  "logo": "https://ganzz.digital/favicon.svg",
  "description": "Türkiye genelinde Google Ads, SEO, sosyal medya yönetimi ve web tasarım hizmetleri sunan dijital pazarlama ajansı.",
  "foundingDate": "2009",
  "telephone": "+905078805608",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+905078805608",
    "contactType": "sales",
    "availableLanguage": ["Turkish"]
  },
  "sameAs": [
    "https://wa.me/905078805608"
  ],
  "areaServed": {
    "@type": "Country",
    "name": "Turkey"
  }
}
</script>"""
    if '"@type": "MarketingAgency"' not in content:
        content = content.replace("<!-- Schema.org - Organization -->", organization_block, 1)
    content = content.replace(
        '<a href="#" class="nav-logo">',
        '<a href="/" class="nav-logo" aria-label="Ganz Dijital ana sayfa">',
        1,
    )
    content = content.replace(
        '    "availableLanguage": "Turkish",\n    "contactOption": "TollFree"',
        '    "availableLanguage": ["Turkish"]',
        1,
    )
    content = content.replace(
        '"logo": "https://ganzz.digital/og-image.png"',
        '"logo": "https://ganzz.digital/favicon.svg"',
        1,
    )
    content = content.replace('  "hasMap": "https://ganzz.digital",\n', "", 1)

    content = re.sub(
        r'\n<link rel="dns-prefetch" href="//www\.googletagmanager\.com">\n<link rel="preconnect" href="https://www\.googletagmanager\.com">',
        "",
        content,
        count=1,
    )
    content = re.sub(
        r'<!-- Google Analytics 4 -->\s*<script async src="https://www\.googletagmanager\.com/gtag/js\?id=[^"]+"></script>\s*<script>.*?</script>\s*',
        "",
        content,
        flags=re.DOTALL,
    )

    content = remove_jsonld_block(content, "LocalBusiness")

    website_block = """<!-- Schema.org - WebSite -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://ganzz.digital/#website",
  "name": "Ganz Dijital",
  "url": "https://ganzz.digital/"
}
</script>"""
    content = replace_jsonld_block(content, "WebSite", website_block)

    return write_text(path, content) if content != original else False


def fix_hakkimizda_html() -> bool:
    path = ROOT / "hakkimizda.html"
    content = read_text(path)
    updated = replace_og_refs(content)
    return write_text(path, updated) if updated != content else False


def fix_legacy_homepage() -> bool:
    path = ROOT / "ganz-dijital-FINAL.html"
    content = read_text(path)
    original = content
    content = replace_og_refs(content)
    if 'name="robots"' not in content:
        content = content.replace(
            '<meta name="description" content="Türkiye\'nin 15+ yıllık deneyimli dijital pazarlama ajansı. 280+ firma ortaklığı, 80+ güzellik merkezi. Google Ads, SEO, sosyal medya, web tasarım.">',
            '<meta name="description" content="Türkiye\'nin 15+ yıllık deneyimli dijital pazarlama ajansı. 280+ firma ortaklığı, 80+ güzellik merkezi. Google Ads, SEO, sosyal medya, web tasarım.">\n<meta name="robots" content="noindex, follow">\n<link rel="canonical" href="https://ganzz.digital/">',
            1,
        )
    return write_text(path, content) if content != original else False


def repair_broken_blog_pages() -> int:
    repaired = 0
    footer = extract_blog_footer()
    for path in sorted(BLOG_DIR.glob("*.html")):
        content = read_text(path)
        if BROKEN_ARTICLE_MARKER not in content:
            continue
        prefix = content.split("<article>", 1)[0]
        suffix = content.split(BROKEN_ARTICLE_MARKER, 1)[1].lstrip()
        if not suffix.startswith("<article"):
            suffix = "<article>\n" + suffix
        updated = ensure_complete_blog_document(replace_og_refs(prefix + suffix), footer)
        if write_text(path, updated):
            repaired += 1
    return repaired


def normalize_blog_pages() -> int:
    updated_count = 0
    footer = extract_blog_footer()
    for path in sorted(BLOG_DIR.glob("*.html")):
        content = read_text(path)
        original = content
        content = replace_og_refs(content)
        content = ensure_complete_blog_document(content, footer)

        if 'twitter:site' not in content and 'twitter:card' in content:
            content = content.replace(
                '<meta name="twitter:card" content="summary_large_image">',
                '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:site" content="@ganzdijital">',
                1,
            )

        article_headline = extract(r'"@type":\s*"Article".*?"headline":\s*"([^"]+)"', content)
        meta_description = extract(r'<meta name="description" content="([^"]+)"', content)
        page_title = extract(r"<title>([^<]+)</title>", content)

        clean_headline = article_headline or clean_title(page_title or "")
        if clean_headline:
            content = replace_first_jsonld_field(content, "BlogPosting", "headline", clean_headline)

        if meta_description:
            content = replace_first_jsonld_field(content, "BlogPosting", "description", meta_description)

        if path.name in DUPLICATE_SLUGS:
            canonical_slug = DUPLICATE_SLUGS[path.name]
            old_url = f"{BASE_URL}/blog/{path.name}"
            new_url = f"{BASE_URL}/blog/{canonical_slug}"
            content = re.sub(
                r'<meta name="robots" content="[^"]+">',
                '<meta name="robots" content="noindex, follow">',
                content,
                count=1,
            )
            content = content.replace(old_url, new_url)

        if content != original and write_text(path, content):
            updated_count += 1
    return updated_count


def update_entrypoints() -> int:
    updates = 0

    staticfile_path = ROOT / "Staticfile"
    staticfile = read_text(staticfile_path)
    staticfile_updated = staticfile.replace(
        '      index: "ganz-dijital-FINAL.html"',
        '      index: "index.html"',
    )
    if staticfile_updated != staticfile and write_text(staticfile_path, staticfile_updated):
        updates += 1

    app_path = ROOT / "app" / "main.py"
    app_content = read_text(app_path)
    app_updated = app_content.replace(
        "from flask import Flask, render_template_string",
        "from flask import Flask",
    ).replace("../ganz-dijital-FINAL.html", "../index.html")
    if app_updated != app_content and write_text(app_path, app_updated):
        updates += 1

    return updates


def url_for(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        return f"{BASE_URL}/"
    return f"{BASE_URL}/{relative}"


def build_sitemap() -> bool:
    entries: list[tuple[Path, str, str, str]] = [
        (ROOT / "index.html", "weekly", "1.00", url_for(ROOT / "index.html")),
        (ROOT / "hakkimizda.html", "monthly", "0.80", url_for(ROOT / "hakkimizda.html")),
    ]

    for path in sorted(BLOG_DIR.glob("*.html")):
        if any(ord(char) > 127 for char in path.name):
            continue
        entries.append((path, "monthly", "0.75", url_for(path)))

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, changefreq, priority, loc in entries:
        lastmod = datetime.fromtimestamp(path.stat().st_mtime, UTC).strftime("%Y-%m-%d")
        parts.extend(
            [
                "  <url>",
                f"    <loc>{loc}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    parts.append("</urlset>")

    return write_text(ROOT / "sitemap.xml", "\n".join(parts))


def write_robots() -> bool:
    robots = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /private/",
            "",
            f"Sitemap: {BASE_URL}/sitemap.xml",
        ]
    )
    return write_text(ROOT / "robots.txt", robots)


def audit() -> list[str]:
    issues: list[str] = []

    if not (ROOT / OG_IMAGE_NAME).exists():
        issues.append("og-image.png bulunamadi")

    html_files = [ROOT / "index.html", ROOT / "hakkimizda.html", ROOT / "ganz-dijital-FINAL.html"]
    html_files.extend(sorted(BLOG_DIR.glob("*.html")))
    for path in html_files:
        content = read_text(path)
        if "og-image.jpg" in content:
            issues.append(f"{path.relative_to(ROOT)} halen og-image.jpg kullaniyor")
        if BROKEN_ARTICLE_MARKER in content:
            issues.append(f"{path.relative_to(ROOT)} halen bozuk blog birlesimi iceriyor")
        if path.parent == BLOG_DIR and ("</body>" not in content or "</html>" not in content):
            issues.append(f"{path.relative_to(ROOT)} eksik kapanis etiketleri iceriyor")
        if path.parent == BLOG_DIR and re.search(r"\n>\s*$", content):
            issues.append(f"{path.relative_to(ROOT)} sonda gecersiz karakter birakiyor")

    index_html = read_text(ROOT / "index.html")
    if "G-XXXXXXXXXX" in index_html:
        issues.append("index.html halen sahte GA olcum kimligi iceriyor")
    if '"@type": "LocalBusiness"' in index_html:
        issues.append("index.html halen LocalBusiness schema iceriyor")
    if '"@type": "SearchAction"' in index_html:
        issues.append("index.html halen SearchAction schema iceriyor")
    if "WebSite + SearchAction" in index_html:
        issues.append("index.html halen eski SearchAction yorumu iceriyor")

    for duplicate_slug, canonical_slug in DUPLICATE_SLUGS.items():
        content = read_text(BLOG_DIR / duplicate_slug)
        if 'content="noindex, follow"' not in content:
            issues.append(f"{duplicate_slug} noindex degil")
        if f"{BASE_URL}/blog/{canonical_slug}" not in content:
            issues.append(f"{duplicate_slug} canonical ASCII slug'a yonlenmemis")

    sitemap = read_text(ROOT / "sitemap.xml")
    for duplicate_slug in DUPLICATE_SLUGS:
        if duplicate_slug in sitemap:
            issues.append(f"sitemap duplicate slug iceriyor: {duplicate_slug}")

    return issues


def run_apply() -> None:
    og_changed = create_og_image()
    index_changed = fix_index_html()
    about_changed = fix_hakkimizda_html()
    legacy_changed = fix_legacy_homepage()
    repaired = repair_broken_blog_pages()
    normalized = normalize_blog_pages()
    entrypoint_updates = update_entrypoints()
    sitemap_changed = build_sitemap()
    robots_changed = write_robots()

    print("=== Ganz Dijital SEO Maintenance ===")
    print(f"og-image.png: {'UPDATED' if og_changed else 'OK'}")
    print(f"index.html: {'UPDATED' if index_changed else 'OK'}")
    print(f"hakkimizda.html: {'UPDATED' if about_changed else 'OK'}")
    print(f"ganz-dijital-FINAL.html: {'UPDATED' if legacy_changed else 'OK'}")
    print(f"broken blog pages repaired: {repaired}")
    print(f"blog pages normalized: {normalized}")
    print(f"entrypoints updated: {entrypoint_updates}")
    print(f"sitemap.xml: {'UPDATED' if sitemap_changed else 'OK'}")
    print(f"robots.txt: {'UPDATED' if robots_changed else 'OK'}")

    issues = audit()
    if issues:
        print("\nAUDIT FAILED:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print("\nAudit passed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Maintain Ganz Dijital SEO assets.")
    parser.add_argument("--audit", action="store_true", help="Only run audit checks.")
    args = parser.parse_args()

    os.chdir(ROOT)

    if args.audit:
        issues = audit()
        if issues:
            for issue in issues:
                print(f"- {issue}")
            raise SystemExit(1)
        print("Audit passed.")
        return

    run_apply()


if __name__ == "__main__":
    main()
