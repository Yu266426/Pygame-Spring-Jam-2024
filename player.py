import random

import pygame
import pygbase
from utils import get_sign

from level import Level
from particle_collider import CollisionParticleGroup


class Player:
	def __init__(self, pos: tuple, level: Level, camera: pygbase.Camera, particle_manager: pygbase.ParticleManager) -> None:
		self.gravity = pygbase.Common.get_value("gravity")
		self.gravity_down_multiplier = 1.5

		self.max_speed_x = 500
		self.max_speed_y = 100000
		self.damping = 9.0
		self.air_damping = 2.0
		self.acceleration_speed = 1200
		self.jump_impulse = 600

		self.on_ground = False
		self.turn_timer = pygbase.Timer(0.2, True, False)
		self.fall_timer = pygbase.Timer(0.1, True, False)

		self.acceleration = pygame.Vector2()
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)

		self.rect = pygame.FRect((0, 0, 40, 80))
		self.rect.midbottom = self.pos

		self.flip_x = False
		self.animation = pygbase.AnimationManager([
			("idle", pygbase.Animation("sprite_sheets", "player_idle", 0, 4), 4),
			("run", pygbase.Animation("sprite_sheets", "player_walk", 0, 4), 8),
			("slowing", pygbase.Animation("sprite_sheets", "player_walk", 0, 4), 6)
		], "idle")

		self.level = level
		self.camera = camera

		self.particle_manager = particle_manager
		self.particle_spawner_offset = (0, -50)
		self.particle_spawner_pos = self.pos + self.particle_spawner_offset

		self.fire_angle_deviation = 3
		self.fire_velocity_range = (630, 800)
		self.particle_spawner = particle_manager.add_spawner(pygbase.PointSpawner(self.pos, 0.01, 1, False, "flamethrower", particle_manager, velocity_range=self.fire_velocity_range).link_pos(self.particle_spawner_pos))
		self.fire_particle_settings = pygbase.Common.get_particle_setting("fire")
		self.smoke_particle_settings = pygbase.Common.get_particle_setting("smoke")

		self.collision_particle_timer = pygbase.Timer(0.1, True, True)
		self.collision_particle_group = CollisionParticleGroup("flamethrower", self.level.get_colliders())

		self.level_colliders = self.level.get_colliders()

	def movement(self, delta):
		self.turn_timer.tick(delta)
		self.fall_timer.tick(delta)

		# X movement
		input_x = pygbase.InputManager.get_key_pressed(pygame.K_d) - pygbase.InputManager.get_key_pressed(pygame.K_a)
		if input_x != 0:
			self.animation.switch_state("run")
			if input_x < 0:
				self.flip_x = True
			elif input_x > 0:
				self.flip_x = False

			if not self.turn_timer.done():  # Turning
				self.acceleration.x = input_x * self.acceleration_speed * 2
				pygbase.DebugDisplay.draw_circle((10, 10), 5, "yellow")
			else:
				self.acceleration.x = input_x * self.acceleration_speed

			if abs(self.velocity.x) > 200 and input_x != get_sign(self.velocity.x):
				self.turn_timer.start()
		else:
			self.animation.switch_state("slowing")

			if self.on_ground:
				self.acceleration.x = -self.velocity.x * self.damping
			else:
				self.acceleration.x = -self.velocity.x * self.air_damping

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
		if self.velocity.y <= 0:
			self.acceleration.y = self.gravity
		elif not self.on_ground:
			self.acceleration.y = self.gravity * self.gravity_down_multiplier
			pygbase.DebugDisplay.draw_circle((20, 10), 2, "red")

		input_jump = pygbase.InputManager.get_key_pressed(pygame.K_w)

		if input_jump and (self.on_ground or not self.fall_timer.done()):
			self.velocity.y = 0
			self.acceleration.y -= self.jump_impulse / delta
			pygbase.DebugDisplay.draw_circle((20, 10), 5, "green")
			self.fall_timer.finish()

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

		if prev_on_ground and not self.on_ground and input_jump == 0:
			self.fall_timer.start()

		self.rect.midbottom = self.pos

	def update(self, delta: float):
		self.animation.update(delta)

		particle_collision_positions = self.collision_particle_group.update(delta)

		for particle_collision_position in particle_collision_positions:
			for _ in range(random.randint(5, 10)):
				self.particle_manager.add_particle(particle_collision_position + pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20)), self.fire_particle_settings)
			for _ in range(random.randint(10, 15)):
				offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, 20))
				self.particle_manager.add_particle(particle_collision_position + offset, self.smoke_particle_settings, initial_velocity=offset * random.uniform(2, 5))

		self.collision_particle_timer.tick(delta)

		self.movement(delta)
		if abs(self.velocity.x) < 2:
			self.animation.switch_state("idle")

		self.particle_spawner_pos.update(self.pos + self.particle_spawner_offset)

		if pygbase.InputManager.get_mouse_pressed(0):
			mouse_world_pos = self.camera.screen_to_world(pygame.mouse.get_pos())
			angle_to_mouse = -pygbase.utils.get_angle_to(self.particle_spawner_pos, mouse_world_pos)

			self.particle_spawner.angle_range = (angle_to_mouse - self.fire_angle_deviation, angle_to_mouse + self.fire_angle_deviation)

			mouse_vector = pygbase.utils.get_angled_vector(angle_to_mouse, 1)
			additional_velocity = self.velocity.dot(mouse_vector)
			self.particle_spawner.velocity_range = (self.fire_velocity_range[0] + additional_velocity, self.fire_velocity_range[1] + additional_velocity)
			self.particle_spawner.active = True

			if self.collision_particle_timer.done():
				self.collision_particle_group.add_particle(self.particle_spawner_pos, pygbase.utils.get_angled_vector(random.uniform(*self.particle_spawner.angle_range), random.uniform(*self.particle_spawner.velocity_range)))

				self.collision_particle_timer.start()
		else:
			self.particle_spawner.active = False
			self.collision_particle_timer.finish()

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.animation.draw_at_pos(surface, self.pos, camera, flip=(self.flip_x, False), draw_pos="midbottom")

# self.collision_particle_group.draw(surface, camera)
