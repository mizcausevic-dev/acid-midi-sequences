"""Procedural raster artwork and ffmpeg media steps.

The painter is original and deterministic. It draws an abstract timing system:
a ring, a tick grid, a rolling ribbon, and kick markers. It is an illustration,
not a photograph of a session or of performers.

DejaVu Sans Bold is used only to rasterize the disclosure into the film and the
poster. The font file is not shipped.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ON_PICTURE = "preview, not master"


def _clamp(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else value


def paint(width: int, height: int, framing: str) -> bytes:
    ribbon = [0] * width
    support = [0] * width
    block = max(8, width // 52)
    for x in range(width):
        phase = (x // block) * block / max(1, width - 1)
        wave = (1.0 if int(phase * 12) % 2 == 0 else -1.0) * 0.72
        envelope = math.sin(phase * math.pi)
        center = height * (0.58 if framing == "square" else 0.50)
        amplitude = height * (0.20 if framing == "square" else 0.17)
        ribbon[x] = int(center - wave * envelope * amplitude)
        support[x] = int(center + 8 - math.sin(phase * math.pi * 2.0) * amplitude * 0.28)
    if framing == "square":
        cone_x = int(width * 0.50)
        cone_y = int(height * 0.34)
    else:
        cone_x = int(width * 0.16)
        cone_y = int(height * 0.46)
    kick_xs = [int((index + 0.5) * width / 16) for index in range(16)]
    kick_y = int(height * 0.78)
    cone_limit = width * 0.22
    pixels = bytearray(width * height * 3)
    for y in range(height):
        row = y * width * 3
        shade = y / max(1, height - 1)
        base_r = int(7 + 12 * shade)
        base_g = int(6 + 8 * shade)
        base_b = int(10 + 22 * shade)
        dy = y - cone_y
        near_kick = abs(y - kick_y) <= 5
        on_baseline = abs(y - kick_y) <= 1
        for x in range(width):
            r, g, b = base_r, base_g, base_b
            if x % (block * 4) == 0:
                r, g, b = 28, 36, 42
            elif x % block == 0:
                r, g, b = 16, 18, 26
            if on_baseline:
                r, g, b = 40, 48, 58
            dx = x - cone_x
            if abs(dx) < cone_limit and abs(dy) < cone_limit:
                dist = math.hypot(dx, dy)
                if dist < cone_limit and int(dist) % 28 < 2:
                    mix = 0.55 if dist > 36 else 0.25
                    r = int(r * (1 - mix))
                    g = int(g * (1 - mix) + 224 * mix)
                    b = int(b * (1 - mix) + 255 * mix)
            gap = y - ribbon[x]
            if -2 <= gap <= 2:
                r, g, b = 255, 62, 165
            elif gap == 3 or gap == -3:
                r, g, b = 120, 30, 70
            if abs(y - support[x]) <= 1:
                r, g, b = 57, 255, 20
            if near_kick:
                for kick_x in kick_xs:
                    if abs(x - kick_x) <= 5:
                        r, g, b = 255, 45, 85
                        break
            pixels[row + x * 3] = r
            pixels[row + x * 3 + 1] = g
            pixels[row + x * 3 + 2] = b
    return bytes(pixels)


def write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + " ".join(command)
            + "\n"
            + completed.stderr[-2000:]
        )


def ppm_to_jpeg(ppm: Path, jpeg: Path, quality: int = 3) -> None:
    jpeg.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", "-q:v", str(quality), str(jpeg)])


def draw_disclosure(source: Path, dest: Path, textfile: Path) -> list[str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-vf",
        (
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest),
    ]
    run(command)
    return command


def encode_mp3(wav: Path, mp3: Path) -> list[str]:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", "192k",
        str(mp3),
    ]
    run(command)
    return command


def encode_film(plate: Path, mp3: Path, mp4: Path, textfile: Path, duration: str) -> list[str]:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plate),
        "-i", str(mp3),
        "-t", duration,
        "-vf",
        (
            "scale=1280:720,"
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-r", "24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(mp4),
    ]
    run(command)
    return command


def derive_social(hero: Path, square: Path, portrait: Path, card: Path) -> dict[str, list[str]]:
    portrait.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    portrait_cmd = [
        "ffmpeg", "-y", "-i", str(square),
        "-vf", "crop=864:1080:108:0,scale=1080:1350",
        "-q:v", "3",
        str(portrait),
    ]
    card_cmd = [
        "ffmpeg", "-y", "-i", str(hero),
        "-vf", "scale=1600:900",
        "-q:v", "3",
        str(card),
    ]
    run(portrait_cmd)
    run(card_cmd)
    return {"portrait": portrait_cmd, "card": card_cmd}
