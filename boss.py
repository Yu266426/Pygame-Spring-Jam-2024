import pygame
import pygbase


class HeartOfTheSeaBoss:
	def __init__(self, pos: tuple):
		self.pos = pygame.Vector2(pos)

		self.animations = pygbase.AnimationManager([
			("idle", pygbase.Animation("sprite_sheets", "clam_boss_idle", 0, 1, True), 0),
			("slam", pygbase.Animation("sprite_sheets", "clam_boss_slam", 0, 16, True), 12),
		], "slam")

	def update(self, delta: float):
		self.animations.update(delta)

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.circle(surface, "light blue", camera.world_to_screen(self.pos), 200, width=10)

		self.animations.draw_at_pos(surface, self.pos, camera, draw_pos="midbottom")
