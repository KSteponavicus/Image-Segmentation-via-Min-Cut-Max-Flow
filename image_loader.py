from collections import defaultdict
from PIL import Image
import math

# image = Image.open("small_test.jpg")
# image2 = Image.open("dog.jpg")

LAMBDA = 100


def get_distributions(image, pixels):
    eps = 0.001
    proba_bg = dict(zip(range(0,256), [eps] * 256))

    counts = defaultdict(int)
    for (x,y) in pixels:
        Ip = image.getpixel((x, y))[0]
        proba_bg[Ip] = proba_bg[Ip] + 1

    total = sum(proba_bg.values(), 0.0)
    return {k: v / total for k, v in proba_bg.items()}

# print(get_distributions(image, [(0,1), (1,0)]))



def image_to_graph(image, fg_pixels, bg_pixels, sigma = 30):


    # inf = LAMBDA
    inf = 10**9
    proba_bg= get_distributions(image, bg_pixels)
    proba_fg = get_distributions(image, fg_pixels)

    width, height = image.size
    
    graph_caps = {}
        
    for x in range(width):
        for y in range(height):
            # For grayscale images all channels have the same value
            Ip = image.getpixel((x, y))[0]

            if (x, y) in fg_pixels:
                 graph_caps['s', (x, y)] = inf
                 graph_caps[(x, y), 't'] = 0
            elif (x, y) in bg_pixels:
                 graph_caps['s', (x, y)] = 0
                 graph_caps[(x, y), 't'] = inf
            else:
                graph_caps['s', (x,y)] = int(-math.log2(proba_bg[Ip]))
                graph_caps[(x, y), 't'] = int(-math.log2(proba_fg[Ip]))

            for dx, dy in [(1,0), (0,1)]:
                nx = x + dx
                ny = y + dy

                if 0 <= nx < width and 0 <= ny < height:
                    Iq = image.getpixel((nx, ny))[0]

                    w = int(LAMBDA * math.exp(-((Ip-Iq)**2)/(2*sigma**2)))

                    graph_caps[(x,y), (nx, ny)] = w 
                    graph_caps[(nx, ny), (x,y)] = w
                

    return graph_caps

# print(image_to_graph(image))