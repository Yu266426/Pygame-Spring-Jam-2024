import pygame
import pygbase

from water_orb import WaterOrbGroup


class WaterMonster:
	def __init__(self, pos: tuple):
		self.pos = pygame.Vector2(pos)

		self.water_orb_group = WaterOrbGroup(pos, (0, -50), 15, (5, 30), ("blue", "light blue", "dark blue"), attraction_offset_range=((-10, 10), (-50, 10))).link_pos(self.pos)

	def update(self, delta: float):
		self.water_orb_group.update(delta)

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.water_orb_group.draw(surface, camera)


class WaterMonsterGroup:
	def __init__(self):
		self.water_monsters: list[WaterMonster] = []

	def get_monsters(self, pos: tuple | pygame.Vector2 | None = None, radius: int = 1000) -> list[WaterMonster]:
		if pos is None:
			return self.water_monsters
		else:
			return [water_monster for water_monster in self.water_monsters if water_monster.pos.distance_to(pos) < radius]

	def update(self, delta):
		for water_monster in self.water_monsters:
			water_monster.update(delta)
