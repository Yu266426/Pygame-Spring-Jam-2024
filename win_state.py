import pygame
import pygbase

from files import FONT_PATH


class Win(pygbase.GameState, name="win"):
	def __init__(self):
		super().__init__()

		self.ui = pygbase.UIManager()
		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.3, False)),
				FONT_PATH,
				pygbase.UIValue(40),
				"black",
				"Thank you for saving the world.",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)

		self.ui.add_element(
			pygbase.TextElement(
				(pygbase.UIValue(0.5, False), pygbase.UIValue(0.6, False)),
				FONT_PATH,
				pygbase.UIValue(20),
				"black",
				"The end",
				self.ui.base_container,
				use_sys=False,
				alignment=pygbase.UIAlignment.TOP_MID
			)
		)

	def update(self, delta: float):
		self.ui.update(delta)

	def draw(self, surface: pygame.Surface):
		surface.fill("white")

		self.ui.draw(surface)
