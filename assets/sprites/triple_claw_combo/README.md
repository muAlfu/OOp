# Triple claw combo – sprite sheet

Made from `Triple_claw_combo.MOV` (1080×1080, 30 fps, 1.23 s). **All 37 video frames are included, in order.**
The background is removed (transparent PNG).

| File | Sheet size | Grid | Frame size |
| --- | --- | --- | --- |
| `triple_claw_combo_spritesheet.png` | 7336×4320 | 7 columns × 6 rows | 1048×720 (original resolution) |
| `triple_claw_combo_spritesheet_half.png` | 3668×2160 | 7 columns × 6 rows | 524×360 |
| `triple_claw_combo_spritesheet*.json` | frame rectangles + 33 ms per frame (Aseprite / TexturePacker "JSON Array" format, works with Phaser, PixiJS, …) | | |
| `triple_claw_combo_preview.gif` | animation preview on a dark background (not for use in the game) | | |

- Frames go left to right, top to bottom: frame `i` is at column `i % 7`, row `i / 7`. The last 5 cells of row 6 are empty.
- Every frame is cut with the same rectangle, so the whole character fits in every cell (at least 16 px of empty space
  around it at full size) and it stays in the same place from frame to frame. Draw each frame at the same position,
  with no per-frame offsets.
- Play at 30 fps (33 ms per frame).

Java example (half-size sheet):

```java
BufferedImage sheet = ImageIO.read(new File("assets/sprites/triple_claw_combo/triple_claw_combo_spritesheet_half.png"));
int w = 524, h = 360, columns = 7, count = 37;
BufferedImage[] frames = new BufferedImage[count];
for (int i = 0; i < count; i++) {
    frames[i] = sheet.getSubimage((i % columns) * w, (i / columns) * h, w, h);
}
// current frame at 30 fps: frames[(int) (elapsedMillis * 30 / 1000) % count]
```

To regenerate the sheet or make one from another clip, use `tools/video_to_spritesheet.py`. Usage is in the script's docstring.
