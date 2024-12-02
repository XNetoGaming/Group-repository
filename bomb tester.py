from tkinter import *
import tkinter
import random
from threading import Thread
from time import sleep
from random import randint
import board
from adafruit_ht16k33.segments import Seg7x4
from digitalio import DigitalInOut, Direction, Pull
from adafruit_matrixkeypad import Matrix_Keypad

# Constants
COUNTDOWN = 300
MAX_PASS_LEN = 11
STAR_CLEARS_PASS = True

# LCD Display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        window.after(500, window.attributes, '-fullscreen', 'True')
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

        # Add equation label for binary multiplication
        self._equation_label = Label(self, bg="black", fg="white", font=("Courier New", 24), text="")
        self._equation_label.grid(row=5, column=0, columnspan=2, sticky=W)

        # New label for displaying the question
        self._lquestion = Label(self, bg="black", fg="white", font=("Courier New", 12), text="")
        self._lquestion.grid(row=7, column=0, columnspan=2, sticky=W)

        # New label for displaying the answer choices
        self._lwires_choices = Label(self, bg="black", fg="white", font=("Courier New", 18), text="")
        self._lwires_choices.grid(row=8, column=0, columnspan=2, sticky=W)

    def setTimer(self, timer):
        self._timer = timer

    def setButton(self, button):
        self._button = button

    def update_equation(self, equation):
        self._equation_label.config(text=f"Multiply: {equation[0]} x {equation[1]}")

    def setTimer(self, timer):
        self._timer = timer

    def display_question(self, question):
        self._lquestion.config(text=question)

    def display_choices(self, choices):
        self._lwires_choices.config(text="\n".join(choices))

# Base Phase Thread
class PhaseThread(Thread):
    def __init__(self, name):
        super().__init__(name=name, daemon=True)
        self._running = False

    def reset(self):
        self._value = None

# Timer Phase
class Timer(PhaseThread):
    def __init__(self, value, display, name="Timer"):
        super().__init__(name)
        self._value = value
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
                if self._value <= 0:
                    self._running = False
                    break
                self._value -= 1
            else:
                sleep(0.1)

    def pause(self):
        self._paused = not self._paused

    def __str__(self):
        return f"{self._min}:{self._sec}"

# Toggles Phase
class Toggles(PhaseThread):
    def __init__(self, pins, gui, name="Toggles"):
        super().__init__(name)
        self._value = ""
        self._pins = pins
        self._gui = gui
        self._solution, self._math_problem = self.generate_solution()  # Generate a binary solution based on a math problem
        self._gui._ltoggles.config(text=f"Toggles: Solve the equation: {self._math_problem}")

    def generate_solution(self):
        # Generate a random math problem and calculate the solution
        problems = [
            ("2 ** 3 + 3", 2 ** 3 + 3),  # 8 + 3 = 11
            ("4 * 3 - 2", 4 * 3 - 2),    # 12 - 2 = 10
            ("5 + 2 ** 2", 5 + 2 ** 2),   # 5 + 4 = 9
        ]
        self._math_problem, answer = random.choice(problems)
        # Convert the answer to a 4-digit binary string
        binary_solution = format(answer, '04b')
        return binary_solution, self._math_problem

    def run(self):
        self._running = True
        while self._running:
            self._value = "".join([str(int(pin.value)) for pin in self._pins])
            self._gui._ltoggles.config(text=f"Toggles: {self._value} | Solve: {self._math_problem}")
            if self._value == self._solution:
                self._gui._ltoggles.config(text="Toggles: SOLVED!", fg="green")
                break
            sleep(0.1)
