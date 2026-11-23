#!/bin/zsh
# Videos und Standbilder vom Termin vor Ort (18.11.2026), 19.11.2026.
#
# Quelle: "Bilder & Videos/Bilder vor Ort 2026-11-18/Videos/" (DJI, HEVC 10 bit,
# 1920x1080, BT.709, nicht im Repo). Die Originale werden nur gelesen.
# Ziel: H.264 (yuv420p, +faststart), ohne Ton, damit jeder Browser sie
# abspielt. Farbe unveraendert: kein Filter, keine Saettigung (Kundenwunsch
# "natuerlich, nicht wie mit Filter").
#
#   (Bis 23.11.2026 erzeugte das Skript auch einen Hero-Film aus Clip 0184.
#   Lukas wollte wieder den urspruenglichen Film hero.mp4; die Hero-Zeilen
#   sind deshalb entfernt, siehe Git-Verlauf d542f12. hero-poster.jpg gehoert
#   wieder zum alten Film und darf hier nicht ueberschrieben werden.)
#   vo-laser.mp4                       Clip 0219, 14 bis 27,8 s: Mitarbeiter am
#       Mikroskop, Schweisslicht am Werkstueck, nahtlos geschlossen (13 s).
#       1280x720, Ziel <= 2,5 MB.
#   vo-laser-poster.jpg                erstes Bild davon.
#   vo-laser-mitarbeiter.jpg           Standbild aus 0218 bei 9,5 s (Karriere).
#
# Aufruf im Projektordner:  zsh tools/fotos-vor-ort/videos.sh
set -e
cd "${0:A:h}/../.."
Q="Bilder & Videos/Bilder vor Ort 2026-11-18/Videos"
# Erst in einen Zwischenordner ausserhalb von OneDrive schreiben und am Ende
# kopieren: ffmpeg brach beim direkten Schreiben in den OneDrive-Ordner mit
# "Operation timed out" ab (19.11.2026).
T=$(mktemp -d)
V=$T I=$T
src() { print -r -- "$Q"/DJI_*_${1}_D.MP4 }
FF=(ffmpeg -v error -y)
H264=(-c:v libx264 -preset slow -pix_fmt yuv420p -profile:v high -movflags +faststart -an)

# Laserschweissen, nahtlose Schleife (Korrekturrunde 1): Quelle 14,0 bis
# 27,8 s. Der Film ist 13 s lang; in den ersten 0,8 s wird das Ende der
# Quelle (27,0 bis 27,8 s) weich in den Anfang (14,0 bis 14,8 s) uebergeblendet.
# Am Schleifenende steht dadurch genau das Bild, mit dem der Film beginnt:
# kein Sprung mehr. Rechnung: out(t) = Mischung aus S(L + t) und S(t) fuer
# t < d, danach S(t); out(L) schliesst an out(0) = S(L) an.
L=13; D=0.8
"${FF[@]}" -ss 14 -t $((L + D)) -i "$(src 0219)" -filter_complex \
  "[0:v]fps=25,scale=1280:-2:flags=lanczos,format=yuv420p,setpts=PTS-STARTPTS,split[a][b];\
   [a]trim=start=${L}:end=$((L + D)),setpts=PTS-STARTPTS[ende];\
   [b]trim=start=0:end=${L},setpts=PTS-STARTPTS[haupt];\
   [ende][haupt]xfade=transition=fade:duration=${D}:offset=0,format=yuv420p[v]" \
  -map "[v]" "${H264[@]}" -crf 27 -g 50 $V/vo-laser.mp4
# Poster = erstes Bild des fertigen Films (dort steht schon die Ueberblendung)
"${FF[@]}" -i $V/vo-laser.mp4 -frames:v 1 -q:v 3 $I/vo-laser-poster.jpg

# Karriere: Standbild, 4:3 aus der Bildmitte rechts (Mitarbeiter ganz im Bild)
"${FF[@]}" -ss 9.5 -i "$(src 0218)" -frames:v 1 \
  -vf "crop=1440:1080:336:0,scale=1200:900:flags=lanczos,unsharp=5:5:0.4" -q:v 3 $I/vo-laser-mitarbeiter.jpg

cp $T/vo-laser.mp4 assets/video/
cp $T/vo-laser-poster.jpg $T/vo-laser-mitarbeiter.jpg assets/img/
rm -rf $T
for f in assets/video/vo-laser.mp4 \
         assets/img/vo-laser-poster.jpg assets/img/vo-laser-mitarbeiter.jpg; do
  printf '%-38s %6d kB\n' $f $(( $(stat -f %z $f) / 1024 ))
done
