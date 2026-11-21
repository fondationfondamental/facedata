"""The data dictionary as one HTML page that opens from the disk, with no network.

Step 3 of 3 (dictionary/README.md). Puts dictionary/face_dictionary.json
inside dictionary/template.html and writes dictionary/FACE-data-dictionary.html.
The page reads nothing else: styles, script and data are in the one file.

    .venv/bin/python dictionary/build_html.py
"""

import json
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
PLACE = "__FACE_DICTIONARY_JSON__"


def for_a_script_tag(text):
    """JSON text that can sit inside a <script> element.

    The page's parser would end the element at "</script" and change its
    reading at "<!--". Both can only occur inside a JSON string, where the
    replacements below mean the same characters.
    """
    return text.replace("</", "<\\/").replace("<!--", "\\u003c!--")


def build(json_path=None, template_path=None, target=None):
    """Write the page and return its path."""
    json_path = Path(json_path or FOLDER / "face_dictionary.json")
    template = Path(template_path or FOLDER / "template.html").read_text(encoding="utf-8")
    dictionary = json.loads(json_path.read_text(encoding="utf-8"))             # read it: a broken file must not be published
    data = json.dumps(dictionary, ensure_ascii=False, separators=(",", ":"))
    if template.count(PLACE) != 1:
        raise ValueError("template.html must hold %s exactly once" % PLACE)
    target = Path(target or FOLDER / "FACE-data-dictionary.html")
    target.write_text(template.replace(PLACE, for_a_script_tag(data)), encoding="utf-8")
    return target


if __name__ == "__main__":
    page = build()
    print("%.1f MB -> %s" % (page.stat().st_size / 1e6, page.relative_to(FOLDER.parent)))