# Button Phase
class Button(PhaseThread):
    colors = ["G", "B", "R"]  # the button's possible colors: Green, Blue, Red

    def __init__(self, state, rgb, gui, name="Button"):
        super().__init__(name)
        self._value = False
        self._state = state  # the pushbutton's state pin
        self._rgb = rgb  # the pushbutton's LED pins
        self._press_count = 0  # button press counter
        self._previous_state = False  # track previous state
        self._game_started = False  # track if the game has started
        self._gui = gui  # reference to the GUI for updating button status

    # runs the thread
    def run(self):
        self._running = True
        rgb_index = 0  # start with the first color (Green)
        rgb_counter = 0  # counter for color change timing

        while self._running:
            # Set the LED to the current color
            self._rgb[0].value = False if Button.colors[rgb_index] == "R" else True
            self._rgb[1].value = False if Button.colors[rgb_index] == "G" else True
            self._rgb[2].value = False if Button.colors[rgb_index] == "B" else True
            
            # Get the pushbutton's state
            current_state = self._state.value
            
            # Detect button press
            if current_state and not self._previous_state:
                self._press_count += 1
                self._value = True
                self.handle_button_press()  # Handle the button press logic
            elif not current_state:
                self._value = False
            
            # Update previous state to current state
            self._previous_state = current_state
            
            # Increment the RGB counter
            rgb_counter += 1
            
            # Switch to the next RGB color every 1s (10 * 0.1s = 1s)
            if rgb_counter == 10:
                rgb_index = (rgb_index + 1) % len(Button.colors)
                rgb_counter = 0
            
            sleep(0.1)

    def handle_button_press(self):
        current_time = time.time()
        
        # Check for double press
        if self._press_count == 1:
            if not self._game_started:  # If game hasn't started
                self.start_game()
            else:  # If game is running, resume
                self.resume_game()
        elif self._press_count == 2:
            if self._game_started:  # If game is running, pause
                self.pause_game()

    def start_game(self):
        self._game_started = True
        self.change_button_color("B")  # Change to blue when game starts
        self._gui._lbutton.config(text="Button: BLUE", fg="blue")  # Update GUI
        print("Game started!")

    def pause_game(self):
        self._running = False  # Stop the button thread
        self.change_button_color("R")  # Change to red when paused
        self._gui._lbutton.config(text="Button: RED", fg="red")  # Update GUI
        print("Game paused!")

    def resume_game(self):
        self._running = True  # Restart the button thread
        self.change_button_color("B")  # Change back to blue when resumed
        self._gui._lbutton.config(text="Button: BLUE", fg="blue")  # Update GUI
        print("Game resumed!")

    def change_button_color(self, color):
        # Change the button color based on the game state
        if color == "G":
            self._rgb[0].value = True  # Red LED off
            self._rgb[1].value = True  # Green LED on
            self._rgb[2].value = True  # Blue LED off
        elif color == "B":
            self._rgb[0].value = False  # Red LED off
            self._rgb[1].value = False  # Green LED off
            self._rgb[2].value = True  # Blue LED on
        elif color == "R":
            self._rgb[0].value = False  # Red LED on
            self._rgb[1].value = True  # Green LED off
            self._rgb[2].value = True  # Blue LED off

    def __str__(self):
        return f"Pressed {self._press_count} times" if self._value else "Released"


# Keypad Phase
class Keypad(PhaseThread):
    def __init__(self, keypad, gui, name="Keypad"):
        super().__init__(name)
        self._keypad = keypad
        self._value = ""
        self._equation, self._solution = self.generate_equation()  # Generate equation and solution
        self._gui = gui

    def generate_equation(self):
        # Generate equations until we find one with a 4-digit decimal result
        while True:
            # Generate two random binary numbers
            num1 = bin(random.randint(1, 255))[2:]  # Random binary number (1-255)
            num2 = bin(random.randint(1, 255))[2:]  # Random binary number (1-255)
            
            # Calculate the decimal result
            decimal_result = int(num1, 2) * int(num2, 2)
            
            # Check if the result is a 4-digit number
            if 1000 <= decimal_result <= 9999:
                return (num1, num2), decimal_result

    def run(self):
        self._running = True
        # Display the equation next to the keypad
        self._gui._equation_label.config(text=f"Multiply: {self._equation[0]} x {self._equation[1]}")

        while self._running:
            if self._keypad.pressed_keys:
                key = self._keypad.pressed_keys[0]
                while self._keypad.pressed_keys:
                    sleep(0.1)

                # Handle the input based on the key pressed
                if key == '#':  # Delete button
                    self._value = self._value[:-1]  # Remove the last digit
                elif key == '*':  # Enter button
                    if self._value:  # Only print if there is a value
                        if int(self._value) == self._solution:
                            self._gui._lkeypad.config(text="Keypad: SOLVED!", fg="green")
                            break
                        else:
                            self._gui._lkeypad.config(text="Incorrect! Try Again.", fg="red")
                            self._value = ""  # Reset value on incorrect entry
                else:  # Digit keys
                    if len(self._value) < 4:  # Limit to 4 digits
                        self._value += str(key)

                self._gui._lkeypad.config(text=f"Combination: {self._value}")

            sleep(0.1)
