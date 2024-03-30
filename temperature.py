import pygame
import pygbase


class Temperature:
	def __init__(self, pos: tuple | pygame.Vector2, offset: tuple[int, int] = (0, 0), cooling_speed: float = 5, max_temperature: float = 100):
		self.pos = pygame.Vector2(pos)
		self.offset = pygame.Vector2(offset)

		self.cooling_speed = cooling_speed
		self.max_temperature = max_temperature
		self.temperature = 0

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

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.rect(surface, (40, 40, 40), (camera.world_to_screen(self.pos + self.offset), (40, 100)))
		pygame.draw.rect(surface, (200, 200, 200), (camera.world_to_screen(self.pos + self.offset + (3, 3 + 94 * (1 - self.get_percentage()))), (34, 94 * self.get_percentage())))
