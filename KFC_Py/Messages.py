class Messages:
    def __init__(self):
        self.started = False

    def on_start(self, data):
        if not self.started:
            print("🎬 Game Started!")
            self.started = True

    def on_win(self, data):
        print(f"🏆 {data['winner']} wins!")
