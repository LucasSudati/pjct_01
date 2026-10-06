import random
import sys

from PySide6.QtCore import QPointF, QSettings, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget,
)


class SnakeBoard(QWidget):
    GRID = 20
    CELL = 24
    BASE_SPEED = 135
    MIN_SPEED = 55

    def __init__(self, score_label, best_label, level_label, status_label):
        super().__init__()
        self.setFixedSize(self.GRID * self.CELL, self.GRID * self.CELL)
        self.setFocusPolicy(Qt.StrongFocus)
        self.score_label = score_label
        self.best_label = best_label
        self.level_label = level_label
        self.status_label = status_label

        self.settings = QSettings("LS", "pjct_01_snake")
        self.best = int(self.settings.value("best", 0))
        self.best_label.setText(str(self.best))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

        self.flash = 0
        self.state = "ready"
        self.reset()

    def reset(self):
        self.timer.stop()
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.flash = 0
        self.state = "ready"
        self.score_label.setText("0")
        self.level_label.setText("1")
        self.status_label.setText("ESPAÇO PARA JOGAR")
        self.spawn_food()
        self.update()

    @property
    def running(self):
        return self.state == "playing"

    def level(self):
        return 1 + self.score // 5

    def speed(self):
        return max(self.MIN_SPEED, self.BASE_SPEED - (self.level() - 1) * 12)

    def start(self):
        if self.state in ("ready", "gameover"):
            if self.state == "gameover":
                self.reset()
            self.state = "playing"
            self.status_label.setText("JOGANDO")
            self.timer.start(self.speed())
            self.setFocus()
            self.update()

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.timer.stop()
            self.status_label.setText("PAUSADO")
        elif self.state == "paused":
            self.state = "playing"
            self.timer.start(self.speed())
            self.status_label.setText("JOGANDO")
        self.setFocus()
        self.update()

    def spawn_food(self):
        free = [
            (x, y)
            for x in range(self.GRID)
            for y in range(self.GRID)
            if (x, y) not in self.snake
        ]
        self.food = random.choice(free) if free else None

    def change_direction(self, direction):
        if self.state != "playing":
            return
        if direction != (-self.direction[0], -self.direction[1]):
            self.next_direction = direction

    def tick(self):
        if self.state != "playing":
            return

        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        head = (hx + dx, hy + dy)

        hit_wall = not (0 <= head[0] < self.GRID and 0 <= head[1] < self.GRID)
        growing = head == self.food
        body_to_check = self.snake if growing else self.snake[:-1]
        hit_self = head in body_to_check

        if hit_wall or hit_self:
            self.game_over()
            return

        self.snake.insert(0, head)

        if growing:
            self.score += 1
            self.flash = 3
            self.score_label.setText(str(self.score))
            self.level_label.setText(str(self.level()))

            if self.score > self.best:
                self.best = self.score
                self.best_label.setText(str(self.best))
                self.settings.setValue("best", self.best)

            self.spawn_food()
            if self.food is None:
                self.game_over(won=True)
                return
            self.timer.start(self.speed())
        else:
            self.snake.pop()

        if self.flash > 0:
            self.flash -= 1
        self.update()

    def game_over(self, won=False):
        self.timer.stop()
        self.state = "gameover"
        self.status_label.setText("TABULEIRO COMPLETO!" if won else "FIM DE JOGO")
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        keys = {
            Qt.Key_Up: (0, -1), Qt.Key_W: (0, -1),
            Qt.Key_Down: (0, 1), Qt.Key_S: (0, 1),
            Qt.Key_Left: (-1, 0), Qt.Key_A: (-1, 0),
            Qt.Key_Right: (1, 0), Qt.Key_D: (1, 0),
        }

        if event.key() in keys:
            self.change_direction(keys[event.key()])
        elif event.key() == Qt.Key_Space:
            if self.state in ("ready", "gameover"):
                self.start()
            else:
                self.toggle_pause()
        elif event.key() == Qt.Key_R:
            self.reset()
            self.start()

    def draw_overlay(self, painter, title, subtitle):
        painter.fillRect(self.rect(), QColor(4, 8, 13, 185))
        painter.setPen(QColor("#f3f7ff"))
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        painter.drawText(self.rect().adjusted(0, -24, 0, 0), Qt.AlignCenter, title)
        painter.setPen(QColor("#8290a5"))
        painter.setFont(QFont("Arial", 10, QFont.DemiBold))
        painter.drawText(self.rect().adjusted(0, 34, 0, 0), Qt.AlignCenter, subtitle)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        background = QColor("#0a0e14")
        if self.flash:
            background = QColor("#0d1520")
        painter.fillRect(self.rect(), background)

        painter.setPen(QPen(QColor("#111923"), 1))
        for i in range(self.GRID + 1):
            p = i * self.CELL
            painter.drawLine(p, 0, p, self.height())
            painter.drawLine(0, p, self.width(), p)

        if self.food:
            x, y = self.food
            cx = x * self.CELL + self.CELL / 2
            cy = y * self.CELL + self.CELL / 2
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 83, 105, 35))
            painter.drawEllipse(QPointF(cx, cy), 10, 10)
            painter.setBrush(QColor("#ff5369"))
            painter.drawEllipse(QPointF(cx, cy), 6, 6)

        painter.setPen(Qt.NoPen)
        for i, (x, y) in reversed(list(enumerate(self.snake))):
            rect_x = x * self.CELL + 2
            rect_y = y * self.CELL + 2
            if i == 0:
                painter.setBrush(QColor("#63a5ff"))
                painter.drawRoundedRect(rect_x, rect_y, 20, 20, 7, 7)
                self.draw_eyes(painter, x, y)
            else:
                fade = max(120, 225 - i * 5)
                painter.setBrush(QColor(205, 226, 255, fade))
                painter.drawRoundedRect(rect_x + 1, rect_y + 1, 18, 18, 6, 6)

        if self.state == "ready":
            self.draw_overlay(painter, "SNAKE", "ESPAÇO PARA COMEÇAR")
        elif self.state == "paused":
            self.draw_overlay(painter, "PAUSADO", "ESPAÇO PARA CONTINUAR")
        elif self.state == "gameover":
            self.draw_overlay(painter, "GAME OVER", f"{self.score} PONTOS  •  ESPAÇO PARA TENTAR NOVAMENTE")

    def draw_eyes(self, painter, x, y):
        dx, dy = self.direction
        base_x = x * self.CELL
        base_y = y * self.CELL

        if dx:
            eye_x = base_x + (17 if dx > 0 else 7)
            positions = [(eye_x, base_y + 8), (eye_x, base_y + 16)]
        else:
            eye_y = base_y + (17 if dy > 0 else 7)
            positions = [(base_x + 8, eye_y), (base_x + 16, eye_y)]

        painter.setBrush(QColor("#07101c"))
        for ex, ey in positions:
            painter.drawEllipse(QPointF(ex, ey), 1.7, 1.7)


class SnakeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pjct_01 — Snake")
        self.setFixedSize(560, 700)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(13)

        header = QHBoxLayout()
        name_box = QVBoxLayout()
        title = QLabel("SNAKE")
        title.setObjectName("title")
        subtitle = QLabel("pjct_01")
        subtitle.setObjectName("muted")
        name_box.addWidget(title)
        name_box.addWidget(subtitle)
        header.addLayout(name_box)
        header.addStretch()

        self.score = QLabel("0")
        self.best = QLabel("0")
        self.level_value = QLabel("1")

        stats = QHBoxLayout()
        stats.setSpacing(34)
        stats.addWidget(self.stat("PONTOS", self.score))
        stats.addWidget(self.stat("RECORDE", self.best))
        stats.addWidget(self.stat("NÍVEL", self.level_value))
        header.addLayout(stats)

        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignCenter)

        self.board = SnakeBoard(self.score, self.best, self.level_value, self.status)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.play_button = QPushButton("Jogar / Pausar")
        restart_button = QPushButton("Reiniciar")
        self.play_button.clicked.connect(self.play_pause)
        restart_button.clicked.connect(self.restart)
        buttons.addWidget(self.play_button)
        buttons.addWidget(restart_button)

        hint = QLabel("WASD / SETAS  •  ESPAÇO PAUSA  •  R REINICIA")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignCenter)

        layout.addLayout(header)
        layout.addSpacing(4)
        layout.addWidget(self.board, alignment=Qt.AlignCenter)
        layout.addWidget(self.status)
        layout.addLayout(buttons)
        layout.addWidget(hint)

        self.setStyleSheet("""
            #root { background: #070a0f; color: #eef5ff; }
            QLabel { color: #eef5ff; }
            QLabel#title { font-size: 24px; font-weight: 800; letter-spacing: 3px; }
            QLabel#muted { color: #66758a; font-size: 11px; }
            QLabel#status {
                color: #8290a5; font-size: 10px; font-weight: 700;
                letter-spacing: 1px; padding: 3px;
            }
            QLabel#hint { color: #536074; font-size: 9px; letter-spacing: 1px; }
            QPushButton {
                background: #101720; color: #dce9fb;
                border: 1px solid #202c3d; border-radius: 8px;
                padding: 10px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #162131; border-color: #4e82c5; }
            QPushButton:pressed { background: #0c1118; }
        """)

    def stat(self, name, value):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(1)
        label = QLabel(name)
        label.setObjectName("muted")
        label.setAlignment(Qt.AlignRight)
        value.setFont(QFont("Arial", 16, QFont.Bold))
        value.setAlignment(Qt.AlignRight)
        lay.addWidget(label)
        lay.addWidget(value)
        return box

    def play_pause(self):
        if self.board.state in ("ready", "gameover"):
            self.board.start()
        else:
            self.board.toggle_pause()

    def restart(self):
        self.board.reset()
        self.board.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("pjct_01 Snake")
    window = SnakeWindow()
    window.show()
    sys.exit(app.exec())
