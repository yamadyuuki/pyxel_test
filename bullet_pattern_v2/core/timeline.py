class Timeline:
    def __init__(self, script):
        # 例: [{"at":60,"cmd":"use","pattern":"circular_16"}, {"at":240,"cmd":"use","pattern":"aimed_burst"}]
        self.script = sorted(script, key=lambda c: c["at"])
        self.idx = 0

    def tick(self, t, emitter, ctx):
        # 時間tに達したコマンドを順に実行
        while self.idx < len(self.script) and self.script[self.idx]["at"] <= t:
            cmd = self.script[self.idx]
            if cmd["cmd"] == "use":
                emitter.set_pattern(cmd["pattern"])
            elif cmd["cmd"] == "stop":
                emitter.set_pattern(None)
            self.idx += 1
