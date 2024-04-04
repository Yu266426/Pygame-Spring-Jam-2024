import logging
import random

import pygame
import pygame.geometry

import pygbase

from level import Level


class Projectile:
	def __init__(self, pos: tuple | pygame.Vector2, initial_velocity: tuple | pygame.Vector2, radius: float, damage: int, despawn_time: float = 3.0, bounce: tuple[float, float] = (0.5, 0.2)):
		self.gravity = pygbase.Common.get_value("gravity")
		self.water_lever = pygbase.Common.get_value("water_level")

		self.max_speed_x = 10000
		self.max_speed_y = 10000

		self.on_ground = False
		self.ground_damping = 5.0
		self.water_damping = 1.0

		self.bounce = bounce

		self.acceleration = pygame.Vector2(0, self.gravity)
		self.velocity = pygame.Vector2(initial_velocity)
		self.pos = pygame.Vector2(pos)

		self.collider = pygame.geometry.Circle(self.pos, radius)

		self.despawn_timer = pygbase.Timer(despawn_time, False, False)

		self.has_collided = False  # If projectile has_collided, then no more damage
		self.has_just_collided = False
		self.damage = damage

	def movement(self, delta, colliders: list[pygame.Rect]):
		if self.on_ground:
			self.acceleration.x = -self.velocity.x * self.ground_damping
		elif self.pos.y > self.water_lever:
			self.acceleration.x = -self.velocity.x * self.water_damping
		else:
			self.acceleration.x = 0

		self.velocity.x += self.acceleration.x * delta
		self.velocity.x = pygame.math.clamp(self.velocity.x, -self.max_speed_x, self.max_speed_x)

		x_movement = self.velocity.x * delta + 0.5 * self.acceleration.x * (delta ** 2)

		self.pos.x += x_movement
		self.collider.center = self.pos

		for rect in colliders:
			if self.collider.colliderect(rect):
				self.pos.x -= x_movement
				self.collider.center = self.pos

				if self.collider.colliderect(rect):
					if abs(self.pos.x - rect.left) < abs(self.pos.x - rect.right):  # Closer to left than right
						self.pos.x = rect.left - self.collider.radius * 1.3
					else:
						self.pos.x = rect.right + self.collider.radius * 1.3

				self.velocity.x *= -self.bounce[0]

				if not self.has_collided:
					self.has_just_collided = True
					self.has_collided = True

				break

		self.collider.center = self.pos

		# Y movement
		# Upwards has less gravity than downwards
		if self.pos.y > self.water_lever:
			self.acceleration.y = -self.velocity.y * self.water_damping
		else:
			self.acceleration.y = self.gravity

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_speed_y, self.max_speed_y)

		y_movement = self.velocity.y * delta + 0.5 * self.acceleration.y * (delta ** 2)

		self.pos.y += y_movement
		self.collider.center = self.pos

		self.on_ground = False
		for rect in colliders:
			if self.collider.colliderect(rect):
				self.on_ground = True

				self.pos.y -= y_movement
				self.collider.center = self.pos

				if self.collider.colliderect(rect):
					if abs(self.pos.x - rect.left) < abs(self.pos.x - rect.right):  # Closer to left than right
						self.pos.x = rect.left - self.collider.radius * 1.3
					else:
						self.pos.x = rect.right + self.collider.radius * 1.3

				self.velocity.y *= -self.bounce[1]

				if not self.has_collided:  # The or is for both collisions in same frame
					self.has_just_collided = True
					self.has_collided = True

				break

		self.collider.center = self.pos

	def update(self, delta: float, colliders: list[pygame.Rect]):
		if self.velocity.length() < 50:
			self.has_collided = True

		self.despawn_timer.tick(delta)

		if self.has_collided:
			self.has_just_collided = False
		self.movement(delta, colliders)

	def alive(self):
		return not self.despawn_timer.done()

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pass


class GarbageProjectile(Projectile):
	def __init__(self, pos: tuple | pygame.Vector2, initial_velocity: tuple | pygame.Vector2):
		sprite_sheet: pygbase.SpriteSheet = pygbase.ResourceManager.get_resource("sprite_sheets", "small_garbage")
		self.image = sprite_sheet.get_image(random.randrange(sprite_sheet.n_cols))

		self.angle = random.uniform(0, 360)

		super().__init__(pos, initial_velocity, 10, 3)

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.image.draw(surface, camera.world_to_screen(self.pos), angle=self.angle, draw_pos="center")


class ProjectileGroup:
	def __init__(self, level: Level):
		self.projectiles: list[Projectile] = []

		self.level_colliders = {tile_pos: tile.rect for tile_pos, tile in level.tiles[0].items()}
		self.colliders = level.get_colliders()
		self.tile_size = pygbase.Common.get_value("tile_size")

	def add_projectile(self, projectile: Projectile):
		self.projectiles.append(projectile)

	def update(self, delta: float, dynamic_colliders: list[pygame.Rect]):
		# list[(collider, damage)]
		hits: list[tuple[pygame.geometry.Circle, int]] = []

		for projectile in self.projectiles:
			tile_pos = int(projectile.pos.x // self.tile_size[0]), int(projectile.pos.y // self.tile_size[1])
			top_left = (tile_pos[0] - 2, tile_pos[1] - 2)
			bottom_right = (tile_pos[0] + 2, tile_pos[1] + 2)

			surrounding_colliders = []
			for row in range(top_left[1], bottom_right[1]):
				for col in range(top_left[0], bottom_right[0]):
					rect = self.level_colliders.get((col, row))
					if rect is not None:
						surrounding_colliders.append(rect)

			projectile.update(delta, [*surrounding_colliders, *dynamic_colliders])

			# print(projectile, projectile.has_collided, projectile.has_just_collided)
			if projectile.has_just_collided:
				hits.append((pygame.geometry.Circle(projectile.collider.center, projectile.collider.radius * 2), projectile.damage))

		self.projectiles[:] = [projectile for projectile in self.projectiles if projectile.alive()]

		return hits

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		for projectile in self.projectiles:
			# pygbase.DebugDisplay.draw_circle(camera.world_to_screen(projectile.collider.center), projectile.collider.radius, "yellow")

			projectile.draw(surface, camera)
