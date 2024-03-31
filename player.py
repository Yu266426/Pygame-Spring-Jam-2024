import random

import pygame
import pygame.geometry
import pygbase

from health import Health
from temperature import Temperature
from utils import get_sign

from level import Level
from particle_collider import CollisionParticleGroup


class Player:
	def __init__(self, pos: tuple, level: Level, camera: pygbase.Camera, particle_manager: pygbase.ParticleManager, collision_particle_group: CollisionParticleGroup) -> None:
		self.gravity = pygbase.Common.get_value("gravity")
		self.gravity_down_multiplier = 1.5

		self.max_speed_x = 500
		self.max_speed_y = 1000
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

		self.rect = pygame.FRect((0, 0, 30, 110))
		self.rect.midbottom = self.pos

		self.flip_x = False
		self.animation = pygbase.AnimationManager([
			("idle", pygbase.Animation("sprite_sheets", "player_idle", 0, 4), 4),
			("run", pygbase.Animation("sprite_sheets", "player_walk", 0, 4), 8),
			("slowing", pygbase.Animation("sprite_sheets", "player_walk", 0, 4), 6)
		], "idle")

		self.fire_gun: pygbase.Image = pygbase.ResourceManager.get_resource("images", "fire_gun")

		self.level = level
		self.camera = camera

		self.particle_manager = particle_manager
		self.collision_particle_group = collision_particle_group

		self.particle_spawner_offset = (0, -50)
		self.particle_spawner_towards_mouse_offset = 32
		self.particle_spawner_pos = self.pos + self.particle_spawner_offset

		self.fire_angle_deviation = 2
		self.fire_velocity_range = (630, 800)
		self.flamethrower_spawner = particle_manager.add_spawner(pygbase.PointSpawner(self.pos, 0.01, 2, False, "flamethrower", particle_manager, velocity_range=self.fire_velocity_range).link_pos(self.particle_spawner_pos))
		self.gun_tip_fire_spawner = particle_manager.add_spawner(pygbase.CircleSpawner(self.pos, 0.2, 3, 10, False, "fire", particle_manager, radial_velocity_range=(0, 20)).link_pos(self.particle_spawner_pos))

		self.collision_particle_timer = pygbase.Timer(0.1, True, True)

		self.level_colliders = self.level.get_colliders()

		self.temperature = Temperature(self.pos, offset=(0, -self.rect.height * 1.2), cooling_speed=15).link_pos(self.pos)
		gun_duration_secs = 3
		self.gun_heat = (self.temperature.cooling_speed + self.temperature.max_temperature / gun_duration_secs)

		self.can_fire = True

		self.health = Health(100)

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
			if self.animation.current_state == "run":
				self.animation.switch_state("slowing")

			if self.on_ground:
				self.acceleration.x = -self.velocity.x * self.damping
			else:
				self.acceleration.x = -self.velocity.x * self.air_damping

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
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_speed_y, self.max_speed_y)

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
		self.temperature.tick(delta)
		if self.temperature.get_percentage() < 0.8:
			self.can_fire = True

		self.collision_particle_timer.tick(delta)

		mouse_world_pos = self.camera.screen_to_world(pygame.mouse.get_pos())
		angle_to_mouse = -pygbase.utils.get_angle_to(self.pos + self.particle_spawner_offset, mouse_world_pos)

		self.animation.update(delta)

		self.movement(delta)
		if self.animation.current_state != "idle" and abs(self.velocity.x) < 2:
			self.animation.switch_state("idle")

		self.particle_spawner_pos.update(self.pos + self.particle_spawner_offset + pygbase.utils.get_angled_vector(angle_to_mouse, self.particle_spawner_towards_mouse_offset))

		if pygbase.InputManager.get_mouse_pressed(0) and self.can_fire:
			self.flamethrower_spawner.angle_range = (angle_to_mouse - self.fire_angle_deviation, angle_to_mouse + self.fire_angle_deviation)

			mouse_vector = pygbase.utils.get_angled_vector(angle_to_mouse, 1)
			additional_velocity = self.velocity.dot(mouse_vector)
			self.flamethrower_spawner.velocity_range = (self.fire_velocity_range[0] + additional_velocity, self.fire_velocity_range[1] + additional_velocity)
			self.flamethrower_spawner.active = True
			self.gun_tip_fire_spawner.active = True

			if self.collision_particle_timer.done():
				self.collision_particle_group.add_particle(self.particle_spawner_pos, pygbase.utils.get_angled_vector(random.uniform(*self.flamethrower_spawner.angle_range), random.uniform(*self.flamethrower_spawner.velocity_range)))

				self.collision_particle_timer.start()

			self.temperature.heat(self.gun_heat * delta)

			if not self.temperature.not_maxed():
				self.can_fire = False
		else:
			self.flamethrower_spawner.active = False
			self.gun_tip_fire_spawner.active = False

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.animation.draw_at_pos(surface, self.pos, camera, flip=(self.flip_x, False), draw_pos="midbottom")

		mouse_world_pos = self.camera.screen_to_world(pygame.mouse.get_pos())
		angle_to_mouse = pygbase.utils.get_angle_to(self.pos + self.particle_spawner_offset, mouse_world_pos)

		flip_y = 90 < angle_to_mouse % 360 < 270

		self.fire_gun.draw(surface, camera.world_to_screen(self.pos + self.particle_spawner_offset), angle=angle_to_mouse, flip=(False, flip_y), draw_pos="center")

	def draw_ui(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.temperature.draw(surface, camera)

		print(self.health.health)
