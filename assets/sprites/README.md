# Character sprite sheets

Every sheet here keeps **all frames of its video, in order**, with the background removed (transparent PNG).
All animations share one canvas: each frame is the same 1080×756 area of the 1080×1080 video (x 0–1080, y 135–891).
The jump is the exception: it goes higher, so its frames are taller (y 39–891) but end at the same bottom edge.
The whole character fits in every frame, and it sits in the same place in every animation.
Use the `Bottom` pivot for all of them and the character stays put when the animation changes.

| Animation | Frames | Grid | Full sheet (frame 1080×756) | Half sheet (frame 540×378) |
| --- | --- | --- | --- | --- |
| `triple_claw_combo/` | 37 | 7 columns × 6 rows (last 5 cells empty) | 7560×4536 | 3780×2268 |
| `heavy_claw_attack/` | 34 | 7 columns × 5 rows (last cell empty) | 7560×3780 | 3780×1890 |
| `final_heavy_claw_attack/` | 92 | 10 columns × 10 rows (last 8 cells empty) | not made (would be 10800×7560) | 5400×3780 |
| `jump_hallow/` | 66 | 10 columns × 7 rows (last 4 cells empty) | not made (would be 10800×5964) | 5400×2982, **frame 540×426** |

A second character, the rat mage, has its own canvas (x 142–854, y 70–886 of the video, 712×816):

| Animation | Frames | Grid | Full sheet (frame 712×816) | Half sheet (frame 356×408) |
| --- | --- | --- | --- | --- |
| `rat_under_magic_idle/` | 183 | 16 columns × 12 rows (last 9 cells empty) | not made (would be 11392×9792) | 5696×4896 |

- Frames go left to right, top to bottom: frame `i` is at column `i % columns`, row `i / columns`.
- Play at 30 fps (33 ms per frame).
- Each folder also has the frame rectangles as JSON (Aseprite / TexturePacker "JSON Array" format) and a GIF preview
  on a dark background. The GIF is only for viewing, not for the game.
- `heavy_claw_attack`: in frames 22–24 (counting from 0) the dust from the strike runs past the right edge of the
  video, so that part of the dust was never recorded. It fades out toward that edge instead of ending in a straight cut.
  The character itself is complete in every frame.
- `final_heavy_claw_attack`: 92 frames is too many for a full-resolution sheet that a game can load as one texture, so
  it only has the half-size sheet, at the same scale as the other half sheets. Every 5th frame repeats the one before
  it, because the video was converted from 24 to 30 fps. The repeats are kept so the timing matches the video.
  In frames 62–67 (counting from 0) a few fur tips of the cape cross the left edge of the video; the last 8 px there
  are faded.
- `jump_hallow`: the jump rises above the shared canvas, so this sheet's canvas is taller: x 0–1080, y 39–891
  (1080×852, half 540×426). It has the same bottom edge and width as the others, so with the `Bottom` pivot the
  character still stands in the same place. The clip was shot on a green screen; the green light that spilled onto
  the character (claws, skull, body) is removed. The body and cape in the mid-air frames stay darker and more
  olive/orange than in the other animations, because that is how the video lights them.
- `rat_under_magic_idle`: a slow idle, so many neighbouring frames look almost the same; all are kept so the
  timing matches the video. The red sparks around the staff are kept.
- Gaps where the background shows through the character (between cloak and staff, claw and leg, inside the
  staff head) are cut out. Small pale highlights on horns and claws stay.

## Unity

1. Drop the PNG into `Assets`.
2. Inspector: **Texture Type** `Sprite (2D and UI)`, **Sprite Mode** `Multiple`, **Max Size** at least the sheet's
   larger side: `4096` for the 3780-wide half sheets, `8192` for `final_heavy_claw_attack`, `jump_hallow`,
   `rat_under_magic_idle` and the full sheets. The default 2048 shrinks the sheet. Apply.
3. **Sprite Editor → Slice**: **Type** `Grid By Cell Size`, **Pixel Size** `540 × 378` (half) or `1080 × 756` (full),
   except `jump_hallow`: `540 × 426`, and the rat: `356 × 408`. **Pivot** `Bottom`. Slice, then Apply. Empty cells
   at the end are skipped.
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
