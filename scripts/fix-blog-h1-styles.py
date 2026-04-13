#!/usr/bin/env python3
"""Improve blog article hero title readability on mobile across blog/*.html."""
import re
from pathlib import Path

BLOG_DIR = Path(__file__).resolve().parent.parent / "blog"

# Unified rules for main template (covers h1 and .blog-h1)
H1_PAIR = (
    ".blog-hero h1,.blog-h1{font-family:'Syne',sans-serif;font-weight:700;"
    "font-size:clamp(1.45rem,5vw,2.65rem);line-height:1.3;letter-spacing:-0.02em;"
    "margin:0 0 1.1rem;text-wrap:balance;max-width:26ch;}\n"
    ".blog-hero h1 span,.blog-h1 span{background:linear-gradient(90deg,var(--cyan),var(--purple));"
    "-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}\n"
)

# Plain article pages: hero title only (keep following h1 .g or h1 span if present)
H1_BASE = (
    "h1{font-family:'Syne',sans-serif;font-weight:700;"
    "font-size:clamp(1.45rem,5vw,2.65rem);line-height:1.3;letter-spacing:-0.02em;"
    "margin:0 0 1rem;text-wrap:balance;max-width:26ch;}\n"
)

MOBILE_768_INJECT = (
    ".blog-hero h1,.blog-h1{font-size:clamp(1.35rem,6vw,1.65rem)!important;line-height:1.32!important;max-width:100%!important;}"
    ".cta-box-title{font-size:clamp(1.15rem,5vw,1.65rem)!important;line-height:1.25!important;}"
    ".related-title{font-size:clamp(1.1rem,4.5vw,1.35rem)!important;}"
)

MOBILE_700_INJECT = (
    "h1{font-size:clamp(1.35rem,6vw,1.65rem)!important;line-height:1.32!important;max-width:100%!important;}"
    ".cta h2{font-size:clamp(1.1rem,5vw,1.35rem)!important;line-height:1.25!important;}"
)

OLD_BLOG_HERO_H1 = re.compile(
    r"\.blog-hero h1\{[^}]+\}\s*"
    r"(?:\.blog-hero h1 span\{[^}]+\}\s*)?",
    re.DOTALL,
)

# Standalone h1{...} for Syne hero (not already patched)
OLD_PLAIN_H1 = re.compile(
    r"^h1\{font-family:'Syne',sans-serif;[^\n}]+\}\n",
    re.MULTILINE,
)


def inject_after_media_open(content: str, px: str, rules: str) -> str:
    needle = f"@media(max-width:{px}px){{"
    idx = content.find(needle)
    if idx == -1:
        return content
    if rules.strip() in content:
        return content
    start = idx + len(needle)
    return content[:start] + rules + content[start:]


def process_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    new = raw

    if OLD_BLOG_HERO_H1.search(new):
        new = OLD_BLOG_HERO_H1.sub(H1_PAIR, new, count=1)

    # Compact templates: only plain h1{Syne...} at line start
    if ".blog-hero h1,.blog-h1{" not in new and OLD_PLAIN_H1.search(new):
        new = OLD_PLAIN_H1.sub(H1_BASE, new, count=1)

    # Mobile: prefer 768px block (most articles)
    new = inject_after_media_open(new, "768", MOBILE_768_INJECT)
    new = inject_after_media_open(new, "700", MOBILE_700_INJECT)

    if new != raw:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    n = 0
    for path in sorted(BLOG_DIR.glob("*.html")):
        if process_file(path):
            n += 1
            print(path.name)
    print("updated:", n)


if __name__ == "__main__":
    main()
