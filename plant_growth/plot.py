import math
from colorsys import hsv_to_rgb
import numpy as np
import pygame

from plant_growth.vec2D import Vec2D

from math import pi as M_PI

def plot_image_grid(view, world):
    # pixl_arr = np.array(world.pg.img)
    # pixl_arr = np.swapaxes(np.array(world.plants[0].grid), 0, 1)
    # pixl_arr = np.fliplr(pixl_arr)
    # new_surf = pygame.pixelcopy.make_surface(pixl_arr)
    # view.surface.blit(new_surf, (0, 0))

    for plant in world.plants:
        for x in range(world.width):
            for y in range(world.height):
                if plant.grid[x, y]:
                    view.draw_pixel((x, y), (0, 200, 0, 100))

def contiguous_lit_cells(plant):
    run = []
    for i in range(plant.n_cells):
        cid = plant.ordered_cell[i]

        if plant.cell_light[cid] > 0:
            run.append(cid)

        elif len(run):
            yield run
            run = []

def cell_color(plant, cid):
    if plant.cell_light[cid] != 0:
        # angle from 0 to 2pi
        angle = math.atan2(plant.cell_norm[cid, 1], plant.cell_norm[cid, 0])
        # light = angle/M_PI
        # print(angle)

        # map angle to [0, 1]
        light = 1 - abs(M_PI/2 - angle) / (M_PI/2)
        # print(light)
        return (int(255*light), int(248*light), 0)
        # TODO - figure out why this is needed.
        light = (light -.5) * 2
        plant.cell_light[cid] = light
        # plant.cell_light[cid] = light

        # plant.cell_light[cid] += light / 2.0
    #         plant.cell_light[id_prev] += light / 2.0

        # Flowers do not contribute light.
        if not plant.cell_flower[cid]:
            plant.light += light# * derp
    else:
        return (0, 0, 0)

def plot(view, world, title=None):
    width, height = world.width, world.height
    view.start_draw()
    view.draw_rect((0, 0, width, height), (0, 102, 200), width=0)
    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)

    for plant in world.plants:
        view.draw_polygon(plant.polygon, (20, 200, 20))
        # print('\n'*5)
        # print(plant.polygon)

        for i in range(plant.max_i):
            if plant.cell_alive[i]:
                cid = i
                prev_id = plant.cell_prev[cid]
                # cell_light = plant.cell_light[cid]
                # prev_light = plant.cell_light[prev_id]
                c_x = plant.cell_x[cid]
                c_y = plant.cell_y[cid]
                p_x = plant.cell_x[prev_id]
                p_y = plant.cell_y[prev_id]

        #         light = min(1, max(0, plant.cell_light[cid]))
        #         color = (int(255*light), int(248*light), 0, 255)
                color = (0,0,0)
                view.draw_line((c_x, c_y), (p_x, p_y), color, width=1)

        if plant.mesh:
            for face in plant.mesh.elements:
                poly = [plant.mesh.points[f] for f in face]
                view.draw_lines(poly+[poly[0]], (50, 150, 50))


        for cid in range(plant.max_i):
            if plant.cell_alive[cid]:
                c_x = plant.cell_x[cid]
                c_y = plant.cell_y[cid]

                if plant.cell_flower[cid]:
                    view.draw_circle((c_x, c_y), 1, (200, 0, 200, 150), width=0)
                
                # elif plant.cell_water[cid]:
                #     view.draw_circle((c_x, c_y), 1, (0, 0, 200), width=0)

                elif plant.cell_light[cid]:
                    light = min(1, max(0, plant.cell_light[cid]))
                    color = (int(255*light), int(248*light), 0, 255)
                    view.draw_circle((c_x, c_y), 1, color, width=0)

    view.draw_rect((0, 0, width, world.soil_height), (153, 102, 51, 150), width=0)
    # plot_image_grid(view, world)

    for i, plant in enumerate(world.plants):
        x = (i * 400) + 10
        if title:
            view.draw_text((x, height-5), title, font=32)
            y = 40
        else:
            y = 20
        view.draw_text((x, height-y), "Plant id: %i"%i, font=16)
        view.draw_text((x, height-20-y), "Light: %.4f"%plant.light, font=16)
        view.draw_text((x, height-40-y), "Water: %.4f"%plant.water, font=16)
        view.draw_text((x, height-60-y), "Volume: %.4f"%plant.volume, font=16)
        view.draw_text((x, height-80-y), "Energy: %.4f"%plant.energy, font=16)
        view.draw_text((x, height-100-y), "consumption: %.4f"%plant.consumption, font=16)
        view.draw_text((x, height-120-y), "Num cells: %i"%plant.n_cells, font=16)
        view.draw_text((x, height-140-y), "Num flowers: %i"%plant.num_flowers, font=16)
    # view.draw_circle(world.light, 10, (255, 255, 0), width=0)
    view.end_draw()

# import random
# r = lambda: random.randint(0,255)
# c = lambda: (r(),r(),r())

# derp = [c() for _ in range(1000)]

# group_width = 20

# def myround(x, base=5):
#     return int(base * round(float(x)/base))

# colors = dict()

# def group(vec):
#     return myround(vec.x - vec.y, group_width)



    # for plant in world.plants:
    #     for contig_group in contiguous_lit_cells(plant):
    #         if len(contig_group) > 1:
    #             x0 = plant.cell_x[contig_group[0]] + math.cos(world.light) * 1000
    #             y0 = plant.cell_y[contig_group[0]] + math.sin(world.light) * 1000

    #             xn = plant.cell_x[contig_group[-1]] + math.cos(world.light) * 1000
    #             yn = plant.cell_y[contig_group[-1]] + math.sin(world.light) * 1000

    #             poly = [(x0, y0)]+[(plant.cell_x[i], plant.cell_y[i]) for i in contig_group]+[(xn, yn)]
    #             view.draw_polygon(poly, (255, 255, 102, 150))

        # print(list(continuous_lit_cells(plant)))
        # for cid in range(plant.n_cells):
        #     light_cell = plant.cell_light[cid]
        #     light_prev = plant.cell_light[plant.cell_prev[cid]]
        #     if light_cell > 0 and light_prev > 0:
        #         c_x = plant.cell_x[cid]
        #         c_y = plant.cell_y[cid]
        #         d_x = c_x + math.cos(world.light) * 1000
        #         d_y = c_y + math.sin(world.light) * 1000
        #         view.draw_line((d_x, d_y), (c_x, c_y), (255, 255, 102, 150))
