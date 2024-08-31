# Standard libraries
import os  # Operating system functions
import re  # Regular expressions

# Third-party libraries
import cv2  # OpenCV for computer vision tasks
import csv  # CSV file handling
import numpy as np  # NumPy for numerical operations
import face_recognition  # Face recognition library

# Python's built-in libraries
from datetime import datetime, timedelta  # Date and time handling
from pathlib import Path  # Path manipulation
from tkinter import Frame, Label, Tk, Canvas, Button, PhotoImage, Text, Toplevel, messagebox, Entry # GUI library

ASSETS_PATH = Path("build/assets")

def relative_to_assets(frame_directory: str, path: str) -> Path:
    result = ASSETS_PATH / frame_directory / path
    return result

class AttendanceSystemGUI:

    def __init__(self):
        self.login_window = Tk()
        self.login_window.title("Login")
        self.login_window.geometry("700x500")
        self.login_window.configure(bg="#D3D3D3")

        self.username = "admin"
        self.password = "password"

        self.window = None
        self.register_window = None
        self.edit_window = None
        self.delete_window = None

        self.last_attendance_time = {}
        self.init_assets_path()
        self.show_login()

    def on_tab_pressed(self, event, next_widget):
        next_widget.focus_set()
        return "break"  # Prevent default tab behavior

    def init_assets_path(self):
        current_directory = Path(__file__).resolve().parent
        self.ASSETS_PATH = current_directory / "build" / "assets"

    def relative_to_assets(self, frame_directory: str, path: str) -> Path:
        result = self.ASSETS_PATH / frame_directory / path
        return result

    def show_login(self):
        canvas = Canvas(self.login_window, bg="#D3D3D3", height=500, width=700, bd=0, highlightthickness=0, relief="ridge")
        canvas.place(x=0, y=0)

        Label(canvas, text="Username:", anchor="nw", fg="#1D6920", bg="#D3D3D3", font=("Youtube Sans", 25)).place(x=150, y=250)
        Label(canvas, text="Password:", anchor="nw", fg="#1D6920", bg="#D3D3D3", font=("Youtube Sans", 25)).place(x=150, y=300)

        self.username_entry = Entry(canvas, bd=2, bg="white", fg="black", font=("Youtube Sans", 17))
        self.username_entry.place(x=350, y=250, width=200, height=30)
        self.password_entry = Entry(canvas, bd=2, bg="white", fg="black", font=("Youtube Sans", 17), show="*")
        self.password_entry.place(x=350, y=300, width=200, height=30)

        self.username_entry.focus_set()

        login_button = Button(canvas, text="Login", command=self.verify_login, font=("Youtube Sans", 17), relief="flat", bg="#1D6920", fg="#D3D3D3")
        login_button.place(x=400, y=350, width=100, height=35)

        # Bind the Tab key to shift focus
        self.username_entry.bind("<Tab>", lambda event: self.on_tab_pressed(event, self.password_entry))
        self.password_entry.bind("<Tab>", lambda event: self.on_tab_pressed(event, self.username_entry))
        # Bind the Return key to invoke the login_button
        self.username_entry.bind("<Return>", lambda event: login_button.invoke())
        self.password_entry.bind("<Return>", lambda event: login_button.invoke())

        canvas.create_text( 60.0, 30.0, anchor="nw", text=
        "Facial Recognition\n       Attendance System", fill="#1D6920", font=("Pricedown", 70 * -1))

        self.login_window.resizable(False, False)
        self.login_window.mainloop()

    def verify_login(self):
        entered_username = self.username_entry.get()
        entered_password = self.password_entry.get()

        if entered_username == self.username and entered_password == self.password:
            # Close the login window and show the main attendance system
            self.login_window.destroy()
            self.main_menu()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

            # Clear both the username and password entry fields
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')

    def take_attendance(self, confidence_threshold=0.7):
        # Define the interval for marking attendance (24 hours)
        attendance_interval = timedelta(hours=24)

        # Initialize lists to store known face encodings and corresponding names
        known_face_encodings = []
        known_face_names = []

        # Loop through npy files in the npy_data directory to load known face encodings
        for file in os.listdir('npy_data'):
            if file.endswith('.npy'):
                known_face_encodings.append(np.load(os.path.join('npy_data', file)))
                parts = file[:-4].split('_')
                if len(parts) == 3:
                    name, roll_no, _ = parts
                    known_face_names.append((name, roll_no))

        # Start video capture
        video_capture = cv2.VideoCapture(1)

        while True:
            ret, frame = video_capture.read()

            # Detect face locations and encode them
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Calculate face distance (confidence level) between detected face and known faces
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                confidence = 1 - face_distances[best_match_index]

                if confidence >= confidence_threshold:
                    # Get the matched student's name and roll number
                    name, roll_no = known_face_names[best_match_index]
                else:
                    # Confidence is not high enough, mark as "UNKNOWN N/A"
                    name = "UNKNOWN"
                    roll_no = "N/A"

                # Draw a Golden rectangle around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 165, 255), 2)  # Golden rectangle around the face
                cv2.putText(frame, f"{name}-{roll_no}", (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 1.0,
                            (0, 165, 255), 2)
                # Calculate text size and position
                text = "Press Q to stop Taking Attendance"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 1.0, 2)[0]
                text_x = (frame.shape[1] - text_size[0]) // 2  # Center horizontally
                text_y = frame.shape[0] - 20  # Bottom of the frame, leaving a small gap

                # Draw the text
                cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 1.0, (56, 195, 255), 2)

                if name != "UNKNOWN":
                    # Get the last marked attendance time for the student
                    last_marked_time = self.last_attendance_time.get(name, datetime.min)
                    time_diff = datetime.now() - last_marked_time

                    if time_diff >= attendance_interval:
                        # Mark attendance if the time interval is reached
                        self.last_attendance_time[name] = datetime.now()

                        now = datetime.now()
                        month_name = now.strftime('%B')
                        year_name = now.strftime('%Y')
                        file_name = os.path.join('csv_data', f"{month_name}_{year_name}.csv")

                        header_exists = os.path.exists(file_name)
                        with open(file_name, 'a', newline='') as f:
                            writer = csv.writer(f)
                            if not header_exists:
                                writer.writerow(["Roll No", "Date", "Name"])  # Header row with columns reordered
                            writer.writerow([roll_no, now.strftime('%d-%m-%Y'), name])
                            print("\n\nAttendance Marked", f"\n\nRecord added to {file_name}: {roll_no}, {now.strftime('%d-%m-%Y')}, {name}\n")

            # Display the frame with detected faces
            cv2.imshow('Attendance', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release video capture and close the OpenCV windows
        video_capture.release()
        cv2.destroyAllWindows()

    def check_attendance(self):
        now = datetime.now()
        month_name = now.strftime('%B')
        year_name = now.strftime('%Y')
        attendance_file = os.path.join('csv_data', f"{month_name}_{year_name}.csv")
        
        if os.path.exists(attendance_file):
            # Open the attendance CSV file if it exists
            os.startfile(attendance_file)
        pass

    def main_menu(self):
        self.window = Tk()  # Assign the main menu window to self.window
        self.window.title("Attendance System Using Facial Recognition")
        self.window.geometry("1366x768")
        self.window.configure(bg="#F8C400")

        canvas = Canvas( bg = "#F8C400", height = 768, width = 1366, bd = 0, highlightthickness = 0, relief = "ridge")
        canvas.place(x = 0, y = 0)

        image_image_1 = PhotoImage(file=relative_to_assets("frame0", "image_1.png"))
        image_1 = canvas.create_image( 165.0, 163.0, image=image_image_1)

        button_image_1 = PhotoImage(file=relative_to_assets("frame0", "button_1.png"))
        button_1 = Button( image=button_image_1, borderwidth=0, highlightthickness=0, command=self.create_register_gui, relief="flat")
        button_1.place( x=60.0, y=500.0, width=215.0, height=43.0)

        button_image_2 = PhotoImage(file=relative_to_assets("frame0", "button_2.png"))
        button_2 = Button( image=button_image_2, borderwidth=0, highlightthickness=0, command=lambda: self.take_attendance(), relief="flat")
        button_2.place( x=60.0, y=620.0, width=215.0, height=43.0)

        button_image_3 = PhotoImage(file=relative_to_assets("frame0", "button_3.png"))
        button_3 = Button( image=button_image_3, borderwidth=0, highlightthickness=0, command=lambda: self.check_attendance(), relief="flat")
        button_3.place( x=410.0, y=500.0, width=215.0, height=43.0)

        button_image_4 = PhotoImage(file=relative_to_assets("frame0", "button_4.png"))
        button_4 = Button( image=button_image_4, borderwidth=0, highlightthickness=0, command=self.create_edit_gui, relief="flat")
        button_4.place( x=410.0, y=620.0, width=215.0, height=43.0)

        button_image_5 = PhotoImage(file=relative_to_assets("frame0", "button_5.png"))
        button_5 = Button( image=button_image_5, borderwidth=0, highlightthickness=0, command=self.create_delete_gui, relief="flat")
        button_5.place( x=760.0, y=500.0, width=215.0, height=43.0)

        button_image_6 = PhotoImage(file=relative_to_assets("frame0", "button_6.png"))
        button_6 = Button( image=button_image_6, borderwidth=0, highlightthickness=0, command=self.create_exit_gui, relief="flat")
        button_6.place( x=760.0, y=620.0, width=215.0, height=43.0)

        canvas.create_rectangle( -4.249755859375, 335.0, 1027.750244140625, 340.0, fill="#000000", outline="")
        canvas.create_rectangle( 1025.0, -10.0, 1035.0, 768.0, fill="#000000", outline="")

        text_label = Label(text=
        "   AMK Campus\n      Attendance\n             System\n                Using\n                Facial\n     Recognition",
        bg="#F8C400", font=("Youtube Sans", 34))
        text_label.place(x=745, y=0)

        # Create the Contact button
        button_contact = Button(canvas, text="Contact Us", command=self.show_contact_info, font=("Youtube Sans", 17), relief="flat", bg="#F8C400", fg="#000000")
        button_contact.place(x=1035.0, y=0.0, width=330.0, height=1100.0)

        text_label = Label(text="Main Menu", bg="#F8C400", font=("Pricedown", 40))
        text_label.place(x=420, y=370)

        self.window.resizable(False, False)
        self.window.mainloop()

    def register_new_student(self, name_entry, roll_no_entry):
        # Get student's name and roll number from the Text widgets
        name = name_entry.get("1.0", "end-1c")
        roll_no = roll_no_entry.get("1.0", "end-1c")

        # Validate user input against the pattern of no lines and tabs
        if re.search(r'[\t\n]', name) or re.search(r'[\t\n]', roll_no):
            messagebox.showerror("Error", "Name and roll number cannot contain tabs or newlines.")
            self.register_window.destroy()  # Close the window on error
            return
        # Validate user input for name
        if not re.match(r'[A-Za-z ]+$', name):
            messagebox.showerror("Error", "Name can only contain letters and spaces.")
            self.register_window.destroy()  # Close the window on error
            return
        # Validate user input for roll no
        if not re.match(r'\d{1,8}$', roll_no):
            messagebox.showerror("Error", "Roll number must be a number with 1 to 8 digits.")
            self.register_window.destroy()  # Close the window on error
            return

        # Display a message to instruct the user to move their head slightly
        messagebox.showinfo("Scan Instructions", "Please get ready to angle your face UP, DOWN, LEFT, RIGHT\nslightly while scanning your face.\n\nThe Scan will start once you click on 'OK'.")

        # Initialize variables
        num_images_to_capture = 5  # Number of face images to capture
        face_encodings = []
        video_capture = cv2.VideoCapture(1)

        # Capture and process multiple frames to get multiple face encodings
        while len(face_encodings) < num_images_to_capture:
            ret, frame = video_capture.read()

            # Encode the detected face
            face_encodings_current_frame = face_recognition.face_encodings(frame)

            if len(face_encodings_current_frame) > 0:
                # Get face location and draw a bright green rectangle around the face
                top, right, bottom, left = face_recognition.face_locations(frame)[0]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)  # Bright Green rectangle around the face
                cv2.putText(frame, f"{name} - {roll_no}", (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 0), 2)

                # Save the face encoding as a numpy file with a unique filename
                face_encoding_file = os.path.join('npy_data', f"{name}_{roll_no}_{len(face_encodings) + 1}.npy")
                np.save(face_encoding_file, face_encodings_current_frame[0])

                # Display a success message
                cv2.imshow('Face Registration', frame)
                cv2.waitKey(1000)  # Show each frame for the specified interval
                face_encodings.append(face_encodings_current_frame[0])

        # Release video capture and close the OpenCV windows
        video_capture.release()
        cv2.destroyAllWindows()

        messagebox.showinfo("Success", f"Student {name} {roll_no} registered successfully!")

        self.register_window.destroy()  # Close the window after successful registration

    def create_register_gui(self):
        self.register_window = Toplevel(self.window)
        self.register_window.title("Register Student")
        self.register_window.geometry("500x350")
        self.register_window.configure(bg="#F8C400")

        frame = Frame(self.register_window, bg="#F8C400")
        frame.place(x=0, y=0, width=500, height=350)

        name_entry = Text(frame, bd=0, bg="white", fg="black", font=("Youtube Sans", 20), padx=10, pady=10)
        name_entry.place(x=290.0, y=120.0, width=200.0, height=50.0)

        roll_no_entry = Text(frame, bd=0, bg="white", fg="black", font=("Youtube Sans", 20), padx=10, pady=10)
        roll_no_entry.place(x=290.0, y=200.0, width=200.0, height=50.0)

        name_entry.focus_set()

        Label(frame, text="Register a New Student", anchor="nw", fg="#000000", bg="#F8C400", font=("Pricedown", 55 * -1)).place(x=10.0, y=10.0)
        Label(frame, text="Student's Name:", anchor="nw", fg="#000000", bg="#F8C400", font=("Youtube Sans", 30 * -1)).place(x=40.0, y=130.0)
        Label(frame, text="Students's Roll No:", anchor="nw", fg="#000000", bg="#F8C400", font=("Youtube Sans", 30 * -1)).place(x=30.0, y=210.0)

        button_image_1 = PhotoImage(file=relative_to_assets("frame3", "button_1.png"))
        register_button = Button(frame, image=button_image_1, borderwidth=0, highlightthickness=0, command=lambda: self.register_new_student(name_entry, roll_no_entry), relief="flat")
        register_button.place(x=330.0, y=285.0, width=109.0, height=35.0)

        # Bind the Tab key to shift focus
        name_entry.bind("<Tab>", lambda event: self.on_tab_pressed(event, roll_no_entry))
        roll_no_entry.bind("<Tab>", lambda event: self.on_tab_pressed(event, name_entry))
        # Bind the Return key to invoke the register_button
        name_entry.bind("<Return>", lambda event: register_button.invoke())
        roll_no_entry.bind("<Return>", lambda event: register_button.invoke())

        self.register_window.resizable(False, False)
        self.register_window.mainloop()

    def edit_student_info(self, roll_no_entry, new_name_entry):
        roll_no = roll_no_entry.get("1.0", "end-1c")  # Get roll number from the Text widget
        new_name = new_name_entry.get("1.0", "end-1c")  # Get new name from the Text widget

        # Validate user input against the pattern of no lines and tabs
        if re.search(r'[\t\n]', new_name) or re.search(r'[\t\n]', roll_no):
            messagebox.showerror("Error", "Name and roll number cannot contain tabs or newlines.")
            self.edit_window.destroy()  # Close the window on error
            return
        # Validate user input for new name
        if not re.match(r'[A-Za-z ]+$', new_name):
            messagebox.showerror("Error", "New name can only contain letters and spaces.")
            self.edit_window.destroy()  # Close the window on error
            return
        # Validate user input for roll no
        if not re.match(r'\d{1,8}$', roll_no):
            messagebox.showerror("Error", "Roll number must be a number with 1 to 8 digits.")
            self.edit_window.destroy()  # Close the window on error
            return

        found_student = False  # Flag to track if a matching student was found

        for file in os.listdir('npy_data'):
            if file.endswith('.npy'):
                parts = file[:-4].split('_')
                if len(parts) == 3:
                    name, existing_roll_no, num_face_encodings = parts
                    if existing_roll_no == roll_no:
                        # Convert num_face_encodings to an integer
                        num_face_encodings = int(num_face_encodings)
                        
                        # Update the number of face encodings
                        new_num_face_encodings = num_face_encodings + 1
                        
                        new_file_name = os.path.join('npy_data', f"{new_name}_{roll_no}_{new_num_face_encodings}.npy")
                        os.rename(os.path.join('npy_data', file), new_file_name)
                        found_student = True  # Set the flag to True if a matching student was found

        if found_student:
            messagebox.showinfo("Information Updated", "Student's information updated successfully.")
        else:
            messagebox.showerror("Error", "Student not found.")

        self.edit_window.destroy()  # Close the window after editing

    def create_edit_gui(self):
        self.edit_window = Toplevel(self.window)
        self.edit_window.title("Edit Student's Information")
        self.edit_window.geometry("500x350")
        self.edit_window.configure(bg="#F8C400")

        frame = Frame(self.edit_window, bg="#F8C400")
        frame.place(x=0, y=0, width=500, height=350)

        roll_no_entry = Text(frame, bd=0, bg="white", fg="black", font=("Youtube Sans", 20), padx=10, pady=10)
        roll_no_entry.place(x=290.0, y=120.0, width=200.0, height=50.0)

        new_name_entry = Text(frame, bd=0, bg="white", fg="black", font=("Youtube Sans", 20), padx=10, pady=10)
        new_name_entry.place(x=290.0, y=200.0, width=200.0, height=50.0)

        roll_no_entry.focus_set()

        Label(frame, text="Edit Student's Data", anchor="nw", fg="#000000", bg="#F8C400", font=("Pricedown", 55 * -1)).place(x=60.0, y=10.0)
        Label(frame, text="Student's Roll No:", anchor="nw", fg="#000000", bg="#F8C400", font=("Youtube Sans", 30 * -1)).place(x=40.0, y=130.0)
        Label(frame, text="Student's New Name:", anchor="nw", fg="#000000", bg="#F8C400", font=("Youtube Sans", 30 * -1)).place(x=10.0, y=210.0)

        button_image_1 = PhotoImage(file=relative_to_assets("frame2", "button_1.png"))
        edit_button = Button(frame, image=button_image_1, borderwidth=0, highlightthickness=0, command=lambda: self.edit_student_info(roll_no_entry, new_name_entry), relief="flat")
        edit_button.place(x=330.0, y=285.0, width=116.32653045654297, height=35.0)

        # Bind the Tab key to shift focus
        roll_no_entry.bind("<Tab>", lambda event: self.on_tab_pressed(event, new_name_entry))
        new_name_entry.bind("<Tab>", lambda event: self.on_tab_pressed(event, roll_no_entry))
        # Bind the Return key to invoke the edit_button
        roll_no_entry.bind("<Return>", lambda event: edit_button.invoke())
        new_name_entry.bind("<Return>", lambda event: edit_button.invoke())

        self.edit_window.resizable(False, False)
        self.edit_window.mainloop()

    def delete_student_face_data(self, roll_no_entry):
        roll_no = roll_no_entry.get("1.0", "end-1c")  # Get roll number from the Text widget

        # Validate user input against the pattern of no lines and tabs
        if re.search(r'[\t\n]', roll_no):
            messagebox.showerror("Error", "Roll number cannot contain tabs or newlines.")
            self.delete_window.destroy()  # Close the window on error
            return
        # Validate user input for roll no
        if not re.match(r'\d{1,8}$', roll_no):
            messagebox.showerror("Error", "Roll number must be a number with 1 to 8 digits.")
            self.delete_window.destroy()  # Close the window on error
            return

        found_student = False  # Flag to track if a matching student was found

        for file in os.listdir('npy_data'):
            if file.endswith('.npy'):
                parts = file[:-4].split('_')
                if len(parts) == 3:
                    _, existing_roll_no, _ = parts
                    if existing_roll_no == roll_no:
                        os.remove(os.path.join('npy_data', file))
                        found_student = True  # Set the flag to True if a matching student was found

        if found_student:
            messagebox.showinfo("Success", "Face data deleted successfully.")
        else:
            messagebox.showerror("Error", "Student not found.")

        self.delete_window.destroy()  # Close the window after editing

    def create_delete_gui(self):
        self.delete_window = Toplevel(self.window)
        self.delete_window.title("Delete Student's Information")
        self.delete_window.geometry("500x350")
        self.delete_window.configure(bg="#F8C400")

        frame = Frame(self.delete_window, bg="#F8C400")
        frame.place(x=0, y=0, width=500, height=350)

        roll_no_entry = Text(frame, bd=0, bg="white", fg="black", font=("Youtube Sans", 20), padx=10, pady=10)
        roll_no_entry.place(x=290.0, y=150.0, width=200.0, height=50.0)

        roll_no_entry.focus_set()

        Label(frame, text="Delete Student's Data", anchor="nw", fg="#000000", bg="#F8C400", font=("Pricedown", 55 * -1)).place(x=30.0, y=10.0)
        Label(frame, text="Student's Roll No:", anchor="nw", fg="#000000", bg="#F8C400", font=("Youtube Sans", 30 * -1)).place(x=40.0, y=163.0)

        button_image_1 = PhotoImage(file=relative_to_assets("frame1", "button_1.png"))
        delete_button = Button(frame, image=button_image_1, borderwidth=0, highlightthickness=0, command=lambda: self.delete_student_face_data(roll_no_entry), relief="flat")
        delete_button.place(x=330.0, y=245.0, width=80.0, height=35.0)

        # Bind the Tab key to shift focus
        roll_no_entry.bind("<Tab>", lambda event: None)  # No further focus
        # Bind the Return key to invoke the delete_button
        roll_no_entry.bind("<Return>", lambda event: delete_button.invoke())

        self.delete_window.resizable(False, False)
        self.delete_window.mainloop()

    def create_exit_gui(self):
        exit_window = Toplevel(self.window)
        exit_window.title("Exit Application")
        exit_window.geometry("700x500")
        exit_window.configure(bg="#D3D3D3")

        canvas = Canvas(exit_window, bg="#D3D3D3", height=500, width=700, bd=0, highlightthickness=0, relief="ridge")
        canvas.place(x=0, y=0)
        canvas.create_text(50.0, 20.0, anchor="nw", text="THANK YOU FOR USING\nOUR\nFACIAL RECOGNITION\nATTENDANCE\nSYSTEM!\nHAVE A GOOD DAY!", fill="#1D6920", font=("Youtube Sans", 55 * -1))

        canvas.focus_set()

        login_button = Button(canvas, text="Close", command=lambda: self.close_windows(exit_window), font=("Youtube Sans", 17), relief="flat", bg="#1D6920", fg="#D3D3D3")
        login_button.place(x=580, y=450, width=100, height=35)

        exit_window.resizable(False, False)

        # Use the after method to close both windows after 5 seconds
        exit_window.after(10000, self.close_windows, exit_window)

    def show_contact_info(self):
        # Create a new window for contact information
        contact_window = Toplevel(self.window)
        contact_window.title("Contact Information")
        contact_window.geometry("300x800")
        contact_window.configure(bg="#000000")

        # Add labels for program and developer information
        program_info_label = Label(contact_window, text="\nSupervisor:\n\n Prof. Dr. M Idrees\n",fg="#FFFFFF", bg="#000000", font=("Youtube Sans", 17))
        program_info_label.pack(pady=10)

        developer_info_label = Label(contact_window, text="\nDevelopers:\n\n(Project Lead Asim Ismail)\n\n Syed Hamza Ahmed\n Bilal Khan\n", fg="#FFFFFF", bg="#000000", font=("Youtube Sans", 17))
        developer_info_label.pack(pady=10)

        tools_info_label = Label(contact_window, text="\nDevelopment Tools:\n\n Python\n Tkinter\n OpenCv\n Designed in Figma\n",fg="#FFFFFF", bg="#000000", font=("Youtube Sans", 17))
        tools_info_label.pack(pady=10)

        # Create a "Close" button to close the contact window
        close_button = Button(contact_window, text="Close", command=contact_window.destroy, font=("Youtube Sans", 17), relief="flat", bg="#D3D3D3", fg="#000000")
        close_button.pack(pady=20)

        program_info_label.focus_set()

        contact_window.resizable(False, False)

    def close_windows(self, exit_window):
        exit_window.destroy()  # Close the exit window
        self.window.destroy()  # Close the main menu window

    def run(self):
        self.login_window.mainloop()
        # Call self.window.mainloop() here to start the main menu window
        self.window.mainloop()

if __name__ == "__main__":
    app = AttendanceSystemGUI()
    app.run()