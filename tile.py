import pygame
import pygbase


class Tile:
	def __init__(self, pos: tuple[int, int], tile_size: tuple[float, float], parallax_layer: int, parallax_amount: float):
		self.screen_size = pygbase.Common.get_value("screen_size")

		self.parallax_layer: int = parallax_layer
		self.parallax_amount: float = parallax_amount

		self.buffer_factor = 1.08 if self.parallax_layer != 0 else 1

		self.parallax_factor = max(1 + self.parallax_layer * self.parallax_amount, 0)

		self.pos: pygame.Vector2 = pygame.Vector2(pos[0] * tile_size[0], pos[1] * tile_size[1])

		self.from_sheet = False

		self.name: str | None = None
		self.sheet_name: str | None = None
		self.sheet_index: int | None = None

		self.original_image: pygbase.Image | None = None
		self.image: pygame.Surface | None = None

		self._rect: pygame.Rect = pygame.Rect(self.pos, (tile_size[0] * self.parallax_factor, tile_size[1] * self.parallax_factor))
		self.collider_rect: pygame.Rect | None = None

	@property
	def rect(self):
		if self.collider_rect is None:
			return self._rect
		else:
			return self.collider_rect

	def set_image(self, tile_name: str) -> "Tile":
		self.from_sheet = False
		self.name = tile_name

		self.original_image = pygbase.ResourceManager.get_resource("tiles", tile_name)
		image: pygame.Surface = self.original_image.get_image()

		image_cache = pygbase.Common.get_value("parallax_image_cache")
		if (self.parallax_layer, tile_name) not in image_cache:
			self.image = image_cache[(self.parallax_layer, tile_name)] = pygame.transform.scale_by(image, self.parallax_factor * self.buffer_factor)
		else:
			self.image = image_cache[(self.parallax_layer, tile_name)]

		# Custom tiles
		if tile_name == "sand_step_1":
			pixels_down = 1
			self.collider_rect = pygame.Rect(self.pos.x, self.pos.y + self.rect.height * (pixels_down / 16), self.rect.width, self.rect.height * ((16 - pixels_down) / 16))
		elif tile_name == "sand_step_2":
			pixels_down = 3
			self.collider_rect = pygame.Rect(self.pos.x, self.pos.y + self.rect.height * (pixels_down / 16), self.rect.width, self.rect.height * ((16 - pixels_down) / 16))
		elif tile_name == "sand_step_3":
			pixels_down = 4
			self.collider_rect = pygame.Rect(self.pos.x, self.pos.y + self.rect.height * (pixels_down / 16), self.rect.width, self.rect.height * ((16 - pixels_down) / 16))
		elif tile_name == "sand_step_4":
			pixels_down = 5
			self.collider_rect = pygame.Rect(self.pos.x, self.pos.y + self.rect.height * (pixels_down / 16), self.rect.width, self.rect.height * ((16 - pixels_down) / 16))
		elif tile_name == "sand_step_5":
			pixels_down = 6
			self.collider_rect = pygame.Rect(self.pos.x, self.pos.y + self.rect.height * (pixels_down / 16), self.rect.width, self.rect.height * ((16 - pixels_down) / 16))

		return self

	def set_sprite_sheet(self, sheet_name: str, index: int) -> "Tile":
		self.from_sheet = True
		self.sheet_name = sheet_name
		self.sheet_index = index

		self.original_image = pygbase.ResourceManager.get_resource("tile_sheets", sheet_name).get_image(index)
		image: pygame.Surface = self.original_image.get_image()

		image_cache = pygbase.Common.get_value("parallax_image_cache")
		if (self.parallax_layer, sheet_name, index) not in image_cache:
			self.image = image_cache[(self.parallax_layer, sheet_name, index)] = pygame.transform.scale_by(image, self.parallax_factor * self.buffer_factor)
		else:
			self.image = image_cache[(self.parallax_layer, sheet_name, index)]

		# Custom tiles
		if sheet_name == "water" and index < 3:
			self.collider_rect = pygame.Rect(self.pos.x, self.pos.y + self.rect.height * 0.2, self.rect.width, self.rect.height * 0.8)

		return self

	# self.image =

	def _get_parallax_pos(self, camera: pygbase.Camera):
		screen_pos = camera.world_to_screen(self.pos)
		return (screen_pos[0] - self.screen_size[0] / 2) * self.parallax_factor + self.screen_size[0] / 2, (screen_pos[1] - self.screen_size[1] / 2) * self.parallax_factor + self.screen_size[1] / 2

	# return screen_pos

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		surface.blit(self.image, self._get_parallax_pos(camera))

	def editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		surface.blit(self.image, self._get_parallax_pos(camera))

		if self.name is not None and self.name == "blank":
			pygame.draw.rect(surface, "red", camera.world_to_screen_rect(self._rect))

	def editor_draw_overlay(self, surface: pygame.Surface, camera: pygbase.Camera):
		surface.blit(self.image, self._get_parallax_pos(camera), special_flags=pygame.BLEND_ADD)

		if self.name is not None and self.name == "blank":
			pygame.draw.rect(surface, "dark red", camera.world_to_screen_rect(self._rect))

	def editor_draw_dark(self, surface: pygame.Surface, camera: pygbase.Camera):
		image = self.image.convert_alpha()
		image.fill((90, 90, 90, 40), special_flags=pygame.BLEND_MULT)

		surface.blit(image, self._get_parallax_pos(camera))

		if self.name is not None and self.name == "blank":
			pygame.draw.rect(surface, "dark red", camera.world_to_screen_rect(self._rect))
