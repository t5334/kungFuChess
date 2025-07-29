from PubSub import pubsub 

class MoveLogger:
    def __init__(self):
        self.moves = {"white": [], "black": []}
        self.points = {"white": 0, "black": 0}
        self.value_map = {
            "P": 1,
            "N": 3,
            "B": 3,
            "R": 5,
            "Q": 9,
            "K": 0  # או ערך גבוה אם רוצים לתת נקודות גם על אכילת מלך
        }
  
        pubsub.subscribe(self.handle_reset, "reset")

    def handle_move(self, data):
        color = data["color"]         # "white" / "black"
        piece = data["piece"]         # "P", "N", etc.
        from_cell = data["from"]      # "e2"
        to_cell = data["to"]          # "e4"
        self.log_move(color, piece, from_cell, to_cell)

    # def handle_capture(self, data):
    #         color = data["color"]         # "white" / "black"
    #         piece_type = data["piece_type"]  # "P", "N", etc.
    #         self.log_capture(color, piece_type)

    def handle_reset(self):
        self.__init__()

    def log_move(self, color: str, piece: str, from_cell: str, to_cell: str, ate: bool = False):
        notation = f"{piece}: {from_cell} -> {to_cell}"
        # if ate:
        #     notation += " ×"
        #     self.points[color] += 1
        self.moves[color].append(notation)

    def get_moves(self, color: str):
        return self.moves[color]

    def get_points(self, color: str):
        return self.points[color]

    def reset(self):
        self.__init__()
   
    def log_capture(self, color: str, piece_type: str):
        value = self.value_map.get(piece_type.upper(), 0)
        self.points[color] += value
        print(f"[SCORE] {color} gets {value} points. Total: {self.points[color]}")
        pubsub.publish("score_update", {"color": color, "points": self.points[color]})