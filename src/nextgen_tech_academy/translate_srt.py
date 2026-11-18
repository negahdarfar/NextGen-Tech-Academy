"""Optional offline English-to-Persian SRT translation using Argos Translate."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from .subtitles import validate_srt

BLOCK_RE = re.compile(r"\n\s*\n")

def translate_srt_content(content: str, translate_text) -> str:
    """Translate cue text while preserving SRT indices and timestamps."""
    blocks = BLOCK_RE.split(content.strip()) if content.strip() else []
    translated = []
    for block in blocks:
        lines = block.replace("\r\n", "\n").split("\n")
        if len(lines) < 3 or "-->" not in lines[1]:
            raise ValueError("Input is not a valid SRT cue block")
        translated_text = translate_text("\n".join(lines[2:])).strip()
        if not translated_text:
            raise ValueError("Translator returned an empty subtitle cue")
        translated.append("\n".join(lines[:2] + [translated_text]))
    result = "\n\n".join(translated) + "\n"
    errors = validate_srt(result)
    if errors:
        raise ValueError("Translated SRT failed validation: " + "; ".join(errors))
    return result

def argos_translate(text: str) -> str:
    try:
        import argostranslate.translate
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install argostranslate") from exc
    languages = argostranslate.translate.get_installed_languages()
    source = next((lang for lang in languages if lang.code == "en"), None)
    target = next((lang for lang in languages if lang.code == "fa"), None)
    if source is None or target is None:
        raise RuntimeError("Install Argos Translate English (en) and Persian (fa) language packages first")
    translation = source.get_translation(target)
    if translation is None:
        raise RuntimeError("No installed Argos translation model for en -> fa")
    return translation.translate(text)

def main() -> int:
    parser = argparse.ArgumentParser(description="Translate English SRT to Persian offline with Argos Translate")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("build/subtitles-fa.srt"))
    args = parser.parse_args()
    try:
        source = args.input.read_text(encoding="utf-8-sig")
        result = translate_srt_content(source, argos_translate)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"TRANSLATION FAILED: {exc}\n")
    print(f"PERSIAN SRT READY: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
