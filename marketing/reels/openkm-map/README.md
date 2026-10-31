# Open-km reel: «خريطة بخط واحد» (CALL & RENT)

45-second vertical reel (1080×1920, 24 fps). Shot order: key turned in the ignition → red i20 leaves the office → continuous zoom-out (photo → satellite → map) → red route with map/place alternation (Belgrad Forest, Şile, Sapanca, Bursa/Uludağ) → red ∞, with the logo and contacts entering under it.

## Contents
- `hf/`: the six AI clips (Higgsfield and Kling) as 1080p re-encodes. Their native audio is used for the key and office shots.
- `higgs-inputs/`: the start-frame images and the order they were used in.
- `km/finalreel.py`: the whole edit (timeline, zoom-out, route, finale, sound mix, encode).
- `km/zoomdemo.py`, `km/mapboard3.py`, `km/boards.py`: shared helpers (clouds, pins, labels, text).
- `map/`: Esri tile helpers. Tiles are fetched on demand and are not committed. Attribution is drawn on every map frame.
- `final/CALLRENT-openkm-map-FINAL.mp4`: the delivered version.

## Rebuild
```bash
cd marketing/reels/openkm-map
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
for c in 1-key 2-office-clean 3-forest 4-sile 5-sapanca 6-uludag; do
  mkdir -p hf/fr_$c; $FF -v error -y -i hf/$c.mp4 -vf fps=24 -q:v 2 hf/fr_$c/%04d.jpg; done
cd km
python3 finalreel.py prefetch                                         # downloads map + satellite tiles once
python3 finalreel.py check 15 21 42.6                                 # contact sheet -> final_chk.jpg
for a in $(seq 0 137 1091); do python3 finalreel.py chunk $a $((a+137)) & done; wait
python3 finalreel.py sound
python3 finalreel.py encode ../final/CALLRENT-openkm-map-FINAL.mp4 4700   # about 28 MB
```
Requires Pillow, numpy, imageio-ffmpeg, and network access to server.arcgisonline.com.
