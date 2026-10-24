# Makes media/icon.ico and media/splash.png from the two pictures in media/.
# Run it again after changing VERSION or the pictures.
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

MEDIA = Path(__file__).parent / "media"
VERSION = "0.1.0"

icon = Image.open(MEDIA / "icon-512.png")
icon.save(MEDIA / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

art = Image.open(MEDIA / "Anubis.png").convert("RGBA")
art = art.resize((art.width * 440 // art.height, 440), Image.LANCZOS)
alpha = art.getchannel("A").point(lambda a: 255 if a >= 160 else 0)
art.putalpha(alpha)

splash = Image.new("RGBA", (art.width, art.height + 70), (0, 0, 0, 0))
splash.paste(art, (0, 0))
draw = ImageDraw.Draw(splash)
left = splash.width // 2 - 170
top = splash.height - 62
draw.rectangle((left, top, left + 340, top + 56), fill="#1d0f11", outline="#c8102e")
font = ImageFont.truetype("segoeuib.ttf", 19)
draw.text((splash.width // 2, top + 16), f"PodSim  v{VERSION}", fill="#ffc72c", font=font, anchor="mm")
splash.save(MEDIA / "splash.png")
print(splash.size, "text at", (left + 12, top + 50))
