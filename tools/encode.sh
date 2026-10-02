#!/usr/bin/env bash
# Encode one video for the site.
#   tools/encode.sh <source.mp4> <slug> [trailer|long]
# trailer: silent looping preview (hover).  long: keeps audio, plays with controls.
# Writes media/<slug>.av1.mp4, media/<slug>.hevc.mp4, media/<slug>.webp,
# tools/palettes/<slug>.json, then rebuilds palettes.js.
set -euo pipefail
in="$1"; slug="$2"; kind="${3:-trailer}"
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/media"; mkdir -p "$out" "$root/tools/palettes"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")

# Poster: most representative frame from the 20-60% stretch of the clip.
ss=$(python3 -c "print(round($dur*0.2,2))"); len=$(python3 -c "print(round($dur*0.4,2))")
ffmpeg -nostdin -v error -y -ss "$ss" -t "$len" -i "$in" \
  -vf "fps=2,thumbnail=12,scale=1600:-2:flags=lanczos" -frames:v 1 -c:v libwebp -quality 78 "$out/$slug.webp"

python3 "$root/tools/palette.py" "$in" > "$root/tools/palettes/$slug.json"

if [[ $kind == trailer ]]; then
  av1_crf=33; hevc_crf=26; audio=(-an)
else
  av1_crf=32; hevc_crf=25
  abr=$(ffprobe -v error -select_streams a:0 -show_entries stream=bit_rate -of csv=p=0 "$in")
  if (( abr <= 160000 )); then audio=(-map 0:a:0 -c:a copy); else audio=(-map 0:a:0 -c:a aac -b:a 160k); fi
fi

ffmpeg -nostdin -v error -y -i "$in" -map 0:v:0 "${audio[@]}" -vf format=yuv420p10le \
  -c:v libsvtav1 -preset 5 -crf $av1_crf -g 120 -svtav1-params tune=0 \
  -map_metadata -1 -movflags +faststart "$out/$slug.av1.mp4" &
ffmpeg -nostdin -v error -y -i "$in" -map 0:v:0 "${audio[@]}" -pix_fmt yuv420p \
  -c:v libx265 -preset slow -crf $hevc_crf -g 120 -tag:v hvc1 -x265-params log-level=error \
  -map_metadata -1 -movflags +faststart "$out/$slug.hevc.mp4" &
wait

python3 "$root/tools/build_palettes.py" "$root/palettes.js"
ls -la "$out/$slug".*
