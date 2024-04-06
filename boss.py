import random

import pygame
import pygbase

from health import Health


class HeartOfTheSeaBoss:
	def __init__(self, pos: tuple, particle_manager: pygbase.ParticleManager, water_particle_manager: pygbase.ParticleManager):
		self.pos = pygame.Vector2(pos)

		self.animations = pygbase.AnimationManager([
			("idle", pygbase.Animation("sprite_sheets", "clam_boss_idle", 0, 1, True), 0),
			("slam", pygbase.Animation("sprite_sheets", "clam_boss_slam", 0, 16, False), 12),
		], "idle")

		self.summon_cooldown_range = (8, 13)
		self.summon_amount_range = (1, 2)
		self.summon_cooldown = pygbase.Timer(random.uniform(*self.summon_cooldown_range), True, False)

		self.particle_manager = particle_manager

		self.has_summoned = False
		self.particle_summon_pos = self.pos + (0, -40)
		self.water_vapour_particle_setting = pygbase.Common.get_particle_setting("water_vapour")
		self.boiling_water_particle_setting = pygbase.Common.get_particle_setting("boiling_water")
		self.bubbles_particle_setting = pygbase.Common.get_particle_setting("bubble")

		self.health = Health(2000)
		self.colliders = [pygame.Rect(0, 0, 120, 20), pygame.Rect(0, 0, 180, 70), pygame.Rect(0, 0, 120, 30)]
		self.colliders[0].midbottom = self.pos
		for i in range(1, len(self.colliders)):
			self.colliders[i].midbottom = self.colliders[i - 1].midtop

		self.clean_colour = pygame.Color("light blue")
		self.polluted_colour = pygame.Color((152, 143, 100))

		self.inter_surface = pygame.Surface((192, 128), flags=pygame.SRCALPHA)
		self.rect = self.inter_surface.get_rect(midbottom=self.pos)
		self.overlay_surface = pygame.Surface((192, 128))

		self.surrounding_particles = water_particle_manager.add_spawner(pygbase.RectSpawner(self.rect.bottomleft, 0.5, 5, (self.rect.width, 20), True, "bubble", water_particle_manager))

		self.smash_sound: pygame.mixer.Sound = pygbase.ResourceManager.get_resource("sound", "boss_smash")

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
		for collider in self.colliders:
			pygbase.DebugDisplay.draw_rect(pygbase.Common.get_value("camera").world_to_screen_rect(collider), "yellow")

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
			self.smash_sound.play()
			return random.randint(*self.summon_amount_range)

		return 0

	def draw(self, surface: pygame.Surface, camera: pygbase.Camera):
		self.inter_surface.fill((0, 0, 0, 0))
		self.overlay_surface.fill(self.clean_colour.lerp(self.polluted_colour, self.health.get_percentage() ** 2))

		pygame.draw.circle(surface, "light blue", camera.world_to_screen(self.pos), 200, width=10)

		self.animations.get_current_image().draw(self.inter_surface, (0, 0))
		self.inter_surface.blit(self.overlay_surface, (0, 0), special_flags=pygame.BLEND_MULT)

		surface.blit(self.inter_surface, camera.world_to_screen_rect(self.rect))


class BossBar:
	def __init__(self, pos: tuple, size: tuple, health: Health, border: int = 5):
		self.pos = pos
		self.size = size

		self.border = border

		self.health = health

		self.clean_colour = pygame.Color("light blue")
		self.polluted_colour = pygame.Color((152, 143, 100))

	def draw(self, surface: pygame.Surface):
		pygame.draw.rect(surface, (30, 30, 30), (self.pos, self.size))
		pygame.draw.rect(surface, self.clean_colour.lerp(self.polluted_colour, self.health.get_percentage()), (self.pos[0] + self.border, self.pos[1] + self.border, (self.size[0] - self.border * 2) * self.health.get_percentage(), self.size[1] - self.border * 2))
