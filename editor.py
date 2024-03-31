import logging

import pygame
import pygbase

from level import Level
from tile import Tile


class Editor(pygbase.GameState, name="editor"):
	def __init__(self):
		super().__init__()

		self.screen_size = pygbase.Common.get_value("screen_size")
		self.tile_size = pygbase.Common.get_value("tile_size")

		self.camera_controller = pygbase.CameraController((-400, -400))

		self.level = Level()

		self.ui = pygbase.UIManager()

		self.mode_selector = self.ui.add_element(pygbase.TextSelectionMenu(
			(pygbase.UIValue(10), pygbase.UIValue(10)),
			(pygbase.UIValue(250), pygbase.UIValue(50)),
			"ui",
			["Tile", "Sheet", "Entity", "View"],
			self.ui.base_container,
			bg_colour=(40, 40, 40, 40)
		))

		self.hide_other_layers = False
		self.tile_layer_ui = None
		self.tile_layer_text = None
		self.create_tile_layer_ui()

		self.tile_editing_ui: pygbase.Frame | None = None
		self.current_tile = None
		self.create_tile_edit_ui()

		self.sheet_tile_editing_ui: pygbase.Frame | None = None
		self.sprite_sheets: dict[str, pygbase.SpriteSheet] = pygbase.ResourceManager.get_resources_of_type("tile_sheets")
		self.sprite_sheet_tile_frames = None
		self.sheet_selector = None
		self.current_sheet: str | None = None
		self.current_sheet_index: int | None = 0
		self.create_sheet_tile_edit_ui()

		self.entity_editing_ui: pygbase.Frame | None = None
		self.current_entity_mode: pygbase.TextSelectionMenu | None = None
		self.create_entity_editing_ui()

		self.prev_mouse_tile_pos = (0, 0)

	def create_tile_layer_ui(self):
		self.tile_layer_ui = self.ui.add_frame(pygbase.Frame(
			(pygbase.UIValue(0), pygbase.UIValue(0)),
			(pygbase.UIValue(1, False), pygbase.UIValue(1, False)),
			self.ui.base_container,
			blocks_mouse=False
		))

		self.tile_layer_text = self.tile_layer_ui.add_element(pygbase.TextElement(
			(pygbase.UIValue(0.99, False), pygbase.UIValue(0.01, False)),
			"arial", pygbase.UIValue(40),
			"white",
			"0",
			self.tile_layer_ui,
			alignment=pygbase.UIAlignment.TOP_RIGHT
		))

		self.tile_layer_ui.add_element(pygbase.Button(
			(pygbase.UIValue(0.94, False), pygbase.UIValue(0.01, False)),
			(pygbase.UIValue(0), pygbase.UIValue(0.05, False)),
			"ui", "up",
			self.tile_layer_ui,
			self.tile_layer_up_button_callback
		), add_on_to_previous=(False, True))

		self.tile_layer_ui.add_element(pygbase.Button(
			(pygbase.UIValue(0), pygbase.UIValue(0.01, False)),
			(pygbase.UIValue(0), pygbase.UIValue(0.05, False)),
			"ui", "down",
			self.tile_layer_ui,
			self.tile_layer_down_button_callback
		), add_on_to_previous=(False, True), align_with_previous=(True, False))

		self.tile_layer_ui.add_element(pygbase.Button(
			(pygbase.UIValue(0), pygbase.UIValue(0.01, False)),
			(pygbase.UIValue(0), pygbase.UIValue(0.05, False)),
			"ui", "eye",
			self.tile_layer_ui,
			self.hide_layers_button_callback
		), add_on_to_previous=(False, True), align_with_previous=(True, False))

	def create_tile_edit_ui(self):
		self.tile_editing_ui = self.ui.add_frame(pygbase.Frame(
			(pygbase.UIValue(0), pygbase.UIValue(0)),
			(pygbase.UIValue(1, False), pygbase.UIValue(1, False)),
			self.ui.base_container,
			blocks_mouse=False
		))

		tile_names = sorted(pygbase.ResourceManager.get_resources_of_type("tiles").keys())
		logging.debug(f"Tile names: {tile_names}")
		self.current_tile = tile_names[0]

		tile_selector_panel = self.tile_editing_ui.add_element(pygbase.VerticalScrollingFrame(
			(pygbase.UIValue(0), pygbase.UIValue(0.8, False)),
			(pygbase.UIValue(1, False), pygbase.UIValue(0.2, False)),
			10,
			self.tile_editing_ui,
			bg_colour=(80, 80, 80, 80)
		))
		max_tile_cols = int((1.0 - 0.01) / (0.01 + 0.085))
		for index, tile_name in enumerate(tile_names):
			if index != 0 and index % max_tile_cols == 0:  # If at the end, go to next row
				add_on = (False, True)
				align = (False, False)
			else:
				add_on = (True, False)
				align = (False, True)

			tile_selector_panel.add_element(pygbase.Button(
				(pygbase.UIValue(0.01, False), pygbase.UIValue(8)),
				(pygbase.UIValue(0.085, False), pygbase.UIValue(0)),
				"tiles", tile_name,
				tile_selector_panel,
				self.tile_selection_button_callback,
				callback_args=(tile_name,)
			), add_on_to_previous=add_on, align_with_previous=align)

	def create_sheet_tile_edit_ui(self):
		self.sheet_tile_editing_ui = self.ui.add_frame(pygbase.Frame(
			(pygbase.UIValue(0), pygbase.UIValue(0)),
			(pygbase.UIValue(1, False), pygbase.UIValue(1, False)),
			self.ui.base_container,
			blocks_mouse=False
		))

		sprite_sheet_names = sorted(self.sprite_sheets.keys())
		logging.debug(f"Sheet names: {sprite_sheet_names}")
		self.current_sheet = sprite_sheet_names[0]

		self.sheet_selector = self.sheet_tile_editing_ui.add_element(pygbase.TextSelectionMenu(
			(pygbase.UIValue(10), pygbase.UIValue(70)),
			(pygbase.UIValue(500), pygbase.UIValue(50)),
			"ui",
			sprite_sheet_names,
			self.sheet_tile_editing_ui,
			bg_colour=(40, 40, 40, 40)
		))

		self.sprite_sheet_tile_frames = {}
		for sprite_sheet_name in sprite_sheet_names:
			current_frame = pygbase.Frame(
				(pygbase.UIValue(0), pygbase.UIValue(0.8, False)),
				(pygbase.UIValue(1, False), pygbase.UIValue(0.2, False)),
				self.ui.base_container,
				bg_colour=(80, 80, 80, 80)
			)

			self.sprite_sheet_tile_frames[sprite_sheet_name] = self.ui.add_frame(current_frame)

			tile_selector_panel = current_frame.add_element(pygbase.VerticalScrollingFrame(
				(pygbase.UIValue(0), pygbase.UIValue(0)),
				(pygbase.UIValue(1, False), pygbase.UIValue(1, False)),
				10,
				current_frame,
				bg_colour=(80, 80, 80, 80)
			))

			sprite_sheet: pygbase.SpriteSheet = self.sprite_sheets[sprite_sheet_name]
			num_images = sprite_sheet.n_cols * sprite_sheet.n_rows

			for index in range(num_images):
				if index != 0 and index % sprite_sheet.n_cols == 0:  # If at the end, go to next row
					add_on = (False, True)
					align = (False, False)
				else:
					add_on = (True, False)
					align = (False, True)

				tile_selector_panel.add_element(pygbase.Button(
					(pygbase.UIValue(0.01, False), pygbase.UIValue(8)),
					(pygbase.UIValue(((1 - 0.01) / sprite_sheet.n_cols) - 0.01, False), pygbase.UIValue(0)),
					"tile_sheets", sprite_sheet_name,
					tile_selector_panel,
					self.sheet_tile_selection_button_callback,
					callback_args=(sprite_sheet_name, index),
					index=index
				), add_on_to_previous=add_on, align_with_previous=align)

	def create_entity_editing_ui(self):
		self.entity_editing_ui = self.ui.add_frame(pygbase.Frame(
			(pygbase.UIValue(0), pygbase.UIValue(0)),
			(pygbase.UIValue(1, False), pygbase.UIValue(1, False)),
			self.ui.base_container,
			blocks_mouse=False
		))

		self.current_entity_mode = self.entity_editing_ui.add_element(pygbase.TextSelectionMenu(
			(pygbase.UIValue(10), pygbase.UIValue(70)),
			(pygbase.UIValue(500), pygbase.UIValue(50)),
			"ui",
			["player", "w_monster", "heart_of_sea"],
			self.sheet_tile_editing_ui,
			bg_colour=(40, 40, 40, 40)
		))

	def tile_layer_up_button_callback(self):
		self.tile_layer_text.set_text(str(self.get_current_tile_layer() + 1))

	def tile_layer_down_button_callback(self):
		self.tile_layer_text.set_text(str(self.get_current_tile_layer() - 1))

	def tile_selection_button_callback(self, tile_name: str):
		self.current_tile = tile_name

	def hide_layers_button_callback(self):
		self.hide_other_layers = not self.hide_other_layers

	def sheet_tile_selection_button_callback(self, sprite_sheet_name: str, index: int):
		if self.ui.on_ui():
			self.current_sheet = sprite_sheet_name
			self.current_sheet_index = index

	def set_active_sheet_tiles(self, all_false: bool = False):
		for tile_selector_name, tile_selector in self.sprite_sheet_tile_frames.items():
			if all_false:
				tile_selector.active = False
				continue

			if tile_selector_name == self.sheet_selector.get_current_text():
				tile_selector.active = True
			else:
				tile_selector.active = False

	def get_current_tile_layer(self) -> int:
		return int(self.tile_layer_text.text.text)

	def get_mouse_pos(self):
		mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
		mouse_pos.x = (mouse_pos.x - self.screen_size[0] / 2) * (1 - self.level.get_parallax_layer(self.get_current_tile_layer()) * self.level.parallax_amount) + self.screen_size[0] / 2
		mouse_pos.y = (mouse_pos.y - self.screen_size[1] / 2) * (1 - self.level.get_parallax_layer(self.get_current_tile_layer()) * self.level.parallax_amount) + self.screen_size[1] / 2

		return self.camera_controller.camera.screen_to_world(mouse_pos)

	def get_mouse_tile_pos(self):
		return self.level.get_tile_pos(self.get_mouse_pos())

	def update(self, delta: float):
		self.ui.update(delta)
		match (self.mode_selector.get_current_text()):
			case "Tile":
				self.tile_layer_ui.active = True
				self.tile_editing_ui.active = True
				self.sheet_tile_editing_ui.active = False
				self.entity_editing_ui.active = False
				self.set_active_sheet_tiles(all_false=True)
			case "Sheet":
				self.tile_layer_ui.active = True
				self.tile_editing_ui.active = False
				self.sheet_tile_editing_ui.active = True
				self.entity_editing_ui.active = False
				self.set_active_sheet_tiles()
			case "Entity":
				self.tile_layer_ui.active = False
				self.tile_editing_ui.active = False
				self.sheet_tile_editing_ui.active = False
				self.entity_editing_ui.active = True
				self.set_active_sheet_tiles(all_false=True)
			case _:
				self.tile_layer_ui.active = False
				self.tile_editing_ui.active = False
				self.sheet_tile_editing_ui.active = False
				self.entity_editing_ui.active = False
				self.set_active_sheet_tiles(all_false=True)

		if pygbase.InputManager.get_key_just_pressed(pygame.K_s) and (pygbase.InputManager.check_modifiers(pygame.KMOD_CTRL) or pygbase.InputManager.check_modifiers(pygame.KMOD_META)):
			self.level.save()

		if not (pygbase.InputManager.get_key_pressed(pygame.K_s) and (pygbase.InputManager.check_modifiers(pygame.KMOD_CTRL) or pygbase.InputManager.check_modifiers(pygame.KMOD_META))):
			self.camera_controller.update(delta)

		if not self.ui.on_ui():
			match (self.mode_selector.get_current_text()):
				case "Tile":
					if pygbase.InputManager.get_mouse_pressed(0):
						self.level.add_tile(self.get_mouse_tile_pos(), self.get_current_tile_layer(), self.current_tile)
					if pygbase.InputManager.get_mouse_pressed(2):
						self.level.remove_tile(self.get_mouse_tile_pos(), self.get_current_tile_layer())
				case "Sheet":
					if pygbase.InputManager.get_mouse_pressed(0):
						if pygbase.InputManager.get_key_pressed(pygame.K_SPACE) and self.prev_mouse_tile_pos != self.get_mouse_tile_pos():
							offset = self.get_mouse_tile_pos()[0] - self.prev_mouse_tile_pos[0], self.get_mouse_tile_pos()[1] - self.prev_mouse_tile_pos[1]

							self.current_sheet_index += offset[0] + offset[1] * self.sprite_sheets[self.current_sheet].n_cols

							self.current_sheet_index = max(min(self.current_sheet_index, self.sprite_sheets[self.current_sheet].n_cols * self.sprite_sheets[self.current_sheet].n_rows - 1), 0)

						self.level.add_sheet_tile(self.get_mouse_tile_pos(), self.get_current_tile_layer(), self.current_sheet, self.current_sheet_index)
					if pygbase.InputManager.get_mouse_pressed(2):
						self.level.remove_tile(self.get_mouse_tile_pos(), self.get_current_tile_layer())
				case "Entity":
					if pygbase.InputManager.get_mouse_just_pressed(0):
						if self.current_entity_mode.get_current_text() == "player":
							if pygbase.InputManager.check_modifiers(pygame.KMOD_SHIFT):
								self.level.player_spawn_pos = (self.get_mouse_pos()[0], self.get_mouse_tile_pos()[1] * self.level.tile_size[1])
							else:
								self.level.player_spawn_pos = tuple(self.get_mouse_pos())

						elif self.current_entity_mode.get_current_text() == "w_monster":
							if pygbase.InputManager.check_modifiers(pygame.KMOD_SHIFT):
								spawn_pos = (self.get_mouse_pos()[0], self.get_mouse_tile_pos()[1] * self.level.tile_size[1])
							else:
								spawn_pos = tuple(self.get_mouse_pos())
							self.level.water_enemy_spawn_locations.append(spawn_pos)

						elif self.current_entity_mode.get_current_text() == "heart_of_sea":
							if pygbase.InputManager.check_modifiers(pygame.KMOD_SHIFT):
								self.level.heart_of_the_sea_pos = (self.get_mouse_pos()[0], self.get_mouse_tile_pos()[1] * self.level.tile_size[1])
							else:
								self.level.heart_of_the_sea_pos = tuple(self.get_mouse_pos())

					elif pygbase.InputManager.get_mouse_pressed(2):
						if self.current_entity_mode.get_current_text() == "w_monster":
							for pos in self.level.water_enemy_spawn_locations[:]:
								if self.get_mouse_pos().distance_to(pos) < 40:
									self.level.water_enemy_spawn_locations.remove(pos)

			self.prev_mouse_tile_pos = self.get_mouse_tile_pos()

	def draw(self, surface: pygame.Surface):
		surface.fill("black")

		# Level
		match (self.mode_selector.get_current_text()):
			case "Tile":
				if not self.hide_other_layers:
					self.level.layered_editor_draw(surface, self.camera_controller.camera, self.get_current_tile_layer())
				else:
					self.level.single_layer_editor_draw(surface, self.camera_controller.camera, self.get_current_tile_layer())
			case "Sheet":
				if not self.hide_other_layers:
					self.level.layered_editor_draw(surface, self.camera_controller.camera, self.get_current_tile_layer())
				else:
					self.level.single_layer_editor_draw(surface, self.camera_controller.camera, self.get_current_tile_layer())
			case "Entity":
				self.level.editor_draw(surface, self.camera_controller.camera)
			case "View":
				self.level.draw(surface, self.camera_controller.camera, [], 0)
			case _:
				self.level.editor_draw(surface, self.camera_controller.camera)

		if not self.ui.on_ui():
			match (self.mode_selector.get_current_text()):
				case "Tile":
					if not pygbase.InputManager.get_mouse_pressed(2):
						Tile(self.get_mouse_tile_pos(), self.tile_size, self.level.get_parallax_layer(self.get_current_tile_layer()), self.level.parallax_amount).set_image(self.current_tile).editor_draw_overlay(surface, self.camera_controller.camera)
					else:
						tile_size = (
							self.tile_size[0] * (1 + self.level.get_parallax_layer(self.get_current_tile_layer()) * self.level.parallax_amount),
							self.tile_size[1] * (1 + self.level.get_parallax_layer(self.get_current_tile_layer()) * self.level.parallax_amount)
						)

						screen_pos = self.camera_controller.camera.world_to_screen((
							self.get_mouse_tile_pos()[0] * self.tile_size[0],
							self.get_mouse_tile_pos()[1] * self.tile_size[1]
						))

						parallax_factor = (1 + self.level.get_parallax_layer(self.get_current_tile_layer()) * self.level.parallax_amount)
						screen_pos = (
							(screen_pos[0] - self.screen_size[0] / 2) * parallax_factor + self.screen_size[0] / 2,
							(screen_pos[1] - self.screen_size[1] / 2) * parallax_factor + self.screen_size[1] / 2
						)

						pygame.draw.rect(surface, "red", (screen_pos, tile_size), width=2)
				case "Sheet":
					if not pygbase.InputManager.get_mouse_pressed(2):
						Tile(self.get_mouse_tile_pos(), self.tile_size, self.level.get_parallax_layer(self.get_current_tile_layer()), self.level.parallax_amount).set_sprite_sheet(self.current_sheet, self.current_sheet_index).editor_draw_overlay(surface, self.camera_controller.camera)
					else:
						pygame.draw.rect(surface, "red", (self.camera_controller.camera.world_to_screen((self.get_mouse_tile_pos()[0] * self.tile_size[0], self.get_mouse_tile_pos()[1] * self.tile_size[1])), self.tile_size), width=2)
				case "Entity":
					pygame.draw.circle(surface, "yellow", pygame.mouse.get_pos(), 5)

		if self.mode_selector.get_current_text() != "View":
			# World Reference
			center_point = self.camera_controller.camera.world_to_screen((0, 0))
			pygame.draw.line(surface, "yellow", (0, center_point[1]), (800, center_point[1]))

			pygame.draw.circle(surface, "yellow", center_point, 5)

		self.ui.draw(surface)
