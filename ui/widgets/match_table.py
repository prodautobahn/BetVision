# ui/widgets/match_table.py
from PyQt5.QtCore import QAbstractTableModel, Qt

class MatchTableModel(QAbstractTableModel):
    headers = ["Fixture", "League", "Date", "Status",
               "Home", "Away", "1", "X", "2", "EV(1)", "EV(X)", "EV(2)"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []

    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self._data[index.row()]
        col = index.column()
        # Map columns to JSON keys
        keys = ["fixture", "league", "date", "status",
                "home", "away", "1", "X", "2", "ev_1", "ev_X", "ev_2"]
        return str(row.get(keys[col], ""))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers[section]
        return section + 1
