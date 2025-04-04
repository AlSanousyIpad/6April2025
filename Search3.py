import sys
import os
import csv
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
                            QPushButton, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QFileDialog, QHeaderView, QMessageBox, QCheckBox,
                            QTabWidget, QMenu, QAction, QComboBox)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QCursor


class CSVSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patient Management System")
        self.resize(800, 600)
        self.existing_names = set()  # To track names for deduplication
        
        # Create central widget with tab layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create main tab
        self.create_main_tab()
        
        # Create daily visits tab
        self.create_daily_visits_tab()
        
        # Status bar for feedback
        self.statusBar().showMessage("Ready. Import a CSV file to begin.")
    
    def create_main_tab(self):
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        
        # Create search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search...")
        font = QFont()
        font.setPointSize(14)
        self.search_edit.setFont(font)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Create import buttons
        import_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import CSV")
        self.import_btn.clicked.connect(self.import_csv)
        self.import_btn.setMinimumHeight(40)
        
        self.import_dedupe_btn = QPushButton("Import CSV (No Duplicates)")
        self.import_dedupe_btn.clicked.connect(lambda: self.import_csv(deduplicate=True))
        self.import_dedupe_btn.setMinimumHeight(40)
        
        import_layout.addWidget(self.import_btn)
        import_layout.addWidget(self.import_dedupe_btn)
        import_layout.addStretch()
        layout.addLayout(import_layout)
        
        # Create options layout
        options_layout = QHBoxLayout()
        self.clear_on_import = QCheckBox("Clear existing data on import")
        self.clear_on_import.setChecked(True)
        options_layout.addWidget(self.clear_on_import)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Create table
        self.data_table = QTableWidget(0, 2)  # Start with 0 rows, 2 columns
        self.data_table.setHorizontalHeaderLabels(["Name", "Date"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.data_table)
        
        # Connect search functionality
        self.search_edit.textChanged.connect(self.filter_items)
        
        # Add tab
        self.tabs.addTab(main_tab, "Patient Records")
    
    def create_daily_visits_tab(self):
        daily_tab = QWidget()
        layout = QVBoxLayout(daily_tab)
        
        # Create instructions label
        instructions = QLabel("Enter patient visits or receive them from the Patient Records tab")
        layout.addWidget(instructions)
        
        # Create table
        self.daily_table = QTableWidget(0, 3)
        self.daily_table.setHorizontalHeaderLabels(["Name", "N/R", "1st Visit"])
        self.daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.daily_table)
        
        # Add row button
        add_row_btn = QPushButton("Add New Visit")
        add_row_btn.clicked.connect(self.add_empty_daily_row)
        layout.addWidget(add_row_btn)
        
        # Add tab
        self.tabs.addTab(daily_tab, "Daily Visits")
    
    def show_context_menu(self, position):
        # Get the clicked row
        clicked_row = self.data_table.rowAt(position.y())
        if clicked_row < 0:
            return
        
        # Create context menu
        context_menu = QMenu(self)
        send_to_daily = QAction("Send to Daily Visits", self)
        send_to_daily.triggered.connect(lambda: self.send_to_daily(clicked_row))
        context_menu.addAction(send_to_daily)
        
        # Show context menu
        context_menu.exec_(QCursor.pos())
    
    def send_to_daily(self, row):
        # Get data from main table
        name_item = self.data_table.item(row, 0)
        date_item = self.data_table.item(row, 1)
        
        if name_item and date_item:
            name = name_item.text()
            date = date_item.text()
            
            # Add to daily visits table
            self.add_daily_visit(name, "Recurrent", date)
            
            # Switch to daily tab
            self.tabs.setCurrentIndex(1)
            
            self.statusBar().showMessage(f"Added {name} to Daily Visits")
    
    def add_daily_visit(self, name, visit_type, date):
        row_count = self.daily_table.rowCount()
        self.daily_table.insertRow(row_count)
        
        # Add items to the row
        self.daily_table.setItem(row_count, 0, QTableWidgetItem(name))
        
        # Create combo box for N/R column
        combo = QComboBox()
        combo.addItems(["New", "Recurrent"])
        combo.setCurrentText(visit_type)
        self.daily_table.setCellWidget(row_count, 1, combo)
        
        # Add date
        self.daily_table.setItem(row_count, 2, QTableWidgetItem(date))
    
    def add_empty_daily_row(self):
        row_count = self.daily_table.rowCount()
        self.daily_table.insertRow(row_count)
        
        # Create empty name cell that's editable
        self.daily_table.setItem(row_count, 0, QTableWidgetItem(""))
        
        # Create combo box for N/R column
        combo = QComboBox()
        combo.addItems(["New", "Recurrent"])
        combo.setCurrentText("New")  # Default to "New" for manually added rows
        self.daily_table.setCellWidget(row_count, 1, combo)
        
        # Add today's date
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_table.setItem(row_count, 2, QTableWidgetItem(today))
    
    def import_csv(self, deduplicate=False):
        # Open file dialog, default to downloads folder
        downloads_path = os.path.expanduser("~/Downloads")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", downloads_path, "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Clear existing data if option is checked
                if self.clear_on_import.isChecked():
                    self.data_table.setRowCount(0)
                    self.existing_names.clear()
                else:
                    # Populate existing_names set with current table data
                    for row in range(self.data_table.rowCount()):
                        name_item = self.data_table.item(row, 0)
                        if name_item:
                            self.existing_names.add(name_item.text().lower())
                
                with open(file_path, 'r', newline='', encoding='utf-8') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    
                    # Get headers
                    headers = next(csv_reader, None)
                    if not headers:
                        QMessageBox.warning(self, "Empty File", "The CSV file appears to be empty.")
                        return
                    
                    # Look for Name and Date columns
                    name_idx = -1
                    date_idx = -1
                    
                    for i, header in enumerate(headers):
                        if header.strip().lower() == "name":
                            name_idx = i
                        elif header.strip().lower() == "date":
                            date_idx = i
                    
                    if name_idx == -1 or date_idx == -1:
                        QMessageBox.warning(self, "Invalid Format", 
                                          "CSV must have 'Name' and 'Date' columns.")
                        return
                    
                    # Set the table headers from the CSV
                    self.data_table.setHorizontalHeaderLabels([headers[name_idx], headers[date_idx]])
                    
                    # Process data from CSV
                    row_count = self.data_table.rowCount()
                    imported = 0
                    skipped = 0
                    
                    for row in csv_reader:
                        if len(row) > max(name_idx, date_idx):
                            name = row[name_idx]
                            date = row[date_idx]
                            
                            # Check for duplicates if deduplication is enabled
                            if deduplicate and name.lower() in self.existing_names:
                                skipped += 1
                                continue
                            
                            # Add to table
                            self.data_table.insertRow(row_count)
                            
                            name_item = QTableWidgetItem(name)
                            date_item = QTableWidgetItem(date)
                            
                            self.data_table.setItem(row_count, 0, name_item)
                            self.data_table.setItem(row_count, 1, date_item)
                            
                            # Add to existing names set
                            self.existing_names.add(name.lower())
                            
                            row_count += 1
                            imported += 1
                
                # Update status message
                status_msg = f"Imported {imported} records from {os.path.basename(file_path)}"
                if deduplicate and skipped > 0:
                    status_msg += f" (Skipped {skipped} duplicates)"
                self.statusBar().showMessage(status_msg)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import CSV: {str(e)}")
                self.statusBar().showMessage("Import failed")
    
    def filter_items(self, text):
        """Filter the table as user types in the search box"""
        search_text = text.lower()
        
        for row in range(self.data_table.rowCount()):
            name_item = self.data_table.item(row, 0)
            
            if name_item:
                name = name_item.text().lower()
                if search_text in name:
                    self.data_table.setRowHidden(row, False)
                else:
                    self.data_table.setRowHidden(row, True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVSearchApp()
    window.show()
    sys.exit(app.exec_())