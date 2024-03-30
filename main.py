import cProfile
import sys

import pygame
import pygbase

from editor import Editor
from files import ASSET_DIR
from game import Game

DEBUG = False
DO_PROFILE = False

if __name__ == '__main__':
	cl_args = sys.argv

	if "-game" in cl_args and "-editor" in cl_args:
		raise ValueError("`-game` and `-editor` are mutually exclusive")

	pygbase.init((800, 800), max_light_radius=0)

	if DEBUG:
		pygbase.DebugDisplay.show()

	pygbase.add_particle_setting(
		"flamethrower",
		[(249, 194, 43), (245, 125, 74), (234, 79, 54), (251, 107, 29), (232, 59, 59)],
		(6, 12),
		(2, 3),
		(0.2, 1),
		(0, 10),
		True,
		((0.0, 0.1), (0.0, 0.4))
	)
	pygbase.add_particle_setting(
		"fire",
		[(249, 194, 43), (245, 125, 74), (234, 79, 54), (251, 107, 29), (232, 59, 59)],
		(6, 12),
		(5, 8),
		(0, 1),
		(0, -2),
		True,
		((0.0, 0.1), (0.0, 0.4))
	)
	pygbase.add_particle_setting(
		"smoke",
		[(10 * i, 10 * i, 10 * i) for i in range(7, 10)],
		(3, 10),
		(7, 10),
		(0, 0),
		(0, -5),
		True,
		((0.0, 0.1), (0.0, 0.4))
	)
	pygbase.add_particle_setting(
		"water",
		["blue", "light blue"],
		(5, 11),
		(5, 8),
		(4, 0),
		(0, 5),
		True,
		((0.0, 0.1), (0.0, 0.4))
	)

	pygbase.Common.set_value("tile_size", (16 * 4, 16 * 4))
	pygbase.Common.set_value("gravity", 1600)

	water_monster_colors = ("blue", "light blue", "dark blue")
	pygbase.Common.set_value("water_monster_colors", water_monster_colors)
	pygbase.Common.set_value("water_alpha", 100)

	pygbase.Common.set_value("water_outline_surface", pygame.Surface(pygbase.Common.get_value("screen_size"), flags=pygame.SRCALPHA))

	water_draw_surfaces: dict[str | tuple, pygame.Surface] = {}
	for color in water_monster_colors:
		water_draw_surfaces[color] = pygame.Surface(pygbase.Common.get_value("screen_size"), flags=pygame.SRCALPHA)

	pygbase.Common.set_value("water_surfaces", water_draw_surfaces)

	pygbase.EventManager.add_handler("all", pygame.KEYDOWN, lambda e: pygbase.EventManager.post_event(pygame.QUIT) if e.key == pygame.K_ESCAPE else None)

	pygbase.add_image_resource("tiles", 0, str(ASSET_DIR / "tiles"), default_scale=4)
	pygbase.add_sprite_sheet_resource("tile_sheets", 1, str(ASSET_DIR / "tile_sheets"), default_scale=4)
	pygbase.add_sprite_sheet_resource("sprite_sheets", 2, str(ASSET_DIR / "sprite_sheets"), default_scale=4)
	pygbase.add_image_resource("images", 3, str(ASSET_DIR / "images"), default_scale=4)
	pygbase.add_image_resource("ui", 4, str(ASSET_DIR / "ui"))

	if DO_PROFILE:
		profiler = cProfile.Profile()
		profiler.enable()

		pygbase.App(Game).run()
		profiler.disable()

		profiler.dump_stats("stats.prof")
	else:
		if "-game" in cl_args:
			pygbase.App(Game).run()
		elif "-editor" in cl_args:
			pygbase.App(Editor).run()

	pygbase.quit()
