import enum
import random

import pygame
import pygbase


# class BossAttacks(enum.Enum):
# 	NONE = enum.auto()
# 	SUMMON = enum.auto()
#
#
# class BossStates(enum.Enum):
# 	IDLE = enum.auto()
# 	SUMMON = enum.auto()
#
#
# class BossAI:
# 	def __init__(self, pos: tuple):
# 		self.pos = pygame.Vector2(pos)
#
# 		self.current_state = BossStates.IDLE
#
# 		self.movement = pygame.Vector2()
#
# 	def update(self, delta: float, player_pos: pygame.Vector2):
# 		offset_vector = player_pos - self.pos
# 		dist_to_player = offset_vector.length()
# 		if offset_vector.length() != 0:
# 			offset_vector.normalize_ip()
#
# 		match self.current_state:
# 			case _:
# 				pass
#
# 	def get_movement(self) -> pygame.Vector2:
# 		return self.movement
#
# 	def get_attack(self):
# 		match self.current_state:
# 			case WaterMonsterStates.GARBAGE_ATTACK:
# 				return WaterMonsterAttacks.GARBAGE_THROW
# 			case _:
# 				return WaterMonsterAttacks.NONE


class HeartOfTheSeaBoss:
	def __init__(self, pos: tuple, particle_manager: pygbase.ParticleManager):
		self.pos = pygame.Vector2(pos)

		self.animations = pygbase.AnimationManager([
			("idle", pygbase.Animation("sprite_sheets", "clam_boss_idle", 0, 1, True), 0),
			("slam", pygbase.Animation("sprite_sheets", "clam_boss_slam", 0, 16, False), 12),
		], "idle")

		self.summon_cooldown_range = (9, 13)
		self.summon_amount_range = (1, 2)
		self.summon_cooldown = pygbase.Timer(random.uniform(*self.summon_cooldown_range), True, False)

		self.particle_manager = particle_manager

		self.has_summoned = False
		self.particle_summon_pos = self.pos + (0, -40)
		self.water_vapour_particle_setting = pygbase.Common.get_particle_setting("water_vapour")
		self.boiling_water_particle_setting = pygbase.Common.get_particle_setting("boiling_water")
		self.bubbles_particle_setting = pygbase.Common.get_particle_setting("bubble")

	def create_summon_particles(self):
		for _ in range(random.randint(30, 60)):
			offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), 1)
			self.particle_manager.add_particle(self.particle_summon_pos + offset * random.uniform(0, 40), self.water_vapour_particle_setting, offset * random.uniform(100, 300))

		for _ in range(random.randint(100, 200)):
			offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), 1)
			self.particle_manager.add_particle(self.particle_summon_pos + offset * random.uniform(0, 40), self.boiling_water_particle_setting, offset * random.uniform(20, 300))

		for _ in range(random.randint(5, 15)):
			offset = pygbase.utils.get_angled_vector(random.uniform(0, 360), 1)
			self.particle_manager.add_particle(self.particle_summon_pos + offset * random.uniform(0, 40), self.bubbles_particle_setting, offset * random.uniform(100, 200))

	def update(self, delta: float):
		self.animations.update(delta)
		self.summon_cooldown.tick(delta)

		if self.summon_cooldown.done():
			self.animations.switch_state("slam")
			self.summon_cooldown.set_cooldown(random.uniform(*self.summon_cooldown_range))
			self.summon_cooldown.start()

			self.has_summoned = False

		if self.animations.done():
			self.animations.switch_state("idle")

		if not self.has_summoned and self.animations.current_state == "slam" and int(self.animations.states[self.animations.current_state].frame) == 6:
			self.has_summoned = True
			self.create_summon_particles()
			return random.randint(*self.summon_amount_range)

		return 0

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		pygame.draw.circle(surface, "light blue", camera.world_to_screen(self.pos), 200, width=10)

		self.animations.draw_at_pos(surface, self.pos, camera, draw_pos="midbottom")
