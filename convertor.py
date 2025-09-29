import os
import json
import numpy as np
from string import Template
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from typing import List
import sys

items = os.listdir("./")

tileset = []
tilemaps = []

DEF_MAX = 9999999999
DEF_MIN = -9999999999
PROPERTIES = "properties"

COLLIDE_PROPERTY = "Collide"
ANIMATE_PROPERTY = "ANIMATE"

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
            dest[cy + i][cx + j] = (data[i*cw + j] - first_id)


def process_tile_map(file_path:str, out_location:str):
    with open(file_path) as tile_map_file,\
        open(out_location + "\\layers.bin", "wb") as output_file,\
        open("layers.go.tmpl", "r") as layer_go_template,\
        open(out_location + "\\layers.go", "w") as layers_go_output:

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
            first_id = min(first_id, tileset.get("firstgid", 0))

        for layer in layers:
            # x_max , y_max = DEF_MIN, DEF_MIN
            for chunk in layer.get("chunks"):
                x_min = min(x_min, chunk.get("x"))
                y_min = min(y_min, chunk.get("y"))
                
                # x_max = max(x_max, chunk.get("x"))
                # y_max = max(y_max, chunk.get("y"))
            # print([x_min , x_max])
            # print([y_min , y_max])

        # print("Min ",x_min,"Min Y", y_min)

        for layer in layers:
            values = np.zeros((w,h),dtype=">u"+str(num_bytes)) # Storing 2 bytes for now will change it to 4 bytes once we cross number > 2^16
            # values = np.zeros((w,h),dtype=int)
            for chunk in layer.get("chunks"):
                handle_chunk(chunk, (x_min, y_min), values, first_id)
            
            # merge all the layers into one file
            output_file.write(values.tobytes())
            print("Wrote file to Layer ",l_count)
            # np.savetxt("Layer {}.csv".format(l_count), values, delimiter=',', fmt="%d")
            # print(len(values.tobytes()))
            l_count += 1
            # print(values)
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

def process_tileset(filepath:str, out_location:str):
    with open(filepath) as tile_set_json_file,\
        open(out_location+"\\tileCollision.bin", "wb") as collision_file:
        tile_set_json = json.load(tile_set_json_file)
        collisions:List[int] = []
        for tile in tile_set_json['tiles']:
            if PROPERTIES in tile:
                properties = tile[PROPERTIES]
                for prop in properties:
                    if prop['name'] == COLLIDE_PROPERTY and prop['value']:
                        tile_id:int = tile.get('id')
                        collisions.append(tile_id)
        
        collisions.sort()
        print(collisions)
        for tile_id in collisions:
            collision_file.write(tile_id.to_bytes(2, byteorder='big'))

class TimeMapHandler(FileSystemEventHandler):
    def __init__(self, tilemaps:List[str], tilesets:List[str], out_location:str):
        super().__init__()
        self.tilemaps = tilemaps
        self.tilesets = tilesets
        self.out_location = out_location
    
    def process_file(self, filename:str):
        if filename in self.tilemaps:
            print("Update in File", filename)
            process_tile_map(filename, self.out_location)
        
        if filename in self.tilesets:
            print("Update in Tileset File", filename)
            process_tileset(filename, self.out_location)
    
    def on_modified(self, event):
        super().on_modified(event)
        filename = os.path.basename(event.src_path)
        self.process_file(filename)

    def on_moved(self, event):
        super().on_modified(event)
        filename = os.path.basename(event.dest_path)
        self.process_file(filename)



if __name__ == "__main__":
    out_location = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = TimeMapHandler(tilemaps, tileset, out_location)
    observer = Observer()
    observer.schedule(event_handler, '.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()