from config import COLORS

def get_cyberpunk_stylesheet():
    return f"""
    /* Global Styles */
    QMainWindow, QWidget {{
        background-color: {COLORS['bg']};
        color: {COLORS['text']};
        font-family: 'Segoe UI', 'Space Grotesk', sans-serif;
        font-size: 13px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {COLORS['surface']};
        width: 6px;
        margin: 0px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border2']};
        min-height: 20px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['cyan']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {COLORS['surface']};
        height: 6px;
        margin: 0px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS['border2']};
        min-width: 20px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS['cyan']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Card Panels */
    QFrame[class="card"] {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border2']};
        border-radius: 14px;
    }}

    QFrame[class="card2"] {{
        background-color: {COLORS['card2']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
    }}

    /* Navigation Buttons */
    QPushButton[class="nav-btn"] {{
        background-color: transparent;
        color: {COLORS['muted']};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 13px;
    }}
    QPushButton[class="nav-btn"]:hover {{
        color: {COLORS['dim']};
        background-color: rgba(255, 255, 255, 0.04);
    }}
    QPushButton[class="nav-btn-active"] {{
        background-color: rgba(0, 229, 255, 0.12);
        color: {COLORS['cyan']};
        border: 1px solid rgba(0, 229, 255, 0.35);
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 13px;
    }}

    /* Standard Buttons */
    QPushButton {{
        background-color: {COLORS['card2']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border2']};
        border-radius: 8px;
        padding: 7px 15px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        border-color: {COLORS['cyan']};
        color: {COLORS['cyan']};
        background-color: rgba(0, 229, 255, 0.06);
    }}
    QPushButton:pressed {{
        background-color: rgba(0, 229, 255, 0.15);
    }}
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['muted']};
        border-color: {COLORS['border']};
    }}

    /* Accent Buttons */
    QPushButton[class="btn-primary"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['cyan']}, stop:1 #0099cc);
        color: #04080f;
        font-weight: 800;
        border: none;
    }}
    QPushButton[class="btn-primary"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #33ecff, stop:1 #00bbee);
    }}

    QPushButton[class="btn-success"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['green']}, stop:1 #00bb66);
        color: #04080f;
        font-weight: 800;
        border: none;
    }}
    QPushButton[class="btn-success"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #33ff99, stop:1 #00dd77);
    }}

    QPushButton[class="btn-danger"] {{
        background: rgba(255, 61, 90, 0.1);
        border: 1px solid rgba(255, 61, 90, 0.35);
        color: {COLORS['red']};
        font-weight: 700;
    }}
    QPushButton[class="btn-danger"]:hover {{
        background: rgba(255, 61, 90, 0.25);
        border-color: {COLORS['red']};
    }}

    QPushButton[class="btn-purple"] {{
        background: rgba(176, 102, 255, 0.12);
        border: 1px solid rgba(176, 102, 255, 0.35);
        color: {COLORS['purple']};
        font-weight: 700;
    }}
    QPushButton[class="btn-purple"]:hover {{
        background: rgba(176, 102, 255, 0.25);
        border-color: {COLORS['purple']};
    }}

    /* Inputs & Combos */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {{
        background-color: {COLORS['card2']};
        border: 1px solid {COLORS['border2']};
        border-radius: 8px;
        padding: 7px 12px;
        color: {COLORS['text']};
        selection-background-color: {COLORS['cyan']};
        selection-color: #000;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
        border: 1px solid {COLORS['cyan']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['card2']};
        border: 1px solid {COLORS['border2']};
        color: {COLORS['text']};
        selection-background-color: rgba(0, 229, 255, 0.2);
        selection-color: {COLORS['cyan']};
    }}

    /* Tables */
    QTableWidget, QTableView {{
        background-color: {COLORS['card']};
        border: 1px solid {COLORS['border2']};
        border-radius: 12px;
        gridline-color: {COLORS['border']};
        selection-background-color: rgba(0, 229, 255, 0.1);
        selection-color: {COLORS['cyan']};
    }}
    QHeaderView::section {{
        background-color: {COLORS['surface']};
        color: {COLORS['muted']};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        padding: 8px;
        border: none;
        border-bottom: 1px solid {COLORS['border']};
    }}

    /* Labels */
    QLabel {{
        background: transparent;
    }}
    QLabel[class="title"] {{
        font-size: 20px;
        font-weight: 800;
        color: {COLORS['text']};
    }}
    QLabel[class="subtitle"] {{
        font-size: 11px;
        color: {COLORS['muted']};
    }}
    QLabel[class="card-header"] {{
        font-size: 11px;
        font-weight: 700;
        color: {COLORS['muted']};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* Progress Bars */
    QProgressBar {{
        background-color: {COLORS['border']};
        border-radius: 3px;
        height: 6px;
        text-align: right;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['green']}, stop:1 {COLORS['cyan']});
        border-radius: 3px;
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: none;
    }}
    """
