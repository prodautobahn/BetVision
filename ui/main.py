# ui/main.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, QThread
from .widgets.match_table import MatchTableModel
from .widgets.bet_table import BetTableModel
from .widgets.combined_widget import CombinedWidget
import requests

API_BASE = "http://localhost:8000"  # FastAPI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bet‑Vision 2026 – Dashboard")
        self.resize(1200, 800)

        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Match table
        self.match_table = QTableView()
        self.match_model = MatchTableModel()
        self.match_table.setModel(self.match_model)
        layout.addWidget(self.match_table)

        # Bet table
        self.bet_table = QTableView()
        self.bet_model = BetTableModel()
        self.bet_table.setModel(self.bet_model)
        layout.addWidget(self.bet_table)

        # Combined bets widget
        self.combined_widget = CombinedWidget()
        layout.addWidget(self.combined_widget)

        # Timer to refresh every 30s
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)

        self.refresh_data()

    def refresh_data(self):
        # 1. Load matches
        resp = requests.get(f"{API_BASE}/api/matches")
        self.match_model.set_data(resp.json())

        # 2. Load value bets
        resp = requests.get(f"{API_BASE}/api/value_bets")
        self.bet_model.set_data(resp.json())

        # 3. Load combined bets
        resp = requests.get(f"{API_BASE}/api/combined_bets")
        self.combined_widget.set_data(resp.json())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
