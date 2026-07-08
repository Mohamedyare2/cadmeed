from PIL import Image
try:
    img = Image.open(r"IMG-20260702-WA0004.jpg").convert("RGB")
    colors = img.getcolors(img.size[0]*img.size[1])
    if colors:
        colors = sorted(colors, key=lambda t: t[0], reverse=True)
        valid_colors = [(count, c) for count, c in colors if c[0] > c[1] and c[1] > c[2] and c[0] - c[2] > 50 and c[0] > 100]
        for count, color in valid_colors[:5]:
            print(f"Hex: #{color[0]:02x}{color[1]:02x}{color[2]:02x} count: {count}")
except Exception as e:
    print(f"Error: {e}")
