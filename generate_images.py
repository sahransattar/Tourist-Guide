import os
from PIL import Image, ImageDraw, ImageFont

img_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(img_dir, exist_ok=True)

images_to_create = [
    ('default_place.jpg', 'Tourist Destination', (14, 165, 233), (15, 23, 42)),
    ('taj_mahal.jpg', 'Taj Mahal - Agra', (244, 244, 245), (14, 116, 144)),
    ('jaipur_palace.jpg', 'Jaipur City Palace', (244, 114, 182), (136, 19, 55)),
    ('goa_beach.jpg', 'Goa Beach & Fort', (251, 191, 36), (15, 118, 110)),
    ('kerala_backwaters.jpg', 'Kerala Backwaters', (52, 211, 153), (6, 78, 59)),
    ('varanasi_ghats.jpg', 'Varanasi Ghats', (249, 115, 22), (124, 45, 18)),
    ('pangong_lake.jpg', 'Pangong Lake Ladakh', (56, 189, 248), (30, 58, 138)),
]

for filename, text, color1, color2 in images_to_create:
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color2)
    draw = ImageDraw.Draw(img)

    # Draw gradient effect
    for y in range(height):
        r = int(color2[0] + (color1[0] - color2[0]) * (y / height))
        g = int(color2[1] + (color1[1] - color2[1]) * (y / height))
        b = int(color2[2] + (color1[2] - color2[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add overlay box
    draw.rectangle([(60, 180), (740, 320)], fill=(0, 0, 0, 120), outline=(255, 255, 255, 100))

    # Draw text
    draw.text((width // 2, height // 2 - 20), text, fill=(255, 255, 255), anchor="mm")
    draw.text((width // 2, height // 2 + 25), "Explore India PWA Guide", fill=(200, 225, 255), anchor="mm")

    filepath = os.path.join(img_dir, filename)
    img.save(filepath, 'JPEG', quality=90)
    print(f"[ASSET] Generated: {filename}")

# Generate App Icons
for size in [192, 512]:
    icon = Image.new('RGB', (size, size), (6, 182, 212))
    draw = ImageDraw.Draw(icon)

    # Draw circle compass background
    draw.ellipse([size * 0.1, size * 0.1, size * 0.9, size * 0.9], fill=(15, 23, 42), outline=(255, 255, 255), width=int(size * 0.03))
    draw.polygon([(size * 0.5, size * 0.2), (size * 0.7, size * 0.7), (size * 0.5, size * 0.5), (size * 0.3, size * 0.7)], fill=(6, 182, 212))

    icon_path = os.path.join(img_dir, f'icon-{size}.png')
    icon.save(icon_path, 'PNG')
    print(f"[ASSET] Generated: icon-{size}.png")

print("All sample images generated successfully!")
