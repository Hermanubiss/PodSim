# PodSim window: set up the button mapping and steering, then fly.
# Same binder as podsim.py (binder.py), with a face on it.
#
# Run it from the project folder:  python podsim\gui.py

import sys
import time
from pathlib import Path
from string import Template

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from binder import (
    XBOX_BUTTONS,
    Binder,
    all_devices,
    install_vigem_driver,
    pygame,
    vid_pid_from_guid,
    vigem_driver_installed,
)
from config import (
    add_missing,
    clean_profile_name,
    list_profiles,
    load_settings,
    pitch_keys,
    save_settings,
)
from podengine import pitch_clash
import sheets
from paths import VERSION, first_run, resource_dir, user_dir

first_run()
CONFIG_PATH = user_dir() / "config.json"  # the active settings
PROFILES_FOLDER = user_dir() / "profiles"  # saved copies, one per file

try:
    import pyi_splash  # only exists inside PodSim.exe
except ImportError:
    pyi_splash = None
SPLASH_SECONDS = 2.5

# How big the binding-sheet pictures are drawn (1.0 = 2000 pixels wide).
PICTURE_SCALE = 0.55


# --- Looks -------------------------------------------------------------------

# The Flash colour scheme: scarlet suit, lightning-bolt gold, on a dark
# crimson-black. EVERY colour in the window comes from this list, so to
# change the theme, change it here.
BG = "#120a0b"           # window background: almost black, a hint of red
PANEL = "#1d0f11"        # boxes and cards
RAISED = "#2a1518"       # buttons, the selected tab
BORDER = "#4a1f25"       # thin lines around things
TEXT = "#fbf3e9"         # warm white
MUTED = "#c9a9a3"        # quieter text
DIM = "#8a6560"          # quietest: disabled things, centre lines
SCARLET = "#c8102e"      # the suit
SCARLET_HOT = "#e8202f"  # scarlet under the mouse
GOLD = "#ffc72c"         # the lightning bolt
GOLD_HOT = "#ffd84d"     # gold under the mouse
ON_GOLD = "#1a0b06"      # dark text that reads well on gold
WARNING = "#ff8c1a"      # orange: "needs attention"
ERROR = "#ff5a5f"        # light red: "not found" (lighter than the suit)

# What the dropdowns show for each config.json name. "" = not bound.
XBOX_LABELS = {
    "": "—",
    "A": "A",
    "B": "B",
    "X": "X",
    "Y": "Y",
    "LB": "LB",
    "RB": "RB",
    "BACK": "Back",
    "START": "Start",
    "LS": "LS click",
    "RS": "RS click",
    "DPAD_UP": "D-pad ↑",
    "DPAD_RIGHT": "D-pad →",
    "DPAD_DOWN": "D-pad ↓",
    "DPAD_LEFT": "D-pad ←",
}

# Dropdown colour per Xbox button. A/B/X/Y keep the real Xbox colours so
# they're easy to recognise.
XBOX_COLOURS = {
    "A": "#2ea043",
    "B": "#da3633",
    "X": "#1f6feb",
    "Y": "#bb8009",
}
OTHER_COLOUR = "#8e1526"  # deep scarlet for every other Xbox button
PRESSED_COLOUR = GOLD  # while you hold the VKB button

STEERING_MODES = {
    "right_stick": "Right stick steers",
    "podracer": "Podracer (two engines)",
}
PITCH_STICKS = {
    "right": "Right stick",
    "left": "Left stick",
    "off": "Off",
}

MODE_HELP = {
    "right_stick": "Left stick forward/back = gas and brake.\n"
    "Right stick left/right = steering.",
    "podracer": "Both sticks forward = full power.\n"
    "Ease one off to turn towards that side.\n"
    "Both back = brake.",
}

# The $NAME spots are filled in from the colour list above by Template.
STYLE = Template("""
QWidget { font-family: "Segoe UI"; font-size: 10pt; }
QGroupBox {
    border: 1px solid $BORDER; border-radius: 8px;
    margin-top: 14px; padding: 10px 8px 8px 8px;
    background: $PANEL;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 10px; padding: 0 4px;
    color: $GOLD; font-weight: 600;
}
QPushButton {
    background: $RAISED; border: 1px solid $BORDER; border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover { background: $BORDER; }
QPushButton:disabled { color: $DIM; }
QPushButton#start {
    background: $GOLD; border-color: $GOLD_HOT; color: $ON_GOLD; font-weight: 700;
}
QPushButton#start:hover { background: $GOLD_HOT; }
QPushButton#start[running="true"] {
    background: $SCARLET; border-color: $SCARLET_HOT; color: $TEXT;
}
QPushButton#start[running="true"]:hover { background: $SCARLET_HOT; }
QPushButton#save { background: $SCARLET; border-color: $SCARLET_HOT; font-weight: 600; }
QPushButton#save:hover { background: $SCARLET_HOT; }
QPushButton#save:disabled { background: $RAISED; color: $DIM; border-color: $BORDER; }
QComboBox {
    background: $BG; border: 1px solid $BORDER; border-radius: 5px;
    padding: 3px 6px;
}
QComboBox:hover { border-color: $SCARLET; }
QSpinBox, QDoubleSpinBox { min-height: 24px; }
QCheckBox::indicator {
    width: 14px; height: 14px; border: 1px solid $MUTED; border-radius: 3px;
    background: $BG;
}
QCheckBox::indicator:checked { background: $GOLD; border-color: $GOLD; }
QTabWidget::pane { border: 1px solid $BORDER; border-radius: 8px; top: -1px; }
QTabBar::tab {
    background: $PANEL; border: 1px solid $BORDER; padding: 7px 16px;
    border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px;
    color: $MUTED;
}
QTabBar::tab:selected {
    background: $RAISED; color: $TEXT; border-top: 3px solid $SCARLET;
}
QScrollArea { border: none; }
QFrame#card {
    background: $PANEL; border: 1px solid $BORDER; border-left: 4px solid $SCARLET;
    border-radius: 8px;
}
QTableWidget {
    background: $BG; border: 1px solid $BORDER; border-radius: 6px;
    gridline-color: $RAISED;
}
QHeaderView::section {
    background: $PANEL; color: $GOLD; border: none;
    border-bottom: 1px solid $BORDER; padding: 5px; font-weight: 600;
}
QToolTip { background: $PANEL; color: $TEXT; border: 1px solid $SCARLET; }
""").substitute(globals())