# Wires Phase
class Wires(PhaseThread):
    def __init__(self, pins, gui, name="Wires"):
        super().__init__(name)
        self._pins = pins
        self._gui = gui
        
        # Define a list of questions
        self._questions = [
            {
                "question": "What year was the University of Tampa founded?",
                "choices": ["A. 1940", "B. 1931", "C. 1933", "D. 1924", "E. 2005"],
                "correct": "B"
            },
            {
                "question": "What was the cause of the first ever computer bug?",
                "choices": ["A. Syntax error", "B. Logic error", "C. Server crash", "D. A real life bug", "E. None of the above"],
                "correct": "D"
            },
            {
                "question": "What was the first school with a computer science program?",
                "choices": ["A. Harvard", "B. UPenn", "C. Princeton", "D. MIT", "E. Cambridge"],
                "correct": "E"
            },
            {
                "question": "Who is considered the first ever programmer?",
                "choices": ["A. Rohan Khanad", "B. Murot Yildiz", "C. Ada Lovelace", "D. Dr. Kancharla", "E. Ricardo Almeida"],
                "correct": "C"
            }
        ]
        
        # Select a random question once
        self._current_question = random.choice(self._questions)
        
        # Display the question and choices
        self._gui._lwires.config(text=self._current_question["question"])
        self._gui._lwires_choices.config(text="\n".join(self._current_question["choices"]))
        
        self._initial_state = True  # Indicates if all wires are intact
        self._running = True
        self._solved = False  # Flag to indicate if the question has been solved

    def run(self):
        while self._running:
            # Read wire states
            self._value = [pin.value for pin in self._pins]
            self._gui._lwires.config(text=f"Wires: {self._value}")  # Show current wire states
            
            # Check if all wires are intact (assuming True means intact)
            if all(pin.value for pin in self._pins):  # If all wires are intact (True)
                self._initial_state = True
                # Display the current question again if needed
                if not self._solved:  # Only display if not solved
                    self._gui._lwires.config(text=self._current_question["question"])
                    self._gui._lwires_choices.config(text="\n".join(self._current_question["choices"]))
            else:
                self._initial_state = False  # At least one wire is cut

            # Check if any wire is cut (assuming False means cut)
            for index, pin in enumerate(self._pins):
                if not pin.value:  # If this wire is cut (False)
                    selected_wire = chr(65 + index)  # Convert index to corresponding letter A, B, C, D, E
                    print(f"Detected cut on wire: {selected_wire}")  # Debugging line
                    if selected_wire == self._current_question["correct"]:
                        self._gui._lwires.config(text="Wires: SOLVED! Correct wire cut.", fg="green")
                        print("Correct wire cut!")  # Debugging line
                        self._solved = True  # Mark the question as solved
                    else:
                        self._gui._lwires.config(text=f"Wires: WRONG! Cut {selected_wire}. Try again.", fg="red")
                        print(f"Wrong wire cut: {selected_wire}")  # Debugging line
                    
                    sleep(2)  # Pause for a moment to show the result
                    break  # Exit the loop after one wire cut

            sleep(0.1)

    def stop(self):
        self._running = False  # Method to stop the thread safely       
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

wire_pins = [DigitalInOut(i) for i in (board.D14, board.D15, board.D18, board.D23, board.D24)]
for pin in wire_pins:
    pin.direction = Direction.INPUT
    pin.pull = Pull.DOWN
wires = Wires(wire_pins, gui)

timer.start()
toggles.start()
button.start()
keypad.start()
wires.start()

# Initialize game state and start the check loop
game_state = GameState()
check()
window.mainloop()
