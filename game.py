import random

import pygame
import pygbase

from boss import HeartOfTheSeaBoss
from level import Level
from particle_collider import CollisionParticleGroup
from player import Player
from projectiles import ProjectileGroup, GarbageProjectile
from water_monster import WaterMonster, WaterMonsterGroup


class Game(pygbase.GameState, name="game"):
	def __init__(self):
		super().__init__()

		self.water_alpha = pygbase.Common.get_value("water_alpha")
		self.outline_draw_surface: pygame.Surface = pygbase.Common.get_value("water_outline_surface")
		self.water_draw_surfaces: dict[str | tuple, pygame.Surface] = pygbase.Common.get_value("water_surfaces")

		self.level = Level()
		self.particle_manager = pygbase.ParticleManager(chunk_size=pygbase.Common.get_value("tile_size")[0], colliders=(*self.level.get_colliders(), *self.level.get_colliders(1)))  # NoQA
		self.in_water_particle_manager = pygbase.ParticleManager(chunk_size=pygbase.Common.get_value("tile_size")[0], colliders=self.level.get_colliders())
		self.projectile_group = ProjectileGroup(self.level)

		self.water_monster_group = WaterMonsterGroup()
		for spawn_pos in self.level.water_enemy_spawn_locations:
			self.water_monster_group.water_monsters.append(WaterMonster(spawn_pos, self.level, self.in_water_particle_manager, self.projectile_group))

		self.on_ground_particle_colliders = {tile_pos: tile.rect for tile_pos, tile in self.level.tiles[0].items()}
		self.on_ground_particle_colliders.update({tile_pos: tile.rect for tile_pos, tile in self.level.tiles[1].items()})

		self.in_water_particle_colliders = {tile_pos: tile.rect for tile_pos, tile in self.level.tiles[0].items()}

		self.collision_particle_group = CollisionParticleGroup("flamethrower", self.on_ground_particle_colliders)
		self.flamethrower_particle_settings = pygbase.Common.get_particle_setting("flamethrower")
		self.fire_particle_settings = pygbase.Common.get_particle_setting("fire")
		self.smoke_particle_settings = pygbase.Common.get_particle_setting("smoke")
		self.boiling_water_particle_settings = pygbase.Common.get_particle_setting("boiling_water")
		self.water_vapour_particle_settings = pygbase.Common.get_particle_setting("water_vapour")

		self.camera = pygbase.Camera(self.level.player_spawn_pos - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2)
		pygbase.Common.set_value("camera", self.camera)
		self.player = Player(self.level.player_spawn_pos, self.level, self.camera, self.particle_manager, self.in_water_particle_manager, self.collision_particle_group)

		self.heart_of_the_sea = HeartOfTheSeaBoss(self.level.heart_of_the_sea_pos)

	def update(self, delta: float):
		self.camera.tick(delta)

		water_monster_colliders = self.water_monster_group.get_colliders(self.player.pos)
		self.particle_manager.pass_dynamic_colliders(water_monster_colliders)
		self.in_water_particle_manager.pass_dynamic_colliders(water_monster_colliders)
		self.particle_manager.update(delta)
		self.in_water_particle_manager.update(delta)
		particle_collision_positions = self.collision_particle_group.update(delta, water_monster_colliders)

		hits = self.projectile_group.update(delta, [self.player.rect])
		for hit in hits:
			if hit[0].colliderect(self.player.ground_rect):
				self.player.health.damage(hit[1])

				self.camera.shake_screen(0.3)

		particle_collision_circle_colliders = []
		for particle_collision_info in particle_collision_positions:
			particle_collision_position = particle_collision_info[0]
			particle_setting_name = particle_collision_info[1]

			if particle_setting_name == "flamethrower":
				for _ in range(random.randint(5, 10)):
					self.particle_manager.add_particle(particle_collision_position + pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20)), self.fire_particle_settings)
				for _ in range(random.randint(10, 15)):
					offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20))
					self.particle_manager.add_particle(particle_collision_position + offset, self.smoke_particle_settings, initial_velocity=offset * random.uniform(2, 5))
			elif particle_setting_name == "boiling_water":
				for _ in range(random.randint(20, 30)):
					offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20))
					self.in_water_particle_manager.add_particle(particle_collision_position + offset, self.water_vapour_particle_settings, initial_velocity=offset * random.uniform(4, 8))

			particle_collision_circle_colliders.append(pygame.geometry.Circle(particle_collision_position, 10))

		self.water_monster_group.update(delta, self.player.pos + (0, -10 if self.player.is_swimming else -80), particle_collision_circle_colliders, self.camera)

		self.player.update(delta)

		if self.player.pos.distance_to(self.heart_of_the_sea.pos) < 700:
			self.heart_of_the_sea.update(delta)

		if self.player.pos.distance_to(self.heart_of_the_sea.pos) < 400:
			self.camera.lerp_to_target(((self.player.pos * 2 + self.heart_of_the_sea.pos) / 3) - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2, 2 * delta)
		else:
			self.camera.lerp_to_target(self.player.pos - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2, 3 * delta)

		if self.player.gun_water_to_land:
			self.collision_particle_group.particle_settings = self.flamethrower_particle_settings
			self.collision_particle_group.colliders = self.on_ground_particle_colliders
			self.collision_particle_group.particles.clear()
		elif self.player.gun_land_to_water:
			self.collision_particle_group.particle_settings = self.boiling_water_particle_settings
			self.collision_particle_group.colliders = self.in_water_particle_colliders
			self.collision_particle_group.particles.clear()

	def draw(self, surface: pygame.Surface):
		surface.fill((150, 180, 223))
		self.outline_draw_surface.fill((0, 0, 0, 0))
		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((0, 0, 0, 0))

		near_water_monsters = self.water_monster_group.get_monsters(self.player.pos)
		self.level.draw(surface, self.camera, [self.heart_of_the_sea, self.player, *near_water_monsters], 0, exclude_layers={1})

		self.projectile_group.draw(surface, self.camera)

		self.particle_manager.draw(surface, self.camera)
		self.in_water_particle_manager.draw(surface, self.camera)
		# self.collision_particle_group.draw(surface, self.camera)

		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((255, 255, 255, self.water_alpha), special_flags=pygame.BLEND_RGBA_MIN)

			surface.blit(water_draw_surface, (0, 0))
		surface.blit(self.outline_draw_surface, (0, 0))

		self.level.single_layer_draw(surface, self.camera, 1)  # Water

		for water_monster in near_water_monsters:
			water_monster.draw_ui(surface, self.camera)

		self.player.draw_ui(surface, self.camera)
