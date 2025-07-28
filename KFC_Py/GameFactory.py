import pathlib
from Board import Board
from PieceFactory import PieceFactory
from Game import Game
from GraphicsFactory import GraphicsFactory
from BackgroundBoardFactory import create_background_board


CELL_PX = 64


def create_game(pieces_root: str | pathlib.Path, img_factory) -> Game:
    """Build a *Game* from the on-disk asset hierarchy rooted at *pieces_root*.

    This reads *board.csv* located inside *pieces_root*, creates a blank board
    (or loads board.png if present), instantiates every piece via PieceFactory
    and returns a ready-to-run *Game* instance.
    """
    pieces_root = pathlib.Path(pieces_root)
    board_csv = pieces_root / "board.csv"
    if not board_csv.exists():
        raise FileNotFoundError(board_csv)

    background_path = pieces_root / "background.jpg"
    board_img_path = pieces_root / "board.png"

    if not background_path.exists():
        raise FileNotFoundError(background_path)
    if not board_img_path.exists():
        raise FileNotFoundError(board_img_path)

    board = create_background_board(
        background_path=str(background_path),
        board_img_path=str(board_img_path)
    )

    gfx_factory = GraphicsFactory(img_factory)
    pf = PieceFactory(board, pieces_root, graphics_factory=gfx_factory)

    pieces = []
    with board_csv.open() as f:
        for r, line in enumerate(f):
            for c, code in enumerate(line.strip().split(",")):
                if code:
                    pieces.append(pf.create_piece(code, (r, c)))

    return Game(pieces, board) 