import random

import pygame
import pygbase


class WaterOrb:
	def __init__(self, pos: tuple, size: float, color: str | tuple, outline_size: int = 3, outline_color: str | tuple = (230, 230, 230), attraction_offset: tuple = (0, 0)):
		self.acceleration = pygame.Vector2()
		self.velocity = pygame.Vector2()
		self.pos = pygame.Vector2(pos)

		self.size = size
		self.outline_size = outline_size

		self.color = color
		self.outline_color = outline_color

		self.attraction_offset = pygame.Vector2(attraction_offset)

	def update(self, delta: float, attraction_point: pygame.Vector2 | tuple, deflectors):
		self.acceleration.y = 30  # Gravity

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
		attraction_vector.x *= 0.1 * attraction_scaler  # Reduce x movement

		# Deflection
		for deflector in deflectors:
			deflection_vector = (self.pos - deflector)
			deflector_distance = deflection_vector.length()

			deflection_vector.normalize_ip()

			self.acceleration += deflection_vector * min((20 / deflector_distance ** 1.3), 800)

		self.acceleration += attraction_vector * (5 * attraction_scaler * (attractor_distance ** 0.5))
		self.acceleration.x += self.acceleration.x * -4.0 * delta  # Damp the x
		self.acceleration.x += self.velocity.x * -4.0 * delta  # Damp the x

		self.velocity += self.acceleration * delta
		self.pos += self.velocity * delta + 0.5 * self.acceleration * (delta ** 2)

	def draw_water(self, surface: pygame.Surface):
		pygame.draw.circle(surface, self.color, self.pos, self.size)

	def draw_outline(self, surface: pygame.Surface):
		pygame.draw.circle(surface, self.outline_color, self.pos, self.size + self.outline_size)

	def draw_inner_clear(self, surface: pygame.Surface):
		pygame.draw.circle(surface, (0, 0, 0, 0), self.pos, self.size)


class WaterOrbGroup:
	def __init__(self, pos: tuple, offset: tuple, num_orbs: int, orb_size_range: tuple[float, float], water_colors: tuple, water_alpha: int = 100, attraction_offset_range: tuple[tuple, tuple] = ((0, 0), (0, 0))):
		self.pos = pygame.Vector2(pos)
		self.offset = offset

		self.water_colors = water_colors
		self.water_alpha = water_alpha

		surface_size_multiplier = 12
		self.outline_draw_surface = pygame.Surface((int(orb_size_range[1] * surface_size_multiplier), int(orb_size_range[1] * surface_size_multiplier)), flags=pygame.SRCALPHA)

		self.water_draw_surfaces: dict[str | tuple, pygame.Surface] = {}
		for color in self.water_colors:
			self.water_draw_surfaces[color] = pygame.Surface((int(orb_size_range[1] * surface_size_multiplier), int(orb_size_range[1] * surface_size_multiplier)), flags=pygame.SRCALPHA)

		self.center = int(orb_size_range[1] * surface_size_multiplier / 2), int(orb_size_range[1] * surface_size_multiplier / 2)

		self.orb_size_range = orb_size_range
		self.water_orbs: dict[str | tuple, list[WaterOrb]] = {}
		for _ in range(num_orbs):
			color = random.choice(water_colors)

			offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), random.uniform(0, orb_size_range[1] * 2))
			offset.x *= 0.5

			self.water_orbs.setdefault(color, []).append(WaterOrb(
				self.center + offset, random.uniform(*orb_size_range), color,
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
				orb.update(delta, self.center, [deflect_orb.pos for deflect_orb in water_orbs if deflect_orb is not orb and deflect_orb.pos.distance_to(orb.pos) < 15])

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.outline_draw_surface.fill((0, 0, 0, 0))

		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((0, 0, 0, 0))

		for water_orbs in self.water_orbs.values():
			for orb in water_orbs:
				orb.draw_outline(self.outline_draw_surface)
		for water_orbs in self.water_orbs.values():
			for orb in water_orbs:
				orb.draw_inner_clear(self.outline_draw_surface)

		for color, water_draw_surface in self.water_draw_surfaces.items():
			if color in self.water_orbs:
				for orb in self.water_orbs[color]:
					orb.draw_water(water_draw_surface)

		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((255, 255, 255, self.water_alpha), special_flags=pygame.BLEND_RGBA_MIN)

			surface.blit(water_draw_surface, camera.world_to_screen(self.pos - self.center + self.offset))
		surface.blit(self.outline_draw_surface, camera.world_to_screen(self.pos - self.center + self.offset))

		pygbase.DebugDisplay.draw_rect(self.outline_draw_surface.get_rect(topleft=camera.world_to_screen(self.pos - self.center + self.offset)), "yellow")
