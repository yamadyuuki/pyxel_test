# entity_manager.py
from enemy import Goomba

class EntityManager:
    def __init__(self):
        self.goombas = []

    def add_goomba(self, x, y):
        """クリボーを追加"""
        self.goombas.append(Goomba(x, y))

    def update_all(self):
        """全てのエンティティを更新"""
        for goomba in self.goombas:
            goomba.update()

    def draw_all(self):
        """全てのエンティティを描画"""
        for goomba in self.goombas:
            goomba.draw()

    def reset(self):
        """全てのエンティティをクリア"""
        self.goombas.clear()
