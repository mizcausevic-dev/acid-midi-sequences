"""Catalog-backed static preview page. No checkout and no client-side requirement."""

from __future__ import annotations

import html
from pathlib import Path

from tools.article import PARAGRAPHS, SUBTITLE, TAG_LINE, TITLE
from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _diagram() -> str:
    boxes = [
        (40, 40, "Canonical score"),
        (250, 40, "MIDI files"),
        (460, 40, "Reopened-byte report"),
        (700, 40, "MP3 preview"),
        (910, 40, "MP4 film"),
        (40, 160, "Raster stills"),
        (280, 160, "Social drafts"),
        (520, 160, "Catalog"),
        (740, 160, "This page"),
    ]
    parts = [
        '<svg class="diagram" viewBox="0 0 1120 250" role="img" aria-labelledby="diagram-title">',
        '<title id="diagram-title">File contract from score and MIDI through validation, preview, and film. Stills lead to social drafts. The catalog leads to this page.</title>',
    ]
    arrows = [(190, 78, 250, 78), (400, 78, 460, 78), (650, 78, 700, 78), (850, 78, 910, 78), (190, 198, 280, 198), (450, 198, 520, 198), (670, 198, 740, 198)]
    for x1, y1, x2, y2 in arrows:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />')
        parts.append(f'<polygon points="{x2},{y2} {x2-8},{y2-4} {x2-8},{y2+4}" />')
    for x, y, label in boxes:
        parts.append(f'<rect x="{x}" y="{y}" width="150" height="76" rx="8" />')
        parts.append(f'<text x="{x + 75}" y="{y + 44}">{_esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _set_map(catalog: dict) -> str:
    parts_by_study: dict[str, list[dict]] = {}
    for part in catalog["parts"]:
        parts_by_study.setdefault(part["study_id"], []).append(part)
    rows = []
    for study in catalog["studies"]:
        chips = []
        for part in parts_by_study[study["id"]]:
            kind = "core" if part["core"] else "reference"
            chips.append(f'<li class="{kind}"><code>{_esc(part["id"])}</code></li>')
        rows.append(
            "<section class=\"map-row\">"
            f"<h3>{_esc(study['id'])} {_esc(study['title'])}</h3>"
            f"<p>{_esc(study['bpm'])} BPM, {_esc(study['bars'])} bars, {_esc(study['collection_name'])}</p>"
            f"<ul>{''.join(chips)}</ul>"
            "</section>"
        )
    return "".join(rows)


def _studies(catalog: dict) -> str:
    blocks = []
    parts_by_study: dict[str, list[dict]] = {}
    for part in catalog["parts"]:
        parts_by_study.setdefault(part["study_id"], []).append(part)
    for study in catalog["studies"]:
        files = []
        for part in parts_by_study[study["id"]]:
            label = "core" if part["core"] else "reference"
            files.append(
                "<li>"
                f"<a href=\"{_esc(part['path'])}\">{_esc(part['path'])}</a> "
                f"<span>{_esc(part['role'])} {_esc(part['variation'] or '')} · {label} · "
                f"{_esc(part['notes'])} notes · channel {_esc(part['channel'] + 1)}</span>"
                "</li>"
            )
        departures = study["departures"] or ["None."]
        departure_text = " ".join(departures)
        blocks.append(
            f"<article class=\"study\" id=\"{_esc(study['id'])}\">"
            f"<h3>{_esc(study['title'])}</h3>"
            "<dl>"
            f"<div><dt>ID</dt><dd><code>{_esc(study['id'])}</code></dd></div>"
            f"<div><dt>Tempo</dt><dd>{_esc(study['bpm'])} BPM requested, {_esc(round(study['effective_bpm'], 5))} effective</dd></div>"
            f"<div><dt>Meter and length</dt><dd>{_esc(study['meter'])}, {_esc(study['bars'])} bars, {_esc(study['bar_ticks'])} ticks per bar</dd></div>"
            f"<div><dt>Tonal reference</dt><dd>{_esc(study['tonal_reference'])}</dd></div>"
            f"<div><dt>Collection</dt><dd>{_esc(study['collection_name'])} pitch classes {_esc(study['pitch_classes'])}</dd></div>"
            f"<div><dt>Seed</dt><dd>{_esc(study['seed'])}. No stochastic draws.</dd></div>"
            f"<div><dt>Identity</dt><dd>{_esc(study['identity'])}</dd></div>"
            f"<div><dt>Departures</dt><dd>{_esc(departure_text)}</dd></div>"
            f"<div><dt>Limitations</dt><dd>{_esc(study['limitations'])}</dd></div>"
            "</dl>"
            f"<ul class=\"files\">{''.join(files)}</ul>"
            "</article>"
        )
    return "".join(blocks)


def render_page(catalog: dict, report: dict, preview: dict, film: dict) -> str:
    duration = f"{preview['score_seconds']:.3f}"
    encoded = f"{preview['seconds_encoded']:.3f}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Acid MIDI Sequences</title>
  <meta name="description" content="Eight original note-only acid sequence studies, a matched MIDI validation report, and a simple-synth preview that is not a master.">
  <link rel="icon" href="art/mark.svg" type="image/svg+xml">
  <style>
    :root {{
      --ink: #07060a;
      --panel: #14121c;
      --bone: #f4f1ea;
      --muted: #b7b3c7;
      --acid: #d6ff3f;
      --hot: #ff2d55;
      --cyber: #7ee7ff;
      --line: rgba(244, 241, 234, 0.16);
      --grape: #8b5cff;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px),
        var(--ink);
      background-size: 44px 44px, 44px 44px, auto;
      color: var(--bone);
      font-family: "Space Grotesk", "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    a {{ color: var(--acid); }}
    a:focus-visible, video:focus-visible, audio:focus-visible, .skip:focus {{
      outline: 2px solid var(--acid);
      outline-offset: 3px;
    }}
    .skip {{
      position: absolute;
      left: 1rem;
      top: -4rem;
      background: var(--acid);
      color: #111;
      padding: .4rem .7rem;
    }}
    .skip:focus {{ top: 1rem; }}
    header, main, footer {{ width: min(1120px, calc(100% - 2rem)); margin: 0 auto; }}
    header {{ padding: 1.5rem 0 1rem; }}
    .kicker {{
      letter-spacing: .14em;
      text-transform: uppercase;
      color: var(--cyber);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: .78rem;
    }}
    h1 {{ font-size: clamp(2.2rem, 6vw, 4.4rem); line-height: .92; margin: .3rem 0; letter-spacing: -.03em; }}
    h2 {{ margin-top: 2.4rem; font-size: 1.5rem; }}
    h3 {{ margin-bottom: .2rem; }}
    .status {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }}
    .chip {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,.03);
      padding: .35rem .6rem;
      border-radius: 999px;
      font-size: .85rem;
    }}
    .chip.hot {{ color: var(--hot); border-color: rgba(255,45,85,.5); animation: pulse-glow 2.8s ease-in-out infinite; }}
    @keyframes pulse-glow {{
      0%, 100% {{ box-shadow: 0 0 rgba(255,45,85,.0); }}
      50% {{ box-shadow: 0 0 18px rgba(255,45,85,.35); }}
    }}
    figure {{ margin: 1rem 0; }}
    img, video, audio {{ width: 100%; height: auto; background: #000; }}
    figcaption, .note {{ color: var(--muted); font-size: .95rem; }}
    .panel {{
      background: rgba(20, 18, 28, .92);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 1rem;
      margin: 1rem 0;
    }}
    .warning {{ border-color: var(--acid); }}
    .study {{ border-top: 1px solid var(--line); padding: 1rem 0; }}
    dl {{ display: grid; grid-template-columns: 11rem 1fr; gap: .35rem .8rem; margin: .6rem 0; }}
    dt {{ color: var(--cyber); font-family: "JetBrains Mono", ui-monospace, monospace; font-size: .78rem; }}
    dd {{ margin: 0; }}
    ul {{ padding-left: 1.1rem; }}
    code {{ font-family: "JetBrains Mono", ui-monospace, monospace; font-size: .86em; }}
    .diagram {{ width: 100%; min-width: 720px; height: auto; }}
    .diagram rect {{ fill: #14121c; stroke: var(--acid); }}
    .diagram line, .diagram polygon {{ stroke: var(--bone); fill: var(--bone); }}
    .diagram text {{ fill: var(--bone); font-size: 13px; text-anchor: middle; font-family: "Space Grotesk", sans-serif; }}
    .scroll {{ overflow-x: auto; }}
    .map-row {{ border-top: 1px solid var(--line); padding: .6rem 0; }}
    .map-row ul {{ display: flex; flex-wrap: wrap; gap: .4rem; list-style: none; padding: 0; }}
    .map-row li {{ border: 1px solid var(--line); padding: .2rem .4rem; border-radius: 6px; }}
    .map-row li.core {{ border-color: var(--acid); }}
    .map-row li.reference {{ border-color: var(--grape); }}
    .checks li {{ margin: .2rem 0; }}
    footer {{ padding: 2rem 0 3rem; color: var(--muted); }}
    @media (max-width: 720px) {{
      dl {{ grid-template-columns: 1fr; }}
      header, main, footer {{ width: min(1120px, calc(100% - 1.2rem)); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      *, *::before, *::after {{
        animation-duration: .001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: .001ms !important;
      }}
    }}
  </style>
</head>
<body>
  <a class="skip" href="#content">Skip to content</a>
  <header>
    <p class="kicker">Note-only MIDI study pack</p>
    <h1>Acid MIDI Sequences</h1>
    <p>Eight original monophonic acid sequences. Two variations each. Reference harmony and kicks are cataloged separately and are not part of the core count.</p>
    <div class="status">
      <span class="chip hot">{_esc(PREVIEW_LINE)}</span>
      <span class="chip">DRAFT publication</span>
      <span class="chip">Validation { _esc(report["result"]) }</span>
    </div>
  </header>
  <main id="content">
    <section>
      <h2>What this is</h2>
      <div class="panel">
        <p>This is a study pack of monophonic acid sequences in 4/4, with one integer tempo per study between 125 and 145 BPM. It is for producers who edit MIDI. The preview is a repo-owned simple synth so the files can be heard without a soundfont. It is not a finished production and it is not for sale here.</p>
        <p>There is no checkout, no scarcity claim, and no live URL. {_esc(PUBLICATION)} The page is the file catalog.</p>
      </div>
    </section>
    <figure>
      <img src="art/hero.jpg" width="1280" height="720" alt="Illustration of an abstract timing grid, a ring, a rolling ribbon, and kick markers. Not a photograph of a recording session or performers.">
      <figcaption>Illustration of a symbolic timing system. Not a photograph of a recording session or of performers.</figcaption>
    </figure>
    <section>
      <h2>Film</h2>
      <p class="note">The picture reads “{_esc(ON_PICTURE)}”. Captions carry the same words. Nothing starts until a control is used.</p>
      <p class="note">{_esc(film["duration_relation"])}</p>
      <video controls preload="metadata" poster="film/poster.jpg" width="1280" height="720" aria-label="Film preview">
        <source src="film/preview.mp4" type="video/mp4">
        <track kind="captions" src="film/preview.vtt" srclang="en" label="English" default>
      </video>
    </section>
    <section>
      <h2>Primary audio preview</h2>
      <p class="note">{_esc(PREVIEW_LINE)}. Score length { _esc(duration) } seconds. The MP3 container probe is { _esc(encoded) } seconds because the encoder adds padding. Source is study 01, variation A, with its harmonic reference and kick-a. Renderer { _esc(preview["renderer"]) }.</p>
      <audio controls preload="metadata" src="preview/preview.mp3" aria-label="Music preview"></audio>
      <p><a href="preview/preview-manifest-Cursor.txt">Preview manifest</a></p>
      <p>{_esc(PROGRAM)}</p>
      <p>The synth mapping is a preview choice. Explicit renderer mappings do not become encoded MIDI instructions. {_esc(AUDITION)}</p>
    </section>
    <section class="panel warning">
      <h2>File warning</h2>
      <p>{_esc(WARNING)}</p>
      <p><a href="midi/arrangement.mid">midi/arrangement.mid</a> is the 16-bar preview arrangement of study 01 only. <a href="midi/validation-Cursor.json">Validation report</a>.</p>
    </section>
    <section>
      <h2>Studies</h2>
      <p class="note">Core identity is the acid sequence. Harmonic references and kicks are reference-only. Container lengths were chosen before the notes were written. PPQ is 960. Pitched notes stay in 36-84. The sequence is monophonic. Glide is not encoded.</p>
      {_studies(catalog)}
    </section>
    <section>
      <h2>File contract</h2>
      <div class="scroll">{_diagram()}</div>
    </section>
    <section>
      <h2>Set map</h2>
      <p class="note">Acid borders are core bass variations. Grape borders are reference parts. IDs match the catalog.</p>
      {_set_map(catalog)}
    </section>
    <section>
      <h2>Validator</h2>
      <p>Result: {_esc(report["result"])}. Validator {_esc(report["validator_version"])}. Generator {_esc(report["generator_version"])}.</p>
      <ul class="checks">
        {''.join(f'<li>{_esc(rule)}</li>' for rule in report["rules"])}
      </ul>
      <p>{_esc(report["repair_note"])}</p>
      <p>{_esc(AUDITION)} Structural checks and signal measurements are not listening. Sample peak in the preview manifest is not LUFS and not true peak. Film duration reported by the encoder probe: {_esc(film["duration_seconds"])} seconds.</p>
    </section>
    <section>
      <h2>Article draft</h2>
      <p class="note">DRAFT. Not published to Medium. { _esc(TAG_LINE) }</p>
      <p><a href="articles/medium-draft-Cursor.md">Markdown draft</a> · <a href="articles/medium-paste-Cursor.txt">Plain-text draft</a></p>
      <article class="panel">
        <h3>{_esc(TITLE)}</h3>
        <p>{_esc(SUBTITLE)}</p>
        {''.join(f'<p>{_esc(paragraph)}</p>' for paragraph in PARAGRAPHS)}
      </article>
    </section>
  </main>
  <footer>
    <p>{_esc(AUDITION)}</p>
    <p>{_esc(PUBLICATION)} Draft files in a public repository are public. This page sets noindex until a deployment is actually verified.</p>
    <p>Square still: <a href="art/square.jpg">art/square.jpg</a>. Poster: <a href="film/poster.jpg">film/poster.jpg</a>.</p>
  </footer>
</body>
</html>
"""


def write_page(path: Path, catalog: dict, report: dict, preview: dict, film: dict) -> None:
    path.write_text(render_page(catalog, report, preview, film), encoding="utf-8")
