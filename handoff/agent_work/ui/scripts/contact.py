"""contact.py out.png cols cellw img1 img2 ...  -> montage with captions (for reviewing many screenshots at once)"""
import sys
from PIL import Image, ImageDraw
out, cols, cw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); files = sys.argv[4:]
ims = []
for f in files:
    im = Image.open(f).convert('RGB'); r = cw / im.width; ims.append((f, im.resize((cw, max(1, int(im.height * r))))))
rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
H = sum(max(i.height for _, i in r) + 18 for r in rows)
sheet = Image.new('RGB', (cols * (cw + 8), H), 'white'); y = 0
for r in rows:
    x = 0
    for f, im in r:
        sheet.paste(im, (x, y + 16)); ImageDraw.Draw(sheet).text((x + 2, y + 2), f.split('/')[-1][:48], fill='red'); x += cw + 8
    y += max(i.height for _, i in r) + 18
sheet.save(out)
print(sheet.size)
