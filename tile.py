import pygame
import pygbase


class Tile:
	def __init__(self, pos: tuple[int, int], tile_size: tuple[float, float]):
		self.pos: pygame.Vector2 = pygame.Vector2(pos[0] * tile_size[0], pos[1] * tile_size[1])

		self.from_sheet = False

		self.name: str | None = None
		self.sheet_name: str | None = None
		self.sheet_index: int | None = None

		self.image: pygbase.Image | None = None
		self.rect: pygame.Rect = pygame.Rect(self.pos, tile_size)

	def set_image(self, tile_name: str) -> "Tile":
		self.from_sheet = False
		self.name = tile_name

		self.image: pygbase.Image = pygbase.ResourceManager.get_resource("tiles", tile_name)

		return self

	def set_sprite_sheet(self, sheet_name: str, index: int) -> "Tile":
		self.from_sheet = True
		self.sheet_name = sheet_name
		self.sheet_index = index

		self.image: pygbase.Image = pygbase.ResourceManager.get_resource("tile_sheets", sheet_name).get_image(index)

		return self

	# self.image =

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.image.draw(surface, camera.world_to_screen(self.pos))

	def editor_draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.image.draw(surface, camera.world_to_screen(self.pos), flags=pygame.BLEND_ADD)

	def editor_draw_dark(self, surface: pygame.Surface, camera: pygbase.Camera):
		image = self.image.get_image(0).convert_alpha()
		image.fill((90, 90, 90, 40), special_flags=pygame.BLEND_MULT)

		surface.blit(image, (camera.world_to_screen(self.rect.topleft), self.rect.size))
