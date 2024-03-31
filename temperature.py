import pygame
import pygbase


class Temperature:
	def __init__(
			self,
			pos: tuple | pygame.Vector2,
			offset: tuple[float, float] = (0, 0),
			cooling_speed: float = 5,
			max_temperature: float = 100,
			color_range: tuple[pygame.Color, pygame.Color] = (pygame.Color("green"), pygame.Color("red"))
	):
		self.pos = pygame.Vector2(pos)
		self.offset = pygame.Vector2(offset)

		self.cooling_speed = cooling_speed
		self.max_temperature = max_temperature
		self.temperature = 0

		self.image: pygbase.Image = pygbase.ResourceManager.get_resource("images", "thermometer")
		self.background_image: pygbase.Image = pygbase.ResourceManager.get_resource("images", "thermometer_background")
		self.background_mask = pygame.Surface(self.image.get_image().get_rect().size, flags=pygame.SRCALPHA)

		self.color_range: tuple[pygame.Color, pygame.Color] = color_range

	def link_pos(self, pos: pygame.Vector2) -> "Temperature":
		self.pos = pos
		return self

	def heat(self, amount: float):
		self.temperature = min(self.temperature + amount, self.max_temperature)

	def tick(self, delta: float):
		self.temperature = max(self.temperature - self.cooling_speed * delta, 0)

	def not_maxed(self, buffer: float = 0.1) -> bool:
		return self.temperature < self.max_temperature - buffer

	def get_percentage(self) -> float:
		return self.temperature / self.max_temperature

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera, color_override: tuple[int, int, int] | None = None):
		self.background_mask.fill((0, 0, 0, 0))

		if color_override is None:
			color = self.color_range[0].lerp(self.color_range[1], self.get_percentage())
			mask_color = (color.r, color.g, color.b, 255)
		else:
			mask_color = (*color_override, 255)
		pygame.draw.rect(self.background_mask, mask_color, (
			0, self.background_mask.get_height() * (1 - self.get_percentage()),
			self.background_mask.get_width(), self.background_mask.get_height() * self.get_percentage()
		))

		background_surface = self.background_image.get_image().copy()
		background_surface.blit(self.background_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

		surface.blit(background_surface, camera.world_to_screen(self.pos + self.offset + (-self.background_mask.get_width() / 2, -self.background_mask.get_height())))
		self.image.draw(surface, camera.world_to_screen(self.pos + self.offset), draw_pos="midbottom")

# pygame.draw.rect(surface, (40, 40, 40), (camera.world_to_screen(self.pos + self.offset), (40, 100)))
# pygame.draw.rect(surface, (200, 200, 200), (camera.world_to_screen(self.pos + self.offset + (3, 3 + 94 * (1 - self.get_percentage()))), (34, 94 * self.get_percentage())))
