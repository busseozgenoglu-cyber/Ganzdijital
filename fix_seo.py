#!/usr/bin/env python3
"""
Comprehensive SEO fix script for Ganz Dijital website.
Fixes all SEO issues across all HTML pages.
"""
import os
import re
import glob
import json
import shutil

BASE_URL = "https://ganzz.digital"
FONT_PRECONNECT = """\
<link rel="dns-prefetch" href="//fonts.googleapis.com">
<link rel="dns-prefetch" href="//fonts.gstatic.com">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Syne:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">"""

FAVICON_LINKS = """\
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon.svg">
<link rel="apple-touch-icon" href="/favicon.svg">
<link rel="manifest" href="/manifest.json">"""

def fix_blog_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    filename = os.path.basename(filepath)
    slug = filename  # e.g. seo-nedir-rehber.html
    page_url = f"{BASE_URL}/blog/{slug}"

    # Extract page title and description from existing correct meta
    title_m = re.search(r'<title>([^<]+)</title>', content)
    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', content)
    page_title = title_m.group(1).strip() if title_m else ""
    page_desc = desc_m.group(1).strip() if desc_m else ""

    # Build clean og:title (without " | Türkiye | Ganz Dijital - Dijital Pazarlama Ajansı" suffix)
    og_title = page_title
    for suffix in [
        " | Türkiye | Ganz Dijital - Dijital Pazarlama Ajansı",
        " | Ganz Dijital",
    ]:
        if og_title.endswith(suffix):
            og_title = og_title[:-len(suffix)]
            break
    og_title = og_title.strip()

    # Build correct keywords from title words (topic-specific)
    keywords_m = re.search(r'<meta\s+name="keywords"\s+content="([^"]+)"', content)
    existing_kw = keywords_m.group(1) if keywords_m else ""
    # Only fix if it's the generic "Güzellik & Estetik" one
    if "Güzellik & Estetik" in existing_kw and "güzellik" not in page_title.lower() and "kuaför" not in page_title.lower() and "estetik" not in page_title.lower():
        # Build topic-relevant keywords from page title
        new_kw = f"dijital pazarlama, {og_title}, Google Ads, SEO, sosyal medya yönetimi, Ganz Dijital"
        content = content.replace(
            f'content="{existing_kw}"',
            f'content="{new_kw}"',
            1  # only first occurrence = keywords
        )

    # Step 1: Remove duplicate early OG tags (before <style>) 
    # Pattern: the 3 early meta tags og:title, og:description, og:type before <style>
    style_pos = content.find('<style>')
    if style_pos != -1:
        before_style = content[:style_pos]
        after_style = content[style_pos:]
        # Remove ALL early og: meta tags (before style, they're duplicates/wrong)
        before_style = re.sub(
            r'\n?<meta\s+property="og:[^"]+"\s+content="[^"]*">\n?',
            '\n',
            before_style
        )
        # Also fix 2024 → 2026 in title within before_style
        before_style = before_style.replace('2024', '2026')
        content = before_style + after_style

    # Step 2: Fix wrong guzellik og: block in after-style section (if still present)
    # Replace the broken OG block with correct one
    wrong_og_pattern = re.compile(
        r'(<!-- Open Graph -->)\s*'
        r'<meta property="og:type" content="article">\s*'
        r'<meta property="og:locale" content="tr_TR">\s*'
        r'<meta property="og:title" content="Güzellik Merkezi[^"]*">\s*'
        r'<meta property="og:description" content="Güzellik merkezi[^"]*">\s*'
        r'<meta property="og:url" content="https://ganzz\.digital/blog/guzellik-merkezi-reklam\.html">\s*'
        r'<meta property="og:site_name" content="Ganz Dijital">\s*'
        r'<meta property="og:image" content="https://ganzz\.digital/og-image\.jpg">',
        re.DOTALL
    )
    correct_og = (
        f'<!-- Open Graph -->\n'
        f'<meta property="og:type" content="article">\n'
        f'<meta property="og:locale" content="tr_TR">\n'
        f'<meta property="og:title" content="{og_title} | Ganz Dijital">\n'
        f'<meta property="og:description" content="{page_desc}">\n'
        f'<meta property="og:url" content="{page_url}">\n'
        f'<meta property="og:site_name" content="Ganz Dijital">\n'
        f'<meta property="og:image" content="{BASE_URL}/og-image.jpg">\n'
        f'<meta property="og:image:width" content="1200">\n'
        f'<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="{og_title} — Ganz Dijital">'
    )
    content = wrong_og_pattern.sub(correct_og, content)

    # Step 3: Add og:image dimensions/alt where missing (correct OG blocks)
    # For pages that already have correct og: but lack og:image:width
    if 'og:image:width' not in content:
        # Insert after og:image line
        content = re.sub(
            r'(<meta property="og:image" content="[^"]+">)',
            r'\1\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            + f'<meta property="og:image:alt" content="{og_title} — Ganz Dijital">',
            content,
            count=1
        )

    # Step 4: Fix wrong twitter block (guzellik template)
    wrong_tw_pattern = re.compile(
        r'(<!-- Twitter -->)\s*'
        r'<meta name="twitter:card" content="summary_large_image">\s*'
        r'<meta name="twitter:title" content="Güzellik Merkezi[^"]*">\s*'
        r'<meta name="twitter:description" content="Güzellik merkezi[^"]*">\s*'
        r'<meta name="twitter:image" content="https://ganzz\.digital/og-image\.jpg">',
        re.DOTALL
    )
    correct_tw = (
        f'<!-- Twitter Card -->\n'
        f'<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:site" content="@ganzdijital">\n'
        f'<meta name="twitter:title" content="{og_title} | Ganz Dijital">\n'
        f'<meta name="twitter:description" content="{page_desc}">\n'
        f'<meta name="twitter:image" content="{BASE_URL}/og-image.jpg">\n'
        f'<meta name="twitter:image:alt" content="{og_title} — Ganz Dijital">'
    )
    content = wrong_tw_pattern.sub(correct_tw, content)

    # Step 4b: Fix wrong JSON-LD schemas (Article and BlogPosting with guzellik data)
    wrong_article_url = "https://ganzz.digital/blog/guzellik-merkezi-reklam.html"
    if wrong_article_url in content:
        # Replace wrong Article schema
        wrong_article_schema = re.compile(
            r'<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"Article"[^<]*?"url":\s*"https://ganzz\.digital/blog/guzellik-merkezi-reklam\.html".*?</script>',
            re.DOTALL
        )
        correct_article_schema = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "Article",\n'
            f'  "headline": "{og_title}",\n'
            f'  "description": "{page_desc}",\n'
            f'  "url": "{page_url}",\n'
            f'  "author": {{"@type": "Organization", "name": "Ganz Dijital", "url": "https://ganzz.digital"}},\n'
            f'  "publisher": {{\n'
            f'    "@type": "Organization",\n'
            f'    "name": "Ganz Dijital",\n'
            f'    "logo": {{"@type": "ImageObject", "url": "https://ganzz.digital/og-image.jpg"}}\n'
            f'  }},\n'
            f'  "dateModified": "2026-04-13",\n'
            f'  "datePublished": "2026-01-01",\n'
            f'  "mainEntityOfPage": {{"@type": "WebPage", "@id": "{page_url}"}}\n'
            f'}}\n'
            f'</script>'
        )
        content = wrong_article_schema.sub(correct_article_schema, content)

        # Replace wrong BreadcrumbList schema
        wrong_breadcrumb = re.compile(
            r'<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"BreadcrumbList".*?"item":\s*"https://ganzz\.digital/blog/guzellik-merkezi-reklam\.html".*?</script>',
            re.DOTALL
        )
        # Extract title for breadcrumb from og_title
        bc_title = og_title
        correct_breadcrumb = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "BreadcrumbList",\n'
            f'  "itemListElement": [\n'
            f'    {{"@type":"ListItem","position":1,"name":"Ana Sayfa","item":"https://ganzz.digital/"}},\n'
            f'    {{"@type":"ListItem","position":2,"name":"Blog","item":"https://ganzz.digital/#blog"}},\n'
            f'    {{"@type":"ListItem","position":3,"name":"{bc_title}","item":"{page_url}"}}\n'
            f'  ]\n'
            f'}}\n'
            f'</script>'
        )
        content = wrong_breadcrumb.sub(correct_breadcrumb, content)

        # Replace wrong BlogPosting schema
        wrong_blogposting = re.compile(
            r'<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"BlogPosting".*?"@id":\s*"https://ganzz\.digital/blog/guzellik-merkezi-reklam\.html".*?</script>',
            re.DOTALL
        )
        correct_blogposting = (
            f'<script type="application/ld+json">\n'
            f'{{\n'
            f'  "@context": "https://schema.org",\n'
            f'  "@type": "BlogPosting",\n'
            f'  "headline": "{og_title}",\n'
            f'  "description": "{page_desc}",\n'
            f'  "url": "{page_url}",\n'
            f'  "datePublished": "2026-01-01",\n'
            f'  "dateModified": "2026-04-13",\n'
            f'  "author": {{\n'
            f'    "@type": "Organization",\n'
            f'    "name": "Ganz Dijital",\n'
            f'    "url": "https://ganzz.digital"\n'
            f'  }},\n'
            f'  "publisher": {{\n'
            f'    "@type": "Organization",\n'
            f'    "name": "Ganz Dijital",\n'
            f'    "url": "https://ganzz.digital",\n'
            f'    "logo": {{"@type":"ImageObject","url":"https://ganzz.digital/og-image.jpg"}}\n'
            f'  }},\n'
            f'  "mainEntityOfPage": {{\n'
            f'    "@type": "WebPage",\n'
            f'    "@id": "{page_url}"\n'
            f'  }}\n'
            f'}}\n'
            f'</script>'
        )
        content = wrong_blogposting.sub(correct_blogposting, content)

    # Step 5: Add twitter:site and twitter:image:alt to pages with existing correct twitter block
    if 'twitter:site' not in content and 'twitter:card' in content:
        content = content.replace(
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:site" content="@ganzdijital">'
        )
    if 'twitter:image:alt' not in content and 'twitter:image' in content:
        content = re.sub(
            r'(<meta name="twitter:image" content="[^"]+">)',
            r'\1\n' + f'<meta name="twitter:image:alt" content="{og_title} — Ganz Dijital">',
            content,
            count=1
        )

    # Step 6: Replace CSS @import with <link> for font (performance)
    import_pattern = re.compile(
        r"@import\s+url\('https://fonts\.googleapis\.com/css2[^']+'\);\s*"
    )
    if import_pattern.search(content):
        content = import_pattern.sub('', content)
        # Add preconnect + link tag right after </style>
        content = content.replace(
            '</style>',
            f'</style>\n{FONT_PRECONNECT}',
            1
        )

    # Step 7: Add favicon links (after <meta charset>)
    if 'rel="icon"' not in content and 'rel="manifest"' not in content:
        content = content.replace(
            '<meta charset="UTF-8">',
            f'<meta charset="UTF-8">\n{FAVICON_LINKS}'
        )

    # Step 8: Fix 2024 → 2026 in title and description meta
    # (do targeted replacement in the head section only to avoid content body)
    head_end = content.find('</head>')
    if head_end != -1:
        head = content[:head_end]
        body = content[head_end:]
        # Replace 2024 with 2026 in title and meta tags only
        head = re.sub(
            r'(<(?:title|meta)[^>]+)2024([^>]*>)',
            r'\g<1>2026\2',
            head
        )
        content = head + body

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def fix_index_html():
    filepath = 'index.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Add favicon links after charset
    if 'rel="icon"' not in content:
        content = content.replace(
            '<meta charset="UTF-8">',
            f'<meta charset="UTF-8">\n{FAVICON_LINKS}'
        )

    # Add og:image:width/height/alt if missing
    if 'og:image:width' not in content:
        content = re.sub(
            r'(<meta property="og:image" content="[^"]+">)',
            r'\1\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n<meta property="og:image:alt" content="Ganz Dijital — Dijital Pazarlama Ajansı">',
            content,
            count=1
        )
    
    # Add twitter:site if missing
    if 'twitter:site' not in content:
        content = content.replace(
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:site" content="@ganzdijital">'
        )

    # Add twitter:image:alt if missing
    if 'twitter:image:alt' not in content:
        content = re.sub(
            r'(<meta name="twitter:image" content="[^"]+">)',
            r'\1\n<meta name="twitter:image:alt" content="Ganz Dijital — Dijital Pazarlama Ajansı">',
            content,
            count=1
        )

    # Fix SearchAction schema - improve to be valid
    old_search = '''"potentialAction": {
    "@type": "SearchAction",
    "target": "https://ganzz.digital/blog/{search_term_string}",
    "query-input": "required name=search_term_string"
  }'''
    new_search = '''"potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://ganzz.digital/blog/{search_term_string}.html"
    },
    "query-input": "required name=search_term_string"
  }'''
    content = content.replace(old_search, new_search)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def fix_hakkimizda_html():
    filepath = 'hakkimizda.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Add favicon links
    if 'rel="icon"' not in content:
        content = content.replace(
            '<meta charset="UTF-8">',
            f'<meta charset="UTF-8">\n{FAVICON_LINKS}'
        )

    # Add robots meta if missing
    if 'name="robots"' not in content:
        content = content.replace(
            '<link rel="canonical"',
            '<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">\n<link rel="canonical"'
        )

    # Add author meta if missing
    if 'name="author"' not in content:
        content = content.replace(
            '<link rel="canonical"',
            '<meta name="author" content="Ganz Dijital">\n<link rel="canonical"'
        )

    # Add google-site-verification
    if 'google-site-verification' not in content:
        content = content.replace(
            '<link rel="canonical"',
            '<meta name="google-site-verification" content="481c9008f61997cd">\n<link rel="canonical"'
        )

    # Add OG/Twitter if missing
    if 'og:title' not in content:
        og_block = """\
<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="Hakkımızda — Ganz Dijital | 15+ Yıllık Dijital Pazarlama Ajansı">
<meta property="og:description" content="Ganz Dijital, 2009'dan bu yana Türkiye genelinde 280+ firmaya dijital pazarlama hizmetleri sunan uzman ekip. Google Ads, SEO, sosyal medya yönetimi.">
<meta property="og:url" content="https://ganzz.digital/hakkimizda.html">
<meta property="og:site_name" content="Ganz Dijital">
<meta property="og:image" content="https://ganzz.digital/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Ganz Dijital — Dijital Pazarlama Ajansı">
<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@ganzdijital">
<meta name="twitter:title" content="Hakkımızda — Ganz Dijital | 15+ Yıllık Dijital Pazarlama Ajansı">
<meta name="twitter:description" content="Ganz Dijital, 2009'dan bu yana Türkiye genelinde 280+ firmaya dijital pazarlama hizmetleri sunan uzman ekip.">
<meta name="twitter:image" content="https://ganzz.digital/og-image.jpg">
<meta name="twitter:image:alt" content="Ganz Dijital — Dijital Pazarlama Ajansı">"""
        # Insert before </head>
        content = content.replace('</head>', f'{og_block}\n</head>', 1)

    # Add font preconnect+link if missing
    if 'preconnect' not in content:
        content = content.replace(
            '<link href="https://fonts.googleapis.com/',
            f'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/'
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def fix_404_html():
    filepath = '404.html'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Add favicon links
    if 'rel="icon"' not in content:
        content = content.replace(
            '<meta charset="UTF-8">',
            f'<meta charset="UTF-8">\n{FAVICON_LINKS}'
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def create_favicon():
    """Create a simple SVG favicon matching the brand colors."""
    favicon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="#020408"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" 
        font-family="monospace" font-size="52" font-weight="bold" fill="#00f5ff">[G]</text>
</svg>"""
    with open('favicon.svg', 'w', encoding='utf-8') as f:
        f.write(favicon_svg)
    print("Created favicon.svg")


def create_manifest():
    """Create web app manifest."""
    manifest = {
        "name": "Ganz Dijital",
        "short_name": "Ganz",
        "description": "Türkiye'nin dijital pazarlama ajansı — Google Ads, SEO, Sosyal Medya",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#020408",
        "theme_color": "#00f5ff",
        "lang": "tr",
        "icons": [
            {
                "src": "/favicon.svg",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }
    with open('manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("Created manifest.json")


def fix_server_py():
    """Add improved security headers and HSTS to server."""
    with open('server.py', 'r') as f:
        content = f.read()
    original = content

    old_headers = """        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")"""

    new_headers = """        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://www.google-analytics.com; frame-ancestors 'none'")
        self.send_header("X-DNS-Prefetch-Control", "on")"""

    if old_headers in content:
        content = content.replace(old_headers, new_headers)

    if content != original:
        with open('server.py', 'w') as f:
            f.write(content)
        print("Fixed server.py")
        return True
    return False


def rename_turkish_char_files():
    """Rename files with Turkish characters to ASCII equivalents."""
    renames = {
        'blog/tarım-ciftlik-dijital-pazarlama.html': 'blog/tarim-ciftlik-dijital-pazarlama.html',
        'blog/danismanlik-koçluk-dijital-pazarlama.html': 'blog/danismanlik-kocluk-dijital-pazarlama.html',
    }
    for old, new in renames.items():
        if os.path.exists(old) and not os.path.exists(new):
            shutil.copy2(old, new)
            # Fix canonical and og:url in the new file
            with open(new, 'r', encoding='utf-8') as f:
                c = f.read()
            old_basename = os.path.basename(old)
            new_basename = os.path.basename(new)
            c = c.replace(f'/{old_basename}', f'/{new_basename}')
            with open(new, 'w', encoding='utf-8') as f:
                f.write(c)
            print(f"Created {new} (ASCII-safe copy of {old})")
    return renames


def fix_sitemap(renames):
    """Update sitemap to use ASCII-safe URLs and add missing pages."""
    with open('sitemap.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Replace Turkish-char URLs with ASCII versions
    for old_path, new_path in renames.items():
        old_basename = os.path.basename(old_path)
        new_basename = os.path.basename(new_path)
        # Sitemap has URL-encoded version
        import urllib.parse
        old_encoded = urllib.parse.quote(old_basename, safe='-.')
        new_clean = new_basename
        content = content.replace(
            f'{BASE_URL}/blog/{old_encoded}',
            f'{BASE_URL}/blog/{new_clean}'
        )
        # Also try unencoded
        content = content.replace(
            f'{BASE_URL}/blog/{old_basename}',
            f'{BASE_URL}/blog/{new_clean}'
        )

    if content != original:
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed sitemap.xml")


def fix_robots_txt():
    """Improve robots.txt."""
    with open('robots.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Add sitemap index hint for image and video if not there
    # Add additional bot allowances
    new_content = """User-agent: *
Allow: /
Disallow: /private/

User-agent: Googlebot
Allow: /
Crawl-delay: 0

User-agent: Bingbot
Allow: /
Crawl-delay: 1

User-agent: AhrefsBot
Crawl-delay: 2

User-agent: SemrushBot
Crawl-delay: 2

Sitemap: https://ganzz.digital/sitemap.xml
"""
    if content != new_content:
        with open('robots.txt', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Fixed robots.txt")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=== Ganz Dijital SEO Fix Script ===\n")

    # 1. Create favicon and manifest
    create_favicon()
    create_manifest()

    # 2. Rename Turkish-char files
    renames = rename_turkish_char_files()

    # 3. Fix sitemap
    fix_sitemap(renames)

    # 4. Fix robots.txt
    fix_robots_txt()

    # 5. Fix server.py
    fix_server_py()

    # 6. Fix index.html
    changed = fix_index_html()
    print(f"index.html: {'FIXED' if changed else 'OK'}")

    # 7. Fix hakkimizda.html
    changed = fix_hakkimizda_html()
    print(f"hakkimizda.html: {'FIXED' if changed else 'OK'}")

    # 8. Fix 404.html
    changed = fix_404_html()
    print(f"404.html: {'FIXED' if changed else 'OK'}")

    # 9. Fix all blog files
    blog_files = glob.glob('blog/*.html')
    fixed = 0
    for bf in sorted(blog_files):
        changed = fix_blog_file(bf)
        if changed:
            fixed += 1
    print(f"\nBlog files fixed: {fixed}/{len(blog_files)}")

    print("\n=== SEO Fix Complete ===")


if __name__ == '__main__':
    main()
