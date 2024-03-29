import pygame
import pygbase

from level import Level
from water_orb import WaterOrbGroup


class WaterMonster:
	def __init__(self, pos: tuple, level: Level):
		self.gravity = pygbase.Common.get_value("gravity")
		self.on_ground = False

		self.max_speed_x = 100
		self.max_speed_y = 100

		self.acceleration = pygame.Vector2(10, 0)
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)

		self.rect = pygame.Rect((0, 0), (20, 60))
		self.rect.midbottom = self.pos

		self.water_orb_group = WaterOrbGroup(pos, (0, -50), 15, (5, 30), ("blue", "light blue", "dark blue"), attraction_offset_range=((-10, 10), (-50, 10))).link_pos(self.pos)

		self.level = level
		self.level_colliders = self.level.get_colliders(0)

	def movement(self, delta):
		self.velocity.x += self.acceleration.x * delta
		self.velocity.x = min(max(self.velocity.x, -self.max_speed_x), self.max_speed_x)

		self.pos.x += self.velocity.x * delta + 0.5 * self.acceleration.x * (delta ** 2)
		self.rect.midbottom = self.pos

		for rect in self.level_colliders:
			if self.rect.colliderect(rect):
				if self.velocity.x > 0:
					self.pos.x = rect.left - self.rect.width / 2
					self.velocity.x = 0
				elif self.velocity.x < 0:
					self.pos.x = rect.right + self.rect.width / 2
					self.velocity.x = 0

		self.rect.midbottom = self.pos

		# Y movement
		# Upwards has less gravity than downwards
		self.acceleration.y = self.gravity

		input_jump = pygbase.InputManager.get_key_pressed(pygame.K_w)

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = min(max(self.velocity.y, -self.max_speed_y), self.max_speed_y)

		self.pos.y += self.velocity.y * delta + 0.5 * self.acceleration.y * (delta ** 2)
		self.rect.midbottom = self.pos

		prev_on_ground = self.on_ground
		self.on_ground = False
		for rect in self.level_colliders:
			if self.rect.colliderect(rect):
				if self.velocity.y > 0:
					self.pos.y = rect.top
					self.velocity.y = 0
					self.on_ground = True

				elif self.velocity.y < 0:
					self.pos.y = rect.bottom + self.rect.height
					self.velocity.y = 0

		self.rect.midbottom = self.pos

	def update(self, delta: float):
		self.water_orb_group.update(delta, self.velocity)

		self.movement(delta)

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.water_orb_group.draw(surface, camera)


class WaterMonsterGroup:
	def __init__(self):
		self.water_monsters: list[WaterMonster] = []

	def get_monsters(self, pos: tuple | pygame.Vector2 | None = None, radius: int = 1000) -> list[WaterMonster]:
		if pos is None:
			return self.water_monsters
		else:
			return [water_monster for water_monster in self.water_monsters if water_monster.pos.distance_to(pos) < radius]

	def update(self, delta):
		for water_monster in self.water_monsters:
			water_monster.update(delta)
