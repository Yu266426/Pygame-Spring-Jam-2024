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
	def __init__(self, pos: tuple, level: Level, camera: pygbase.Camera, on_land_particle_manager: pygbase.ParticleManager, in_water_particle_manager: pygbase.ParticleManager, collision_particle_group: CollisionParticleGroup) -> None:
		self.input = pygame.Vector2()

		self.gravity = pygbase.Common.get_value("gravity")
		self.gravity_down_multiplier = 1.5

		self.max_speed_x = 500
		self.max_speed_y = 1000

		self.max_water_speed_x = 250
		self.max_water_speed_y = 300

		self.damping = 9.0
		self.air_damping = 2.0
		self.water_damping = 2.0
		self.acceleration_speed = 1200
		self.jump_impulse = 600

		self.on_ground = False
		self.turn_timer = pygbase.Timer(0.2, True, False)
		self.fall_timer = pygbase.Timer(0.1, True, False)

		self.water_level = pygbase.Common.get_value("water_level")

		self.acceleration = pygame.Vector2()
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)
		self.prev_pos = self.pos.copy()

		self.ground_rect = pygame.Rect((0, 0, 30, 110))
		self.ground_rect.midbottom = self.pos

		self.water_rect = pygame.Rect((0, 0, 110, 30))
		self.water_rect.midbottom = self.pos

		self.is_swimming = False
		self.gun_land_to_water = False
		self.gun_water_to_land = False

		self.flip_x = False
		self.animation = pygbase.AnimationManager([
			("idle", pygbase.Animation("sprite_sheets", "player_idle", 0, 4), 4),
			("run", pygbase.Animation("sprite_sheets", "player_walk", 0, 4), 8),
			("slowing", pygbase.Animation("sprite_sheets", "player_walk", 0, 4), 6),
			("swim", pygbase.Animation("sprite_sheets", "player_swim", 0, 4), 6)
		], "idle")

		self.fire_gun: pygbase.Image = pygbase.ResourceManager.get_resource("images", "fire_gun")

		self.level = level
		self.camera = camera

		self.on_land_particle_manager = on_land_particle_manager
		self.in_water_particle_manager = in_water_particle_manager
		self.collision_particle_group = collision_particle_group

		self.fire_gun_offset_land = (0, -60)
		self.fire_gun_offset_water = (0, -20)
		self.fire_gun_offset = self.fire_gun_offset_land
		self.particle_spawner_towards_mouse_offset = 32
		self.particle_spawner_pos = self.pos + self.fire_gun_offset

		self.fire_angle_deviation = 3
		self.fire_velocity_range = (720, 830)
		self.flamethrower_spawner = on_land_particle_manager.add_spawner(pygbase.PointSpawner(self.pos, 0.01, 2, False, "flamethrower", on_land_particle_manager, velocity_range=self.fire_velocity_range).link_pos(self.particle_spawner_pos))
		self.boiling_water_spawner = in_water_particle_manager.add_spawner(pygbase.PointSpawner(self.pos, 0.01, 2, False, "boiling_water", in_water_particle_manager, velocity_range=self.fire_velocity_range).link_pos(self.particle_spawner_pos))
		self.gun_tip_fire_spawner = on_land_particle_manager.add_spawner(pygbase.CircleSpawner(self.pos, 0.2, 3, 10, False, "fire", on_land_particle_manager, radial_velocity_range=(0, 20)).link_pos(self.particle_spawner_pos))
		self.gun_tip_water_spawner = in_water_particle_manager.add_spawner(pygbase.CircleSpawner(self.pos, 0.2, 3, 10, False, "water_vapour", in_water_particle_manager, radial_velocity_range=(0, 20)).link_pos(self.particle_spawner_pos))

		self.collision_particle_timer = pygbase.Timer(0.1, True, True)

		self.level_colliders = self.level.get_colliders()

		self.thermometer_offset_ground = (0, -self.ground_rect.height - 20)
		self.thermometer_offset_water = (0, -self.water_rect.height - 20)
		self.temperature = Temperature(self.pos, offset=(0, -self.ground_rect.height * 1.2), cooling_speed=15).link_pos(self.pos)
		gun_duration_secs = 3
		self.gun_heat = (self.temperature.cooling_speed + self.temperature.max_temperature / gun_duration_secs)
		self.gun_heat = 0

		self.can_fire = True

		self.health = Health(100)

	@property
	def rect(self):
		if not self.is_swimming:
			return self.ground_rect
		else:
			return self.water_rect

	def ground_movement(self, delta):
		is_water_animation = self.animation.current_state == "swim"

		# X movement
		if self.input.x != 0:
			if not is_water_animation:
				self.animation.switch_state("run")
			if self.input.x < 0:
				self.flip_x = True
			elif self.input.x > 0:
				self.flip_x = False

			if not self.turn_timer.done():  # Turning
				self.acceleration.x = self.input.x * self.acceleration_speed * 2
				pygbase.DebugDisplay.draw_circle((10, 10), 5, "yellow")
			else:
				self.acceleration.x = self.input.x * self.acceleration_speed

			if abs(self.velocity.x) > 200 and self.input.x != get_sign(self.velocity.x):
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

		if self.input.y < 0 and (self.on_ground or not self.fall_timer.done()):
			self.velocity.y = 0
			self.acceleration.y -= self.jump_impulse / delta
			pygbase.DebugDisplay.draw_circle((20, 10), 5, "green")
			self.fall_timer.finish()

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_speed_y * 2, self.max_speed_y)

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

		if prev_on_ground and not self.on_ground and self.input.y < 0 == 0:
			self.fall_timer.start()

		self.rect.midbottom = self.pos

	def water_movement(self, delta):
		# X movement
		if self.input.x != 0:
			if self.input.x < 0:
				self.flip_x = True
			elif self.input.x > 0:
				self.flip_x = False

			if not self.turn_timer.done():  # Turning
				self.acceleration.x = self.input.x * self.acceleration_speed * 2
				pygbase.DebugDisplay.draw_circle((10, 10), 5, "yellow")
			else:
				self.acceleration.x = self.input.x * self.acceleration_speed

			if abs(self.velocity.x) > 200 and self.input.x != get_sign(self.velocity.x):
				self.turn_timer.start()
		else:
			self.acceleration.x = -self.velocity.x * self.water_damping

		self.velocity.x += self.acceleration.x * delta

		if self.velocity.x < -self.max_water_speed_x:
			self.velocity.x = pygame.math.lerp(self.velocity.x, -self.max_water_speed_x, 15 * delta)
		if self.velocity.x > self.max_water_speed_x:
			self.velocity.x = pygame.math.lerp(self.velocity.x, self.max_water_speed_x, 15 * delta)

		# self.velocity.x = pygame.math.clamp(self.velocity.x, -self.max_water_speed_x, self.max_water_speed_x)

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
		if self.input.y != 0:
			if not self.turn_timer.done():  # Turning
				self.acceleration.y = self.input.y * self.acceleration_speed * 2
				pygbase.DebugDisplay.draw_circle((10, 10), 5, "yellow")
			else:
				self.acceleration.y = self.input.y * self.acceleration_speed

			if abs(self.velocity.y) > 200 and self.input.y != get_sign(self.velocity.y):
				self.turn_timer.start()
		else:
			self.acceleration.y = -self.velocity.y * self.water_damping

		self.velocity.y += self.acceleration.y * delta
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.max_water_speed_y, self.max_water_speed_y)

		self.pos.y += self.velocity.y * delta + 0.5 * self.acceleration.y * (delta ** 2)
		self.rect.midbottom = self.pos

		for rect in self.level_colliders:
			if self.rect.colliderect(rect):
				if self.velocity.y > 0:
					self.pos.y = rect.top
					self.velocity.y = 0

				elif self.velocity.y < 0:
					self.pos.y = rect.bottom + self.rect.height
					self.velocity.y = 0

		self.rect.midbottom = self.pos

	def update(self, delta: float):
		self.gun_land_to_water = False
		self.gun_water_to_land = False

		self.temperature.tick(delta)
		if self.temperature.get_percentage() < 0.8:
			self.can_fire = True

		self.collision_particle_timer.tick(delta)

		mouse_world_pos = self.camera.screen_to_world(pygame.mouse.get_pos())
		angle_to_mouse = -pygbase.utils.get_angle_to(self.pos + self.fire_gun_offset, mouse_world_pos)

		self.animation.update(delta)
		self.is_swimming = self.animation.current_state == "swim"
		if self.is_swimming:
			self.fire_gun_offset = self.fire_gun_offset_water
			self.temperature.offset = self.thermometer_offset_water
		else:
			self.fire_gun_offset = self.fire_gun_offset_land
			self.temperature.offset = self.thermometer_offset_ground

		self.turn_timer.tick(delta)
		self.fall_timer.tick(delta)

		self.input.x = pygbase.InputManager.get_key_pressed(pygame.K_d) - pygbase.InputManager.get_key_pressed(pygame.K_a)
		self.input.y = pygbase.InputManager.get_key_pressed(pygame.K_s) - pygbase.InputManager.get_key_pressed(pygame.K_w)

		if self.pos.y <= self.water_level:
			self.ground_movement(delta)
			if self.animation.current_state == "swim" and self.on_ground:
				self.animation.switch_state("idle")

			elif self.input.x == 0 and self.animation.current_state != "idle" and abs(self.velocity.x) < 2:
				self.animation.switch_state("idle")
		else:
			will_collide = False

			for collider in self.level_colliders:
				if self.water_rect.colliderect(collider):
					will_collide = True
					break

			if not will_collide:
				self.animation.switch_state("swim")

			self.water_movement(delta)

		self.ground_rect.midbottom = self.pos
		self.water_rect.midbottom = self.pos

		self.particle_spawner_pos.update(self.pos + self.fire_gun_offset + pygbase.utils.get_angled_vector(angle_to_mouse, self.particle_spawner_towards_mouse_offset))

		if self.prev_pos.y + self.fire_gun_offset[1] <= self.water_level < self.pos.y + self.fire_gun_offset[1]:
			self.gun_land_to_water = True
			self.flamethrower_spawner.active = False
			self.gun_tip_fire_spawner.active = False
		elif self.prev_pos.y + self.fire_gun_offset[1] > self.water_level >= self.pos.y + self.fire_gun_offset[1]:
			self.gun_water_to_land = True
			self.boiling_water_spawner.active = False
			self.gun_tip_water_spawner.active = False

		if self.water_level < self.pos.y + self.fire_gun_offset[1]:
			stream_spawner = self.boiling_water_spawner
			tip_spawner = self.gun_tip_water_spawner
			fire_deviation = self.fire_angle_deviation * 3
		else:
			stream_spawner = self.flamethrower_spawner
			tip_spawner = self.gun_tip_fire_spawner
			fire_deviation = self.fire_angle_deviation

		if pygbase.InputManager.get_mouse_pressed(0) and self.can_fire:
			stream_spawner.angle_range = (angle_to_mouse - fire_deviation, angle_to_mouse + fire_deviation)

			mouse_vector = pygbase.utils.get_angled_vector(angle_to_mouse, 1)
			additional_velocity = self.velocity.dot(mouse_vector)
			stream_spawner.velocity_range = (self.fire_velocity_range[0] + additional_velocity, self.fire_velocity_range[1] + additional_velocity)
			stream_spawner.active = True
			tip_spawner.active = True

			if self.collision_particle_timer.done():
				self.collision_particle_group.add_particle(self.particle_spawner_pos, pygbase.utils.get_angled_vector(random.uniform(*stream_spawner.angle_range), random.uniform(*stream_spawner.velocity_range)))

				self.collision_particle_timer.start()

			self.temperature.heat(self.gun_heat * delta)

			if not self.temperature.not_maxed():
				self.can_fire = False
		else:
			stream_spawner.active = False
			tip_spawner.active = False

		self.prev_pos = self.pos.copy()

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.animation.draw_at_pos(surface, self.pos, camera, flip=(self.flip_x, False), draw_pos="midbottom")

		mouse_world_pos = self.camera.screen_to_world(pygame.mouse.get_pos())
		angle_to_mouse = pygbase.utils.get_angle_to(self.pos + self.fire_gun_offset, mouse_world_pos)

		flip_y = 90 < angle_to_mouse % 360 < 270

		self.fire_gun.draw(surface, camera.world_to_screen(self.pos + self.fire_gun_offset), angle=angle_to_mouse, flip=(False, flip_y), draw_pos="center")

		pygbase.DebugDisplay.draw_rect(camera.world_to_screen_rect(self.rect), "light blue", width=4)

	def draw_ui(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.temperature.draw(surface, camera)

# print(self.health.health)
