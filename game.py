import pygame
import pygbase

from level import Level
from player import Player
from water_monster import WaterMonster, WaterMonsterGroup


class Game(pygbase.GameState, name="game"):
	def __init__(self):
		super().__init__()

		self.level = Level()
		self.particle_manager = pygbase.ParticleManager(chunk_size=pygbase.Common.get_value("tile_size")[0], colliders=self.level.get_colliders())

		self.water_alpha = pygbase.Common.get_value("water_alpha")
		self.outline_draw_surface: pygame.Surface = pygbase.Common.get_value("water_outline_surface")
		self.water_draw_surfaces: dict[str | tuple, pygame.Surface] = pygbase.Common.get_value("water_surfaces")

		self.water_monster_group = WaterMonsterGroup()
		for i in range(100):
			self.water_monster_group.water_monsters.append(WaterMonster((100 + 300 * i, 0), self.level, self.particle_manager))

		player_spawn_pos = (0, 0)
		self.camera = pygbase.Camera(player_spawn_pos - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2)
		pygbase.Common.set_value("camera", self.camera)
		self.player = Player(player_spawn_pos, self.level, self.camera, self.particle_manager)

	def update(self, delta: float):
		self.particle_manager.update(delta)

		self.water_monster_group.update(delta, self.player.pos)

		self.player.update(delta)

		self.camera.lerp_to_target(self.player.pos - pygame.Vector2(pygbase.Common.get_value("screen_size")) / 2, 2 * delta)

	def draw(self, surface: pygame.Surface):
		surface.fill((230, 240, 253))
		self.outline_draw_surface.fill((0, 0, 0, 0))
		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((0, 0, 0, 0))

		self.level.draw(surface, self.camera, [self.player, *self.water_monster_group.get_monsters(self.player.pos)], 0)

		self.particle_manager.draw(surface, self.camera)

		for water_draw_surface in self.water_draw_surfaces.values():
			water_draw_surface.fill((255, 255, 255, self.water_alpha), special_flags=pygame.BLEND_RGBA_MIN)

			surface.blit(water_draw_surface, (0, 0))
		surface.blit(self.outline_draw_surface, (0, 0))
