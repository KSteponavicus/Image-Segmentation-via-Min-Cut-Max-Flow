from PIL import Image
import math

image = Image.open("small_test.jpg")
image2 = Image.open("dog.jpg")

LAMBDA = 100

def image_to_graph(image, sigma = 25):

    width, height = image.size
    
    graph_caps = {}
        
    for x in range(width):
        for y in range(height):
            # For grayscale images all channels have the same value
            Ip, _, _ = image.getpixel((x, y))

            for dx, dy in [(1,0), (0,1)]:
                nx = x + dx
                ny = y + dy

                if 0 <= nx < width and 0 <= ny < height:
                    Iq, _, _ = image.getpixel((nx, ny))

                    w = int(LAMBDA * math.exp(-((Ip-Iq)**2)/(2*sigma**2)))

                    graph_caps[(x,y), (nx, ny)] = w 
                    graph_caps[(nx, ny), (x,y)] = w
                

    return graph_caps

print(image_to_graph(image))