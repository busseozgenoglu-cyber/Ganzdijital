#!/usr/bin/env python3
"""
Comprehensive SEO fix script for Ganz Dijital website.
Fixes missing meta tags, structured data, accessibility, and performance issues
across all blog pages and main pages.
"""

import os
import glob
import re


def fix_blog_pages():
    blog_files = sorted(glob.glob("blog/*.html"))

    skip_files = [
        "blog/tarım-ciftlik-dijital-pazarlama.html",
        "blog/danismanlik-koçluk-dijital-pazarlama.html",
    ]

    for filepath in blog_files:
        if filepath in skip_files:
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        slug = os.path.basename(filepath)
        canonical_url = f"https://ganzz.digital/blog/{slug}"

        if 'google-site-verification' not in content:
            content = content.replace(
                '<meta name="author" content="Ganz Dijital">',
                '<meta name="author" content="Ganz Dijital">\n'
                '<meta name="google-site-verification" content="481c9008f61997cd">'
            )

        if 'hreflang' not in content:
            canonical_line = f'<link rel="canonical" href="{canonical_url}">'
            if canonical_line in content:
                content = content.replace(
                    canonical_line,
                    canonical_line + '\n'
                    f'<link rel="alternate" hreflang="tr" href="{canonical_url}">\n'
                    f'<link rel="alternate" hreflang="x-default" href="{canonical_url}">'
                )

        if 'prefix="og:' not in content:
            content = content.replace(
                '<html lang="tr-TR">',
                '<html lang="tr-TR" prefix="og: https://ogp.me/ns#">'
            )

        if 'max-video-preview' not in content:
            content = content.replace(
                'max-image-preview:large">',
                'max-image-preview:large, max-video-preview:-1">'
            )

        if '<meta name="googlebot"' not in content:
            content = content.replace(
                '<meta name="robots" content="index, follow',
                '<meta name="googlebot" content="index, follow">\n'
                '<meta name="robots" content="index, follow'
            )

        if 'rel="noopener' not in content:
            content = content.replace(
                'target="_blank">',
                'target="_blank" rel="noopener noreferrer">'
            )
            content = content.replace(
                'target="_blank" rel="noopener noreferrer" rel="noopener noreferrer">',
                'target="_blank" rel="noopener noreferrer">'
            )

        if 'role="navigation"' not in content and '<nav>' not in content.lower():
            content = content.replace(
                '<nav>',
                '<nav role="navigation" aria-label="Ana menü">'
            )

        if '<main' not in content:
            content = content.replace(
                '</nav>\n\n<div class="blog-hero"',
                '</nav>\n\n<main>\n<div class="blog-hero"'
            )
            content = content.replace(
                '</nav>\n<div class="blog-hero"',
                '</nav>\n\n<main>\n<div class="blog-hero"'
            )

            if '<footer' in content:
                content = content.replace(
                    '<footer',
                    '</main>\n\n<footer'
                )

        if content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {filepath}")


def fix_index_page():
    filepath = "index.html"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    if 'loading="lazy"' not in content:
        content = re.sub(
            r'(<img\s+(?!.*loading=))',
            r'\1loading="lazy" ',
            content
        )

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed: {filepath}")


def fix_manifest():
    import json

    with open("manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["id"] = "/"
    manifest["scope"] = "/"
    manifest["orientation"] = "any"
    manifest["categories"] = ["business", "marketing"]
    manifest["icons"] = [
        {
            "src": "/favicon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any"
        },
        {
            "src": "/favicon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "maskable"
        }
    ]

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("Fixed: manifest.json")


if __name__ == "__main__":
    fix_blog_pages()
    fix_index_page()
    fix_manifest()
    print("\nAll SEO fixes applied!")
