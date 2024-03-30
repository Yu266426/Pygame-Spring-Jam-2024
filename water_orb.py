import random

import pygame
import pygbase


class WaterOrb:
	GRAVITY = 70

	ATTRACTION = 7
	DEFLECTION = 300

	MAX_SPEED = 100

	def __init__(self, pos: tuple, size: float, color: str | tuple, outline_size: int = 3, outline_color: str | tuple = (230, 230, 230), attraction_offset: tuple = (0, 0)):
		self.acceleration = pygame.Vector2()
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)

		self.size = size
		self.outline_size = outline_size

		self.color = color
		self.outline_color = outline_color

		self.attraction_offset = pygame.Vector2(attraction_offset)

	def update(self, delta: float, attraction_point: pygame.Vector2 | tuple, deflectors: list[pygame.Vector2]):
		self.acceleration.y = self.GRAVITY

		# This is the most messed up physics I've ever written
		# Attraction
		attraction_vector = ((attraction_point + self.attraction_offset) - self.pos)
		attractor_distance = attraction_vector.length()

		if attractor_distance < 5:
			attraction_scaler = 0
		elif attraction_vector.dot(self.velocity) < 0:  # Moving away
			attraction_scaler = 3
		else:
			attraction_scaler = 1

		attraction_vector.normalize_ip()
		attraction_vector.x *= 0.5 * attraction_scaler  # Reduce x movement
		attraction_vector.y *= 2.0

		self.acceleration += attraction_vector * (self.ATTRACTION * attraction_scaler * (attractor_distance ** 0.5))

		# Deflection
		for deflector in deflectors:
			deflection_vector = (self.pos - deflector)
			deflector_distance = deflection_vector.length()

			deflection_vector.normalize_ip()

			self.acceleration += deflection_vector * min((self.DEFLECTION / deflector_distance ** 1.3), 800)

		self.acceleration.x += self.acceleration.x * -4.0 * delta  # Damp the x
		self.acceleration.x += self.velocity.x * -4.0 * delta  # Damp the x

		self.velocity += self.acceleration * delta
		self.velocity.x = pygame.math.clamp(self.velocity.x, -self.MAX_SPEED, self.MAX_SPEED)
		self.velocity.y = pygame.math.clamp(self.velocity.y, -self.MAX_SPEED, self.MAX_SPEED)

		self.pos += self.velocity * delta + 0.5 * self.acceleration * (delta ** 2)

	def draw_water(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.circle(surface, self.color, camera.world_to_screen(self.pos), self.size)

	def draw_outline(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.circle(surface, self.outline_color, camera.world_to_screen(self.pos), self.size + self.outline_size)

	def draw_inner_clear(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.circle(surface, (0, 0, 0, 0), camera.world_to_screen(self.pos), self.size)


class WaterOrbGroup:
	def __init__(self, pos: tuple, offset: tuple, num_orbs: int, orb_size_range: tuple[float, float], attraction_offset_range: tuple[tuple, tuple] = ((0, 0), (0, 0))):
		self.pos = pygame.Vector2(pos)
		self.offset = offset

		self.water_colors = pygbase.Common.get_value("water_monster_colors")

		self.orb_size_range = orb_size_range
		self.water_orbs: dict[str | tuple, list[WaterOrb]] = {}
		for _ in range(num_orbs):
			color = random.choice(self.water_colors)

			spawn_offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, orb_size_range[1] * 2))
			spawn_offset.x *= 0.5

			self.water_orbs.setdefault(color, []).append(WaterOrb(
				self.pos + self.offset + spawn_offset, random.uniform(*orb_size_range), color,
				attraction_offset=(random.uniform(*attraction_offset_range[0]), random.uniform(*attraction_offset_range[1]))
			))

	def link_pos(self, pos: pygame.Vector2) -> "WaterOrbGroup":
		self.pos = pos
		return self

	def update(self, delta: float):
		camera: pygbase.Camera = pygbase.Common.get_value("camera")
		pygbase.DebugDisplay.draw_circle(camera.world_to_screen(self.pos + self.offset), 5, "yellow")

		for water_orbs in self.water_orbs.values():
			for orb in water_orbs:
				orb.update(delta, self.pos + self.offset, [deflect_orb.pos for deflect_orb in water_orbs if deflect_orb is not orb and deflect_orb.pos.distance_to(orb.pos) < 15])

	def draw(self, outline_draw_surface, water_draw_surfaces, camera: pygbase.Camera):
		for water_orbs in self.water_orbs.values():
			for orb in water_orbs:
				orb.draw_outline(outline_draw_surface, camera)
		for water_orbs in self.water_orbs.values():
			for orb in water_orbs:
				orb.draw_inner_clear(outline_draw_surface, camera)

		for color, water_draw_surface in water_draw_surfaces.items():
			if color in self.water_orbs:
				for orb in self.water_orbs[color]:
					orb.draw_water(water_draw_surface, camera)
