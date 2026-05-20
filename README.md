# campusx-video-to-pdf-with-multiple-video-skills

Turn a CampusX YouTube lecture on **Model Context Protocol (MCP)** into a PDF explainer that pairs scene-change frames with Whisper-transcribed prose — fully autonomously from a single `/goal` invocation.

## Overview

This is a "build the road while driving it" project. The spec ([problem_statement.md](problem_statement.md)) names four skills to be built along the way; running `/goal @problem_statement.md` against the spec creates them globally, then uses them to produce the PDF.

The pipeline:

1. **S0** verifies the YT URL really is CampusX-on-MCP (via `yt-dlp --print` metadata).
2. **S1.a/b** download the video (`yt-dlp`), then crystallize the workflow as a global skill `yt-video-download`.
3. **S2.a/b** extract scene-change frames (`ffmpeg select=gt(scene,0.1)`), then crystallize as `video-frames-extract`.
4. **S3.a/b** transcribe the audio (`faster-whisper` small model, GPU-or-CPU), then crystallize as `video-transcripts-extract`.
5. **S4** assembles a composite skill `yt-video-processing` that chains S1.b → S2.b → S3.b and deletes the source video.
6. **S5** assembles `output.pdf` with `reportlab.Platypus`, aligning each frame with the transcript window centered on its timestamp.
7. **S6** emails the PDF to `vivekjobapp123@gmail.com` via the Gmail API (multipart upload to bypass `ARG_MAX` on the base64 attachment).
8. **S7** syncs the four new skills + README updates into the `claude-code-os` repo.
9. **S8** commits and pushes this repo, then auto-generates this README.

Each `.a/.b` split is deliberate: do the thing inline first (feel the rough edges of the library), then package it as a global skill. The skills outlive this project — they're now available everywhere.

## Output

- **[`output.pdf`](output.pdf)** (1.9 MB) — 50 sections, each pairing one scene-change frame with the Whisper-transcribed speech delivered in the window around that frame. Source: [Model Context Protocol — The Why](https://youtu.be/Zmy439spZB4) by CampusX (52 minutes).

## The four skills this project builds

All four live globally under `~/.claude/skills/`, are mirrored in [claude-code-os](https://github.com/VivekKarmarkar/claude-code-os), and are usable from any project:

| Skill | What it does |
|-------|--------------|
| [`yt-video-download`](https://github.com/VivekKarmarkar/claude-code-os/tree/main/skills/yt-video-download) | Thin `yt-dlp` wrapper. Downloads 720p mp4 to the caller's CWD, with a JS-runtime-free format fallback so it works even without `deno`/`node`. |
| [`video-frames-extract`](https://github.com/VivekKarmarkar/claude-code-os/tree/main/skills/video-frames-extract) | `ffmpeg` scene detector tuned at **0.1** (not the textbook 0.3) because CampusX-style PIP overlays add a ~0.05 motion baseline that suppresses scene scores. Writes a sidecar `scene_metadata.txt` with per-frame `pts_time` for transcript alignment. |
| [`video-transcripts-extract`](https://github.com/VivekKarmarkar/claude-code-os/tree/main/skills/video-transcripts-extract) | `faster-whisper` with CUDA auto-detection and CPU `int8` fallback. Writes `transcript.txt` (prose) and `transcript.json` (segmented with timestamps). |
| [`yt-video-processing`](https://github.com/VivekKarmarkar/claude-code-os/tree/main/skills/yt-video-processing) | Composite that chains the three above and **deletes the source video** on success, leaving only frames + transcript. |

## Repo contents

```
.
├── problem_statement.md       # The 9-step spec (S0–S8) — authoritative
├── video_skill_to_build.md    # Skill names to build in S1.b/S2.b/S3.b
├── CLAUDE.md                  # Guidance for future Claude Code invocations
├── make_pdf.py                # S5: reportlab.Platypus assembler
├── send_pdf_email.py          # S6: gws multipart-upload wrapper (adds attachment support around /email skill)
├── transcribe_inline.py       # S3.a: the visceral-experience transcription script
├── transcript.txt             # Whisper output — 862 segments, English
├── transcript.json            # Same with start/end timestamps per segment
├── frames/
│   ├── frame_0001.jpg … frame_0050.jpg
│   └── scene_metadata.txt     # per-frame pts_time, used by make_pdf.py
└── output.pdf                 # The deliverable
```

## Re-running the pipeline

Once the global skills are in place, the entire workflow collapses to:

```bash
bash ~/.claude/skills/yt-video-processing/run.sh "<youtube-url>"
python3 make_pdf.py
python3 send_pdf_email.py --to recipient@example.com \
  --subject "..." --body "..." --attach output.pdf
```

…or, from inside Claude Code with the spec in front of you, just:

```
/goal @problem_statement.md
```

## Tech stack

- **`yt-dlp`** 2026.x — YouTube download
- **`ffmpeg`** — frame extraction via the `select='gt(scene,0.1)'` filter
- **`faster-whisper`** 1.x on **`ctranslate2`** 4.x — speech-to-text, ~9x realtime on CPU `int8`
- **`reportlab`** 4.x (Platypus) + **Pillow** — PDF assembly
- **`gws`** CLI — Gmail API for the final email delivery
- **Python 3.10** project venv at `.venv/`

## Notes

- The source MP4 is deleted at the end of the pipeline per spec. `.gitignore` belts-and-braces with `*.mp4`.
- Whisper ran on CPU (~5.9 minutes wall-clock for 52-min audio, 8.9× realtime). GPU was attempted but the NVIDIA driver returned `CUDA_ERROR_UNKNOWN` at `cuInit()` despite `nvidia-smi` reporting the GPU idle — a stale-driver-state issue that usually clears with a reboot. The skill's CUDA→CPU fallback handled it transparently.
- Source video metadata used in the PDF: **Channel** CampusX · **Title** *Model Context Protocol - The Why | MCP Trilogy* · **Duration** 52:01 · **Uploaded** 2025-09-07.

## License

This project is published publicly without an explicit license file. The PDF and transcript derive from the CampusX YouTube lecture and remain the IP of the original creator (Nitish Singh / CampusX). The pipeline code and global skills are MIT-style — feel free to reuse.
