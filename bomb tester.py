from tkinter import *
import tkinter
from threading import Thread
from time import sleep
from random import randint
import board
from adafruit_ht16k33.segments import Seg7x4
from digitalio import DigitalInOut, Direction, Pull
from adafruit_matrixkeypad import Matrix_Keypad

# constants
COUNTDOWN = 300
MAX_PASS_LEN = 11
STAR_CLEARS_PASS = True

# LCD Display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        window.after(500, window.attributes, '-fullscreen', 'True')
        self._timer = None
        self._button = None
        self.setup()

    def setup(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.pack(fill=BOTH, expand=True)
        self._ltimer = Label(self, bg="black", fg="white", font=("Courier New", 24), text="Time left: ")
        self._ltimer.grid(row=0, column=0, columnspan=2, sticky=W)
        self._lkeypad = Label(self, bg="black", fg="white", font=("Courier New", 24), text="Combination: ")
        self._lkeypad.grid(row=1, column=0, columnspan=2, sticky=W)
        self._lwires = Label(self, bg="black", fg="white", font=("Courier New", 24), text="Wires: ")
        self._lwires.grid(row=2, column=0, columnspan=2, sticky=W)
        self._lbutton = Label(self, bg="black", fg="white", font=("Courier New", 24), text="Button: ")
        self._lbutton.grid(row=3, column=0, columnspan=2, sticky=W)
        self._ltoggles = Label(self, bg="black", fg="white", font=("Courier New", 24), text="Toggles: ")
        self._ltoggles.grid(row=4, column=0, columnspan=2, sticky=W)
        self._lstatus = Label(self, bg="black", fg="green", font=("Courier New", 24), text="Status Normal")
        self._lstatus.grid(row=6, column=0, columnspan=2, sticky=W)

    def setTimer(self, timer):
        self._timer = timer

    def setButton(self, button):
        self._button = button

# Base Phase Thread
class PhaseThread(Thread):
    def __init__(self, name):
        super().__init__(name=name, daemon=True)
        self._running = False
        self._value = None

    def reset(self):
        self._value = None

# Timer Phase
class Timer(PhaseThread):
    def __init__(self, value, display, name="Timer"):
        super().__init__(name)
        self._value = value
        self._initial_value = value
        self._display = display
        self._paused = False

    def update(self):
        self._min = f"{self._value // 60}".zfill(2)
        self._sec = f"{self._value % 60}".zfill(2)

    def run(self):
        self._running = True
        while self._running:
            if not self._paused:
                self.update()
                self._display.print(str(self))
                sleep(1)
                if self._value == 0:
                    break
                self._value -= 1
            else:
                sleep(0.1)
        self._running = False

    def pause(self):
        self._paused = not self._paused
        self._display.blink_rate = (2 if self._paused else 0)

    def __str__(self):
        return f"{self._min}:{self._sec}"

# Toggles Phase
class Toggles(PhaseThread):
    def __init__(self, pins, gui, name="Toggles"):
        super().__init__(name)
        self._value = ""
        self._pins = pins
        self._solution = "1000"
        self._gui = gui

    def run(self):
        self._running = True
        while self._running:
            self._value = "".join([str(int(pin.value)) for pin in self._pins])
            self._gui._ltoggles.config(text=f"Toggles: {self._value}")
            if self._value == self._solution:
                self._gui._ltoggles.config(text="Toggles: SOLVED!", fg="green")
                break
            sleep(0.1)
        self._running = False

# Button Phase
class Button(PhaseThread):
    def __init__(self, state, rgb, gui, name="Button"):
        super().__init__(name)
        self._value = False
        self._state = state
        self._rgb = rgb
        self._gui = gui
        self._color = "Green"

    def run(self):
        self._running = True
        while self._running:
            if self._state.value:
                if self._color == "Green":
                    self._gui._lbutton.config(text="Button: GREEN PRESSED", fg="green")
                else:
                    self._gui._lbutton.config(text="Button: WRONG ACTION!", fg="red")
            sleep(0.1)
        self._running = False

# Keypad Phase
class Keypad(PhaseThread):
    def __init__(self, keypad, gui, name="Keypad"):
        super().__init__(name)
        self._value = ""
        self._keypad = keypad
        self._solution = "782"
        self._gui = gui

    def run(self):
        self._running = True
        while self._running:
            if self._keypad.pressed_keys:
                key = self._keypad.pressed_keys[0]
                while self._keypad.pressed_keys:
                    sleep(0.1)
                if len(self._value) < len(self._solution):
                    self._value += str(key)
                self._gui._lkeypad.config(text=f"Combination: {self._value}")
                if self._value == self._solution:
                    self._gui._lkeypad.config(text="Keypad: SOLVED!", fg="green")
                    break
            sleep(0.1)
        self._running = False

# Wires Phase
class Wires(PhaseThread):
    def __init__(self, pins, gui, name="Wires"):
        super().__init__(name)
        self._value = ""
        self._pins = pins
        self._solution = [True, False, True, False]
        self._gui = gui

    def run(self):
        self._running = True
        while self._running:
            self._value = [pin.value for pin in self._pins]
            self._gui._lwires.config(text=f"Wires: {self._value}")
            if self._value == self._solution:
                self._gui._lwires.config(text="Wires: SOLVED!", fg="green")
                break
            sleep(0.1)
        self._running = False

# Game State Manager
class GameState:
    def __init__(self):
        self.current_phase = 1

    def next_phase(self):
        self.current_phase += 1

    def check_phase(self):
        if self.current_phase == 1:
            return toggles
        elif self.current_phase == 2:
            return button
        elif self.current_phase == 3:
            return keypad
        elif self.current_phase == 4:
            return wires
        return None

# Main Game Loop
def check():
    phase = game_state.check_phase()
    if timer._running:
        gui._ltimer.config(text=f"Time left: {timer}")
    else:
        gui._lstatus.config(text="BOMB EXPLODED!", fg="red")
        quit()
    gui.after(100, check)

# Initialize Components
window = Tk()
gui = Lcd(window)
i2c = board.I2C()
display = Seg7x4(i2c)
display.brightness = 0.5
timer = Timer(COUNTDOWN, display)
gui.setTimer(timer)

toggle_pins = [DigitalInOut(i) for i in (board.D12, board.D16, board.D20, board.D21)]
for pin in toggle_pins:
    pin.direction = Direction.INPUT
    pin.pull = Pull.DOWN
toggles = Toggles(toggle_pins, gui)

button_input = DigitalInOut(board.D4)
button_RGB = [DigitalInOut(i) for i in (board.D17, board.D27, board.D22)]
button_input.direction = Direction.INPUT
button_input.pull = Pull.DOWN
for pin in button_RGB:
    pin.direction = Direction.OUTPUT
    pin.value = True
button = Button(button_input, button_RGB, gui)
gui.setButton(button)

keypad_cols = [DigitalInOut(i) for i in (board.D10, board.D9, board.D11)]
keypad_rows = [DigitalInOut(i) for i in (board.D5, board.D6, board.D13, board.D19)]
keypad_keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ("*", 0, "#"))
matrix_keypad = Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)
keypad = Keypad(matrix_keypad, gui)

wire_pins = [DigitalInOut(i) for i in (board.D14, board.D15, board.D18, board.D23)]
for pin in wire_pins:
    pin.direction = Direction.INPUT
    pin.pull = Pull.DOWN
wires = Wires(wire_pins, gui)

timer.start()
toggles.start()
button.start()
keypad.start()
wires.start()

game_state = GameState()
check()
window.mainloop()
