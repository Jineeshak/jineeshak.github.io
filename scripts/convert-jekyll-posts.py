#!/usr/bin/env python3
"""Convert the old Jekyll/Chirpy _posts into this site's Astro content format.

Usage: python3 scripts/convert-jekyll-posts.py <posts-dir> <output-dir>
"""
import re, sys, pathlib, yaml

src, out = sys.argv[1], sys.argv[2]
dst = pathlib.Path(out)
dst.mkdir(parents=True, exist_ok=True)
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

for f in sorted(pathlib.Path(src).glob("*.md")):
    text = f.read_text(encoding="utf-8")
    m = FM.match(text)
    if not m:
        print("skip (no front matter):", f)
        continue
    fm = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]

    stem = f.stem
    date_match = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)$", stem)
    file_date, slug_base = date_match.groups() if date_match else (None, stem)
    slug = re.sub(r"[^A-Za-z0-9-]+", "-", slug_base).strip("-")

    title = fm.get("title") or slug_base
    date = str(fm.get("date") or file_date)
    categories = fm.get("categories") or []
    tags = fm.get("tags") or []
    if isinstance(categories, str):
        categories = [categories]
    if isinstance(tags, str):
        tags = [tags]

    # first non-empty paragraph as description
    plain = re.sub(r"```.*?```", "", body, flags=re.S)
    paras = [p.strip() for p in plain.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    description = re.sub(r"[`*_#\[\]]", "", paras[0])[:200].strip() if paras else ""

    out_fm = {
        "title": title,
        "description": description,
        "date": date,
        "slug": slug,
        "categories": categories,
        "tags": tags,
    }
    header = yaml.safe_dump(out_fm, sort_keys=False, allow_unicode=True, width=1000)
    target = dst / f"{slug}.md"
    target.write_text(f"---\n{header}---\n{body.lstrip()}", encoding="utf-8")
    print("wrote", target)
