#!/usr/bin/env python3
"""Standardize Astro blog article frontmatter (src/content/blog/<slug>/index.md|index.mdx).

Modes:
  default   Fill missing optional fields, normalize values and rewrite frontmatter.
  --check   Validate only; exit code 1 when violations are found.
  --dry-run Report planned changes without writing.
  --init    Scaffold a complete frontmatter for a new article (requires --title).

Examples:
  python standardize_frontmatter.py src/content/blog/how-to-learn-pytorch
  python standardize_frontmatter.py src/content/blog/how-to-learn-pytorch --check
  python standardize_frontmatter.py src/content/blog/foo --init --title "..." --description "..."
  python standardize_frontmatter.py src/content/blog/foo --updated-date --ai assisted
"""

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

try:
    from PIL import Image
except ImportError:  # pragma: no cover - color extraction degrades gracefully
    Image = None

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}
CANONICAL_ORDER = [
    "title",
    "description",
    "publishDate",
    "updatedDate",
    "tags",
    "heroImage",
    "draft",
    "language",
    "comment",
    "ai",
]
DEFAULTS = {"tags": [], "draft": False, "language": "English", "comment": True, "ai": "human"}
LANGUAGE_MAP = {
    "中文": "Chinese",
    "汉语": "Chinese",
    "英文": "English",
    "英语": "English",
    "日文": "Japanese",
    "日语": "Japanese",
    "韩文": "Korean",
    "韩语": "Korean",
    "法语": "French",
    "德语": "German",
    "西班牙语": "Spanish",
    "俄语": "Russian",
}
AI_VALUES = {"human", "assisted", "ai"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2})?$")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ASCII_RE = re.compile(r"[A-Za-z]")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")


class FixError(Exception):
    """Raised when frontmatter cannot be fixed automatically."""


def find_article_file(target: Path) -> Path | None:
    if target.is_file():
        return target
    if target.is_dir():
        for name in ("index.md", "index.mdx"):
            candidate = target / name
            if candidate.exists():
                return candidate
    return None


