import json
import logging

import pygame
import pygbase

from files import ASSET_DIR
from tile import Tile


class Level:
	LEVEL_NAME = "level"

	def __init__(self) -> None:
		self.tile_size = pygbase.Common.get_value("tile_size")
		self.tiles: dict[int, dict[tuple[int, int], Tile]] = {0: {}}

		self.parallax_amount = 0.1
		self.screen_size = pygbase.Common.get_value("screen_size")

		# {tile_layer: parallax_layer}
		self.parallax_layer_key: dict[int, int] = {
			3: 1,
			2: 0,
			1: 0,
			0: 0,
			-1: 0,
			-2: -1,
			-3: -2
		}

		# Validate layer keys
		for layer in self.tiles.keys():
			if layer not in self.parallax_layer_key:
				raise ValueError(f"Missing parallax key for tile layer {layer}")

		self.player_spawn_pos, self.water_enemy_spawn_locations, self.heart_of_the_sea_pos = self.load()

	def load(self) -> tuple[tuple, list[tuple], tuple]:
		file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}.json"

		if not file_path.is_file():
			init_data = {
				"tiles": {
					0: {}
				},
				"player_spawn_pos": [0, 0],
				"water_enemy_spawn_locations": [],
				"heart_of_the_sea_pos": [10000, 0]
			}

			with open(file_path, "x") as level_file:
				level_file.write(json.dumps(init_data))

			return (0, 0), [], (10000, 0)
		else:
			with open(file_path, "r") as level_file:
				level_data = json.load(level_file)

			player_spawn_pos = level_data["player_spawn_pos"] if "player_spawn_pos" in level_data else (0, 0)
			enemy_spawn_locations = level_data["water_enemy_spawn_locations"] if "water_enemy_spawn_locations" in level_data else []
			heart_of_the_sea_pos = level_data["heart_of_the_sea_pos"] if "heart_of_the_sea_pos" in level_data else [10000, 0]

			for layer_index, layer in level_data["tiles"].items():
				for str_tile_pos, tile in layer.items():
					split_str_tile_pos = str_tile_pos.split(",")

					tile_pos = int(split_str_tile_pos[0]), int(split_str_tile_pos[1])

					if not tile["from_sheet"]:
						self.add_tile(tile_pos, int(layer_index), tile["tile_name"])
					else:
						self.add_sheet_tile(tile_pos, int(layer_index), tile["sheet_name"], tile["index"])

			return player_spawn_pos, enemy_spawn_locations, heart_of_the_sea_pos

	def save(self):
		logging.info("Saving level")

		file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}.json"

		if not file_path.is_file():
			init_data = {
				"tiles": {
					0: {}
				},
				"player_spawn_pos": [0, 0],
				"water_enemy_spawn_locations": [],
				"heart_of_the_sea_pos": [10000, 0]
			}

			with open(file_path, "x") as level_file:
				level_file.write(json.dumps(init_data))

		else:
			with open(file_path, "r") as level_file:
				level_data = json.load(level_file)

			json_tiles = {}
			for layer_index, layer in self.tiles.items():
				json_tiles[layer_index] = {}
				for tile_pos, tile in layer.items():
					str_tile_pos = f"{tile_pos[0]},{tile_pos[1]}"

					if not tile.from_sheet:
						json_tiles[layer_index][str_tile_pos] = {
							"from_sheet": False,
							"tile_name": tile.name
						}
					else:
						json_tiles[layer_index][str_tile_pos] = {
							"from_sheet": True,
							"sheet_name": tile.sheet_name,
							"index": tile.sheet_index
						}

			level_data["tiles"] = json_tiles

			level_data["player_spawn_pos"] = self.player_spawn_pos
			level_data["water_enemy_spawn_locations"] = self.water_enemy_spawn_locations
			level_data["heart_of_the_sea_pos"] = self.heart_of_the_sea_pos

			with open(file_path, "w") as level_file:
				level_file.write(json.dumps(level_data))

	def get_parallax_layer(self, layer: int):
		if layer in self.parallax_layer_key:
			return self.parallax_layer_key[layer]
		else:
			return 0

	def get_colliders(self, layer: int = 0) -> tuple[pygame.Rect]:
		return tuple(tile.rect for tile in self.tiles[layer].values())  # NoQA

	def get_tile_pos(self, pos: tuple):
		return int(pos[0] // self.tile_size[0]), int(pos[1] // self.tile_size[1])

	def add_tile(self, tile_pos: tuple[int, int], layer: int, tile_name):
		self.tiles.setdefault(layer, {})[tile_pos] = Tile(tile_pos, self.tile_size, self.get_parallax_layer(layer), self.parallax_amount).set_image(tile_name)

	def add_sheet_tile(self, tile_pos: tuple[int, int], layer: int, sheet_name: str, index: int):
		self.tiles.setdefault(layer, {})[tile_pos] = Tile(tile_pos, self.tile_size, self.get_parallax_layer(layer), self.parallax_amount).set_sprite_sheet(sheet_name, index)

	def remove_tile(self, tile_pos: tuple[int, int], layer: int):
		if layer in self.tiles and tile_pos in self.tiles[layer]:
			del self.tiles[layer][tile_pos]

			if len(self.tiles[layer].keys()) == 0:
				del self.tiles[layer]

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera, entities: list, entity_layer: int, exclude_layers: set[int] | None = None):
		exclude_layers = {} if exclude_layers is None else exclude_layers

		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			if layer_index in exclude_layers:
				continue

			parallax_key = self.get_parallax_layer(layer_index)

			x_parallax_amount = self.screen_size[0] * (1 + parallax_key * self.parallax_amount) / 2
			y_parallax_amount = self.screen_size[1] * (1 + parallax_key * self.parallax_amount) / 2

			top_left = self.get_tile_pos(camera.screen_to_world((-x_parallax_amount, -y_parallax_amount)))
			bottom_right = self.get_tile_pos(camera.screen_to_world((self.screen_size[0] + x_parallax_amount, self.screen_size[1] + y_parallax_amount)))

			# print(top_left, bottom_right)

			for row in range(top_left[1], bottom_right[1]):
				for col in range(top_left[0], bottom_right[0]):
					tile = layer.get((col, row))
					if tile is not None:
						tile.draw(surface, camera)

			# for tile in layer.values():
			# 	tile.draw(surface, camera)

			if layer_index == entity_layer:
				for entities in entities:
					entities.draw(surface, camera)

	def single_layer_draw(self, surface: pygame.Surface, camera: pygbase.Camera, layer_index: int):
		layer = self.tiles[layer_index]
		parallax_key = self.get_parallax_layer(layer_index)

		x_parallax_amount = self.screen_size[0] * (1 + parallax_key * self.parallax_amount) / 2
		y_parallax_amount = self.screen_size[1] * (1 + parallax_key * self.parallax_amount) / 2

		top_left = self.get_tile_pos(camera.screen_to_world((-x_parallax_amount, -y_parallax_amount)))
		bottom_right = self.get_tile_pos(camera.screen_to_world((self.screen_size[0] + x_parallax_amount, self.screen_size[1] + y_parallax_amount)))

		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				tile = layer.get((col, row))
				if tile is not None:
					tile.draw(surface, camera)

	def editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			for tile in layer.values():
				tile.editor_draw(surface, camera)

		pygame.draw.circle(surface, "yellow", camera.world_to_screen(self.player_spawn_pos), 50, width=5)

		for water_monster_spawn_pos in self.water_enemy_spawn_locations:
			pygame.draw.circle(surface, "light blue", camera.world_to_screen(water_monster_spawn_pos), 40, width=5)

		pygame.draw.circle(surface, "light blue", camera.world_to_screen(self.heart_of_the_sea_pos), 400, width=10)

	def layered_editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_layer: int):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			if layer_index == current_layer:
				for tile in layer.values():
					tile.editor_draw(surface, camera)
			else:
				for tile in layer.values():
					tile.editor_draw_dark(surface, camera)

	def single_layer_editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_layer: int):
		if current_layer in self.tiles:
			for tile in self.tiles[current_layer].values():
				tile.editor_draw(surface, camera)
