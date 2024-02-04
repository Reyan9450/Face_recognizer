import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from PIL import Image, ImageTk
import os
import cv2
from simple_facerec import SimpleFacerec
import csv
import tkinter.messagebox as messagebox

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition App")

        # Initialize SimpleFacerec
        self.sfr = SimpleFacerec()
        self.sfr.load_encoding_images("images/")

        # Load Camera
        self.cap = cv2.VideoCapture(0)

        # Create main frame for organization
        self.main_frame = ttk.Frame(root)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10)

        # Create frame for video feed
        self.video_frame = ttk.Frame(self.main_frame)
        self.video_frame.grid(row=0, column=0)

        # Create canvas to display video feed
        self.canvas = tk.Canvas(self.video_frame, width=800, height=600)
        self.canvas.pack()

        # Create frame for buttons and labels
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=1, padx=10)

        add_photo_button = tk.Button(self.button_frame, text="Add Person Photo", command=self.show_add_person_popup,
                                     font=("Helvetica", 14), padx=10, pady=5)
        add_photo_button.grid(row=0, column=0, pady=10, sticky=tk.W + tk.E + tk.N + tk.S)

        # Label to show details
        self.message_label = tk.Label(self.button_frame, text="", font=("Helvetica", 16), fg="red")
        self.message_label.grid(row=1, column=0, pady=10, sticky=tk.W + tk.E + tk.N + tk.S)

        # Button to show person details
        show_details_button = tk.Button(self.button_frame, text="Show Person Details", command=self.show_person_details_popup,
                                        font=("Helvetica", 14), padx=10, pady=5)
        show_details_button.grid(row=2, column=0, pady=10, sticky=tk.W + tk.E + tk.N + tk.S)

        # Store detected faces and corresponding details
        self.detected_faces = []

        # Start video feed
        self.update_video_feed()

        # Bind the close button to exit the application
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_video_feed(self):
        ret, frame = self.cap.read()

        if ret:
            # Detect Faces
            face_locations, face_names = self.sfr.detect_known_faces(frame)
            self.detected_faces = list(zip(face_locations, face_names))

            for face_loc, name in self.detected_faces:
                y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

            # Convert the OpenCV frame to ImageTk format and display it on the canvas
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            self.canvas.img_tk = img_tk

            # Bind click event to canvas
            self.canvas.bind("<Button-1>", self.show_person_details_on_click)

        # Schedule the next update after 10 milliseconds
        self.root.after(10, self.update_video_feed)

    def show_add_person_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add Person")

        # Entry for person's name
        ttk.Label(popup, text="Person Name:").grid(row=0, column=0, padx=10, pady=10)
        person_name_entry = ttk.Entry(popup)
        person_name_entry.grid(row=0, column=1, padx=10, pady=10)

        # Entry for ERP ID
        ttk.Label(popup, text="ERP ID:").grid(row=1, column=0, padx=10, pady=10)
        erp_id_entry = ttk.Entry(popup)
        erp_id_entry.grid(row=1, column=1, padx=10, pady=10)

        # Entry for branch
        ttk.Label(popup, text="Branch:").grid(row=2, column=0, padx=10, pady=10)
        branch_entry = ttk.Entry(popup)
        branch_entry.grid(row=2, column=1, padx=10, pady=10)

        # Entry for gender
        ttk.Label(popup, text="Gender:").grid(row=3, column=0, padx=10, pady=10)
        gender_entry = ttk.Entry(popup)
        gender_entry.grid(row=3, column=1, padx=10, pady=10)

        # Button to add a person's photo
        add_photo_button = tk.Button(popup, text="Add Photo", command=lambda: self.add_person_photo(popup, person_name_entry.get(), erp_id_entry.get(), branch_entry.get(), gender_entry.get()),
                                     font=("Helvetica", 14), padx=10, pady=5)
        add_photo_button.grid(row=4, column=0, columnspan=2, pady=10)

    def add_person_photo(self, popup, person_name, erp_id, branch, gender):
        file_path = filedialog.askopenfilename(title="Select Image",
                                               filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            # Save the image to the "images/" folder
            destination_path = os.path.join("images", f"{person_name}.jpg")
            try:
                os.makedirs("images", exist_ok=True)
                os.rename(file_path, destination_path)

                # Save details to CSV file
                csv_file = "person_details.csv"
                with open(csv_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([person_name, erp_id, branch, gender])

                self.message_label.config(text=f"{person_name}'s photo and details added successfully!")
                popup.destroy()
            except Exception as e:
                self.message_label.config(text=f"Error adding {person_name}'s photo and details: {str(e)}")
        else:
            self.message_label.config(text="No file selected.")

    def show_person_details_popup(self):
        person_name = simpledialog.askstring("Show Person Details", "Enter person's name:")
        if person_name:
            details_message = self.get_person_details(person_name)
            if details_message:
                messagebox.showinfo("Person Details", details_message)
            else:
                messagebox.showinfo("No Information", "No information found for the person.")
        else:
            messagebox.showwarning("Invalid Name", "Invalid name.")

    def show_person_details_on_click(self, event):
        # Check if a face is clicked
        for face_loc, name in self.detected_faces:
            y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
            if x1 < event.x < x2 and y1 < event.y < y2:
                details_message = self.get_person_details(name)
                if details_message:
                    messagebox.showinfo("Person Details", details_message)
                else:
                    messagebox.showinfo("No Information", "No information found for the person.")
                break

    def get_person_details(self, person_name):
        csv_file = "person_details.csv"
        try:
            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row[0] == person_name:
                        details_message = f"Person Name: {row[0]}\nERP ID: {row[1]}\nBranch: {row[2]}\nGender: {row[3]}"
                        return details_message
            return None
        except Exception as e:
            return f"Error reading details: {str(e)}"

    def on_closing(self):
        # Release camera and close the application
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()
