# entity_manager.py
from enemy import Goomba

class EntityManager:
    def __init__(self, initial_goombas=None):
        """
        initial_goombas: クリボーの初期配置 [(x, y), (x, y), ...]
        """
        self.goombas = []
        self.initial_goombas = initial_goombas or []
        self.reset()

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
        """全てのエンティティをクリアして初期配置に戻す"""
        self.goombas.clear()
        for x, y in self.initial_goombas:
            self.add_goomba(x, y)

    def check_collision_with_player(self, player):
        """
        プレイヤーと全クリボーの衝突判定
        戻り値: ("踏んだ", goomba) or ("横から当たった", goomba) or None
        """
        for goomba in self.goombas:
            if self._aabb_collision(player, goomba):
                # 踏み判定: プレイヤーが落下中 & クリボーの上半分に当たった
                if player.vy > 0 and player.y + player.h <= goomba.y + goomba.h / 2:
                    return ("stomp", goomba)
                else:
                    return ("hit", goomba)
        return None

    def _aabb_collision(self, obj1, obj2):
        """矩形同士の衝突判定（AABB）"""
        return (obj1.x < obj2.x + obj2.w and
                obj1.x + obj1.w > obj2.x and
                obj1.y < obj2.y + obj2.h and
                obj1.y + obj1.h > obj2.y)

    def remove_goomba(self, goomba):
        """クリボーをリストから削除"""
        if goomba in self.goombas:
            self.goombas.remove(goomba)
