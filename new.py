import tkinter as tk
from tkinter import ttk
import RPi.GPIO as GPIO
import time


# Define the GPIO pins connected to the relay module for ingredients
#relay_pins = [40, 38, 36, 32, 37, 35, 33, 31, 23, 21]
#relay_pins = [23, 21, 19, 15, 13, 11, 7, 40`, 38, 36, 32, 37, 35, 33, 31]

#relay_pins = [40, 38, 36, 32, 37, 35, 33, 31, 23, 21]
relay_pins = [23, 21, 19, 15, 13, 11, 7,5, 31,33,35] 


class IngredientPumpControl:
    def __init__(self, root):
        self.root = root
        self.root.title("Ingredient Pump Control")

        # Initialize GPIO setup here
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for pin in relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)

        self.label = ttk.Label(root, text="Select Ingredient Motor:")
        self.label.pack(pady=10)

        # Dropdown menu to select the ingredient motor
        self.selected_motor = tk.StringVar()
        self.ingredient_motor_dropdown = ttk.Combobox(root, textvariable=self.selected_motor)
        self.ingredient_motor_dropdown['values'] = [f"Motor {i+1}" for i in range(len(relay_pins))]
        self.ingredient_motor_dropdown.pack()

        self.label = ttk.Label(root, text="Enter Volume (ml):")
        self.label.pack(pady=10)

        # Entry field to input the volume
        self.volume_entry = ttk.Entry(root)
        self.volume_entry.pack()

        self.start_button = ttk.Button(root, text="Start", command=self.start_pump)
        self.start_button.pack(pady=10)

    def start_pump(self):
        motor_idx = self.ingredient_motor_dropdown.current()
        volume = int(self.volume_entry.get())

        if motor_idx >= 0 and 0 <= volume <= 100:
            motor_pin = relay_pins[motor_idx]
            run_time = volume / 100  # Volume / flow rate

            try:
                GPIO.output(motor_pin, GPIO.LOW)
                time.sleep(run_time)
                GPIO.output(motor_pin, GPIO.HIGH)
                print(f"Pumping {volume} ml from Motor {motor_idx + 1}")
            except KeyboardInterrupt:
                print("Process interrupted by the user.")
            finally:
                print("Pumping complete!")

if __name__ == "__main__":
    root = tk.Tk()
    app = IngredientPumpControl(root)
    root.mainloop()
    GPIO.cleanup()
