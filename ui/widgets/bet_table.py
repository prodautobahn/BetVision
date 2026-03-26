# ui/widgets/bet_table.py
from PyQt5.QtCore import QAbstractTableModel, Qt

class BetTableModel(QAbstractTableModel):
    headers = ["Fixture", "Market", "Outcome", "Odd", "Model Prob", "EV", "Stake"]

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
        keys = ["fixture", "market", "outcome", "odd", "model_prob", "ev", "stake"]
        val = row.get(keys[col], "")
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers[section]
        return section + 1
