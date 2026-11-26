"""Generate wordcloud.json from portfolio cards and project articles.

Run from anywhere: python scripts/generate_wordcloud.py
Requires: beautifulsoup4
"""

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "wordcloud.json"
MAX_WORDS = 50
MIN_SCORE = 2.75

# Add words you don't want to appear in the cloud (lowercase).
EXCLUDE = set("""
    project projects page website example examples overview implementation
    result results conclusion figure figures section sections click here
    back link links demo demos code see shown show following using used use
    work works working well make made can would could one two three
    really quite even much many different various something
    http https www com org html github
    jos stam produces new view followed due low chance produce
""".split())

# Standard English stop words; kept locally to avoid an NLP dependency.
STOPWORDS = set("""
    a about above across after afterwards again against all almost alone
    along already also although always am among amongst an and another any
    anyone anything are around as at be became because become becomes been
    before behind being below beside besides between beyond both but by
    cannot could did do does doing done down during each either else enough
    especially etc ever every everyone everything few first for former
    formerly from further had has have having he her here hers herself him
    himself his how however i if in into is it its itself just last latter
    least less like may me meanwhile might mine more moreover most mostly
    much must my myself neither never nevertheless next no nobody none nor
    not nothing now of off often on once one only onto or other others our
    ours ourselves out over own per perhaps rather same seem seemed seems
    several she should since so some somehow someone something sometimes
    somewhere still such than that the their theirs them themselves then
    there therefore these they this those though through throughout thus
    to together too toward towards under unless until up upon us very via
    was we were what whatever when whenever where whereas wherever whether
    which while who whoever whom whose why will with within without would
    yet you your yours yourself yourselves
""".split())

# Only explicit equivalences: automatic stemming would produce ugly labels.
ALIASES = {
    "maths": "mathematics", "mathematical": "mathematics",
    "simulations": "simulation", "algorithms": "algorithm",
    "equations": "equation", "methods": "method",
    "ripples": "ripple", "waves": "wave", "fluids": "fluid",
    "sets": "set", "graphs": "graph", "languages": "language",
    "functions": "function", "vectors": "vector", "shaders": "shader",
    "iterations": "iteration", "pixels": "pixel",
    "matrices": "matrix", "models": "model",
    "parallelised": "parallelisation", "parallelized": "parallelisation",
    "optimization": "optimisation",
}

DISPLAY = {
    "c++": "C++", "c#": "C#", "gpu": "GPU", "webgpu": "WebGPU",
    "opencl": "OpenCL", "hpc": "HPC", "aoc": "AoC",
    "ascii": "ASCII", "javascript": "JavaScript", "webgl": "WebGL",
    "julia": "Julia", "python": "Python", "java": "Java",
}

WORDS = re.compile(r"(?<!\w)(?:c\+\+|c#|[a-z][a-z0-9]*)(?!\w)", re.I)
TEX = re.compile(r"\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$|\$[^$]*\$", re.S)
UNWANTED = "script, style, noscript, template, iframe, svg, canvas, pre, code, math"
IGNORED = STOPWORDS | EXCLUDE


def count_words(text):
    counts = Counter()
    for match in WORDS.finditer(TEX.sub(" ", text).casefold()):
        word = ALIASES.get(match.group(), match.group())
        if (len(word) >= 3 or word in {"c++", "c#"}) and word not in IGNORED:
            counts[word] += 1
    return counts


def card_texts():
    """Return {relative project HTML path: (title, description)}."""
    soup = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
    cards = {}
    for link in soup.select("#projectGrid a.project-card[href]"):
        path = urlsplit(link["href"]).path.lstrip("/")
        if not (path.startswith("projects/") and path.endswith(".html")):
            continue
        paragraphs = link.find_all("p")
        if not paragraphs:
            continue
        title = paragraphs[0].get_text(" ", strip=True)
        description = " ".join(p.get_text(" ", strip=True) for p in paragraphs[1:])
        cards[path] = (title, description)
    return cards


def article_text(path):
    if not path.is_file():
        return ""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    article = soup.select_one("main article")
    if article is None:
        return ""  # Some projects only embed an app; their card still counts.
    for element in article.select(UNWANTED):
        element.decompose()
    return article.get_text(" ", strip=True)


def main():
    cards = card_texts()
    paths = {p.relative_to(ROOT).as_posix() for p in (ROOT / "projects").glob("*.html")}
    paths.update(cards)
    if not paths:
        raise RuntimeError("No project articles or cards found")

    scores = defaultdict(float)
    for relative_path in sorted(paths):
        title, description = cards.get(relative_path, ("", ""))
        title_counts = count_words(title)
        desc_counts = count_words(description)
        body_counts = count_words(article_text(ROOT / relative_path))

        for word in title_counts.keys() | desc_counts.keys() | body_counts.keys():
            scores[word] += (
                4 * (word in title_counts)
                + 2 * math.log2(1 + desc_counts[word])
                + math.log2(1 + min(body_counts[word], 20))
            )

    ranked = sorted(
        ((word, score) for word, score in scores.items() if score >= MIN_SCORE),
        key=lambda item: (-item[1], item[0]),
    )[:MAX_WORDS]
    if not ranked:
        raise RuntimeError("No words met the minimum score")

    data = [[DISPLAY.get(word, word), round(score, 2)] for word, score in ranked]
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Analysed {len(paths)} projects ({len(cards)} cards); wrote {len(data)} words to {OUTPUT.name}")
    print("Top words:", ", ".join(f"{word} ({score:.1f})" for word, score in ranked[:15]))


if __name__ == "__main__":
    main()
