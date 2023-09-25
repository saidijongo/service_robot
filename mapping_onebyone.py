import tkinter as tk
from PIL import ImageTk, Image
import json
import requests
import RPi.GPIO as GPIO
import time
from io import BytesIO
from tkinter import ttk
import os

# Defining the GPIO pins connected to the relay module
relay_pins = [23, 21, 19, 15, 13, 11, 7, 5, 31, 33, 35]

# Motor mapping from JSON indices (starting from 1) to relay_pins indices (starting from 0)
motor_mapping = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    7: 6,
    8: 7,
    9: 8,
    10: 9,
    11: 10,
}

# Defining the GPIO pins connected to the LED strip
led_red_pin = 26
led_green_pin = 24
led_white_pin = 22

# Loading recipes from JSON
with open('holiday.json') as file:
    recipes = json.load(file)

class CocktailBartenderRobotGUI:
    def __init__(self, root, recipes):
        self.root = root
        self.recipes = recipes
        self.cocktail_images = []
        self.cocktail_names = []

        # Initializing GPIO setup here
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for pin in relay_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)

        # Initializing LED GPIO pins
        GPIO.setup(led_red_pin, GPIO.OUT)
        GPIO.setup(led_green_pin, GPIO.OUT)
        GPIO.setup(led_white_pin, GPIO.OUT)

        # Turning on the white LED by default
        GPIO.output(led_red_pin, GPIO.LOW)
        GPIO.output(led_green_pin, GPIO.LOW)
        GPIO.output(led_white_pin, GPIO.HIGH)

        self.jongo = tk.Frame(self.root, bg="#F8C471")
        self.jongo.pack(fill=tk.BOTH, expand=1)

        self.canva = tk.Canvas(self.jongo)
        self.canva.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.v_scrollbar = ttk.Scrollbar(self.jongo, orient=tk.VERTICAL, command=self.canva.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scrollbar = ttk.Scrollbar(self.jongo, orient=tk.HORIZONTAL, command=self.canva.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canva.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.canva.bind("<Configure>", lambda e: self.canva.configure(scrollregion=self.canva.bbox("all")))

        self.jongo2 = tk.Frame(self.canva, bg="#F8C471")
        self.canva.create_window((0, 0), window=self.jongo2, anchor="nw")

        self.load_cocktail_data()
        self.create_cocktail_buttons()

    def load_cocktail_data(self):
        for cocktail in self.recipes:
            self.cocktail_names.append(cocktail)

            # Check if the image is available in the local "imgpath"
            local_img_path = self.recipes[cocktail]['imgpath']
            if os.path.exists(local_img_path):
                try:
                    image = Image.open(local_img_path)
                    image = image.resize((210, 210), Image.BILINEAR)
                    self.cocktail_images.append(ImageTk.PhotoImage(image))
                except Exception as e:
                    print(f"Error loading image for {cocktail} from local imgpath: {e}")
                    # Fall back to image_url if there is an error with the local image
                    self.load_image_from_url(cocktail)
            else:
                # If the image is not available in "imgpath," load it from "image_url"
                self.load_image_from_url(cocktail)

    def load_image_from_url(self, cocktail):
        # Load the image from "image_url"
        response = requests.get(self.recipes[cocktail]['image_url'])
        try:
            image = Image.open(BytesIO(response.content))
            image = image.resize((210, 210), Image.BILINEAR)
            self.cocktail_images.append(ImageTk.PhotoImage(image))
        except Exception as e:
            print(f"Error loading image for {cocktail} from image_url: {e}")
            # Set a default image or handle the error accordingly
            self.cocktail_images.append(None)

    def create_cocktail_buttons(self):
        for i, cocktail in enumerate(self.cocktail_names):
            btn_frame = tk.Frame(self.jongo2, bg="#F8C471")
            btn_frame.grid(row=i // 2, column=i % 2, padx=10, pady=10)

            btn = tk.Button(btn_frame, image=self.cocktail_images[i],
                            command=lambda idx=i: self.show_cocktail_details(idx))
            btn.pack()

            label = tk.Label(btn_frame, text=cocktail)
            label.pack()

    def show_cocktail_details(self, idx):
        selected_cocktail = self.cocktail_names[idx]
        cocktail_data = self.recipes[selected_cocktail]

        details_window = tk.Toplevel(self.root, bg="#F8C471")
        details_window.title(selected_cocktail)
        details_window.geometry("500x500") 

        # Displaying cocktail image
        image_frame = tk.Frame(details_window, bg="#F8C471")
        image_frame.pack(pady=10)
        image_label = tk.Label(image_frame, image=self.cocktail_images[idx])
        image_label.pack()

        # Displaying cocktail ingredients
        ingredients_frame = tk.Frame(details_window, bg="#F8C471")
        ingredients_frame.pack(pady=10)
        for ingredient in cocktail_data['ingredients']:
            ingredient_label = tk.Label(ingredients_frame, text=f"{ingredient['name']}: {ingredient['quantity']} ml", bg="#F8C471")
            ingredient_label.pack()

        # Order button
        def order_cocktails():
            num_cocktails = 1  # Since we removed the slider
            self.make_cocktails(selected_cocktail, num_cocktails)
            details_window.destroy()

        order_button = tk.Button(details_window, text="Press to order", command=order_cocktails)
        order_button.pack(pady=10)

        # Calculate the position of the top-level window on the right-hand side
        x, y, _, _ = self.canva.bbox("all")
        x_offset = 10  # Adjust this value as needed
        y_offset = 10  # Adjust this value as needed
        details_window.geometry(f"+{self.root.winfo_x() + x + x_offset}+{self.root.winfo_y() + y + y_offset}")

    def make_cocktails(self, cocktail_name, num_cocktails):
        selected_cocktail = self.recipes[cocktail_name]
        print(f"Preparing {num_cocktails} {cocktail_name}(s)...")

        # Getting the ingredient motors and volumes for the selected cocktail
        ingredients = selected_cocktail['ingredients']

        # Turn LEDs red while making cocktails
        GPIO.output(led_red_pin, GPIO.HIGH)
        GPIO.output(led_green_pin, GPIO.LOW)
        GPIO.output(led_white_pin, GPIO.LOW)

        # Calculating the estimated pump run times based on ingredient volumes
        run_times = []
        for ingredient in ingredients:
            volume = ingredient['quantity']
            motor_idx = ingredient['motor']
            motor_pin = relay_pins[motor_mapping[motor_idx]]  # Map motor index to relay pin
            run_time = volume / 1.75  # Volume / flow rate
            run_times.append((motor_pin, run_time))

        # Activating all the required motors to pour the ingredients
        try:
            for motor_pin, run_time in run_times:
                GPIO.output(motor_pin, GPIO.LOW)
                time.sleep(run_time)
                GPIO.output(motor_pin, GPIO.HIGH)
        except KeyboardInterrupt:
            print("Process interrupted by the user.")
        finally:
            print("Cocktails ready!")

            # Turn LEDs green when cocktails are ready
            GPIO.output(led_red_pin, GPIO.LOW)
            GPIO.output(led_green_pin, GPIO.HIGH)
            GPIO.output(led_white_pin, GPIO.LOW)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cocktail Bartender Robot")
    root.geometry("700x500")
    app = CocktailBartenderRobotGUI(root, recipes)
    app.run()
    GPIO.cleanup()
