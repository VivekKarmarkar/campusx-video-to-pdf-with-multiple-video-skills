"""S3.a inline transcript extraction.

Run faster-whisper on the downloaded video and dump:
  transcript.txt       — plain segment-joined prose
  transcript.json      — segment list with start/end/text for downstream alignment
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from faster_whisper import WhisperModel


def transcribe(video_path: str, model_size: str = "small") -> None:
    video = Path(video_path)
    if not video.is_file():
        sys.exit(f"video not found: {video}")

    try:
        import ctranslate2

        cuda_devices = ctranslate2.get_cuda_device_count()
    except Exception:
        cuda_devices = 0

    if cuda_devices > 0:
        device, compute_type = "cuda", "float16"
    else:
        device, compute_type = "cpu", "int8"

    print(f"[transcribe] loading model={model_size} on {device}/{compute_type}")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print(f"[transcribe] starting transcription of {video.name}")
    t0 = time.monotonic()
    segments_iter, info = model.transcribe(
        str(video),
        language="en",
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    segments = []
    for seg in segments_iter:
        segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
        if len(segments) % 25 == 0:
            print(f"  …{len(segments)} segments  ({seg.end:.0f}s of audio processed)")

    elapsed = time.monotonic() - t0

    json_path = video.with_name("transcript.json")
    json_path.write_text(
        json.dumps(
            {
                "language": info.language,
                "duration": info.duration,
                "model": model_size,
                "segments": segments,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    txt_path = video.with_name("transcript.txt")
    txt_path.write_text("\n".join(s["text"] for s in segments))

    print(
        f"[transcribe] done in {elapsed:.1f}s — "
        f"{len(segments)} segments, "
        f"{info.duration:.0f}s of audio, "
        f"realtime factor ~{info.duration / elapsed:.1f}x"
    )
    print(f"  -> {txt_path}")
    print(f"  -> {json_path}")


if __name__ == "__main__":
    transcribe(sys.argv[1] if len(sys.argv) > 1 else "video.mp4")