def dark_palette():
    # The base colours every widget starts from (the stylesheet adds detail).
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BG))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(BG))
    palette.setColor(QPalette.AlternateBase, QColor(PANEL))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor(RAISED))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.Highlight, QColor(SCARLET))
    palette.setColor(QPalette.HighlightedText, QColor(TEXT))
    palette.setColor(QPalette.ToolTipBase, QColor(PANEL))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT))
    return palette


# --- Live preview widgets -------------------------------------------------------

class AxisBar(QWidget):
    # A bar for one value. centred=True: -1..1 filling out from the middle
    # (sticks). centred=False: 0..1 filling from the left (triggers).
    def __init__(self, centred=True, colour=GOLD):
        super().__init__()
        self.centred = centred
        self.colour = QColor(colour)
        self.value = 0.0
        self.setFixedHeight(16)
        self.setMinimumWidth(140)

    def set_value(self, value):
        if value != self.value:
            self.value = value
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(BORDER)))
        p.setBrush(QColor(BG))
        p.drawRoundedRect(rect, 4, 4)

        p.setPen(Qt.NoPen)
        p.setBrush(self.colour)
        if self.centred:
            middle = rect.center().x()
            width = self.value * (rect.width() / 2 - 2)
            fill = QRectF(middle, rect.top() + 2, width, rect.height() - 4).normalized()
            p.drawRoundedRect(fill, 2, 2)
            p.setPen(QPen(QColor(DIM)))
            p.drawLine(QPointF(middle, rect.top() + 2), QPointF(middle, rect.bottom() - 2))
        else:
            fill = QRectF(rect.left() + 2, rect.top() + 2,
                          self.value * (rect.width() - 4), rect.height() - 4)
            p.drawRoundedRect(fill, 2, 2)


class StickBox(QWidget):
    # A square with a dot: where the Xbox left stick is (like Dolphin's In/Out).
    def __init__(self):
        super().__init__()
        self.x_value = 0.0
        self.y_value = 0.0
        self.setFixedSize(110, 110)

    def set_position(self, x, y):
        if (x, y) != (self.x_value, self.y_value):
            self.x_value = x
            self.y_value = y
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(BORDER)))
        p.setBrush(QColor(BG))
        p.drawRoundedRect(rect, 6, 6)
        p.setPen(QPen(QColor(RAISED)))
        p.drawEllipse(rect.adjusted(6, 6, -6, -6))
        c = rect.center()
        p.drawLine(QPointF(c.x(), rect.top() + 6), QPointF(c.x(), rect.bottom() - 6))
        p.drawLine(QPointF(rect.left() + 6, c.y()), QPointF(rect.right() - 6, c.y()))

        # Stick up = positive, but screen y grows downwards: hence the minus.
        radius = rect.width() / 2 - 10
        dot = QPointF(c.x() + self.x_value * radius, c.y() - self.y_value * radius)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(GOLD))
        p.drawEllipse(dot, 5, 5)


# --- One binding-sheet picture with its dropdowns ------------------------------

class SheetPicture(QWidget):
    # The VKB picture, with a dropdown sitting on every numbered box.
    # `bindings` is settings["buttons"]["left"] (or "right") itself, so picking
    # something in a dropdown changes the settings straight away.
    def __init__(self, picture_path, boxes, bindings, on_change):
        super().__init__()
        self.bindings = bindings
        self.on_change = on_change
        self.dropdowns = {}  # sheet number -> its QComboBox
        self.lit = set()  # sheet numbers drawn as "pressed" right now

        # The picture, shrunk.
        pixmap = QPixmap(str(picture_path))
        width = int(sheets.SHEET_WIDTH * PICTURE_SCALE)
        pixmap = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        picture = QLabel(self)
        picture.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())

        # The sheet was measured at 2000 px wide; we draw it at `width`.
        scale = width / sheets.SHEET_WIDTH
        for number, (left, top, right, bottom) in boxes.items():
            dropdown = QComboBox(self)
            for name, label in XBOX_LABELS.items():
                dropdown.addItem(label, name)  # shows `label`, remembers `name`
            current = bindings.get(str(number), "")
            dropdown.setCurrentIndex(dropdown.findData(current))
            dropdown.setToolTip(f"VKB button {number}")

            # Leave the printed number on the sheet visible on the left.
            number_space = 24 if number < 10 else 34
            x = int(left * scale) + int(number_space * scale) + 4
            y = int(top * scale) + 3
            w = int((right - left) * scale) - int(number_space * scale) - 7
            h = min(int((bottom - top) * scale) - 6, 22)
            dropdown.setGeometry(x, y, w, h)

            dropdown.currentIndexChanged.connect(
                lambda index, n=number: self.picked(n)
            )
            self.dropdowns[number] = dropdown
            self.restyle(number)

    def picked(self, number):
        # A dropdown changed: write it into the settings (or remove it).
        name = self.dropdowns[number].currentData()
        if name == "":
            self.bindings.pop(str(number), None)
        else:
            self.bindings[str(number)] = name
        self.restyle(number)
        self.on_change()

    def restyle(self, number):
        # Colour the dropdown by its Xbox button; gold while its VKB button is held.
        dropdown = self.dropdowns[number]
        name = dropdown.currentData()
        held = number in self.lit
        border = PRESSED_COLOUR if held else BORDER
        width = 3 if held else 1
        if name == "" and held:
            background, text = PRESSED_COLOUR, ON_GOLD  # unbound but held: fill it
        elif name == "":
            background, text = "#f6f8fa", "#57606a"  # light grey, on the white sheet
        else:
            background, text = XBOX_COLOURS.get(name, OTHER_COLOUR), "#ffffff"
        dropdown.setStyleSheet(
            f"QComboBox {{ background: {background}; color: {text};"
            f" border: {width}px solid {border}; border-radius: 4px;"
            f" padding: 0 4px; font-size: 9pt; font-weight: 600; }}"
            f" QComboBox::drop-down {{ width: 12px; border: none; }}"
            f" QComboBox QAbstractItemView {{ background: {PANEL}; color: {TEXT};"
            f" font-weight: 400; }}"
        )

    def set_bindings(self, bindings):
        # A profile was loaded: point at its bindings and update every dropdown.
        self.bindings = bindings
        for number, dropdown in self.dropdowns.items():
            dropdown.blockSignals(True)
            dropdown.setCurrentIndex(dropdown.findData(bindings.get(str(number), "")))
            dropdown.blockSignals(False)
            self.restyle(number)

    def light_up(self, pressed):
        # Outline the boxes whose VKB button is held. Only restyles the ones
        # that changed, so it's cheap enough to call 100 times a second.
        pressed = {n for n in pressed if n in self.dropdowns}
        changed = pressed ^ self.lit
        self.lit = pressed
        for number in changed:
            self.restyle(number)


