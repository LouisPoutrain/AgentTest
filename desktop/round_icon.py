import sys
from PIL import Image, ImageDraw

def mask_rounded_rect(img, radius):
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    
    result = img.copy()
    result.putalpha(mask)
    return result

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python round_icon.py <input.jpg> <output.png>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    img = Image.open(input_path).convert("RGBA")
    
    # macOS Big Sur+ corner radius is roughly 22.5% of the size
    # But usually a fixed proportion like 0.225 * width works.
    radius = int(img.width * 0.225)
    
    rounded_img = mask_rounded_rect(img, radius)
    rounded_img.save(output_path, "PNG")
    print(f"Saved rounded icon to {output_path}")
