import json
import logging
import pathlib
import random
from typing import TYPE_CHECKING

import pygame
import pygame.geometry
import pygbase

from files import ASSET_DIR
from tile import Tile

if TYPE_CHECKING:
	from water_monster import WaterMonsterGroup


class Level:
	LEVEL_NAME = "level"

	def __init__(self, particle_manager: pygbase.ParticleManager, in_water_particle_manager: pygbase.ParticleManager, lighting_manager: pygbase.LightingManager) -> None:
		self.particle_manager = particle_manager
		self.in_water_particle_manager = in_water_particle_manager
		self.checkpoint_particles = pygbase.Common.get_particle_setting("checkpoint")
		self.water_level = pygbase.Common.get_value("water_level")

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
			-3: -2,
			-4: -3
		}

		# Validate layer keys
		for layer in self.tiles.keys():
			if layer not in self.parallax_layer_key:
				raise ValueError(f"Missing parallax key for tile layer {layer}")

		(
			self.level_player_spawn_pos,
			self.water_monster_data,
			self.heart_of_the_sea_pos,
			self.focal_point_data,
			self.checkpoint_data
		) = self.load()

		# {id: (pos, strength, radius, monster_ids)}
		self.current_focal_point = -1
		self.focal_points: dict[int, tuple[tuple[float, float], float, float, list[int]]] = {focal_id: (pos, strength, radius, monster_ids) for focal_id, pos, strength, radius, monster_ids in self.focal_point_data}  # Points for the camera to lock onto (Prevents player from skipping fighting monsters)

		# {id: (collider, focal_id)}
		self.checkpoints: dict[int, pygame.geometry.Circle] = {checkpoint_id: pygame.geometry.Circle(pos, 80) for checkpoint_id, pos in self.checkpoint_data}
		self.checkpoint_lights = {}

		self.lighting_manager = lighting_manager
		self.regen_checkpoints()

		self.current_player_checkpoint_id = -1
		self.load_progress()

		if self.current_player_checkpoint_id != -1:
			self.checkpoint_lights[self.current_player_checkpoint_id].set_brightness(1.4)

		self.player_on_checkpoint = False

		self.water_monsters: WaterMonsterGroup | None = None

		self.checkpoint_sound: pygame.mixer.Sound = pygbase.ResourceManager.get_resource("sound", "checkpoint")

	def regen_checkpoints(self):
		for light in self.checkpoint_lights.values():
			self.lighting_manager.remove_light(light)
		self.checkpoint_lights.clear()

		for checkpoint_id, pos in self.checkpoint_data:
			self.checkpoint_lights[checkpoint_id] = self.lighting_manager.add_light(pygbase.Light(
				pos, 1.2, 80, random.uniform(4, 7), random.uniform(2, 3), tint=(255, 255, 200)
			))

	def get_player_spawn_pos(self) -> tuple[float, float]:
		if self.current_player_checkpoint_id != -1:
			return self.checkpoints[self.current_player_checkpoint_id].center
		else:
			return 0, 0

	def get_current_focal_point(self) -> tuple[tuple[float, float], float, list] | None:
		if self.current_focal_point == -1:
			return None
		focal_point = self.focal_points[self.current_focal_point]

		# If there are monsters alive in the group
		for monster_id in focal_point[3]:
			if monster_id in self.water_monsters.water_monster_ids:
				return focal_point[0], focal_point[1], focal_point[3]

		# If not
		self.current_focal_point = -1
		return None

	@classmethod
	def init_save_file(cls, path: pathlib.Path):
		init_data = {
			"tiles": {
				0: {}
			},
			"player_spawn_pos": [0, 0],
			"water_enemy_spawn_locations": [],
			"heart_of_the_sea_pos": [10000, 0],
			"focal_points": [],
			"checkpoints": []
		}

		with open(path, "x") as level_file:
			level_file.write(json.dumps(init_data))

	def load(self) -> tuple[tuple, list[tuple[int, tuple[int, int]]], tuple, list[tuple[int, tuple[float, float], float, float, list]], list[tuple[int, tuple[float, float]]]]:
		file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}.json"

		if not file_path.is_file():
			self.init_save_file(file_path)

			return (0, 0), [], (10000, 0), [], []
		else:
			with open(file_path, "r") as level_file:
				level_data = json.load(level_file)

			player_spawn_pos = level_data["player_spawn_pos"] if "player_spawn_pos" in level_data else (0, 0)
			enemy_spawn_locations = level_data["water_enemy_spawn_locations"] if "water_enemy_spawn_locations" in level_data else []
			heart_of_the_sea_pos = level_data["heart_of_the_sea_pos"] if "heart_of_the_sea_pos" in level_data else [10000, 0]
			focal_points = level_data["focal_points"] if "focal_points" in level_data else []
			checkpoints = level_data["checkpoints"] if "checkpoints" in level_data else []

			for layer_index, layer in level_data["tiles"].items():
				for str_tile_pos, tile in layer.items():
					split_str_tile_pos = str_tile_pos.split(",")

					tile_pos = int(split_str_tile_pos[0]), int(split_str_tile_pos[1])

					if not tile["from_sheet"]:
						self.add_tile(tile_pos, int(layer_index), tile["tile_name"])
					else:
						self.add_sheet_tile(tile_pos, int(layer_index), tile["sheet_name"], tile["index"])

			return player_spawn_pos, enemy_spawn_locations, heart_of_the_sea_pos, focal_points, checkpoints

	def save(self):
		logging.info("Saving level")

		file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}.json"

		if not file_path.is_file():
			self.init_save_file(file_path)

		else:
			with open(file_path, "r") as level_file:
				level_data = json.load(level_file)
				original_data = level_data.copy()

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

			level_data["player_spawn_pos"] = self.level_player_spawn_pos
			level_data["water_enemy_spawn_locations"] = self.water_monster_data
			level_data["heart_of_the_sea_pos"] = self.heart_of_the_sea_pos
			level_data["focal_points"] = self.focal_point_data
			level_data["checkpoints"] = self.checkpoint_data

			try:
				with open(file_path, "w") as level_file:
					level_file.write(json.dumps(level_data))
			except:
				with open(file_path, "w") as level_file:
					level_file.write(json.dumps(original_data))

	def get_parallax_layer(self, layer: int):
		if layer in self.parallax_layer_key:
			return self.parallax_layer_key[layer]
		else:
			return 0

	def get_colliders(self, layer: int = 0) -> tuple[pygame.Rect]:
		if layer in self.tiles:
			return tuple(tile.rect for tile in self.tiles[layer].values())  # NoQA
		else:
			return ()  # NoQA

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

	@classmethod
	def init_progress_file(cls, path: pathlib.Path):
		init_data = {
			"player_checkpoint": -1
		}

		with open(path, "x") as progress_file:
			progress_file.write(json.dumps(init_data))

	def load_progress(self):
		progress_file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}_progress.json"

		if not progress_file_path.is_file():
			self.init_progress_file(progress_file_path)
		else:
			with open(progress_file_path, "r") as progress_file:
				progress_data = json.load(progress_file)

			self.current_player_checkpoint_id = progress_data["player_checkpoint"]
			if self.current_player_checkpoint_id not in self.checkpoints:
				self.current_player_checkpoint_id = -1

	def save_progress(self):
		progress_file_path = ASSET_DIR / "levels" / f"{self.LEVEL_NAME}_progress.json"

		if not progress_file_path.is_file():
			self.init_progress_file(progress_file_path)
		else:
			with open(progress_file_path, "r") as progress_file:
				progress_data = json.load(progress_file)
				original_data = progress_data.copy()

			progress_data["player_checkpoint"] = self.current_player_checkpoint_id

			try:
				with open(progress_file_path, "w") as progress_file:
					progress_file.write(json.dumps(progress_data))
			except:
				with open(progress_file_path, "w") as progress_file:
					progress_file.write(json.dumps(original_data))

	def update(self, delta: float, player_pos: pygame.Vector2):
		player_checkpoint_collision = False
		collided_checkpoint_id = -1
		collided_checkpoint_pos = None

		for checkpoint_id, checkpoint in self.checkpoints.items():
			if checkpoint_id == self.current_player_checkpoint_id:
				continue

			if checkpoint.collidepoint(player_pos):
				player_checkpoint_collision = True
				collided_checkpoint_id = checkpoint_id
				collided_checkpoint_pos = checkpoint.center
				break

		if self.current_focal_point == -1:
			for focal_id, focal_point in self.focal_points.items():
				if player_pos.distance_to(focal_point[0]) < focal_point[2]:
					self.current_focal_point = focal_id

		if player_checkpoint_collision and not self.player_on_checkpoint:
			self.player_on_checkpoint = True

			# Save player progress
			if self.current_player_checkpoint_id != -1:
				self.checkpoint_lights[self.current_player_checkpoint_id].set_brightness(1.2)

			self.current_player_checkpoint_id = collided_checkpoint_id
			self.checkpoint_lights[self.current_player_checkpoint_id].set_brightness(1.4)

			self.checkpoint_sound.play()
			self.save_progress()

			if player_pos.y > self.water_level:
				for _ in range(random.randint(30, 60)):
					offset = pygbase.utils.get_angled_vector(random.uniform(0, -360), 1)
					self.in_water_particle_manager.add_particle(collided_checkpoint_pos + offset * random.uniform(0, 50), self.checkpoint_particles, initial_velocity=offset * random.uniform(200, 400))
			else:
				for _ in range(random.randint(30, 60)):
					offset = pygbase.utils.get_angled_vector(random.uniform(0, -360), 1)
					self.particle_manager.add_particle(collided_checkpoint_pos + offset * random.uniform(0, 50), self.checkpoint_particles, initial_velocity=offset * random.uniform(200, 400))

			return True

		elif not player_checkpoint_collision:
			self.player_on_checkpoint = False

		return False

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera, entities: list, entity_layer: int, exclude_layers: set[int] | None = None):
		for focal_point in self.focal_points.values():
			pygbase.DebugDisplay.draw_circle(camera.world_to_screen(focal_point[0]), focal_point[2], "yellow")

		exclude_layers = {} if exclude_layers is None else exclude_layers

		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			if layer_index in exclude_layers:
				continue

			parallax_key = self.get_parallax_layer(layer_index)

			x_parallax_amount = self.screen_size[0] * parallax_key * self.parallax_amount
			y_parallax_amount = self.screen_size[1] * parallax_key * self.parallax_amount

			tile_size = (64 * (1 + parallax_key * self.parallax_amount), 64 * (1 + parallax_key * self.parallax_amount))

			top_left = self.get_tile_pos(camera.screen_to_world((x_parallax_amount, y_parallax_amount)))
			bottom_right = self.get_tile_pos(camera.screen_to_world((self.screen_size[0] - x_parallax_amount + tile_size[0], self.screen_size[1] - y_parallax_amount + tile_size[1])))

			for row in range(top_left[1], bottom_right[1]):
				for col in range(top_left[0], bottom_right[0]):
					tile = layer.get((col, row))
					if tile is not None:
						tile.draw(surface, camera)
			# print(layer_index, col, row)

			if layer_index == entity_layer:
				for entities in entities:
					entities.draw(surface, camera)

	def single_layer_draw(self, surface: pygame.Surface, camera: pygbase.Camera, layer_index: int):
		layer = self.tiles[layer_index]
		parallax_key = self.get_parallax_layer(layer_index)

		x_parallax_amount = self.screen_size[0] * parallax_key * self.parallax_amount
		y_parallax_amount = self.screen_size[1] * parallax_key * self.parallax_amount

		tile_size = (64 * (1 + parallax_key * self.parallax_amount), 64 * (1 + parallax_key * self.parallax_amount))

		top_left = self.get_tile_pos(camera.screen_to_world((x_parallax_amount, y_parallax_amount)))
		bottom_right = self.get_tile_pos(camera.screen_to_world((self.screen_size[0] - x_parallax_amount + tile_size[0], self.screen_size[1] - y_parallax_amount + tile_size[1])))

		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				tile = layer.get((col, row))
				if tile is not None:
					tile.draw(surface, camera)

	def editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_focus: int = -1):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			parallax_key = self.get_parallax_layer(layer_index)

			x_parallax_amount = self.screen_size[0] * (1 + parallax_key * self.parallax_amount) / 2
			y_parallax_amount = self.screen_size[1] * (1 + parallax_key * self.parallax_amount) / 2

			top_left = self.get_tile_pos(camera.screen_to_world((-x_parallax_amount, -y_parallax_amount)))
			bottom_right = self.get_tile_pos(camera.screen_to_world((self.screen_size[0] + x_parallax_amount, self.screen_size[1] + y_parallax_amount)))

			for row in range(top_left[1], bottom_right[1]):
				for col in range(top_left[0], bottom_right[0]):
					tile = layer.get((col, row))
					if tile is not None:
						tile.editor_draw(surface, camera)

		pygame.draw.circle(surface, "yellow", camera.world_to_screen(self.level_player_spawn_pos), 50, width=5)

		for water_monster in self.water_monster_data:
			pygame.draw.circle(surface, "light blue", camera.world_to_screen(water_monster[1]), 40, width=5)

		pygame.draw.circle(surface, "light blue", camera.world_to_screen(self.heart_of_the_sea_pos), 400, width=10)

		for checkpoint in self.checkpoint_data:
			pygame.draw.circle(surface, "light blue", camera.world_to_screen(checkpoint[1]), 80, width=5)

		for focal_id, focal_point, __, radius, water_monster_ids in self.focal_point_data:
			color = "yellow" if focal_id == current_focus or current_focus == -1 else "orange"
			pygame.draw.circle(surface, color, camera.world_to_screen(focal_point), 40, width=0)
			pygame.draw.circle(surface, color, camera.world_to_screen(focal_point), radius, width=2)

			if focal_id == current_focus:
				for water_monster in self.water_monster_data:
					if water_monster[0] in water_monster_ids:
						pygame.draw.circle(surface, "yellow", camera.world_to_screen(water_monster[1]), 20, width=5)

	def layered_editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_layer: int):
		for layer_index, layer in sorted(self.tiles.items(), key=lambda e: e[0]):
			parallax_key = self.get_parallax_layer(layer_index)

			x_parallax_amount = self.screen_size[0] * (1 + parallax_key * self.parallax_amount) / 2
			y_parallax_amount = self.screen_size[1] * (1 + parallax_key * self.parallax_amount) / 2

			top_left = self.get_tile_pos(camera.screen_to_world((-x_parallax_amount, -y_parallax_amount)))
			bottom_right = self.get_tile_pos(camera.screen_to_world((self.screen_size[0] + x_parallax_amount, self.screen_size[1] + y_parallax_amount)))

			if layer_index == current_layer:
				for row in range(top_left[1], bottom_right[1]):
					for col in range(top_left[0], bottom_right[0]):
						tile = layer.get((col, row))
						if tile is not None:
							tile.editor_draw(surface, camera)

			else:
				for row in range(top_left[1], bottom_right[1]):
					for col in range(top_left[0], bottom_right[0]):
						tile = layer.get((col, row))
						if tile is not None:
							tile.editor_draw_dark(surface, camera)

	def single_layer_editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera, current_layer: int):
		if current_layer in self.tiles:
			for tile in self.tiles[current_layer].values():
				tile.editor_draw(surface, camera)
