import random

import pygame
import pygbase


class CollisionParticle:
	def __init__(self, pos: tuple | pygame.Vector2, settings: dict, initial_velocity=(0, 0)):
		self.pos = pygame.Vector2(pos)

		self.size: float = random.uniform(
			settings[pygbase.common.ParticleOptions.SIZE][0],
			settings[pygbase.common.ParticleOptions.SIZE][1]
		)
		self.size_decay: float = random.uniform(
			settings[pygbase.common.ParticleOptions.SIZE_DECAY][0],
			settings[pygbase.common.ParticleOptions.SIZE_DECAY][1]
		)

		self.colour = random.choice(settings[pygbase.common.ParticleOptions.COLOUR])

		self.velocity: pygame.Vector2 = pygame.Vector2(initial_velocity)
		self.velocity_decay: float = random.uniform(
			settings[pygbase.common.ParticleOptions.VELOCITY_DECAY][0],
			settings[pygbase.common.ParticleOptions.VELOCITY_DECAY][1]
		)

		self.gravity: tuple = settings[pygbase.common.ParticleOptions.GRAVITY]
		self.effector: bool = settings[pygbase.common.ParticleOptions.EFFECTOR]

		self.bounce: tuple = settings[pygbase.common.ParticleOptions.BOUNCE]

		self.is_alive = True

	def alive(self):
		return self.size > 0.2 and self.is_alive

	def update(self, delta: float, colliders: list[pygame.Rect]):
		collide_pos = None

		self.velocity.x += self.gravity[0]
		self.velocity.x -= self.velocity.x * delta * self.velocity_decay

		self.pos.x += self.velocity.x * delta

		for collider in colliders:
			if collider.collidepoint(self.pos):
				# self.pos.x -= self.velocity.x * delta
				# self.velocity.x *= -self.bounce[0]

				collide_pos = self.pos

				self.is_alive = False

		self.velocity.y += self.gravity[1]
		self.velocity.y -= self.velocity.y * delta * self.velocity_decay

		self.pos.y += self.velocity.y * delta

		for collider in colliders:
			if collider.collidepoint(self.pos):
				# self.pos.y -= self.velocity.y * delta
				# self.velocity.y *= -self.bounce[1]

				collide_pos = self.pos

				self.is_alive = False

		self.size -= delta * self.size_decay

		return collide_pos


class CollisionParticleGroup:
	def __init__(self, particle_type: str, colliders: dict[tuple[int, int], pygame.Rect]):
		self.particle_settings = pygbase.Common.get_particle_setting(particle_type)

		self.particles: list[CollisionParticle] = []

		self.colliders = colliders
		self.tile_size = pygbase.Common.get_value("tile_size")

	def add_particle(self, pos: tuple | pygame.Vector2, initial_velocity=(0, 0)):
		self.particles.append(CollisionParticle(pos, self.particle_settings, initial_velocity))

	def update(self, delta: float, dynamic_colliders: list[pygame.Rect]):
		collision_positions: list[tuple[pygame.Vector2, str]] = []

		for particle in self.particles:
			tile_pos = int(particle.pos.x // self.tile_size[0]), int(particle.pos.y // self.tile_size[1])
			top_left = (tile_pos[0] - 1, tile_pos[1] - 1)
			bottom_right = (tile_pos[0] + 1, tile_pos[1] + 1)

			surrounding_colliders = []
			for row in range(top_left[1], bottom_right[1]):
				for col in range(top_left[0], bottom_right[0]):
					rect = self.colliders.get((col, row))
					if rect is not None:
						surrounding_colliders.append(rect)

			collision_pos = particle.update(delta, [*dynamic_colliders, *surrounding_colliders])
			if collision_pos is not None:
				collision_positions.append((collision_pos, self.particle_settings[pygbase.common.ParticleOptions.NAME]))

		self.particles[:] = [particle for particle in self.particles if particle.alive()]

		return collision_positions

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		for particle in self.particles:
			pygame.draw.circle(surface, "blue", camera.world_to_screen(particle.pos), particle.size)

	def debug_draw(self, camera: pygbase.Camera):
		for particle in self.particles:
			pygbase.DebugDisplay.draw_circle(camera.world_to_screen(particle.pos), particle.size, "blue", 0)
