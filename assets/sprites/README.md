# Character sprite sheets

Every sheet here keeps **all frames of its video, in order**, with the background removed (transparent PNG).
All animations share one canvas: each frame is the same 1080×756 area of the 1080×1080 video (x 0–1080, y 135–891).
The whole character fits in every frame, and it sits in the same place in every animation.
Use the same pivot for all of them and the character stays put when the animation changes.

| Animation | Frames | Grid | Full sheet (frame 1080×756) | Half sheet (frame 540×378) |
| --- | --- | --- | --- | --- |
| `triple_claw_combo/` | 37 | 7 columns × 6 rows (last 5 cells empty) | 7560×4536 | 3780×2268 |
| `heavy_claw_attack/` | 34 | 7 columns × 5 rows (last cell empty) | 7560×3780 | 3780×1890 |

- Frames go left to right, top to bottom: frame `i` is at column `i % 7`, row `i / 7`.
- Play at 30 fps (33 ms per frame).
- Each folder also has the frame rectangles as JSON (Aseprite / TexturePacker "JSON Array" format) and a GIF preview
  on a dark background. The GIF is only for viewing, not for the game.
- `heavy_claw_attack`: in frames 22–24 (counting from 0) the dust from the strike runs past the right edge of the
  video, so that part of the dust was never recorded. It fades out toward that edge instead of ending in a straight cut.
  The character itself is complete in every frame.

## Unity

1. Drop the PNG into `Assets`.
2. Inspector: **Texture Type** `Sprite (2D and UI)`, **Sprite Mode** `Multiple`, **Max Size** `4096` for a half sheet
   or `8192` for a full sheet (the default 2048 shrinks it). Apply.
3. **Sprite Editor → Slice**: **Type** `Grid By Cell Size`, **Pixel Size** `540 × 378` (half) or `1080 × 756` (full),
   **Pivot** `Bottom`. Slice, then Apply. Empty cells at the end are skipped.
4. Select the sprites, drag them into the scene to make the animation, and set **Sample Rate** to `30`.

## Java

```java
BufferedImage sheet = ImageIO.read(new File("assets/sprites/heavy_claw_attack/heavy_claw_attack_spritesheet_half.png"));
int w = 540, h = 378, columns = 7, count = 34;
BufferedImage[] frames = new BufferedImage[count];
for (int i = 0; i < count; i++) {
    frames[i] = sheet.getSubimage((i % columns) * w, (i / columns) * h, w, h);
}
// current frame at 30 fps: frames[(int) (elapsedMillis * 30 / 1000) % count]
```

To regenerate a sheet or add another clip of this character, use `tools/video_to_spritesheet.py` with
`--rect 0 135 1080 891`, so the new animation shares the same canvas. The commands are in the script's docstring.
