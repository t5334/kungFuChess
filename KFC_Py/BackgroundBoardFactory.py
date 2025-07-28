# BackgroundBoardFactory.py

import pathlib
from Board import Board
from img import Img


def create_background_board(background_path: str, board_img_path: str) -> Board:
    print(f"[DEBUG] Creating background board with background: {background_path} and board image: {board_img_path}")
    # טען את רקע המסך כולו (למשל 1280x720)
    background = Img().read(background_path, size=(1280, 720))

    # טען את תמונת הלוח (למשל 512x512)
    board = Img().read(board_img_path, size=(512, 512))

    # הדבק את הלוח במיקום בתוך הרקע
    # לדוגמה: מיקום (384, 104) (נקודה זו תלויה בתמונה שלך!)
    board.draw_on(background, 384, 104)


    # יצירת אובייקט Board עם הרקע הזה
    return Board(
        cell_H_pix=64,
        cell_W_pix=64,
        W_cells=8,
        H_cells=8,
        img=background,
        offset_x=384,  # ערך התאם למיקום האמיתי
        offset_y=104
    )
