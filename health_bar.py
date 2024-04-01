import pygame

from health import Health


class HealthBar:
	def __init__(self, pos: tuple, size: tuple, health: Health, border: int = 5):
		self.pos = pos
		self.size = size

		self.border = border

		self.health = health

	def draw(self, surface: pygame.Surface):
		pygame.draw.rect(surface, (30, 30, 30), (self.pos, self.size))
		pygame.draw.rect(surface, (30, 200, 30), (self.pos[0] + self.border, self.pos[1] + self.border, (self.size[0] - self.border * 2) * self.health.get_percentage(), self.size[1] - self.border * 2))
