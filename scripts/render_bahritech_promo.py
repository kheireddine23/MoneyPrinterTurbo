from __future__ import annotations

import asyncio
import math
import tempfile
from pathlib import Path

import arabic_reshaper
import numpy as np
from bidi.algorithm import get_display
from edge_tts import Communicate
from moviepy import AudioFileClip, VideoClip
from PIL import Image, ImageDraw, ImageFont


WIDTH = 720
HEIGHT = 1280
FPS = 20
DURATION = 22.0
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "storage/tasks/bahritech-marketing/final-1.mp4"
VOICE = "ar-DZ-AminaNeural"
NARRATION = (
    "البحر يناديك؟ BahriTech يعاونك تشوف حالة البحر. "
    "سائح، اكتشف خرجات بحرية. صياد، ورّي صيدك. "
    "حرفي، وصل خدماتك. تاجر معدات، وصل للبحّارة. "
    "مجتمع البحر كامل، في تطبيق واحد. ما يعوّضش خبرة الربّان. "
    "حمّل BahriTech من الرابط في البايو."
)

SCENES = [
    ("البحر يناديك؟", "قبل ما تخرج، شوف الحالة وخطّط مليح", "حالة البحر"),
    ("سائح؟", "اكتشف خرجات وتجارب بحرية", "خرجات بحرية"),
    ("صيّاد؟", "عرّف الناس بصيدك اليومي", "صيد اليوم"),
    ("حرفي؟", "وصل خدماتك لناس البحر", "خدمات بحرية"),
    ("تبيع معدات؟", "خلّي البحّارة يلقاو واش يحتاجو", "معدات البحر"),
    ("مجتمع البحر، في تطبيق واحد", "ما يعوّضش خبرة الربّان، بصح يعاونك تكون واجد", "حمّل من الرابط في البايو"),
]

NAVY_TOP = np.array([13, 32, 48], dtype=np.float32)
NAVY_BOTTOM = np.array([24, 58, 70], dtype=np.float32)
TEAL = (51, 222, 190)
WHITE = (248, 251, 250)
MUTED = (181, 203, 207)
CORAL = (255, 151, 112)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_name = "arialbd.ttf" if bold else "arial.ttf"
    font_path = Path("C:/Windows/Fonts") / font_name
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default(size=size)


FONTS = {
    "title": load_font(66, bold=True),
    "body": load_font(34),
    "label": load_font(26, bold=True),
    "small": load_font(23),
    "brand": load_font(35, bold=True),
    "metric": load_font(29, bold=True),
}


def make_background() -> Image.Image:
    gradient = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None, None]
    pixels = NAVY_TOP[None, None, :] * (1.0 - gradient) + NAVY_BOTTOM[None, None, :] * gradient
    pixels = np.broadcast_to(pixels, (HEIGHT, WIDTH, 3)).astype(np.uint8).copy()
    return Image.fromarray(pixels)


BACKGROUND = make_background()


def draw_text(
    draw: ImageDraw.ImageDraw,
    value: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    anchor: str = "mm",
) -> None:
    visual_text = get_display(arabic_reshaper.reshape(value))
    draw.text(xy, visual_text, font=font, fill=fill, anchor=anchor)


def draw_brand(draw: ImageDraw.ImageDraw, t: float, duration: float) -> None:
    draw.rounded_rectangle((42, 40, 103, 101), radius=19, fill=(16, 39, 57), outline=TEAL, width=2)
    draw.arc((54, 56, 91, 87), 190, 350, fill=TEAL, width=4)
    draw_text(draw, "B", (73, 69), load_font(36, bold=True), WHITE)
    draw.text((119, 54), "BahriTech", font=FONTS["brand"], fill=WHITE)
    draw.text((120, 92), "YOUR SEA, CONNECTED", font=load_font(13, bold=True), fill=MUTED)
    draw.rounded_rectangle((566, 61, 678, 70), radius=5, fill=(48, 78, 91))
    progress = min(1.0, max(0.04, t / duration))
    draw.rounded_rectangle((566, 61, 566 + int(112 * progress), 70), radius=5, fill=TEAL)


def draw_sea(draw: ImageDraw.ImageDraw, t: float) -> None:
    horizon = 855
    draw.ellipse((470, 575, 626, 731), fill=(255, 183, 119))
    draw.ellipse((492, 596, 604, 708), fill=(255, 206, 148))
    draw.rectangle((0, horizon, WIDTH, HEIGHT), fill=(16, 62, 78))
    for layer, (color, base, amplitude, wavelength, speed) in enumerate(
        [
            ((26, 91, 104), 884, 15, 180, 15),
            ((22, 78, 94), 928, 19, 220, 24),
            ((17, 66, 81), 1001, 24, 260, 32),
        ]
    ):
        points = [(0, HEIGHT)]
        for x in range(0, WIDTH + 9, 8):
            y = base + math.sin((x / wavelength) * math.tau + t * speed / wavelength + layer) * amplitude
            points.append((x, int(y)))
        points.extend([(WIDTH, HEIGHT)])
        draw.polygon(points, fill=color)
        for x in range(-20, WIDTH, 92):
            y = base + math.sin((x / wavelength) * math.tau + t * speed / wavelength + layer) * amplitude - 5
            draw.line((x, int(y), x + 38, int(y - 1)), fill=(91, 171, 171), width=2)

    boat_x = int(485 + math.sin(t * 0.5) * 17)
    draw.polygon(
        [(boat_x - 92, 855), (boat_x + 97, 855), (boat_x + 68, 884), (boat_x - 62, 884)],
        fill=(11, 33, 47),
    )
    draw.line((boat_x, 786, boat_x, 851), fill=(11, 33, 47), width=5)
    draw.polygon([(boat_x + 5, 792), (boat_x + 61, 844), (boat_x + 5, 844)], fill=(11, 33, 47))


