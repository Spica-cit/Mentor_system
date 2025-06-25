# progress_manager.py
import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QTextEdit,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate

TASK_STATES = ["未着手", "進行中", "完了"]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("進捗管理ツール")
        self.resize(1000, 600)

        self.data_file = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "students.json")
        self.student_data = self.load_data()
        self.data_modified = False

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # 学生リスト
        self.student_list = QListWidget()
        self.student_list.addItems(self.student_data.keys())
        self.student_list.currentItemChanged.connect(self.display_student_details)

        self.add_button = QPushButton("＋ 学生追加")
        self.delete_button = QPushButton("− 学生削除")
        self.add_button.clicked.connect(self.add_student)
        self.delete_button.clicked.connect(self.delete_student)

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("学生一覧:"))
        left_panel.addWidget(self.student_list)
        left_panel.addWidget(self.add_button)
        left_panel.addWidget(self.delete_button)

        left_container = QWidget()
        left_container.setLayout(left_panel)
        main_layout.addWidget(left_container, 2)

        # 詳細表示
        self.detail_area = QWidget()
        detail_layout = QVBoxLayout()
        self.detail_area.setLayout(detail_layout)

        self.research_label = QLabel("研究テーマ:")
        self.research_text = QLineEdit()
        self.research_text.textChanged.connect(self.mark_modified)
        detail_layout.addWidget(self.research_label)
        detail_layout.addWidget(self.research_text)

        task_header_layout = QHBoxLayout()
        task_header_label = QLabel("タスク一覧:")
        self.add_task_button = QPushButton("＋ タスク追加")
        self.delete_task_button = QPushButton("− タスク削除")
        self.add_task_button.clicked.connect(self.add_task_row)
        self.delete_task_button.clicked.connect(self.delete_task_row)

        task_header_layout.addWidget(task_header_label)
        task_header_layout.addStretch()
        task_header_layout.addWidget(self.add_task_button)
        task_header_layout.addWidget(self.delete_task_button)
        detail_layout.addLayout(task_header_layout)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(3)
        self.task_table.setHorizontalHeaderLabels(["タスク名", "期限", "状態"])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        detail_layout.addWidget(self.task_table)

        self.memo_label = QLabel("メモ:")
        self.memo_text = QTextEdit()
        self.memo_text.textChanged.connect(self.mark_modified)
        detail_layout.addWidget(self.memo_label)
        detail_layout.addWidget(self.memo_text)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_student_data)
        detail_layout.addWidget(self.save_button)

        main_layout.addWidget(self.detail_area, 3)
        self.setCentralWidget(main_widget)

    def mark_modified(self):
        self.data_modified = True

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def display_student_details(self, current, previous=None):
        self.task_table.blockSignals(True)
        if current is None:
            self.research_text.clear()
            self.task_table.setRowCount(0)
            self.memo_text.clear()
            return
        name = current.text()
        student = self.student_data.get(name, {})
        self.research_text.setText(student.get("research", ""))
        self.memo_text.setPlainText(student.get("memo", ""))

        tasks = student.get("tasks", [])
        self.task_table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            name_item = QTableWidgetItem(task.get("name", ""))
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.task_table.setItem(row, 0, name_item)

            due_str = task.get("due", "")
            date_edit = QDateEdit()
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setCalendarPopup(True)
            date_edit.dateChanged.connect(self.mark_modified)
            if due_str:
                try:
                    dt = datetime.strptime(due_str, "%Y-%m-%d")
                    qdate = QDate(dt.year, dt.month, dt.day)
                    date_edit.setDate(qdate)
                except ValueError:
                    date_edit.setDate(QDate.currentDate())
            else:
                date_edit.setDate(QDate.currentDate())

            if date_edit.date().toPyDate() < datetime.today().date():
                date_edit.setStyleSheet("background-color: #FFB6B6")

            self.task_table.setCellWidget(row, 1, date_edit)

            state_combo = QComboBox()
            state_combo.addItems(TASK_STATES)
            state_combo.currentIndexChanged.connect(self.mark_modified)
            state = task.get("state", TASK_STATES[0])
            if state in TASK_STATES:
                state_combo.setCurrentText(state)
            self.task_table.setCellWidget(row, 2, state_combo)

        self.task_table.blockSignals(False)

    # 先ほどまでのコードに続きます。変更点は add_task_row() の中にあります。

    def add_task_row(self):
        row = self.task_table.rowCount()
        self.task_table.insertRow(row)
        self.mark_modified()

        # タスク名セル（編集可能に設定）
        name_item = QTableWidgetItem("")
        name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.task_table.setItem(row, 0, name_item)

        # セルを選択状態にし、即編集モードへ
        self.task_table.setCurrentCell(row, 0)
        self.task_table.editItem(name_item)

        # 期限（QDateEdit）
        date_edit = QDateEdit()
        date_edit.setDisplayFormat("yyyy-MM-dd")
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.dateChanged.connect(self.mark_modified)
        self.task_table.setCellWidget(row, 1, date_edit)

        # 状態（QComboBox）
        state_combo = QComboBox()
        state_combo.addItems(TASK_STATES)
        state_combo.currentIndexChanged.connect(self.mark_modified)
        self.task_table.setCellWidget(row, 2, state_combo)

    def delete_task_row(self):
        row = self.task_table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "行未選択", "削除するタスク行を選択してください。")
            return
        self.task_table.removeRow(row)
        self.mark_modified()

    def add_student(self):
        name, ok = QInputDialog.getText(self, "学生の追加", "名前と学年を入力してください（例: 佐藤 三郎 (2年)）:")
        if ok and name.strip():
            name = name.strip()
            if name in self.student_data:
                QMessageBox.warning(self, "重複", f"「{name}」はすでに存在します。")
                return
            self.student_data[name] = {"research": "", "tasks": [], "memo": ""}
            self.student_list.addItem(name)
            self.student_list.setCurrentRow(self.student_list.count() - 1)
            self.save_all_data_to_file()

    def delete_student(self):
        current_item = self.student_list.currentItem()
        if current_item is None:
            return
        name = current_item.text()
        reply = QMessageBox.question(
            self, "削除の確認",
            f"「{name}」を削除してもよろしいですか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del self.student_data[name]
            row = self.student_list.currentRow()
            self.student_list.takeItem(row)
            self.research_text.clear()
            self.task_table.setRowCount(0)
            self.memo_text.clear()
            self.save_all_data_to_file()

    def save_student_data(self):
        current_item = self.student_list.currentItem()
        if current_item is None:
            return
        name = current_item.text()
        tasks = []
        try:
            for row in range(self.task_table.rowCount()):
                name_item = self.task_table.item(row, 0)
                date_widget = self.task_table.cellWidget(row, 1)
                state_widget = self.task_table.cellWidget(row, 2)
                if (
                    name_item and name_item.text().strip() and
                    date_widget and state_widget
                ):
                    due_qdate = date_widget.date()
                    due_str = due_qdate.toString("yyyy-MM-dd")
                    task = {
                        "name": name_item.text().strip(),
                        "due": due_str,
                        "state": state_widget.currentText()
                    }
                    tasks.append(task)
        except Exception as e:
            QMessageBox.critical(self, "保存エラー", f"タスク保存中にエラーが発生しました：\n{e}")
            return

        self.student_data[name] = {
            "research": self.research_text.text(),
            "tasks": tasks,
            "memo": self.memo_text.toPlainText()
        }
        self.save_all_data_to_file()
        self.data_modified = False
        QMessageBox.information(self, "保存完了", "データを保存しました。")

    def save_all_data_to_file(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.student_data, f, indent=2, ensure_ascii=False)

    def closeEvent(self, event):
        if self.data_modified:
            reply = QMessageBox.question(
                self,
                "終了の確認",
                "変更内容を保存しますか？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_student_data()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
