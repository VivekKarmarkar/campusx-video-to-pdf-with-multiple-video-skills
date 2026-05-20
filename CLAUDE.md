# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A **spec-only blueprint** (no code yet) for an autonomous workflow that turns a CampusX YouTube video on MCPs into a PDF explainer with embedded frames. The implementation work has not started — the project's two markdown files describe what should happen when work begins.

## Kickoff

The user starts work by running:

```
/goal @problem_statement.md
```

There are no build, lint, or test commands — there is nothing to build yet. The first invocation of `/goal` is what produces all artifacts (skills + PDF + email + git repo).

## Source-of-truth files

- **`problem_statement.md`** — the authoritative spec. Contains the 9-step workflow (S0 through S8), the target YouTube URL, and the destination email. Read this end-to-end before doing anything.
- **`video_skill_to_build.md`** — a short list of the three atomic skill names to be built.

If these two files disagree, **`problem_statement.md` wins** (it is the longer, more deliberate document).

## Critical workflow facts

- **Skills go in `~/.claude/skills/`, NOT in this repo.** S1.b, S2.b, S3.b, and S4 all create *globally available* skills. The repo itself should only hold the spec, any working artifacts (downloaded video gets deleted in S4, frames + transcript stay), and the final PDF.
- **The video is deleted at the end of S4** by the composite skill. Don't commit the source video.
- **The repo is already initialized and public** (via `gitinit PUBLIC`, run manually before any `/goal` invocation). S8 only does `gitcommit -> gitpush -> gitreadme`.
- **Public repo.** Treat the PDF and any committed artifacts accordingly (no private notes, no credentials).

## Naming inconsistency to resolve at runtime

`video_skill_to_build.md` lists skill #3 as `video-transcript-extract` (singular). `problem_statement.md` writes it as `video-transcripts-extract` (plural) in both S3.b and S4. When the work begins, **pick one and use it everywhere** (skill folder name, S4 composite reference, any code). The plural form (`video-transcripts-extract`) is the one repeated more times in the binding spec, so prefer it unless the user says otherwise.

## Skill composition map

The workflow chains existing user skills with new ones. Future Claude should *invoke* the existing skills via the Skill tool, not reimplement them:

| Step | Skill | Status |
|------|-------|--------|
| S1.b | `yt-video-download` | **to be created** by this project |
| S2.b | `video-frames-extract` | **to be created** by this project |
| S3.b | `video-transcripts-extract` | **to be created** by this project |
| S4 | `yt-video-processing` (composite of the above three + cleanup) | **to be created** by this project |
| S5 | `pdf` | already exists globally |
| S6 | `email` | already exists globally |
| S7 | `sync-os` | already exists globally |
| S8 | `gitcommit`, `gitpush`, `gitreadme` | already exist globally |

## The "visceral experience first" pattern

S1.a/S1.b, S2.a/S2.b, and S3.a/S3.b each split into two halves: first **do the thing inline** (raw library call inside this project), then **package it as a global skill**. Do not skip the `.a` half — the spec explicitly wants the implementer to feel the rough edges of the library before crystallizing the skill. This is a deliberate learning-by-doing discipline, not redundancy.

## Output destinations

- **PDF**: produced by S5, lands in this project directory.
- **Email recipient**: `vivekjobapp123@gmail.com` (S6).
- **GitHub repo**: created public by S8.

## Related global rules

Two rules from the user's global `~/.claude/CLAUDE.md` are especially load-bearing here:

1. **Never modify existing working skills.** S1–S4 create *new* skills. The existing `pdf`, `email`, `sync-os`, and `git*` skills are invoked verbatim.
2. **Use a project-local venv** for any Python work in this directory. Create `.venv/` if it doesn't exist before `pip install`-ing `yt-dlp`, frame-extraction libs, or transcript libs.
