This project will take as input a YT URL of a CampusX YT video focused on MCPs and focus on downloding it, extracting the frames and transcripts and finally providing as output - a concrete deliverable in the form of a PDF that contains prose based on the transcripts and frames embedded as figures. The user will set you off to work on this problem autonomously via the command "slash goal at problem_statement.md"

The user will provide the YT URL of CampusX YT video focused on MCPs before setting you off with "slash goal at problem_statement.md"

CampusX YT video URL: https://youtu.be/Zmy439spZB4?si=Xg5vooj4kQKdrgiv

The workflow involves the following steps:
S0) IF POSSIBLE extract metadata from provided YT URL and again ONLY IF POSSIBLE verify that the YT video URL indeed corresponds to a CampusX YT video on MCPs
S1.a) Download the YT video using the free popular library for YT video downloads that you know from your training data
S1.b) After getting visceral experience of downloading the YT video, package S1.a as a GLOBALLY AVAILABLE SKILL across all projects INCLUDING CODE FILES caled "yt-video-download"
S2.a) Extact frames from the downloaded video
S2.b) After getting visceral experience of extracting frames from the downloaded video, packaged S2.a as a GLOBALLY AVAILABLE SKILL across all projects INCLUDING CODE FILES called "video-frames-extract"
S3.a) Extract transcipts from the dowloaded video
S3.b) After getting visceral experience of extracting trascripts from the downloaded video, package S3.a as a GLOBALLY AVAILABLE SKILL across all projects INCLUDING CODE FILES called "video-transcripts-extract"
S4) Create a GLOBALLY AVAILABLE COMPOSITE SKILL called "yt-video-processing" that takes as input a YT URL argument, then sequentially chains "yt-video-download" -> "video-frames-extract" -> "video-transcripts-extract" and then deletes the video
S5) use your "pdf" skill to build a simple pdf explainer based on the transcripts and directly embed the frames as figures where required
S6) use your "email" skill to email the final pdf to vivekjobapp123@gmail.com
S7) run your "sync-os" skill
S8) run your git skill in sequence: "gitcommit" -> "gitpush" -> "gitreadme"
