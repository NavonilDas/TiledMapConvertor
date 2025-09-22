import os
import json
import numpy as np
from string import Template

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

def handle_chunk(chunk, minimum, dest, first_id):
    x_min, y_min = minimum
    data = chunk.get("data")
    cw = chunk.get("width")
    ch = chunk.get("height")
    cx = abs(x_min) + chunk.get("x")
    cy = abs(y_min) + chunk.get("y")
    for i in range(cw):
        for j in range(ch):
            if data[i*cw + j] == 0:
                continue
            dest[cx + i][cy + j] = (data[i*cw + j] - first_id)


def process_tile_map(file_path:str):
    with open(file_path) as tile_map_file,\
        open("layers.bin", "wb") as output_file,\
        open("layers.go.tmpl", "r") as layer_go_template,\
        open("layers.go", "w") as layers_go_output:

        tile_map_json = json.load(tile_map_file)
        layers = tile_map_json.get('layers')
        tile_width = tile_map_json.get("tilewidth")
        tile_height = tile_map_json.get("tileheight")
        
        if tile_height != tile_width:
            raise ValueError("Tile Width and Height are not same which is unsupported")
        
        w, h, first_id = -1,-1, DEF_MAX
        l_count, num_bytes = 1,2
        x_min , y_min = DEF_MAX, DEF_MAX

        for layer in layers:
            w = max(w, layer.get("width"))
            h = max(h, layer.get("height"))
        
        for tileset in tile_map_json.get("tilesets"):
            first_id = min(first_id, tileset.get("firstgid"))
        
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
            values = np.zeros((w,h),dtype=">u"+str(num_bytes)) # Storing 2 bytes for now will change it to 4 bytes once we cross number > 2^16
            for chunk in layer.get("chunks"):
                handle_chunk(chunk, (x_min, y_min), values, first_id)
            
            # merge all the layers into one file
            output_file.write(values.tobytes())
            # print(w,h)
            # print(len(values.tobytes()))
            l_count += 1
            print(values)
        # generate go files embed and config file storing
        # We can create a separate json file and read it in go, but i don't want read overhead
        template = Template(layer_go_template.read())
        layers_go_output.write(
            template.substitute(
                layer_width = w,
                layer_height = h,
                num_layers = len(layers),
                num_bytes = num_bytes,
                tile_size = tile_width
            )
        )
        
for tile_map in tilemaps:
    process_tile_map(tile_map)