"""S5 — build a PDF explainer that interleaves transcript prose with frame figures.

Inputs (all in CWD):
  transcript.json            — {language, duration, model, segments: [{start,end,text}]}
  frames/scene_metadata.txt  — ffmpeg metadata: per-frame lines `frame:N pts:... pts_time:...` etc.
  frames/frame_NNNN.jpg      — extracted frames

Output:
  output.pdf
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

CWD = Path.cwd()

VIDEO_TITLE = "Model Context Protocol — The Why"
VIDEO_CHANNEL = "CampusX"
VIDEO_URL = "https://youtu.be/Zmy439spZB4"
VIDEO_SERIES = "MCP Trilogy — Part 1"


@dataclass
class Frame:
    path: Path
    pts_time: float


def parse_scene_metadata(path: Path) -> dict[int, float]:
    out: dict[int, float] = {}
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        m = re.match(r"frame:(\d+)\s+pts:\S+\s+pts_time:(\S+)", line)
        if m:
            out[int(m.group(1))] = float(m.group(2))
    return out


def load_frames() -> list[Frame]:
    frames_dir = CWD / "frames"
    paths = sorted(frames_dir.glob("frame_*.jpg"))
    metadata = parse_scene_metadata(frames_dir / "scene_metadata.txt")
    out: list[Frame] = []
    for i, p in enumerate(paths):
        pts = metadata.get(i, float(i) * 60.0)
        out.append(Frame(path=p, pts_time=pts))
    return out


def fmt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:01d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def collect_prose(segments: list[dict], lo: float, hi: float) -> str:
    """Return concatenated prose for transcript segments overlapping [lo, hi]."""
    return " ".join(s["text"] for s in segments if s["start"] < hi and s["end"] > lo).strip()


def build_sections(segments: list[dict], frames: list[Frame], duration: float) -> list:
    """Group transcript into sections aligned to frames.

    Each frame anchors a section whose prose window runs from the previous frame
    (or t=0) up to halfway to the next frame (or end of video).
    """
    sections: list = []
    n = len(frames)
    for i, f in enumerate(frames):
        prev_t = frames[i - 1].pts_time if i > 0 else 0.0
        next_t = frames[i + 1].pts_time if i + 1 < n else duration
        # window: from the midpoint behind this frame to the midpoint ahead.
        lo = (prev_t + f.pts_time) / 2
        hi = (f.pts_time + next_t) / 2
        # but include earlier prose if this is the first frame
        if i == 0:
            lo = 0.0
        if i == n - 1:
            hi = duration
        text = collect_prose(segments, lo, hi)
        sections.append({"frame": f, "lo": lo, "hi": hi, "text": text})
    return sections


def make_pdf(out_path: Path = Path("output.pdf")) -> None:
    transcript = json.loads((CWD / "transcript.json").read_text())
    segments = transcript["segments"]
    duration = float(transcript.get("duration", segments[-1]["end"]))
    frames = load_frames()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleBig",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        spaceAfter=4,
        textColor="#444444",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        spaceAfter=10,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Italic"],
        fontSize=9,
        leading=12,
        textColor="#666666",
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=VIDEO_TITLE,
        author=VIDEO_CHANNEL,
    )

    story = []

    # --- Cover ---
    story.append(Paragraph(VIDEO_TITLE, title_style))
    story.append(Paragraph(f"<b>{VIDEO_SERIES}</b> · {VIDEO_CHANNEL}", subtitle_style))
    story.append(Paragraph(f"<a href='{VIDEO_URL}'>{VIDEO_URL}</a>", subtitle_style))
    story.append(
        Paragraph(
            f"Duration: {fmt_timestamp(duration)} &nbsp;·&nbsp; "
            f"Transcript: Whisper {transcript.get('model','small')} "
            f"({len(segments)} segments) &nbsp;·&nbsp; "
            f"Frames: {len(frames)} scene-change extracts",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 0.25 * inch))

    intro = (
        "This explainer was generated automatically from the CampusX lecture "
        "<i>%s</i> by extracting scene-change frames from the video and aligning "
        "them with a Whisper-transcribed audio track. Each section below pairs a "
        "frame from the lecture with the speech delivered around that point in time. "
        "The frames were chosen by ffmpeg scene-detection at a low (0.10) threshold "
        "so slide transitions, code views, and demos are all captured."
    ) % VIDEO_TITLE
    story.append(Paragraph(intro, body_style))
    story.append(PageBreak())

    # --- Sections ---
    sections = build_sections(segments, frames, duration)
    for i, sec in enumerate(sections, start=1):
        f = sec["frame"]
        story.append(
            Paragraph(
                f"Section {i} — {fmt_timestamp(sec['lo'])} – {fmt_timestamp(sec['hi'])}",
                section_style,
            )
        )

        # Image — fit to a max width preserving aspect ratio.
        max_w = 5.5 * inch
        with PILImage.open(f.path) as img:
            iw, ih = img.size
        scale = min(max_w / iw, (3.5 * inch) / ih)
        img_flow = Image(str(f.path), width=iw * scale, height=ih * scale)
        story.append(img_flow)
        story.append(
            Paragraph(
                f"<i>Figure {i}. Frame at {fmt_timestamp(f.pts_time)}.</i>",
                caption_style,
            )
        )

        text = sec["text"] or "<i>(no transcript in this window)</i>"
        story.append(Paragraph(text, body_style))

    doc.build(story)
    size_kb = out_path.stat().st_size / 1024
    print(f"[make_pdf] wrote {out_path} — {len(sections)} sections, {size_kb:.1f} KB")


if __name__ == "__main__":
    make_pdf()
