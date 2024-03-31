import random

import pygame
import pygbase

from level import Level
from particle_collider import CollisionParticleGroup
from player import Player
from projectiles import ProjectileGroup
from water_monster import WaterMonster, WaterMonsterGroup


class Game(pygbase.GameState, name="game"):
	def __init__(self):
		super().__init__()

		self.water_alpha = pygbase.Common.get_value("water_alpha")
		self.outline_draw_surface: pygame.Surface = pygbase.Common.get_value("water_outline_surface")
		self.water_draw_surfaces: dict[str | tuple, pygame.Surface] = pygbase.Common.get_value("water_surfaces")

		self.level = Level()
		self.particle_manager = pygbase.ParticleManager(chunk_size=pygbase.Common.get_value("tile_size")[0], colliders=self.level.get_colliders())
		self.projectile_group = ProjectileGroup(self.level)

		self.water_monster_group = WaterMonsterGroup()
		for i in range(1000):
			self.water_monster_group.water_monsters.append(WaterMonster((500 + 200 * i, 0), self.level, self.particle_manager, self.projectile_group))

		self.collision_particle_group = CollisionParticleGroup("flamethrower", {tile_pos: tile.rect for tile_pos, tile in self.level.tiles[0].items()})
		self.fire_particle_settings = pygbase.Common.get_particle_setting("fire")
		self.smoke_particle_settings = pygbase.Common.get_particle_setting("smoke")

		player_spawn_pos = (5000, 0)
		self.camera = pygbase.Camera(player_spawn_pos - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2)
		pygbase.Common.set_value("camera", self.camera)
		self.player = Player(player_spawn_pos, self.level, self.camera, self.particle_manager, self.collision_particle_group)

	def update(self, delta: float):
		self.camera.tick(delta)

		water_monster_colliders = self.water_monster_group.get_colliders(self.player.pos)
		self.particle_manager.pass_dynamic_colliders(water_monster_colliders)
		self.particle_manager.update(delta)
		particle_collision_positions = self.collision_particle_group.update(delta, water_monster_colliders)

		hits = self.projectile_group.update(delta, [self.player.ground_rect])
		for hit in hits:
			if hit[0].colliderect(self.player.ground_rect):
				self.player.health.damage(hit[1])

				self.camera.shake_screen(0.3)

		particle_collision_circle_colliders = []
		for particle_collision_position in particle_collision_positions:
			for _ in range(random.randint(5, 10)):
				self.particle_manager.add_particle(particle_collision_position + pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20)), self.fire_particle_settings)
			for _ in range(random.randint(10, 15)):
				offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20))
				self.particle_manager.add_particle(particle_collision_position + offset, self.smoke_particle_settings, initial_velocity=offset * random.uniform(2, 5))

			particle_collision_circle_colliders.append(pygame.geometry.Circle(particle_collision_position, 10))

		self.water_monster_group.update(delta, self.player.pos, particle_collision_circle_colliders, self.camera)

		self.player.update(delta)

		self.camera.lerp_to_target(self.player.pos - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2, 2 * delta)

	def draw(self, surface: pygame.Surface):
		surface.fill((150, 180, 223))
		self.outline_draw_surface.fill((0, 0, 0, 0))
		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((0, 0, 0, 0))

		near_water_monsters = self.water_monster_group.get_monsters(self.player.pos)
		self.level.draw(surface, self.camera, [self.player, *near_water_monsters], 0, exclude_layers={1})

		self.projectile_group.draw(surface, self.camera)

		self.particle_manager.draw(surface, self.camera)
		# self.collision_particle_group.draw(surface, self.camera)

		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((255, 255, 255, self.water_alpha), special_flags=pygame.BLEND_RGBA_MIN)

			surface.blit(water_draw_surface, (0, 0))
		surface.blit(self.outline_draw_surface, (0, 0))

		self.level.single_layer_draw(surface, self.camera, 1)  # Water

		for water_monster in near_water_monsters:
			water_monster.draw_ui(surface, self.camera)

		self.player.draw_ui(surface, self.camera)