# --- Home page: everything about the connected devices --------------------------

def make_card(title):
    # A small box with a grey title and a big value under it.
    # Hands back (the card, the value label) so the value can be changed later.
    card = QFrame()
    card.setObjectName("card")  # the stylesheet's QFrame#card
    layout = QVBoxLayout(card)
    heading = QLabel(title)
    heading.setStyleSheet(f"color: {MUTED}; font-size: 9pt;")
    value = QLabel("—")
    value.setStyleSheet("font-size: 13pt; font-weight: 600;")
    layout.addWidget(heading)
    layout.addWidget(value)
    return card, value


DEVICE_COLUMNS = ["#", "Name", "Used as", "VID:PID", "Axes", "Buttons", "Hats", "Power", "GUID"]


class HomePage(QWidget):
    # The first tab: what's plugged in, what PodSim does with it, and a live
    # tester for one device (like Windows' joy.cpl, but showing sheet numbers).
    def __init__(self, window):
        super().__init__()
        self.window = window  # the MainWindow, for its settings and binder
        self.devices = []  # pygame Joystick objects, one per table row
        self.device_ids = []  # their instance ids, to spot plug/unplug

        page = QVBoxLayout(self)

        # --- Summary cards ---
        cards = QHBoxLayout()
        driver_card, self.driver_value = make_card("ViGEmBus driver")
        pad_card, self.pad_value = make_card("Virtual Xbox pad")
        profile_card, self.profile_value = make_card("Profile")
        mode_card, self.mode_value = make_card("Steering mode")
        bound_card, self.bound_value = make_card("Buttons bound")
        # Shown only while the driver is missing (see refresh).
        self.install_button = QPushButton("Install driver")
        self.install_button.clicked.connect(window.install_driver)
        driver_card.layout().addWidget(self.install_button)
        for card in (driver_card, pad_card, profile_card, mode_card, bound_card):
            cards.addWidget(card)
        page.addLayout(cards)

        # --- Device table ---
        devices_box = QGroupBox("Connected devices")
        devices_layout = QVBoxLayout(devices_box)
        self.table = QTableWidget(0, len(DEVICE_COLUMNS))
        self.table.setHorizontalHeaderLabels(DEVICE_COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name takes the rest
        self.table.setMinimumHeight(150)
        self.table.itemSelectionChanged.connect(self.show_selected)
        devices_layout.addWidget(self.table)
        self.empty_hint = QLabel(
            "No controllers found. Plug in your sticks — they appear here within a second."
        )
        self.empty_hint.setStyleSheet(f"color: {WARNING};")
        devices_layout.addWidget(self.empty_hint)
        page.addWidget(devices_box)

        # --- Live tester for the selected device ---
        details = QGroupBox("Selected device  ·  live")
        grid = QGridLayout(details)
        self.selected_name = QLabel("Click a device in the table above.")
        self.selected_name.setStyleSheet("font-size: 12pt; font-weight: 600;")
        grid.addWidget(self.selected_name, 0, 0, 1, 3)

        self.axis_bars = []
        self.axis_values = []
        for axis in range(8):  # each VKB reports 8 axes
            name = QLabel(f"Axis {axis}")
            bar = AxisBar()
            value = QLabel("")
            value.setMinimumWidth(50)
            grid.addWidget(name, axis + 1, 0)
            grid.addWidget(bar, axis + 1, 1)
            grid.addWidget(value, axis + 1, 2)
            self.axis_bars.append((name, bar))
            self.axis_values.append(value)

        info = QFormLayout()
        self.pressed_label = QLabel("—")
        self.pressed_label.setWordWrap(True)
        self.pressed_label.setStyleSheet(f"color: {PRESSED_COLOUR}; font-weight: 600;")
        self.hats_label = QLabel("—")
        self.role_label = QLabel("—")
        info.addRow("Buttons held (sheet numbers):", self.pressed_label)
        info.addRow("Hats:", self.hats_label)
        info.addRow("Used as:", self.role_label)
        use_row = QHBoxLayout()
        self.use_left = QPushButton("Use as left stick")
        self.use_right = QPushButton("Use as right stick")
        self.use_left.clicked.connect(lambda: self.use_as("left_stick"))
        self.use_right.clicked.connect(lambda: self.use_as("right_stick"))
        use_row.addWidget(self.use_left)
        use_row.addWidget(self.use_right)
        use_row.addStretch()
        info.addRow(use_row)
        tips = QLabel(
            "Tips: push a stick forward and watch which axis moves — that's your "
            "thrust axis. Twist it to find the twist axis. Press a button to see its "
            "number on the binding sheet."
        )
        tips.setWordWrap(True)
        tips.setStyleSheet(f"color: {MUTED};")
        info.addRow(tips)
        grid.addLayout(info, 1, 3, 8, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setRowStretch(9, 1)  # an empty row under everything soaks up spare space
        page.addWidget(details, stretch=1)

        self.driver_ok = vigem_driver_installed()  # asked once: it rarely changes
        self.show_selected()

    # --- What each device is used for ------------------------------------------

    def role_of(self, stick):
        name = stick.get_name()
        settings = self.window.settings
        if name.endswith(settings["left_stick"]):
            return "Left stick (gas/brake)"
        if name.endswith(settings["right_stick"]):
            return "Right stick (steering)"
        lower = name.lower()
        if "xbox" in lower or "xinput" in lower:
            return "Xbox pad (PodSim's output while running)"
        return "Not used"

    def use_as(self, key):
        # Remember the selected device's full name as the left/right stick.
        # (find_stick checks name.endswith(...), and a full name ends with itself.)
        stick = self.selected()
        if stick is None:
            return
        self.window.change_setting(key, stick.get_name())
        self.window.scan_sticks()
        self.refresh()

    # --- Refreshing --------------------------------------------------------------

    def refresh(self):
        # Once a second: summary cards + device table.
        w = self.window
        if not self.driver_ok:
            # Missing: ask Windows again every second, so the card turns
            # "Installed" by itself once the installer has finished.
            self.driver_ok = vigem_driver_installed()
        self.install_button.setVisible(not self.driver_ok)
        self.driver_value.setText("● Installed" if self.driver_ok else "● Missing")
        self.driver_value.setStyleSheet(
            "font-size: 13pt; font-weight: 600; color: "
            + (f"{GOLD};" if self.driver_ok else f"{ERROR};")
        )
        self.pad_value.setText("● On" if w.running else "○ Off (press Start)")
        self.profile_value.setText(w.settings.get("profile", "—"))
        self.mode_value.setText(STEERING_MODES[w.settings["steering_mode"]])
        buttons = w.settings["buttons"]
        self.bound_value.setText(f"{len(buttons['left'])} left  ·  {len(buttons['right'])} right")

        devices = all_devices()
        ids = [stick.get_instance_id() for stick in devices]
        if ids != self.device_ids:
            # Something was plugged in or out: rebuild the table, keeping the
            # same device selected if it is still there.
            old = self.selected()
            old_id = old.get_instance_id() if old is not None else None
            self.devices = devices
            self.device_ids = ids
            self.table.setRowCount(len(devices))
            for row, stick in enumerate(devices):
                vendor, product = vid_pid_from_guid(stick.get_guid())
                vid_pid = f"{vendor}:{product}" if vendor else "?"
                cells = [
                    str(row), stick.get_name(), "", vid_pid,
                    str(stick.get_numaxes()), str(stick.get_numbuttons()),
                    str(stick.get_numhats()), stick.get_power_level(), stick.get_guid(),
                ]
                for column, text in enumerate(cells):
                    self.table.setItem(row, column, QTableWidgetItem(text))
            if old_id in ids:
                self.table.selectRow(ids.index(old_id))
            elif devices:
                self.table.selectRow(0)
            self.empty_hint.setVisible(not devices)

        # The "Used as" column can change without a plug/unplug.
        for row, stick in enumerate(self.devices):
            role = self.role_of(stick)
            item = self.table.item(row, 2)
            if item.text() != role:
                item.setText(role)
                colour = GOLD if role.startswith(("Left", "Right")) else MUTED
                item.setForeground(QColor(colour))
        self.show_selected()

    def selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows or rows[0].row() >= len(self.devices):
            return None
        return self.devices[rows[0].row()]

    def show_selected(self):
        # The parts of the tester that only change when the selection does.
        stick = self.selected()
        enabled = stick is not None
        self.use_left.setEnabled(enabled)
        self.use_right.setEnabled(enabled)
        if stick is None:
            self.selected_name.setText("Click a device in the table above.")
            self.role_label.setText("—")
            for name, bar in self.axis_bars:
                name.setEnabled(False)
                bar.set_value(0.0)
            return
        self.selected_name.setText(stick.get_name())
        self.role_label.setText(self.role_of(stick))
        for axis, (name, bar) in enumerate(self.axis_bars):
            name.setEnabled(axis < stick.get_numaxes())

    def live(self):
        # ~30 times a second while the Home tab is showing: the moving parts.
        stick = self.selected()
        if stick is None or not self.isVisible():
            return
        pygame.event.pump()
        try:
            for axis, (name, bar) in enumerate(self.axis_bars):
                if axis < stick.get_numaxes():
                    value = stick.get_axis(axis)
                    bar.set_value(value)
                    self.axis_values[axis].setText(f"{value:+.2f}")
                else:
                    bar.set_value(0.0)
                    self.axis_values[axis].setText("")
            pressed = [
                str(index + 1)  # sheet numbers, like everywhere else
                for index in range(stick.get_numbuttons())
                if stick.get_button(index)
            ]
            hats = [str(stick.get_hat(hat)) for hat in range(stick.get_numhats())]
        except pygame.error:
            return  # unplugged: the next refresh() removes it from the table
        self.pressed_label.setText(", ".join(pressed) if pressed else "—")
        self.hats_label.setText("  ".join(hats) if hats else "none")


# --- The main window -------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # add_missing: config files from older versions don't have the newest keys.
        self.settings = add_missing(load_settings(CONFIG_PATH))
        self.binder = Binder(self.settings)  # shares the same dictionary
        self.running = False
        self.unsaved = False
        self.laps_waiting = 0  # counts laps while waiting for a stick

        # First run: no profiles yet, so save the current settings as "Default".
        if not list_profiles(PROFILES_FOLDER):
            self.settings["profile"] = "Default"
            PROFILES_FOLDER.mkdir(exist_ok=True)
            save_settings(PROFILES_FOLDER / "Default.json", self.settings)
            save_settings(CONFIG_PATH, self.settings)

        self.setWindowTitle(f"PodSim v{VERSION}")

        # The window is a column: top bar, then (pictures | side panel),
        # then the bottom bar.
        page = QWidget()
        column = QVBoxLayout(page)
        column.addLayout(self.build_top_bar())
        middle = QHBoxLayout()
        middle.addWidget(self.build_tabs(), stretch=1)
        middle.addLayout(self.build_side_panel())
        column.addLayout(middle, stretch=1)
        column.addLayout(self.build_bottom_bar())
        self.setCentralWidget(page)

        # Timer 1: the binder loop, every 10 ms (~100 a second) while running.
        self.loop_timer = QTimer(self)
        self.loop_timer.setInterval(10)
        self.loop_timer.timeout.connect(self.lap)

        # Timer 2: while NOT running, check once a second which sticks are in.
        self.scan_timer = QTimer(self)
        self.scan_timer.setInterval(1000)
        self.scan_timer.timeout.connect(self.scan_sticks)
        self.scan_timer.start()
        self.scan_sticks()

        # Timer 3: the Home page. Cards and device table once a second,
        # the live tester ~30 times a second (it skips itself when hidden).
        self.home_timer = QTimer(self)
        self.home_timer.setInterval(1000)
        self.home_timer.timeout.connect(self.home.refresh)
        self.home_timer.start()
        self.live_timer = QTimer(self)
        self.live_timer.setInterval(33)
        self.live_timer.timeout.connect(self.home.live)
        self.live_timer.start()
        self.home.refresh()

    # --- Building the window -------------------------------------------------

    def build_top_bar(self):
        row = QHBoxLayout()

        sticks = QGroupBox("Sticks")
        sticks_layout = QHBoxLayout(sticks)
        self.left_status = QLabel()
        self.right_status = QLabel()
        sticks_layout.addWidget(QLabel("Left:"))
        sticks_layout.addWidget(self.left_status)
        sticks_layout.addSpacing(30)
        sticks_layout.addWidget(QLabel("Right:"))
        sticks_layout.addWidget(self.right_status)
        sticks_layout.addStretch()
        row.addWidget(sticks, stretch=1)

        # Profiles, like Dolphin's Profile box. The dropdown is "editable":
        # type a new name in it, then "Save as" to make a new profile.
        profile_box = QGroupBox("Profile")
        profile_layout = QHBoxLayout(profile_box)
        self.profile_list = QComboBox()
        self.profile_list.setEditable(True)
        self.profile_list.setMinimumWidth(180)
        self.fill_profile_list()
        load_button = QPushButton("Load")
        save_as_button = QPushButton("Save as")
        delete_button = QPushButton("Delete")
        load_button.clicked.connect(self.load_profile)
        save_as_button.clicked.connect(self.save_profile_as)
        delete_button.clicked.connect(self.delete_profile)
        profile_layout.addWidget(self.profile_list)
        profile_layout.addWidget(load_button)
        profile_layout.addWidget(save_as_button)
        profile_layout.addWidget(delete_button)
        row.addWidget(profile_box)

        binder_box = QGroupBox("Binder")
        binder_layout = QHBoxLayout(binder_box)
        self.start_button = QPushButton("▶  Start")
        self.start_button.setObjectName("start")  # the stylesheet's #start
        self.start_button.setMinimumSize(130, 34)
        self.start_button.clicked.connect(self.start_or_stop)
        self.status = QLabel("Stopped")
        self.status.setMinimumWidth(230)
        binder_layout.addWidget(self.start_button)
        binder_layout.addWidget(self.status)
        row.addWidget(binder_box)
        return row

    def build_tabs(self):
        tabs = QTabWidget()
        self.tabs = tabs
        self.home = HomePage(self)
        tabs.addTab(self.home, "Home")
        buttons = self.settings["buttons"]
        self.left_sheet = SheetPicture(
            sheets.LEFT_PICTURE, sheets.LEFT_BOXES, buttons["left"], self.mark_unsaved
        )
        self.right_sheet = SheetPicture(
            sheets.RIGHT_PICTURE, sheets.RIGHT_BOXES, buttons["right"], self.mark_unsaved
        )
        # A scroll area, in case the window is smaller than the picture.
        for sheet, title in (
            (self.left_sheet, "Left stick  ·  Gladiator NXT EVO Omni"),
            (self.right_sheet, "Right stick  ·  Gladiator NXT EVO"),
        ):
            scroll = QScrollArea()
            scroll.setWidget(sheet)
            scroll.setAlignment(Qt.AlignCenter)
            scroll.setStyleSheet("QScrollArea { background: #ffffff; }")
            tabs.addTab(scroll, title)
        return tabs

    def build_side_panel(self):
        side = QVBoxLayout()

        # --- Steering settings ---
        steering = QGroupBox("Steering")
        form = QFormLayout(steering)
        self.mode = QComboBox()
        for name, label in STEERING_MODES.items():
            self.mode.addItem(label, name)
        self.mode.setCurrentIndex(self.mode.findData(self.settings["steering_mode"]))
        self.mode.currentIndexChanged.connect(self.mode_changed)
        form.addRow("Mode", self.mode)
        self.mode_help = QLabel()
        self.mode_help.setStyleSheet(f"color: {MUTED}; font-size: 9pt;")
        form.addRow(self.mode_help)

        self.thrust_axis = QSpinBox()
        self.thrust_axis.setRange(0, 7)  # each VKB reports 8 axes: 0..7
        self.thrust_axis.setValue(self.settings["thrust_axis"])
        self.thrust_axis.valueChanged.connect(
            lambda value: self.change_setting("thrust_axis", value)
        )
        form.addRow("Thrust axis (both)", self.thrust_axis)

        self.steer_axis = QSpinBox()
        self.steer_axis.setRange(0, 7)
        self.steer_axis.setValue(self.settings["steer_axis"])
        self.steer_axis.valueChanged.connect(
            lambda value: self.change_setting("steer_axis", value)
        )
        form.addRow("Steer axis (right)", self.steer_axis)

        self.deadzone = QDoubleSpinBox()
        self.deadzone.setRange(0.0, 0.5)
        self.deadzone.setSingleStep(0.01)
        self.deadzone.setValue(self.settings["deadzone"])
        self.deadzone.valueChanged.connect(
            lambda value: self.change_setting("deadzone", round(value, 2))
        )
        form.addRow("Deadzone", self.deadzone)
        side.addWidget(steering)

        # --- Pitch: nose up/down (the Xbox left stick's up/down) ---
        pitch = QGroupBox("Pitch  ·  nose up/down")
        self.pitch_box = pitch
        pitch_form = QFormLayout(pitch)
        self.pitch_stick = QComboBox()
        for name, label in PITCH_STICKS.items():
            self.pitch_stick.addItem(label, name)
        # Each steering mode has its own pitch stick and axis: pitch_keys()
        # says which settings these two boxes show right now.
        self.pitch_stick.currentIndexChanged.connect(
            lambda index: self.change_setting(
                pitch_keys(self.settings["steering_mode"])[0], self.pitch_stick.currentData()
            )
        )
        pitch_form.addRow("Stick", self.pitch_stick)

        self.pitch_axis = QSpinBox()
        self.pitch_axis.setRange(0, 7)
        self.pitch_axis.valueChanged.connect(
            lambda value: self.change_setting(pitch_keys(self.settings["steering_mode"])[1], value)
        )
        pitch_form.addRow("Axis", self.pitch_axis)

        self.pitch_invert = QCheckBox("Invert (swap up and down)")
        self.pitch_invert.setChecked(self.settings["pitch_invert"])
        self.pitch_invert.toggled.connect(
            lambda checked: self.change_setting("pitch_invert", checked)
        )
        pitch_form.addRow(self.pitch_invert)

        self.pitch_help = QLabel()
        self.pitch_help.setWordWrap(True)
        pitch_form.addRow(self.pitch_help)
        side.addWidget(pitch)

        # --- Live: what comes in from the VKBs ---
        live_in = QGroupBox("In  ·  VKB sticks")
        in_form = QFormLayout(live_in)
        self.left_thrust_bar = AxisBar()
        self.right_thrust_bar = AxisBar()
        self.right_steer_bar = AxisBar()
        in_form.addRow("Left thrust", self.left_thrust_bar)
        in_form.addRow("Right thrust", self.right_thrust_bar)
        in_form.addRow("Right steer", self.right_steer_bar)
        self.pitch_bar = AxisBar()
        in_form.addRow("Pitch", self.pitch_bar)
        side.addWidget(live_in)

        # --- Live: what goes out to the Xbox pad ---
        live_out = QGroupBox("Out  ·  Xbox pad")
        out_layout = QHBoxLayout(live_out)
        stick_column = QVBoxLayout()
        self.stick_box = StickBox()
        stick_column.addWidget(self.stick_box)
        caption = QLabel("Left stick")
        caption.setAlignment(Qt.AlignCenter)
        caption.setStyleSheet(f"color: {MUTED}; font-size: 9pt;")
        stick_column.addWidget(caption)
        out_layout.addLayout(stick_column)
        trigger_form = QFormLayout()
        self.rt_bar = AxisBar(centred=False, colour=GOLD)
        self.lt_bar = AxisBar(centred=False, colour=SCARLET_HOT)
        self.rt_bar.setMinimumWidth(90)
        self.lt_bar.setMinimumWidth(90)
        trigger_form.addRow("RT", self.rt_bar)
        trigger_form.addRow("LT", self.lt_bar)
        self.held_label = QLabel("—")
        self.held_label.setWordWrap(True)
        trigger_form.addRow("Held", self.held_label)
        out_layout.addLayout(trigger_form)
        side.addWidget(live_out)

        side.addStretch()  # push everything above to the top
        self.show_mode()  # fill in the help text and greying-out
        return side

    def build_bottom_bar(self):
        row = QHBoxLayout()
        hint = QLabel(
            "Pick an Xbox button on any numbered box. While running, "
            "holding a VKB button lights its box up in gold."
        )
        hint.setStyleSheet(f"color: {MUTED};")
        row.addWidget(hint, stretch=1)
        self.saved_label = QLabel()
        row.addWidget(self.saved_label)
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("save")  # the stylesheet's #save
        self.save_button.setMinimumWidth(110)
        self.save_button.clicked.connect(self.save)
        row.addWidget(self.save_button)
        self.show_saved_state()
        return row

    # --- Settings changes ----------------------------------------------------

    def change_setting(self, key, value):
        # Every spin box ends up here. Because the binder shares this
        # dictionary, a running binder uses the new value on its next lap.
        self.settings[key] = value
        self.mark_unsaved()
        self.show_pitch()

    def mode_changed(self):
        self.change_setting("steering_mode", self.mode.currentData())
        self.show_mode()

    def show_mode(self):
        # Help text for the mode, and grey out what it doesn't use.
        mode = self.mode.currentData()
        self.mode_help.setText(MODE_HELP[mode])
        # Podracer mode doesn't use the right stick's left/right at all.
        self.steer_axis.setEnabled(mode == "right_stick")
        self.show_pitch_values()

    def show_pitch_values(self):
        # Put THIS mode's pitch stick and axis into the two boxes. Signals are
        # blocked: showing a value isn't the user changing it.
        s = self.settings
        stick_key, axis_key = pitch_keys(s["steering_mode"])
        for widget in (self.pitch_stick, self.pitch_axis):
            widget.blockSignals(True)
        self.pitch_stick.setCurrentIndex(self.pitch_stick.findData(s[stick_key]))
        self.pitch_axis.setValue(s[axis_key])
        for widget in (self.pitch_stick, self.pitch_axis):
            widget.blockSignals(False)
        self.pitch_box.setTitle(f"Pitch  ·  nose up/down  ·  {STEERING_MODES[s['steering_mode']]}")
        self.show_pitch()

    def show_pitch(self):
        # Grey out the axis when pitch is off, and warn about a clash.
        # (show_mode calls this while the window is still being built,
        # before the pitch widgets exist: hence the hasattr check.)
        if not hasattr(self, "pitch_help"):
            return
        s = self.settings
        mode = s["steering_mode"]
        stick_key, axis_key = pitch_keys(mode)
        off = s[stick_key] == "off"
        self.pitch_axis.setEnabled(not off)
        self.pitch_invert.setEnabled(not off)
        clash = pitch_clash(mode, s[stick_key], s[axis_key], s["thrust_axis"], s["steer_axis"])
        if off:
            self.pitch_help.setText("Pitch is off: the nose is left alone.")
            self.pitch_help.setStyleSheet(f"color: {MUTED}; font-size: 9pt;")
        elif clash:
            self.pitch_help.setText(
                f"⚠ That axis already does {clash}, so pitch is OFF until you "
                "pick another one (the Home tab shows which axis moves)."
            )
            self.pitch_help.setStyleSheet(f"color: {WARNING}; font-size: 9pt;")
        else:
            self.pitch_help.setText(
                "Moves the Xbox left stick up/down. "
                "Nose going the wrong way? Tick Invert."
            )
            self.pitch_help.setStyleSheet(f"color: {MUTED}; font-size: 9pt;")

    def mark_unsaved(self):
        self.unsaved = True
        self.show_saved_state()

    def show_saved_state(self):
        self.save_button.setEnabled(self.unsaved)
        if self.unsaved:
            self.saved_label.setText("● Unsaved changes")
            self.saved_label.setStyleSheet(f"color: {WARNING};")
            self.setWindowTitle(f"PodSim v{VERSION} *")
        else:
            self.saved_label.setText("Saved")
            self.saved_label.setStyleSheet(f"color: {MUTED};")
            self.setWindowTitle(f"PodSim v{VERSION}")

    def save(self):
        # Save to config.json (what podsim.py uses) AND to the active profile.
        save_settings(CONFIG_PATH, self.settings)
        profile = self.settings.get("profile")
        if profile:
            PROFILES_FOLDER.mkdir(exist_ok=True)
            save_settings(PROFILES_FOLDER / f"{profile}.json", self.settings)
        self.unsaved = False
        self.show_saved_state()

    # --- Profiles --------------------------------------------------------------

    def fill_profile_list(self):
        # Refill the dropdown from the profiles folder, showing the active one.
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        self.profile_list.addItems(list_profiles(PROFILES_FOLDER))
        self.profile_list.setCurrentText(self.settings.get("profile", ""))
        self.profile_list.blockSignals(False)

    def typed_profile_name(self):
        return clean_profile_name(self.profile_list.currentText())

    def load_profile(self):
        name = self.typed_profile_name()
        path = PROFILES_FOLDER / f"{name}.json"
        if not name or not path.exists():
            QMessageBox.warning(self, "PodSim", f"There is no profile called “{name}”.")
            return
        if self.unsaved:
            answer = QMessageBox.question(
                self, "PodSim",
                f"Load “{name}”? Your unsaved changes will be lost.",
            )
            if answer != QMessageBox.Yes:
                return
        new_settings = add_missing(load_settings(path))
        new_settings["profile"] = name
        # Change the dictionary IN PLACE (clear + update) instead of making a
        # new one: the binder holds this same dictionary, so a running binder
        # switches to the new profile on its next lap.
        self.settings.clear()
        self.settings.update(new_settings)
        save_settings(CONFIG_PATH, self.settings)  # it's now the active one
        self.show_settings()
        self.unsaved = False
        self.show_saved_state()
        self.scan_sticks()
        self.home.refresh()

    def save_profile_as(self):
        name = self.typed_profile_name()
        if not name:
            QMessageBox.warning(self, "PodSim", "Type a name for the profile first.")
            return
        path = PROFILES_FOLDER / f"{name}.json"
        if path.exists() and name != self.settings.get("profile"):
            answer = QMessageBox.question(
                self, "PodSim", f"“{name}” already exists. Replace it?"
            )
            if answer != QMessageBox.Yes:
                return
        self.settings["profile"] = name
        self.save()  # writes config.json and profiles/<name>.json
        self.fill_profile_list()
        self.home.refresh()

    def delete_profile(self):
        name = self.typed_profile_name()
        path = PROFILES_FOLDER / f"{name}.json"
        if not name or not path.exists():
            QMessageBox.warning(self, "PodSim", f"There is no profile called “{name}”.")
            return
        answer = QMessageBox.question(self, "PodSim", f"Delete the profile “{name}”?")
        if answer != QMessageBox.Yes:
            return
        path.unlink()  # delete the file
        if self.settings.get("profile") == name:
            # The active settings stay as they are, just not tied to a profile.
            self.settings.pop("profile")
            self.mark_unsaved()
        self.fill_profile_list()
        self.home.refresh()

    def show_settings(self):
        # Put every setting from the dictionary back into the widgets
        # (after loading a profile). Signals are blocked so this doesn't
        # count as "the user changed something".
        widgets = (
            self.mode, self.thrust_axis, self.steer_axis, self.deadzone,
            self.pitch_invert,
        )
        for widget in widgets:
            widget.blockSignals(True)
        self.mode.setCurrentIndex(self.mode.findData(self.settings["steering_mode"]))
        self.thrust_axis.setValue(self.settings["thrust_axis"])
        self.steer_axis.setValue(self.settings["steer_axis"])
        self.deadzone.setValue(self.settings["deadzone"])
        self.pitch_invert.setChecked(self.settings["pitch_invert"])
        for widget in widgets:
            widget.blockSignals(False)
        self.show_mode()
        self.left_sheet.set_bindings(self.settings["buttons"]["left"])
        self.right_sheet.set_bindings(self.settings["buttons"]["right"])
        self.fill_profile_list()

    # --- Sticks --------------------------------------------------------------

    def scan_sticks(self):
        # Runs once a second while stopped (and while waiting): who is in?
        self.binder.find_sticks()
        self.show_sticks()

    def show_sticks(self):
        self.show_stick(self.left_status, self.binder.left)
        self.show_stick(self.right_status, self.binder.right)

    def show_stick(self, label, stick):
        if stick is None:
            label.setText("● not found")
            label.setStyleSheet(f"color: {ERROR};")
        else:
            label.setText(f"● {stick.get_name()}")
            label.setStyleSheet(f"color: {GOLD};")

    # --- Start / stop and the loop -----------------------------------------------

    def start_or_stop(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if not vigem_driver_installed():
            answer = QMessageBox.question(
                self, "PodSim",
                "The ViGEmBus driver isn't installed. PodSim needs it to make "
                "the virtual Xbox pad.\n\nInstall it now?",
            )
            if answer == QMessageBox.Yes:
                self.install_driver()
            return
        try:
            self.binder.start()
        except Exception as error:  # usually: ViGEmBus driver not installed
            QMessageBox.critical(self, "PodSim", f"Couldn't create the Xbox pad:\n{error}")
            return
        self.running = True
        self.scan_timer.stop()
        self.scan_sticks()
        self.loop_timer.start()
        self.start_button.setText("■  Stop")
        self.show_running(True)
        self.home.refresh()

    def install_driver(self):
        # Run the ViGEmBus installer that ships inside PodSim. Windows asks
        # "allow changes?" first. The Home card turns "Installed" by itself.
        if install_vigem_driver():
            QMessageBox.information(
                self, "PodSim",
                "The driver installer is running. When it's finished, "
                "the ViGEmBus card on Home turns gold and Start works.",
            )
        else:
            QMessageBox.warning(
                self, "PodSim",
                "The driver installer didn't start (or Windows' question was "
                "answered No). Click Install driver on Home to try again.",
            )

    def stop(self):
        self.loop_timer.stop()
        self.binder.stop()
        self.running = False
        self.start_button.setText("▶  Start")
        self.show_running(False)
        self.status.setText("Stopped")
        self.status.setStyleSheet(f"color: {MUTED};")
        self.show_reading(None)
        self.scan_timer.start()
        self.home.refresh()

    def show_running(self, running):
        # Change the "running" property so the stylesheet turns the button red,
        # then tell Qt to re-read the stylesheet for it ("polish").
        self.start_button.setProperty("running", running)
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)

    def lap(self):
        # Called by loop_timer ~100 times a second while running.
        if self.binder.left is None or self.binder.right is None:
            # Waiting for a stick: only look once a second (every 100 laps).
            self.laps_waiting += 1
            if self.laps_waiting % 100 == 1:
                self.scan_sticks()
            self.status.setText("● Xbox pad on  ·  waiting for both sticks…")
            self.status.setStyleSheet(f"color: {WARNING};")
            return

        self.laps_waiting = 0
        reading = self.binder.step()
        if reading is None:  # a stick was unplugged mid-race
            self.show_sticks()
            self.show_reading(None)
            return
        self.status.setText("● Running  ·  Xbox pad is on")
        self.status.setStyleSheet(f"color: {GOLD};")
        self.show_reading(reading)

    def show_reading(self, reading):
        # Draw one lap's numbers on the live widgets (None = all at rest).
        if reading is None:
            reading = {
                "left_thrust": 0.0, "right_thrust": 0.0, "right_steer": 0.0,
                "steering": 0.0, "pitch_in": 0.0, "pitch": 0.0, "rt": 0.0, "lt": 0.0,
                "left_pressed": set(), "right_pressed": set(), "held": set(),
            }
        self.left_thrust_bar.set_value(reading["left_thrust"])
        self.right_thrust_bar.set_value(reading["right_thrust"])
        self.right_steer_bar.set_value(reading["right_steer"])
        self.pitch_bar.set_value(reading["pitch_in"])
        self.stick_box.set_position(reading["steering"], reading["pitch"])
        self.rt_bar.set_value(reading["rt"])
        self.lt_bar.set_value(reading["lt"])
        held = [XBOX_LABELS[name] for name in XBOX_BUTTONS if name in reading["held"]]
        self.held_label.setText(", ".join(held) if held else "—")
        self.left_sheet.light_up(reading["left_pressed"])
        self.right_sheet.light_up(reading["right_pressed"])

    # --- Closing -------------------------------------------------------------

    def closeEvent(self, event):
        # Qt calls this when the window's X is clicked.
        if self.unsaved:
            answer = QMessageBox.question(
                self, "PodSim", "Save your changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if answer == QMessageBox.Cancel:
                event.ignore()  # stay open
                return
            if answer == QMessageBox.Save:
                self.save()
        if self.running:
            self.stop()  # let go of everything and unplug the virtual pad
        event.accept()


# --- Main program ------------------------------------------------------------

def main():
    started = time.monotonic()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_dir() / "media" / "icon.ico")))
    app.setStyle("Fusion")  # Qt's plain modern style, which we then colour
    app.setPalette(dark_palette())
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    # Big enough for the whole picture, but never bigger than the screen.
    screen = app.primaryScreen().availableGeometry()
    window.resize(min(1560, screen.width()), min(1040, screen.height()))

    def reveal():
        if pyi_splash is not None:
            pyi_splash.close()
        window.show()

    # Keep the splash up for at least SPLASH_SECONDS in total.
    waited = time.monotonic() - started
    QTimer.singleShot(int(max(0, SPLASH_SECONDS - waited) * 1000), reveal)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
