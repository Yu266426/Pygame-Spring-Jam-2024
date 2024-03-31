import pygame
import pygbase


class HeartOfTheSeaBoss:
	def __init__(self, pos: tuple):
		self.pos = pygame.Vector2(pos)

	def update(self, delta):
		pass

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.circle(surface, "light blue", camera.world_to_screen(self.pos), 200, width=10)
