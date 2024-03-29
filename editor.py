import logging

import pygame
import pygbase

from level import Level
from tile import Tile


class Editor(pygbase.GameState, name="editor"):
	def __init__(self):
		super().__init__()

		self.camera_controller = pygbase.CameraController((-400, -400))

		self.level = Level()

		self.ui = pygbase.UIManager()

		self.mode_selector = self.ui.add_element(pygbase.TextSelectionMenu(
			(pygbase.UIValue(10), pygbase.UIValue(10)),
			(pygbase.UIValue(250), pygbase.UIValue(50)),
			"ui",
			["Tile", "Sheet", "View"],
			self.ui.base_container,
			bg_colour=(40, 40, 40, 40)
		))

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

		self.tile_editing_ui = None
		self.current_tile = None
		self.create_tile_edit_ui()

		self.sheet_tile_editing_ui = None
		self.sprite_sheets = pygbase.ResourceManager.get_resources_of_type("tile_sheets")
		self.sprite_sheet_tile_frames = None
		self.sheet_selector = None
		self.current_sheet = None
		self.current_sheet_index = 0
		self.create_sheet_tile_edit_ui()

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

	def tile_layer_up_button_callback(self):
		self.tile_layer_text.set_text(str(self.get_current_tile_layer() + 1))

	def tile_layer_down_button_callback(self):
		self.tile_layer_text.set_text(str(self.get_current_tile_layer() - 1))

	def tile_selection_button_callback(self, tile_name: str):
		self.current_tile = tile_name

	def sheet_tile_selection_button_callback(self, sprite_sheet_name: str, index: int):
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

	def update(self, delta: float):
		self.ui.update(delta)
		match (self.mode_selector.get_current_text()):
			case "Tile":
				self.tile_layer_ui.active = True
				self.tile_editing_ui.active = True
				self.sheet_tile_editing_ui.active = False
				self.set_active_sheet_tiles(all_false=True)
			case "Sheet":
				self.tile_layer_ui.active = True
				self.tile_editing_ui.active = False
				self.sheet_tile_editing_ui.active = True
				self.set_active_sheet_tiles()
			case _:
				self.tile_layer_ui.active = False
				self.tile_editing_ui.active = False
				self.sheet_tile_editing_ui.active = False
				self.set_active_sheet_tiles(all_false=True)

		if pygbase.InputManager.get_key_just_pressed(pygame.K_s) and (pygbase.InputManager.check_modifiers(pygame.KMOD_CTRL) or pygbase.InputManager.check_modifiers(pygame.KMOD_META)):
			self.level.save()

		if not (pygbase.InputManager.get_key_pressed(pygame.K_s) and (pygbase.InputManager.check_modifiers(pygame.KMOD_CTRL) or pygbase.InputManager.check_modifiers(pygame.KMOD_META))):
			self.camera_controller.update(delta)

		if not self.ui.on_ui():
			mouse_pos = self.camera_controller.camera.screen_to_world(pygame.mouse.get_pos())
			mouse_tile_pos = self.level.get_tile_pos(mouse_pos)

			match (self.mode_selector.get_current_text()):
				case "Tile":
					if pygbase.InputManager.get_mouse_pressed(0):
						self.level.add_tile(mouse_tile_pos, self.get_current_tile_layer(), self.current_tile)
					if pygbase.InputManager.get_mouse_pressed(2):
						self.level.remove_tile(mouse_tile_pos, self.get_current_tile_layer())
				case "Sheet":
					if pygbase.InputManager.get_mouse_pressed(0):
						self.level.add_sheet_tile(mouse_tile_pos, self.get_current_tile_layer(), self.current_sheet, self.current_sheet_index)
					if pygbase.InputManager.get_mouse_pressed(2):
						self.level.remove_tile(mouse_tile_pos, self.get_current_tile_layer())

	def draw(self, surface: pygame.Surface):
		surface.fill("black")

		# World Reference
		center_point = self.camera_controller.camera.world_to_screen((0, 0))
		pygame.draw.line(surface, "yellow", (0, center_point[1]), (800, center_point[1]))

		pygame.draw.circle(surface, "yellow", center_point, 5)

		# Level
		match (self.mode_selector.get_current_text()):
			case "Tile":
				self.level.layered_editor_draw(surface, self.camera_controller.camera, self.get_current_tile_layer())
			case "Sheet":
				self.level.layered_editor_draw(surface, self.camera_controller.camera, self.get_current_tile_layer())
			case _:
				self.level.editor_draw(surface, self.camera_controller.camera)

		mouse_pos = self.camera_controller.camera.screen_to_world(pygame.mouse.get_pos())
		tile_size = pygbase.Common.get_value("tile_size")
		mouse_tile_pos = self.level.get_tile_pos(mouse_pos)

		if not self.ui.on_ui():
			match (self.mode_selector.get_current_text()):
				case "Tile":
					if not pygbase.InputManager.get_mouse_pressed(2):
						Tile(mouse_tile_pos, tile_size).set_image(self.current_tile).editor_draw(surface, self.camera_controller.camera)
					else:
						pygame.draw.rect(surface, "red", (self.camera_controller.camera.world_to_screen((mouse_tile_pos[0] * tile_size[0], mouse_tile_pos[1] * tile_size[1])), tile_size), width=2)
				case "Sheet":
					if not pygbase.InputManager.get_mouse_pressed(2):
						Tile(mouse_tile_pos, tile_size).set_sprite_sheet(self.current_sheet, self.current_sheet_index).editor_draw(surface, self.camera_controller.camera)
					else:
						pygame.draw.rect(surface, "red", (self.camera_controller.camera.world_to_screen((mouse_tile_pos[0] * tile_size[0], mouse_tile_pos[1] * tile_size[1])), tile_size), width=2)

		self.ui.draw(surface)
