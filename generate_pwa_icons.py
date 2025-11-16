#!/usr/bin/env python3
"""
Generate icon PNG files for PWA manifest.
Requires: pip install pillow
"""

from PIL import Image, ImageDraw
import os

ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
ICON_DIR = 'static/icons'

def create_app_icon(size, maskable=False):
    """Create a simple library-themed app icon."""
    # Create image with rounded corners
    img = Image.new('RGBA', (size, size), (102, 126, 234, 255))  # Primary color #667eea
    draw = ImageDraw.Draw(img)
    
    # Draw a simple book icon in white
    margin = int(size * 0.2)
    book_x1, book_y1 = margin, margin
    book_x2, book_y2 = size - margin, size - margin
    
    # Draw book outline
    draw.rectangle([book_x1, book_y1, book_x2, book_y2], outline='white', width=max(1, size // 32))
    
    # Draw spine line
    spine_x = size // 2
    draw.line([(spine_x, book_y1), (spine_x, book_y2)], fill='white', width=max(1, size // 32))
    
    # Draw page lines
    line_y_start = book_y1 + int(size * 0.15)
    line_y_end = book_y2 - int(size * 0.1)
    for i in range(3):
        y = line_y_start + (line_y_end - line_y_start) * i // 2
        draw.line([(book_x1 + int(size * 0.1), y), (spine_x - int(size * 0.05), y)], fill='white', width=max(1, size // 48))
    
    return img

# Ensure icon directory exists
os.makedirs(ICON_DIR, exist_ok=True)

# Generate regular icons
for size in ICON_SIZES:
    icon = create_app_icon(size)
    icon_path = os.path.join(ICON_DIR, f'icon-{size}x{size}.png')
    icon.save(icon_path, 'PNG')
    print(f'✅ Created {icon_path}')

# Generate maskable icons (for adaptive icons on Android)
for size in [192, 512]:
    icon = create_app_icon(size, maskable=True)
    icon_path = os.path.join(ICON_DIR, f'icon-{size}x{size}-maskable.png')
    icon.save(icon_path, 'PNG')
    print(f'✅ Created {icon_path}')

# Create screenshot placeholders
os.makedirs(os.path.join(ICON_DIR, '..', 'screenshots'), exist_ok=True)

# Narrow screenshot (540x720)
narrow_ss = Image.new('RGB', (540, 720), (102, 126, 234))
draw = ImageDraw.Draw(narrow_ss)
draw.text((50, 350), 'Library App', fill='white')
narrow_ss.save(os.path.join(ICON_DIR, '..', 'screenshots', 'screenshot-540x720.png'), 'PNG')
print(f'✅ Created static/screenshots/screenshot-540x720.png')

# Wide screenshot (1280x720)
wide_ss = Image.new('RGB', (1280, 720), (102, 126, 234))
draw = ImageDraw.Draw(wide_ss)
draw.text((500, 350), 'Library App', fill='white')
wide_ss.save(os.path.join(ICON_DIR, '..', 'screenshots', 'screenshot-1280x720.png'), 'PNG')
print(f'✅ Created static/screenshots/screenshot-1280x720.png')

print('\n✨ All PWA icons generated successfully!')
