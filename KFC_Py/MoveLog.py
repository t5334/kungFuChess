class MoveLog:
    def __init__(self):
        self.moves = []

    def handle_move(self, data):
        piece_id = data['piece_id']
        cmd = data['cmd']
        self.moves.append(f"{piece_id}: {cmd.type} {cmd.params}")
        print(f"[LOG] {self.moves[-1]}")
