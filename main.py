import random
import sys

from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QKeyEvent, QPainter
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget


class SnakeBoard(QWidget):
    GRID = 20
    CELL = 24
    BASE_SPEED = 130
    MIN_SPEED = 55

    def __init__(self, score_label, best_label, status_label):
        super().__init__()
        self.setFixedSize(self.GRID * self.CELL, self.GRID * self.CELL)
        self.setFocusPolicy(Qt.StrongFocus)
        self.score_label = score_label
        self.best_label = best_label
        self.status_label = status_label
        self.settings = QSettings("LS", "pjct_01_snake")
        self.best = int(self.settings.value("best", 0))
        self.best_label.setText(str(self.best))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.reset()

    def reset(self):
        self.timer.stop()
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.running = False
        self.paused = False
        self.score_label.setText("0")
        self.status_label.setText("Pressione Espaço para jogar")
        self.spawn_food()
        self.update()

    def start(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.status_label.setText("Jogando")
            self.timer.start(self.speed())
            self.setFocus()

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
            self.status_label.setText("Pausado")
        else:
            self.timer.start(self.speed())
            self.status_label.setText("Jogando")

    def speed(self):
        return max(self.MIN_SPEED, self.BASE_SPEED - self.score * 4)

    def spawn_food(self):
        free = [(x, y) for x in range(self.GRID) for y in range(self.GRID)
                if (x, y) not in self.snake]
        self.food = random.choice(free) if free else None

    def change_direction(self, direction):
        if direction != (-self.direction[0], -self.direction[1]):
            self.next_direction = direction

    def tick(self):
        self.direction = self.next_direction
        hx, hy = self.snake[0]
        dx, dy = self.direction
        head = (hx + dx, hy + dy)

        hit_wall = not (0 <= head[0] < self.GRID and 0 <= head[1] < self.GRID)
        hit_self = head in self.snake[:-1]
        if hit_wall or hit_self:
            self.game_over()
            return

        self.snake.insert(0, head)
        if head == self.food:
            self.score += 1
            self.score_label.setText(str(self.score))
            if self.score > self.best:
                self.best = self.score
                self.best_label.setText(str(self.best))
                self.settings.setValue("best", self.best)
            self.spawn_food()
            self.timer.start(self.speed())
        else:
            self.snake.pop()
        self.update()

    def game_over(self):
        self.timer.stop()
        self.running = False
        self.status_label.setText("Fim de jogo — Espaço para reiniciar")
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
            if self.running:
                self.toggle_pause()
            else:
                self.reset()
                self.start()
        elif event.key() == Qt.Key_R:
            self.reset()
            self.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0b0f14"))

        painter.setPen(QColor("#121923"))
        for i in range(self.GRID + 1):
            p = i * self.CELL
            painter.drawLine(p, 0, p, self.height())
            painter.drawLine(0, p, self.width(), p)

        if self.food:
            x, y = self.food
            painter.setBrush(QColor("#ff5c6c"))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x * self.CELL + 5, y * self.CELL + 5,
                                self.CELL - 10, self.CELL - 10)

        painter.setPen(Qt.NoPen)
        for i, (x, y) in enumerate(self.snake):
            painter.setBrush(QColor("#69a7ff") if i == 0 else QColor("#d8e7ff"))
            painter.drawRoundedRect(x * self.CELL + 2, y * self.CELL + 2,
                                    self.CELL - 4, self.CELL - 4, 5, 5)


class SnakeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pjct_01 — Snake")
        self.setFixedSize(540, 650)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(14)

        title = QLabel("SNAKE")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        subtitle = QLabel("pjct_01  •  v0.1.0")
        subtitle.setObjectName("muted")

        stats = QHBoxLayout()
        self.score = QLabel("0")
        self.best = QLabel("0")
        stats.addWidget(self.stat("PONTOS", self.score))
        stats.addStretch()
        stats.addWidget(self.stat("RECORDE", self.best))

        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignCenter)

        self.board = SnakeBoard(self.score, self.best, self.status)

        buttons = QHBoxLayout()
        play = QPushButton("Jogar / Pausar")
        restart = QPushButton("Reiniciar")
        play.clicked.connect(self.play_pause)
        restart.clicked.connect(self.restart)
        buttons.addWidget(play)
        buttons.addWidget(restart)

        hint = QLabel("Setas ou WASD para mover  •  Espaço pausa  •  R reinicia")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(stats)
        layout.addWidget(self.board, alignment=Qt.AlignCenter)
        layout.addWidget(self.status)
        layout.addLayout(buttons)
        layout.addWidget(hint)

        self.setStyleSheet("""
            #root { background: #080b10; color: #eef5ff; }
            QLabel { color: #eef5ff; }
            QLabel#muted { color: #738094; }
            QLabel#status { color: #9db7da; padding: 4px; }
            QPushButton {
                background: #121923; color: #eef5ff; border: 1px solid #263448;
                border-radius: 8px; padding: 9px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #192334; border-color: #69a7ff; }
            QPushButton:pressed { background: #0d131c; }
        """)

    def stat(self, name, value):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        label = QLabel(name)
        label.setObjectName("muted")
        value.setFont(QFont("Arial", 16, QFont.Bold))
        lay.addWidget(label)
        lay.addWidget(value)
        return box

    def play_pause(self):
        if self.board.running:
            self.board.toggle_pause()
        else:
            self.board.reset()
            self.board.start()

    def restart(self):
        self.board.reset()
        self.board.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("pjct_01 Snake")
    window = SnakeWindow()
    window.show()
    sys.exit(app.exec())
