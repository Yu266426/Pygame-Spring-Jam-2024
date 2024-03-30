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

		self.load()

	def load(self):
		file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}.json"

		if not file_path.is_file():
			init_data = {
				"tiles": {
					0: {}
				}
			}

			with open(file_path, "x") as level_file:
				level_file.write(json.dumps(init_data))
		else:
			with open(file_path, "r") as level_file:
				level_data = json.load(level_file)

			for layer_index, layer in level_data["tiles"].items():
				for str_tile_pos, tile in layer.items():
					split_str_tile_pos = str_tile_pos.split(",")

					tile_pos = int(split_str_tile_pos[0]), int(split_str_tile_pos[1])

					if not tile["from_sheet"]:
						self.add_tile(tile_pos, int(layer_index), tile["tile_name"])
					else:
						self.add_sheet_tile(tile_pos, int(layer_index), tile["sheet_name"], tile["index"])

	def save(self):
		logging.info("Saving level")

		file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}.json"

		if not file_path.is_file():
			init_data = {
				"tiles": {
					"0": {}
				}
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

			with open(file_path, "w") as level_file:
				level_file.write(json.dumps(level_data))

	def get_colliders(self, layer: int = 0) -> tuple[pygame.Rect]:
		return tuple(tile.rect for tile in self.tiles[layer].values())  # NoQA

	def get_tile_pos(self, pos: tuple):
		return int(pos[0] // self.tile_size[0]), int(pos[1] // self.tile_size[1])

	def add_tile(self, tile_pos: tuple[int, int], layer: int, tile_name):
		self.tiles.setdefault(layer, {})[tile_pos] = Tile(tile_pos, self.tile_size).set_image(tile_name)

	def add_sheet_tile(self, tile_pos: tuple[int, int], layer: int, sheet_name: str, index: int):
		self.tiles.setdefault(layer, {})[tile_pos] = Tile(tile_pos, self.tile_size).set_sprite_sheet(sheet_name, index)

	def remove_tile(self, tile_pos: tuple[int, int], layer: int):
		if layer in self.tiles and tile_pos in self.tiles[layer]:
			del self.tiles[layer][tile_pos]

			if len(self.tiles[layer].keys()) == 0:
				del self.tiles[layer]

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera, entities: list, entity_layer: int):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			for tile in layer.values():
				tile.draw(surface, camera)

			if layer_index == entity_layer:
				for entity in entities:
					entity.draw(surface, camera)

	def editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			for tile in layer.values():
				tile.draw(surface, camera)

	def layered_editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_layer: int):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			if layer_index == current_layer:
				for tile in layer.values():
					tile.draw(surface, camera)
			else:
				for tile in layer.values():
					tile.editor_draw_dark(surface, camera)

	def single_level_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_layer: int):
		if current_layer in self.tiles:
			for tile in self.tiles[current_layer].values():
				tile.draw(surface, camera)
