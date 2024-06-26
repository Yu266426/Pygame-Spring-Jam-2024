class Health:
	def __init__(self, amount: int):
		self.max_health = amount
		self.health = amount

	def damage(self, amount: int):
		self.health = max(self.health - amount, 0)

	def heal(self, amount: int):
		self.health = min(self.health + amount, self.max_health)

	def get_percentage(self) -> float:
		return self.health / self.max_health

	def alive(self) -> bool:
		return self.health > 0
