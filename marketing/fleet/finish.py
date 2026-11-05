"""Fleet album: AI in-scene photos (ai/<car>-scene.png, made in Canva from the empty shop + the real car photo)
get the branded contact footer and are saved as <car>-album.jpg."""
import sys
from PIL import Image
import album as A

CARS = ['bayon-teal', 'tiggo-grey', 'clio5-white', 'clio6-grey']

def finish(name):
    fr = Image.open(f'ai/{name}-scene.png').convert('RGBA').resize((A.W, A.H), Image.LANCZOS)
    A.contacts_footer(fr)
    out = f'{name}-album.jpg'
    fr.convert('RGB').save(out, quality=95)
    return out

if __name__ == '__main__':
    for n in (sys.argv[1:] or CARS):
        print(finish(n))