def draw_dashboard(draw: ImageDraw.ImageDraw, label: str, scene_index: int, t: float) -> None:
    float_y = int(math.sin(t * 1.7) * 7)
    top = 614 + float_y
    draw.rounded_rectangle((47, top + 12, 673, top + 294), radius=31, fill=(7, 23, 37, 74))
    draw.rounded_rectangle((42, top, 678, top + 282), radius=30, fill=(21, 45, 62), outline=(77, 114, 127), width=2)
    draw.rounded_rectangle((65, top + 24, 655, top + 80), radius=19, fill=(17, 37, 53))
    draw_text(draw, "BahriTech", (603, top + 51), FONTS["label"], WHITE)
    draw.ellipse((81, top + 41, 96, top + 56), fill=TEAL)
    draw_text(draw, label, (358, top + 125), FONTS["title"], WHITE)
    draw_text(draw, "في بلاصة وحدة", (359, top + 177), FONTS["small"], MUTED)

    if scene_index == 0:
        metrics = [("21.4°", "الحرارة"), ("43°", "اتجاه الرياح"), ("7.4", "كم/س")]
        for i, (number, caption) in enumerate(metrics):
            x = 146 + i * 214
            draw.ellipse((x - 9, top + 220, x + 9, top + 238), outline=TEAL, width=3)
            draw_text(draw, number, (x, top + 258), FONTS["metric"], WHITE)
            draw_text(draw, caption, (x, top + 279), FONTS["small"], MUTED)
    else:
        icon_centers = [118, 253, 388, 523]
        labels = ["السياحة", "الصيد", "الخدمات", "المعدات"]
        for i, (x, text) in enumerate(zip(icon_centers, labels)):
            active = i == scene_index - 1
            fill = TEAL if active else (45, 73, 88)
            draw.ellipse((x - 30, top + 214, x + 30, top + 274), fill=fill)
            draw_text(draw, str(i + 1), (x, top + 244), FONTS["label"], (13, 40, 53) if active else WHITE)
            draw_text(draw, text, (x, top + 300), FONTS["small"], WHITE if active else MUTED)


def draw_frame(t: float, duration: float = DURATION) -> np.ndarray:
    image = BACKGROUND.copy()
    draw = ImageDraw.Draw(image, "RGBA")
    draw_sea(draw, t)
    draw_brand(draw, t, duration)

    scene_duration = duration / len(SCENES)
    scene_index = min(len(SCENES) - 1, int(t / scene_duration))
    local_t = (t - scene_index * scene_duration) / scene_duration
    title, body, card_label = SCENES[scene_index]
    entrance = 1.0 - math.pow(1.0 - min(local_t / 0.18, 1.0), 3)
    offset = int((1.0 - entrance) * 44)

    draw.rounded_rectangle((43, 181, 678, 222), radius=18, fill=(28, 63, 76, 225), outline=(65, 123, 129, 190), width=1)
    draw_text(draw, "من البحر، للبحر", (360, 202), FONTS["small"], TEAL)
    draw_text(draw, title, (360, 324 + offset), FONTS["title"], WHITE)
    draw_text(draw, body, (360, 414 + offset), FONTS["body"], MUTED)

    draw_dashboard(draw, card_label, scene_index, t)

    if scene_index == len(SCENES) - 1:
        draw.rounded_rectangle((84, 934, 636, 1018), radius=27, fill=TEAL)
        draw_text(draw, "حمّل التطبيق اليوم", (360, 976), FONTS["label"], (8, 39, 51))
        draw_text(draw, "الرابط في البايو", (360, 1064), FONTS["body"], WHITE)
        draw_text(draw, "ما تفوّتش فرصتك", (360, 1113), FONTS["label"], CORAL)
        draw_text(draw, "تطبيق يعاونك، وخبرة البحر تبقى للربّان", (360, 1190), FONTS["small"], MUTED)
    else:
        draw_text(draw, "كل واحد من مجتمع البحر عندو بلاصتو", (360, 1055), FONTS["small"], WHITE)
        draw.line((264, 1103, 456, 1103), fill=(72, 142, 147), width=2)
        draw_text(draw, "اكتشف BahriTech", (360, 1144), FONTS["small"], TEAL)

    return np.asarray(image.convert("RGB"))


async def synthesize_voice(path: Path) -> None:
    await Communicate(NARRATION, VOICE, rate="+3%", volume="+0%").save(str(path))


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bahritech-promo-") as temp_dir:
        voice_path = Path(temp_dir) / "narration.mp3"
        asyncio.run(synthesize_voice(voice_path))

        voice = AudioFileClip(str(voice_path))
        duration = max(DURATION, voice.duration)
        video = VideoClip(
            frame_function=lambda frame_time: draw_frame(frame_time, duration),
            duration=duration,
        ).with_fps(FPS)
        video = video.with_audio(voice)
        video.write_videofile(
            str(OUTPUT),
            codec="libx264",
            audio_codec="aac",
            fps=FPS,
            preset="medium",
            bitrate="4500k",
            logger="bar",
        )
        video.close()
        voice.close()

    print(f"VIDEO_FILE={OUTPUT.resolve()}")


if __name__ == "__main__":
    main()