import enum
import random

import pygame
import pygame.geometry
import pygbase

from level import Level
from projectiles import ProjectileGroup, GarbageProjectile
from temperature import Temperature
from utils import get_sign
from water_orb import WaterOrbGroup


class WaterMonsterAttacks(enum.Enum):
	NONE = enum.auto()
	GARBAGE_THROW = enum.auto()
	WATER_GUN = enum.auto()  # TODO: Implement


class WaterMonsterStates(enum.Enum):
	SEARCH = enum.auto()
	MOVE_TOWARDS_PLAYER = enum.auto()
	GARBAGE_ATTACK = enum.auto()


class WaterMonsterAI:
	def __init__(self, linked_pos: pygame.Vector2, temperature: Temperature, search_radius: float = 1000, attack_radius: float = 400):
		self.pos = linked_pos
		self.temperature = temperature  # TODO: USE

		self.current_state = WaterMonsterStates.SEARCH

		self.search_radius = search_radius
		self.attack_radius = attack_radius

		self.movement = pygame.Vector2()

		self.camera = pygbase.Common.get_value("camera")
		self.tile_size = pygbase.Common.get_value("tile_size")

	def update(self, delta: float, player_pos: pygame.Vector2, level_colliders: dict[tuple, pygame.Rect], in_water: bool):
		offset_vector = player_pos - self.pos
		dist_to_player = offset_vector.length()
		if offset_vector.length() != 0:
			offset_vector.normalize_ip()

		match self.current_state:
			case WaterMonsterStates.SEARCH:
				pygbase.DebugDisplay.draw_circle(self.camera.world_to_screen(self.pos), self.search_radius, "yellow")

				self.movement.update(0, 0)

				if dist_to_player < self.search_radius:
					self.current_state = WaterMonsterStates.MOVE_TOWARDS_PLAYER
			case WaterMonsterStates.MOVE_TOWARDS_PLAYER:
				pygbase.DebugDisplay.draw_circle(self.camera.world_to_screen(self.pos), self.attack_radius, "red")

				self.movement.x = offset_vector.x

				if dist_to_player > self.search_radius:
					self.current_state = WaterMonsterStates.SEARCH
				elif dist_to_player < self.attack_radius:
					self.current_state = WaterMonsterStates.GARBAGE_ATTACK
			case WaterMonsterStates.GARBAGE_ATTACK:
				if dist_to_player < self.attack_radius * 0.9:
					self.movement.x = -offset_vector.x
				else:
					self.movement.x = offset_vector.x

				if dist_to_player > self.attack_radius:
					self.current_state = WaterMonsterStates.SEARCH

		if in_water:
			self.movement.y = get_sign(offset_vector.y)
		else:
			self.movement.y = 0

		has_collided = False
		in_front_collider = pygame.Rect(self.pos.x + self.movement.x * 20, self.pos.y - 20, 5, 10)
		tile_pos = int(self.pos.x // self.tile_size[0]), int(self.pos.y // self.tile_size[1])
		top_left = (tile_pos[0] - 1, tile_pos[1] - 1)
		bottom_right = (tile_pos[0] + 1, tile_pos[1] + 1)

		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				rect = level_colliders.get((col, row))
				if rect is not None and rect.colliderect(in_front_collider):
					if in_front_collider.colliderect(rect):
						has_collided = True
						self.movement.y = -5000 if in_water else -1
						break

		pygbase.DebugDisplay.draw_rect(self.camera.world_to_screen_rect(in_front_collider), "blue" if not has_collided else "red")

	def get_movement(self) -> pygame.Vector2:
		return self.movement

	def get_attack(self):
		match self.current_state:
			case WaterMonsterStates.GARBAGE_ATTACK:
				return WaterMonsterAttacks.GARBAGE_THROW
			case _:
				return WaterMonsterAttacks.NONE


class WaterMonster:
	def __init__(self, pos: tuple, level: Level, particle_manager: pygbase.ParticleManager, projectile_group: ProjectileGroup):
		self.id = -1

		self.gravity = pygbase.Common.get_value("gravity")
		self.water_level = pygbase.Common.get_value("water_level")
		self.on_ground = False

		self.acceleration_speed = 200
		self.x_damping = 8.0

		self.jump_impulse = 600

		self.max_speed_x = 100
		self.max_speed_y = 100

		self.acceleration = pygame.Vector2(0, 0)
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)

		self.rect = pygame.Rect((0, 0), (20, 120))
		self.rect.midbottom = self.pos

		self.water_orb_group = WaterOrbGroup(pos, (0, -80), random.randint(8, 15), (5, 30), attraction_offset_range=((-10, 10), (-50, 50))).link_pos(self.pos)
		self.water_orb_average_pos = self.water_orb_group.get_orb_average_pos()

		self.level = level
		self.level_colliders = {tile_pos: tile.rect for tile_pos, tile in self.level.tiles[0].items()}

		self.particle_manager = particle_manager
		self.water_particle_spawner = particle_manager.add_spawner(
			pygbase.CircleSpawner(self.pos, 0.1, 4, 30, False, "polluted_water", particle_manager, radial_velocity_range=(0, 100))
		).link_pos(self.water_orb_average_pos)
		self.death_water_particle_settings = pygbase.Common.get_particle_setting("water_vapour")

		self.outline_draw_surface: pygame.Surface = pygbase.Common.get_value("water_outline_surface")
		self.water_draw_surfaces: dict[str | tuple, pygame.Surface] = pygbase.Common.get_value("water_surfaces")

		self.temperature = Temperature(self.water_orb_average_pos, offset=(0, -80)).link_pos(self.water_orb_average_pos)

		self.ai = WaterMonsterAI(self.pos, self.temperature)

		self.projectile_group = projectile_group
		self.garbage_throw_cooldown_range = (0.5, 1.3)
		self.garbage_throw_timer = pygbase.Timer(0, True, True)

		self.damage_collider = pygame.Rect(0, 0, 50, 100)

	def movement(self, delta):
		movement = self.ai.get_movement()

		if movement.x != 0:
			self.acceleration.x = movement.x * self.acceleration_speed
		else:
			self.acceleration.x = -self.velocity.x * self.x_damping

		self.velocity.x += self.acceleration.x * delta
		self.velocity.x = pygame.math.clamp(self.velocity.x, -self.max_speed_x, self.max_speed_x)

		self.pos.x += self.velocity.x * delta + 0.5 * self.acceleration.x * (delta ** 2)
		self.rect.midbottom = self.pos

		tile_pos = int(self.pos.x // self.level.tile_size[0]), int(self.pos.y // self.level.tile_size[1])
		top_left = (tile_pos[0] - 1, tile_pos[1] - 1)
		bottom_right = (tile_pos[0] + 1, tile_pos[1] + 1)

		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				rect = self.level_colliders.get((col, row))
				if rect is not None and rect.colliderect(self.rect):
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

		if self.on_ground and movement.y < 0:  # Jump
			self.acceleration.y -= self.jump_impulse / delta
			self.on_ground = False

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_speed_y * 10, self.max_speed_y)

		self.pos.y += self.velocity.y * delta + 0.5 * self.acceleration.y * (delta ** 2)
		self.rect.midbottom = self.pos

		tile_pos = int(self.pos.x // self.level.tile_size[0]), int(self.pos.y // self.level.tile_size[1])
		top_left = (tile_pos[0] - 1, tile_pos[1] - 1)
		bottom_right = (tile_pos[0] + 1, tile_pos[1] + 1)

		self.on_ground = False
		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				rect = self.level_colliders.get((col, row))
				if rect is not None and rect.colliderect(self.rect):
					if self.velocity.y > 0:
						self.pos.y = rect.top
						self.velocity.y = 0
						self.on_ground = True

					elif self.velocity.y < 0:
						self.pos.y = rect.bottom + self.rect.height
						self.velocity.y = 0

		self.rect.midbottom = self.pos

	def water_movement(self, delta):
		movement = self.ai.get_movement()

		if movement.x != 0:
			self.acceleration.x = movement.x * self.acceleration_speed
		else:
			self.acceleration.x = -self.velocity.x * self.x_damping

		self.velocity.x += self.acceleration.x * delta
		self.velocity.x = pygame.math.clamp(self.velocity.x, -self.max_speed_x, self.max_speed_x)

		self.pos.x += self.velocity.x * delta + 0.5 * self.acceleration.x * (delta ** 2)
		self.rect.midbottom = self.pos

		tile_pos = int(self.pos.x // self.level.tile_size[0]), int(self.pos.y // self.level.tile_size[1])
		top_left = (tile_pos[0] - 1, tile_pos[1] - 1)
		bottom_right = (tile_pos[0] + 1, tile_pos[1] + 1)

		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				rect = self.level_colliders.get((col, row))
				if rect is not None and rect.colliderect(self.rect):
					if self.velocity.x > 0:
						self.pos.x = rect.left - self.rect.width / 2
						self.velocity.x = 0
					elif self.velocity.x < 0:
						self.pos.x = rect.right + self.rect.width / 2
						self.velocity.x = 0

		self.rect.midbottom = self.pos

		# Y movement
		if movement.y != 0:
			self.acceleration.y = movement.y * self.acceleration_speed
		else:
			self.acceleration.y = -self.velocity.y * self.x_damping

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_speed_y, self.max_speed_x)

		self.pos.y += self.velocity.y * delta + 0.5 * self.acceleration.y * (delta ** 2)
		self.rect.midbottom = self.pos

		tile_pos = int(self.pos.x // self.level.tile_size[0]), int(self.pos.y // self.level.tile_size[1])
		top_left = (tile_pos[0] - 1, tile_pos[1] - 1)
		bottom_right = (tile_pos[0] + 1, tile_pos[1] + 1)

		for row in range(top_left[1], bottom_right[1]):
			for col in range(top_left[0], bottom_right[0]):
				rect = self.level_colliders.get((col, row))
				if rect is not None and rect.colliderect(self.rect):
					if self.velocity.y > 0:
						self.pos.y = rect.top
						self.velocity.y = 0

					elif self.velocity.y < 0:
						self.pos.y = rect.bottom + self.rect.height
						self.velocity.y = 0

		self.rect.midbottom = self.pos

	def attacks(self, player_pos: tuple | pygame.Vector2):
		attack = self.ai.get_attack()

		towards_player_vec = player_pos - self.water_orb_average_pos

		match attack:
			case WaterMonsterAttacks.GARBAGE_THROW:
				if self.garbage_throw_timer.done():
					if self.water_orb_average_pos.y > self.water_level:
						throw_vec = towards_player_vec.normalize() * random.uniform(600, 800)
					else:
						initial_x_velocity = towards_player_vec.normalize().x * random.uniform(400, 600)
						throw_vec = pygame.Vector2(
							initial_x_velocity,
							-((0.5 * self.gravity * (towards_player_vec.x ** 2) / initial_x_velocity) - towards_player_vec.y * initial_x_velocity) / towards_player_vec.x
						)

					self.projectile_group.add_projectile(GarbageProjectile(self.water_orb_average_pos, throw_vec))

					self.garbage_throw_timer.set_cooldown(random.uniform(*self.garbage_throw_cooldown_range))
					self.garbage_throw_timer.start()

	def update(self, delta: float, player_pos: pygame.Vector2, no_ai: bool):
		if not no_ai:
			self.ai.update(delta, player_pos, self.level_colliders, self.pos.y > self.water_level)

		self.temperature.tick(delta)
		self.garbage_throw_timer.tick(delta)

		if not no_ai:
			if self.pos.y > self.water_level:
				self.water_movement(delta)
			else:
				self.movement(delta)

		self.water_orb_group.update(delta)
		self.water_orb_average_pos.update(self.water_orb_group.get_orb_average_pos())
		self.damage_collider.center = self.water_orb_average_pos
		self.attacks(player_pos)

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygbase.DebugDisplay.draw_rect(camera.world_to_screen_rect(self.rect), "yellow")
		pygbase.DebugDisplay.draw_rect(camera.world_to_screen_rect(self.damage_collider), "yellow")
		pygbase.DebugDisplay.draw_circle(camera.world_to_screen(self.water_orb_average_pos), 10, "yellow")

		self.water_orb_group.draw(self.outline_draw_surface, self.water_draw_surfaces, camera)

	def draw_ui(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.temperature.draw(surface, camera)

	def alive(self):
		return self.temperature.not_maxed()

	def kill(self):
		self.particle_manager.remove_spawner(self.water_particle_spawner)

		for _ in range(random.randint(50, 120)):
			offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), 1)
			self.particle_manager.add_particle(self.water_orb_average_pos + offset * random.uniform(0, 50), self.death_water_particle_settings, initial_velocity=offset * random.uniform(0, 200))


class WaterMonsterGroup:
	def __init__(self):
		self.water_monsters: list[WaterMonster] = []
		self.water_monster_ids: set[int] = set()

		self.monster_update_range = 1200

		self.monster_death_sounds: list[pygame.mixer.Sound] = [pygbase.ResourceManager.get_resource("sound", sound) for sound in ["explosion", "explosion-1", "explosion-2"]]

	def add_water_monster(self, monster_id: int, monster: WaterMonster):
		if monster_id != -1:
			self.water_monster_ids.add(monster_id)

		monster.id = monster_id
		self.water_monsters.append(monster)

	def get_colliders(self, pos: tuple | pygame.Vector2 | None = None, radius: int = 1000) -> list[pygame.Rect]:
		if pos is None:
			return [water_monster.damage_collider for water_monster in self.water_monsters]
		else:
			return [water_monster.damage_collider for water_monster in self.water_monsters if water_monster.pos.distance_to(pos) < radius]

	def get_monsters(self, pos: tuple | pygame.Vector2 | None = None, radius: int = 800) -> list[WaterMonster]:
		if pos is None:
			return self.water_monsters
		else:
			return [water_monster for water_monster in self.water_monsters if water_monster.pos.distance_to(pos) < radius]

	def kill_all(self, pos: tuple | pygame.Vector2):
		for water_monster in self.water_monsters:
			in_range = water_monster.pos.distance_to(pos) < self.monster_update_range

			water_monster.kill()
			if water_monster.id != -1:
				self.water_monster_ids.remove(water_monster.id)

		self.water_monsters.clear()

		for _ in range(2):
			random.choice(self.monster_death_sounds).play()

	def update(self, delta: float, pos: tuple | pygame.Vector2, particle_colliders: list[pygame.geometry.Circle], camera: pygbase.Camera, should_update: set):
		for water_monster in self.water_monsters:
			in_range = water_monster.pos.distance_to(pos) < self.monster_update_range

			if in_range:
				water_monster.update(delta, pos, water_monster.id != -1 and water_monster.id not in should_update)

				for particle_collider in particle_colliders[:]:
					if particle_collider.colliderect(water_monster.damage_collider):
						water_monster.temperature.heat(10)
						particle_colliders.remove(particle_collider)

			water_monster.water_particle_spawner.active = in_range

			if not water_monster.alive():
				water_monster.kill()
				camera.shake_screen(0.5)
				if water_monster.id != -1:
					self.water_monster_ids.remove(water_monster.id)

				random.choice(self.monster_death_sounds).play()

		self.water_monsters[:] = [water_monster for water_monster in self.water_monsters if water_monster.alive()]
