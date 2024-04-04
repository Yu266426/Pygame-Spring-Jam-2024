import pygbase
import pygame

from files import FONT_PATH
from game import Game


class Intro(pygbase.GameState, name="intro"):
	def __init__(self):
		super().__init__()

		self.ui = pygbase.UIManager()
		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.1, False)),
				FONT_PATH,
				pygbase.UIValue(40),
				"grey",
				"You are Fire Man",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)

		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.23, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"white",
				"The world has been overrun by monsters,",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)
		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.01, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"white",
				"Blobs of pollution given sentience...",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			),
			add_on_to_previous=(False, True)
		)

		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.42, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"white",
				"Using your flamethrower, you can boil away",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)
		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.01, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"white",
				"the water sustaining the monsters.",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			),
			add_on_to_previous=(False, True)
		)

		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.6, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"white",
				"Dive deep into the ocean",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)
		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.01, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"white",
				"and find out what is causing this...",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			),
			add_on_to_previous=(False, True)
		)

		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.8, False)),
				FONT_PATH,
				pygbase.UIValue(16),
				"grey",
				"Press space to start",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)

	def update(self, delta: float):
		self.ui.update(delta)

		if pygbase.InputManager.get_key_just_pressed(pygame.K_SPACE):
			self.set_next_state(pygbase.FadeTransition(self, Game(), 4.0, (0, 0, 0)))

	def draw(self, surface: pygame.Surface):
		surface.fill("black")

		self.ui.draw(surface)
