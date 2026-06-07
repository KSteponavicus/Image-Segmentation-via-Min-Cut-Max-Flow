from PIL import Image
import math

image = Image.open("small_test.jpg")
image2 = Image.open("dog.jpg")

def image_to_graph(image, sigma = 25):

    di = [-1, 0, 1, 0]
    dj = [0, 1, 0, -1]

    width, height = image.size


    graph_caps = {}
        
    for i in range(width):
        for j in range(height):
            # For grayscale images all channels have the same value
            Ip, _, _ = image.getpixel((i, j))

            # Converting to the graph nodes
            p = j * width + i + 1
            #  print(f"({i},{j}) corresponds to {p}")

            for k in range(4):
                i2 = i + di[k]
                j2 = j + dj[k]

                if i2 < 0 or i2 >= width:
                    continue

                if j2 < 0 or j2 >= height:
                    continue

                Iq, _, _ = image.getpixel((i2, j2))
                q = j2 * width + i2 + 1

                w = math.exp(-((Ip-Iq)**2)/(2*sigma**2))
                graph_caps[(p,q)] = w 
                #  print(f"Weight between ({i},{j}) and ({i2},{j2}) is {w}")

    return graph_caps

print(image_to_graph(image))