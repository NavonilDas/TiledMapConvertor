import os
import json
import numpy as np

items = os.listdir("./")

tileset = []
tilemaps = []

DEF_MAX = 9999999999
DEF_MIN = -9999999999

for item in items:
    if item.endswith(".tmj"):
        tilemaps.append(item)
    elif item.endswith(".tsj"):
        tileset.append(item)

def handle_chunk(chunk, minimum, dest):
    x_min, y_min = minimum
    data = chunk.get("data")
    cw = chunk.get("width")
    ch = chunk.get("height")
    cx = abs(x_min) + chunk.get("x")
    cy = abs(y_min) + chunk.get("y")
    for i in range(cw):
        for j in range(ch):
            dest[cx + i][cy + j] = data[i*cw + j]


# def write_values()

def process_tile_map(file_path:str):
    with open(file_path) as tile_map_file, open("layers.b", "wb") as output_file:
        x = json.load(tile_map_file)
        layers = x.get('layers')
        w,h = -1,-1
        for layer in layers:
            w = max(w, layer.get("width"))
            h = max(h, layer.get("height"))
        
        l_count = 1
        x_min , y_min = DEF_MAX, DEF_MAX
        for layer in layers:
            # x_max , y_max = DEF_MIN, DEF_MIN
            for chunk in layer.get("chunks"):
                x_min = min(x_min, chunk.get("x"))
                y_min = min(y_min, chunk.get("y"))
                
                # x_max = max(x_max, chunk.get("x"))
                # y_max = max(y_max, chunk.get("y"))
            # print([x_min , x_max])
            # print([y_min , y_max])

        for layer in layers:
            values = np.zeros((w,h),dtype=">u2") # Storing 2 bytes for now will change it to 4 bytes once we cross number > 2^16
            for chunk in layer.get("chunks"):
                handle_chunk(chunk, (x_min, y_min), values)
            # write_values(values, output_file)
            # np.savetxt("layer"+str(l_count)+".csv", values, delimiter=",", fmt="%d")
            
            # TODO: Read tileset  firstgid if it is one subtract 1 from all
            values.tofile("layer"+str(l_count)+".bin")
            # TODO: generate go files embed and config file storing 
            # TODO: merge all the layers into one file
            l_count += 1

for tile_map in tilemaps:
    process_tile_map(tile_map)