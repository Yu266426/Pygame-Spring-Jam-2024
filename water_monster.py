import random

import pygame
import pygame.geometry
import pygbase

from level import Level
from temperature import Temperature
from water_orb import WaterOrbGroup


class WaterMonster:
	def __init__(self, pos: tuple, level: Level, particle_manager: pygbase.ParticleManager):
		self.gravity = pygbase.Common.get_value("gravity")
		self.on_ground = False

		self.max_speed_x = 100
		self.max_speed_y = 100

		self.acceleration = pygame.Vector2(0, 0)
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)

		self.rect = pygame.Rect((0, 0), (20, 100))
		self.rect.midbottom = self.pos

		self.water_orb_group = WaterOrbGroup(pos, (0, -80), random.randint(8, 15), (5, 30), attraction_offset_range=((-10, 10), (-50, 50))).link_pos(self.pos)

		self.level = level
		self.level_colliders = self.level.get_colliders(0)

		self.particle_manager = particle_manager
		self.particle_spawner_offset = (0, -80)
		self.particle_spawner_pos = self.pos + self.particle_spawner_offset
		self.water_particle_spawner = particle_manager.add_spawner(
			pygbase.CircleSpawner(self.pos, 0.1, 4, 30, True, "water", particle_manager, radial_velocity_range=(0, 100))
		).link_pos(self.particle_spawner_pos)

		self.outline_draw_surface: pygame.Surface = pygbase.Common.get_value("water_outline_surface")
		self.water_draw_surfaces: dict[str | tuple, pygame.Surface] = pygbase.Common.get_value("water_surfaces")

		self.temperature = Temperature(self.pos).link_pos(self.pos)

	def movement(self, delta):
		self.velocity.x += self.acceleration.x * delta
		self.velocity.x = pygame.math.clamp(self.velocity.x, -self.max_speed_x, self.max_speed_x)

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

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_speed_y, self.max_speed_y)

		self.pos.y += self.velocity.y * delta + 0.5 * self.acceleration.y * (delta ** 2)
		self.rect.midbottom = self.pos

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
		self.temperature.tick(delta)

		self.water_orb_group.update(delta)

		self.movement(delta)
		self.particle_spawner_pos.update(self.pos + self.particle_spawner_offset)

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygbase.DebugDisplay.draw_rect(camera.world_to_screen_rect(self.rect), "yellow")
		self.water_orb_group.draw(self.outline_draw_surface, self.water_draw_surfaces, camera)

	def draw_ui(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.temperature.draw(surface, camera)

	def alive(self):
		return self.temperature.not_maxed()

	def kill(self):
		self.particle_manager.remove_spawner(self.water_particle_spawner)


class WaterMonsterGroup:
	def __init__(self):
		self.water_monsters: list[WaterMonster] = []

	def get_colliders(self, pos: tuple | pygame.Vector2 | None = None, radius: int = 1000) -> list[pygame.Rect]:
		if pos is None:
			return [water_monster.rect for water_monster in self.water_monsters]
		else:
			return [water_monster.rect for water_monster in self.water_monsters if water_monster.pos.distance_to(pos) < radius]

	def get_monsters(self, pos: tuple | pygame.Vector2 | None = None, radius: int = 1000) -> list[WaterMonster]:
		if pos is None:
			return self.water_monsters
		else:
			return [water_monster for water_monster in self.water_monsters if water_monster.pos.distance_to(pos) < radius]

	def update(self, delta: float, pos: tuple | pygame.Vector2, particle_colliders: list[pygame.geometry.Circle]):
		for water_monster in self.water_monsters:
			in_range = water_monster.pos.distance_to(pos) < 1000

			if in_range:
				water_monster.update(delta)

				for particle_collider in particle_colliders:
					if particle_collider.colliderect(water_monster.rect):
						water_monster.temperature.heat(10)

			water_monster.water_particle_spawner.active = in_range

			if not water_monster.alive():
				water_monster.kill()

		self.water_monsters[:] = [water_monster for water_monster in self.water_monsters if water_monster.alive()]