def split_frontmatter(text: str) -> tuple[str | None, str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    return parts[1], parts[2]


def parse_date_value(value) -> str | None:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        candidate = value.strip().strip("'\"")
        if DATE_RE.match(candidate):
            return candidate
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                datetime.strptime(candidate, fmt)
                return candidate
            except ValueError:
                continue
    return None


def pick_hero(article_dir: Path, forced: str | None = None) -> Path | None:
    if forced:
        candidate = Path(forced)
        if not candidate.is_absolute():
            candidate = article_dir / candidate
        return candidate if candidate.is_file() else None
    images = sorted(p for p in article_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if not images:
        return None
    preferred = [p for p in images if re.search(r"(thumbnail|cover)", p.stem, re.IGNORECASE)]
    return (preferred or images)[0]


def dominant_color(image_path: Path) -> str | None:
    if Image is None:
        return None
    try:
        with Image.open(image_path) as im:
            im = im.convert("RGB").resize((1, 1))
            r, g, b = im.getpixel((0, 0))
            return "#%02X%02X%02X" % (r, g, b)
    except Exception:
        return None


def normalize_tags(tags) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        tag = tag.strip()
        if ASCII_RE.search(tag):
            tag = tag.lower().replace("-", " ")
            tag = " ".join(tag.split())
        if not tag:
            continue
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(tag)
    return normalized


def validate(frontmatter: dict, article_dir: Path) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []

    def error(msg: str) -> None:
        issues.append(("ERROR", msg))

    def warn(msg: str) -> None:
        issues.append(("WARN", msg))

    title = frontmatter.get("title")
    if not title:
        error("title: missing or empty (required, at most 60 characters)")
    elif not isinstance(title, str):
        error(f"title: must be a string, got {type(title).__name__}")
    elif len(title) > 60:
        error(f"title: exceeds 60 characters (currently {len(title)})")

    description = frontmatter.get("description")
    if not description:
        error("description: missing or empty (required, 10-160 characters)")
    elif not isinstance(description, str):
        error(f"description: must be a string, got {type(description).__name__}")
    else:
        if len(description) < 10:
            error(f"description: shorter than 10 characters (currently {len(description)})")
        if len(description) > 160:
            error(f"description: exceeds 160 characters (currently {len(description)})")

    publish_date = parse_date_value(frontmatter.get("publishDate"))
    if publish_date is None:
        error(
            "publishDate: missing or invalid format, expected 'YYYY-MM-DD' or "
            f"'YYYY-MM-DD HH:MM:SS' (currently {frontmatter.get('publishDate')!r})"
        )

    if "updatedDate" in frontmatter and frontmatter.get("updatedDate") is not None:
        if parse_date_value(frontmatter.get("updatedDate")) is None:
            error(f"updatedDate: invalid format (currently {frontmatter.get('updatedDate')!r})")

    tags = frontmatter.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            error(f"tags: must be a list, got {type(tags).__name__}")
        else:
            for tag in tags:
                if not isinstance(tag, str):
                    error(f"tags: each item must be a string (currently {tag!r})")
                    continue
                if CJK_RE.search(tag) and ASCII_RE.search(tag):
                    error(f"tags: '{tag}' mixes Chinese and English characters, do not mix within one tag")
                if ASCII_RE.search(tag) and ("-" in tag or tag != tag.lower()):
                    error(
                        f"tags: '{tag}' English tags must be lowercase without hyphens "
                        "(example: machine learning)"
                    )

    hero = frontmatter.get("heroImage")
    if hero is not None:
        if not isinstance(hero, dict):
            error(f"heroImage: must be a mapping, not another type (got {type(hero).__name__})")
        else:
            src = hero.get("src")
            if not src:
                error("heroImage.src: missing")
            elif isinstance(src, str) and not src.startswith(("http://", "https://", "/")):
                if not (article_dir / src.lstrip("./")).exists():
                    warn(f"heroImage.src: '{src}' does not exist in the article directory")
            if "color" in hero and not HEX_RE.match(str(hero["color"])):
                warn(f"heroImage.color: '{hero['color']}' is not a valid 6-digit hex color")

    for key in ("draft", "comment"):
        if key in frontmatter and not isinstance(frontmatter[key], bool):
            warn(f"{key}: must be a boolean (currently {frontmatter[key]!r})")

    language = frontmatter.get("language")
    if language is not None and CJK_RE.search(str(language)):
        error(
            "language: must be an English word (e.g. Chinese/English/Japanese), "
            f"not Chinese characters (currently {language!r})"
        )

    ai = frontmatter.get("ai")
    if ai is not None and str(ai).strip().lower() not in AI_VALUES:
        error(f"ai: must be one of human / assisted / ai (currently {ai!r})")

    return issues


def build_fixed(frontmatter: dict, article_dir: Path, args) -> tuple[dict, list[str]]:
    data = dict(frontmatter)
    changes: list[str] = []

    for required in ("title", "description"):
        value = data.get(required)
        if not value:
            raise FixError(
                f"{required} is missing and cannot be generated automatically; "
                "please provide it first (--title/--description are required with --init)"
            )
        if not isinstance(value, str):
            data[required] = str(value)
            changes.append(f"{required}: converted to string")

    if "publishDate" not in data or not data.get("publishDate"):
        data["publishDate"] = args.publish_date or date.today().isoformat()
        changes.append(f"publishDate: set to {data['publishDate']}")
    else:
        parsed = parse_date_value(data["publishDate"])
        if parsed is None:
            raise FixError(f"publishDate has an invalid format: {data['publishDate']!r}")
        if parsed != data["publishDate"]:
            changes.append(f"publishDate: normalized to {parsed}")
        data["publishDate"] = parsed

    if "updatedDate" in data and data.get("updatedDate") is not None:
        parsed = parse_date_value(data["updatedDate"])
        if parsed is None:
            raise FixError(f"updatedDate has an invalid format: {data['updatedDate']!r}")
        if parsed != data["updatedDate"]:
            changes.append(f"updatedDate: normalized to {parsed}")
        data["updatedDate"] = parsed
    if args.updated_date:
        if isinstance(args.updated_date, str) and parse_date_value(args.updated_date) is None:
            raise FixError(f"--updated-date has an invalid format: {args.updated_date!r}")
        today = args.updated_date if isinstance(args.updated_date, str) else date.today().isoformat()
        if data.get("updatedDate") != today:
            data["updatedDate"] = today
            changes.append(f"updatedDate: set to {today}")

    if "tags" not in data or data.get("tags") is None:
        data["tags"] = list(DEFAULTS["tags"])
        changes.append("tags: defaulted to []")
    else:
        raw = data["tags"] if isinstance(data["tags"], list) else [data["tags"]]
        normalized = normalize_tags(raw)
        if normalized != data["tags"]:
            changes.append(f"tags: normalized to {normalized}")
        data["tags"] = normalized

    hero = data.get("heroImage")
    if isinstance(hero, dict):
        hero = dict(hero)
        src = str(hero.get("src", "")).strip()
        if not src:
            raise FixError("heroImage.src is missing")
        hero["src"] = src
        if "alt" not in hero and data.get("title"):
            hero["alt"] = str(data["title"])
            changes.append("heroImage.alt: derived from the article title")
        color = hero.get("color")
        if not color and src.startswith(("./", "/")):
            extracted = dominant_color(article_dir / src.lstrip("./")) if not src.startswith("/") else None
            if extracted:
                hero["color"] = extracted
                changes.append(f"heroImage.color: extracted {extracted}")
        elif color and not HEX_RE.match(str(color)):
            changes.append(f"heroImage.color: invalid format, removed {color!r}")
            hero.pop("color", None)
        ordered_hero = {key: hero[key] for key in ("src", "alt", "inferSize", "width", "height", "color") if key in hero}
        ordered_hero.update({key: value for key, value in hero.items() if key not in ordered_hero})
        data["heroImage"] = ordered_hero
    elif hero is None:
        image = pick_hero(article_dir, args.hero_image)
        if image:
            new_hero = {"src": f"./{image.name}"}
            if data.get("title"):
                new_hero["alt"] = str(data["title"])
            color = dominant_color(image)
            if color:
                new_hero["color"] = color
            data["heroImage"] = new_hero
            changes.append(f"heroImage: generated as {new_hero}")
        else:
            changes.append("heroImage: no image found in the directory, skipped")
    else:
        raise FixError("heroImage has an invalid format (expected a mapping)")

    for key, default in (("draft", False), ("comment", True)):
        if key not in data:
            data[key] = default
            changes.append(f"{key}: defaulted to {default}")
        elif not isinstance(data[key], bool):
            changes.append(f"{key}: invalid type, reset to {default}")
            data[key] = default

    if "language" not in data:
        data["language"] = DEFAULTS["language"]
        changes.append(f"language: defaulted to {DEFAULTS['language']}")
    else:
        language = str(data["language"]).strip()
        if CJK_RE.search(language):
            mapped = LANGUAGE_MAP.get(language)
            if mapped is None:
                raise FixError(
                    f"language cannot be converted automatically: {language!r}, "
                    "please use an English word"
                )
            changes.append(f"language: converted {language!r} to {mapped}")
            data["language"] = mapped
        else:
            data["language"] = language

    if args.ai:
        ai_value = str(args.ai).strip().lower()
        if ai_value not in AI_VALUES:
            raise FixError(f"--ai must be one of human / assisted / ai (got {ai_value!r})")
        if data.get("ai") != ai_value:
            changes.append(f"ai: set to {ai_value}")
        data["ai"] = ai_value
    elif "ai" not in data:
        data["ai"] = DEFAULTS["ai"]
        changes.append(f"ai: defaulted to {DEFAULTS['ai']} (confirm human/assisted/ai with the user)")
    else:
        ai_value = str(data["ai"]).strip().lower()
        if ai_value not in AI_VALUES:
            raise FixError(f"ai has an invalid value: {data['ai']!r}")
        if ai_value != data["ai"]:
            changes.append(f"ai: normalized to {ai_value}")
        data["ai"] = ai_value

    ordered = {key: data[key] for key in CANONICAL_ORDER if key in data}
    ordered.update({key: value for key, value in data.items() if key not in ordered})
    return ordered, changes


def render(frontmatter: dict, body: str, created_from_scratch: bool = False) -> str:
    yaml_text = yaml.safe_dump(
        frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False, width=4096
    ).strip()
    head = f"---\n{yaml_text}\n---"
    if created_from_scratch and body and not body.startswith("\n"):
        body = "\n\n" + body
    return head + body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="article directory or index.md/index.mdx path")
    parser.add_argument("--check", action="store_true", help="validate only, do not write; exit code 1 on violations")
    parser.add_argument("--dry-run", action="store_true", help="print planned changes without writing")
    parser.add_argument("--init", action="store_true", help="scaffold full frontmatter for a new article")
    parser.add_argument("--title", help="article title (required with --init)")
    parser.add_argument("--description", help="article description (10-160 characters)")
    parser.add_argument("--tags", help="comma-separated tags")
    parser.add_argument("--hero-image", help="cover image file name relative to the article directory")
    parser.add_argument("--publish-date", help="override publishDate, e.g. 2026-08-07")
    parser.add_argument("--updated-date", nargs="?", const=True, help="set updatedDate to today, or to a given date")
    parser.add_argument("--ai", choices=["human", "assisted", "ai"], help="how the content was written")
    parser.add_argument("--language", help="language as an English word, e.g. Chinese")
    parser.add_argument("--draft", dest="draft", action="store_true", help="mark as draft")
    parser.add_argument("--no-draft", dest="draft", action="store_false")
    parser.set_defaults(draft=None)
    parser.add_argument("--comment", dest="comment", action="store_true", help="enable comments")
    parser.add_argument("--no-comment", dest="comment", action="store_false")
    parser.set_defaults(comment=None)
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        if not args.init:
            print(f"Error: path does not exist: {target}")
            return 2
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)

    file_path = find_article_file(target)
    if file_path is None and not (args.init and target.is_dir()):
        print(f"Error: no index.md or index.mdx found ({target})")
        return 2

    if file_path is None:
        file_path = target / "index.md"
        original_text = ""
        had_frontmatter = False
    else:
        original_text = file_path.read_text(encoding="utf-8")
        fm_text, body = split_frontmatter(original_text)
        had_frontmatter = fm_text is not None
        if had_frontmatter:
            try:
                frontmatter = yaml.safe_load(fm_text)
            except yaml.YAMLError as exc:
                print(f"Error: failed to parse frontmatter YAML: {exc}")
                return 2
            if not isinstance(frontmatter, dict):
                print("Error: frontmatter must be a YAML mapping")
                return 2
        else:
            frontmatter = {}
        body = body if had_frontmatter else original_text

    if args.check:
        if not had_frontmatter:
            print("Error: no frontmatter found (use --init to create one for a new article)")
            return 1
        issues = validate(frontmatter, file_path.parent)
        if not issues:
            print("OK: frontmatter is valid")
            return 0
        for severity, message in issues:
            print(f"{severity}: {message}")
        return 1 if any(severity == "ERROR" for severity, _ in issues) else 0

    if args.init and not had_frontmatter:
        if not args.title or not args.description:
            print("Error: --init requires --title and --description")
            return 2
        scaffold = {"title": args.title, "description": args.description}
        scaffold["publishDate"] = args.publish_date or date.today().isoformat()
        if args.tags:
            scaffold["tags"] = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        frontmatter = scaffold

    try:
        fixed, changes = build_fixed(frontmatter, file_path.parent, args)
    except FixError as exc:
        print(f"Error: {exc}")
        return 2

    if had_frontmatter and fm_text is not None and re.search(r"heroImage\s*:\s*\{", fm_text):
        changes.append("heroImage: converted from a single-line mapping to indented block style")

    for option_key, key in (("draft", "draft"), ("comment", "comment")):
        value = getattr(args, option_key)
        if value is not None and fixed.get(key) != value:
            changes.append(f"{key}: set to {value}")
            fixed[key] = value
    if args.language:
        if CJK_RE.search(args.language):
            print(f"Error: --language must be an English word, got {args.language!r}")
            return 2
        if fixed.get("language") != args.language:
            changes.append(f"language: set to {args.language}")
        fixed["language"] = args.language
    if args.tags and not (args.init and not had_frontmatter):
        parsed_tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        normalized = normalize_tags(parsed_tags)
        if fixed.get("tags") != normalized:
            changes.append(f"tags: set to {normalized}")
        fixed["tags"] = normalized

    output = render(fixed, body, created_from_scratch=not had_frontmatter)

    if not changes:
        print("No changes: frontmatter already valid")
        if args.dry_run:
            print(output)
        return 0

    print(f"Target: {file_path}")
    for change in changes:
        print(f"  - {change}")
    if args.dry_run:
        print("(dry-run, nothing written)")
        print(output)
        return 0

    file_path.write_text(output, encoding="utf-8")
    print(f"Written: {file_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
