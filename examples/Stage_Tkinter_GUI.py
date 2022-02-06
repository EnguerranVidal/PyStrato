# IMPORTS
import datetime as dt
import csv
import shutil

import matplotlib.pyplot as plt
import tkinter as tk
import tkinter.messagebox
from tkinter.filedialog import askopenfilename
import tkinter.font
import tkinter.ttk
from tkcalendar import Calendar
import os
from PIL import Image, ImageTk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np
import pandas as pd


# MAIN APPLICATION CLASS
class LORAD_Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("LORAD")
        self.minsize(1000, 500)
        # FULLSCREEN
        self.attributes('-fullscreen', False)
        self.bind("<F11>", lambda event: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda event: self.attributes("-fullscreen", False))
        # USED PARAMETERS
        self.button_width = 30
        self.button_height = 30
        with open("parameters", "r") as parameters:
            lines = parameters.readlines()
            threshold = lines[0].split(";")
        self.threshold = float(threshold[1])
        self.selected_captor = None
        # Important paths
        self.icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
        self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
        # If folders don't exist, then create them.
        if not os.path.isdir(self.data_path):
            os.mkdir(self.data_path)
        if not os.path.isdir(self.backup_path):
            os.mkdir(self.backup_path)
        # Add Icon
        add_icon_img = Image.open(os.path.join(self.icon_path, "add.jpg"))
        self.add_icon = ImageTk.PhotoImage(
            add_icon_img.resize((self.button_width, self.button_height), Image.ANTIALIAS))
        # Edit Icon
        edit_icon_img = Image.open(os.path.join(self.icon_path, "edit.png"))
        self.edit_icon = ImageTk.PhotoImage(
            edit_icon_img.resize((self.button_width, self.button_height), Image.ANTIALIAS))
        # Bin Icon
        bin_icon_img = Image.open(os.path.join(self.icon_path, "bin.png"))
        self.bin_icon = ImageTk.PhotoImage(
            bin_icon_img.resize((self.button_width, self.button_height), Image.ANTIALIAS))
        # Clock Icon
        clock_icon_img = Image.open(os.path.join(self.icon_path, "clock.png"))
        self.clock_icon = ImageTk.PhotoImage(
            clock_icon_img.resize((self.button_width, self.button_height), Image.ANTIALIAS))
        # Calendar Icon
        calendar_icon_img = Image.open(os.path.join(self.icon_path, "calendar.png"))
        self.calendar_icon = ImageTk.PhotoImage(
            calendar_icon_img.resize((self.button_width, self.button_height), Image.ANTIALIAS))
        # Refresh Icon
        refresh_icon_img = Image.open(os.path.join(self.icon_path, "refresh.png"))
        self.refresh_icon = ImageTk.PhotoImage(
            refresh_icon_img.resize((self.button_width, self.button_height), Image.ANTIALIAS))

        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.captors = None

        ############## MENUBAR ##############
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # CAPTORS Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Captor", menu=edit_menu)
        edit_menu.add_command(label="Add Captor", command=self.adding_captor)
        edit_menu.add_command(label="Rename Captor", command=self.rename_captor)
        edit_menu.add_command(label="Remove Captor", command=self.deleting_captor)
        edit_menu.add_separator()
        edit_menu.add_command(label="Move Up", command=self.move_up)
        edit_menu.add_command(label="Move Down", command=self.move_down)
        edit_menu.add_command(label="Restore", command=self.restore_captor)

        # PLOT Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plot", menu=view_menu)
        view_menu.add_command(label="Jump To ", command=self.jump_to)
        view_menu.add_separator()
        view_menu.add_command(label="Last 24 Hours ", command=self.plot_day)
        view_menu.add_command(label="Last 7 Days ", command=self.plot_7)
        view_menu.add_command(label="Last 30 Days ", command=self.plot_30)


        # OPTIONS Menu
        option_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options ", menu=option_menu)
        option_menu.add_command(label="Edit Threshold", command=self.set_threshold)
        option_menu.add_separator()
        option_menu.add_command(label="FullScreen", command=self.toggleFullScreen)
        option_menu.add_command(label="Exit", command=self.on_close)

        # COLORS
        self.main_color = "#282828"
        self.secondary_color = "#484848"
        self.text_color = "white"
        self.config(bg=self.main_color)
        # WIDGETS
        # List
        self.list_box = None
        self.list_font = None
        # Buttons
        self.captors_buttons = None
        self.add_button = None
        self.rename_button = None
        self.delete_button = None
        # Figure Canvas
        self.plot_range = None
        self.figure_canvas = None
        self.figure = None
        self.ax = None
        # Adding captor window
        self.captor_window = None
        self.captor_entry = None
        self.accept_captor = None
        self.cancel_captor = None
        # Editing captor window
        self.editing_window = None
        self.editing_entry = None
        self.edit_captor = None
        self.cancel_edit = None
        # Restoring captor window
        self.restore_window = None
        self.restore_entry = None
        self.import_button = None
        self.restore_accept = None
        self.restore_label = None
        self.restore_cancel = None
        self.imported_file = None
        # Setting threshold value window
        self.threshold_window = None
        self.threshold_entry = None
        self.set_button = None
        self.cancel_threshold = None
        # Jumping to date window
        self.jump_window = None
        self.jump_calendar = None
        self.jump_accept = None
        self.jump_cancel = None
        self.jump_date = None
        # Plot Buttons
        self.plot_buttons = None
        self.calendar_button = None
        self.clock_button = None
        self.refresh_button = None
        # Gauge
        self.gauge = None
        self.gauge_size = None
        self.fg_gauge = None
        self.gauge_label = None
        self.level = None
        # Status Label
        self.online = False
        self.status = None
        self.status_label = None

        self.initialize_interface()

    def initialize_interface(self):
        # Icon, title and minimal size
        self.tk.call('wm', 'iconphoto', self._w, tk.PhotoImage(file=os.path.join(self.icon_path, "lora.png")))
        # LEFT LIST
        self.list_box = tk.Listbox(self, bg="#484848", activestyle='none', fg="White", relief="flat", font="Helvetica 14 bold")
        with open("Captors", 'r') as file:
            captors = file.readlines()
        for i in range(len(captors)):
            captors[i] = captors[i].replace("\n", "")
            self.list_box.insert(i, captors[i])
            self.list_box.itemconfig(i, {"selectbackground": "#828282"})
        self.captors = captors
        self.list_box.select_set(0)
        self.selected_captor = 0
        self.list_box.bind("<<ListboxSelect>>", self.list_selection)
        self.list_box.grid(column=0, row=0, sticky='news', padx=5, pady=5)

        # BUTTONS
        self.captors_buttons = tk.Frame(self, bg=self.main_color)
        # Adding Button
        self.add_button = tk.Button(self.captors_buttons, command=self.adding_captor, relief="flat",
                                    bg=self.secondary_color, borderwidth=1, fg="White", width=60, height=60)
        self.add_button.grid(column=0, row=0, padx=5, pady=5)
        self.add_button.config(image=self.add_icon)
        # Renaming Button
        self.rename_button = tk.Button(self.captors_buttons, command=self.rename_captor, relief="flat",
                                       bg=self.secondary_color, borderwidth=1, fg="White", width=60, height=60)
        self.rename_button.grid(column=1, row=0, padx=5, pady=5)
        self.rename_button.config(image=self.edit_icon)
        # Deleting Button
        self.delete_button = tk.Button(self.captors_buttons, command=self.deleting_captor, relief="flat",
                                       bg=self.secondary_color, borderwidth=1, fg="White", width=60, height=60)
        self.delete_button.grid(column=2, row=0, padx=5, pady=5)
        self.delete_button.config(image=self.bin_icon)
        # Overall grid
        self.captors_buttons.grid(column=0, row=1, sticky='nwes')
        self.rowconfigure(0, weight=1)

        # PLOTTING CANVAS
        self.plot_range = "day"
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.plot()
        self.figure_canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().grid(row=0, column=2, sticky="nsew", rowspan=2)
        self.columnconfigure(2, weight=1)

        # PLOT BUTTONS
        tkinter.ttk.Separator(self, orient="vertical").grid(column=3, row=0, rowspan=2, sticky='ns')
        self.plot_buttons = tk.Frame(self, bg=self.main_color)
        # Refresh Button
        self.refresh_button = tk.Button(self.plot_buttons, command=self.refresh, relief="flat",
                                        bg=self.secondary_color, borderwidth=1, fg="White", width=60, height=60)
        self.refresh_button.grid(column=0, row=3, padx=5, pady=5)
        self.refresh_button.config(image=self.refresh_icon)
        # Range Clock Button
        self.clock_button = tk.Button(self.plot_buttons, command=self.flip_range, relief="flat",
                                      bg=self.secondary_color, borderwidth=1, fg="White", width=60, height=60)
        self.clock_button.grid(column=0, row=4, padx=5, pady=5)
        self.clock_button.config(image=self.clock_icon)
        # Calendar Button
        self.calendar_button = tk.Button(self.plot_buttons, command=self.jump_to, relief="flat",
                                         bg=self.secondary_color, borderwidth=1, fg="White", width=60, height=60)
        self.calendar_button.grid(column=0, row=5, padx=5, pady=5, sticky='s')
        self.calendar_button.config(image=self.calendar_icon)
        # GAUGE
        self.get_status()  # getting online status and recent level of CPM
        self.gauge_size = 480
        self.gauge = tk.Canvas(self.plot_buttons, bg=self.main_color, relief="flat", width=60, height=self.gauge_size)
        # Getting the gauge level and colour depending on the value and threshold
        if self.level < self.threshold:
            level = self.level * self.gauge_size / self.threshold
            self.fg_gauge = self.gauge.create_rectangle(0, self.gauge_size - level, 60, self.gauge_size, fill="#1de9b6")
        else:
            level = self.gauge_size
            self.fg_gauge = self.gauge.create_rectangle(0, 0, 60, self.gauge_size, fill="#ff1744")
        self.gauge.grid(column=0, row=1, padx=5, pady=5)
        # STATUS
        self.status = tk.Canvas(self.plot_buttons, bg=self.main_color, relief="flat",
                                width=60, height=150, highlightthickness=0)
        # Changing Status based on message presence or not in the last 10 minutes
        if self.online:
            status_text = "ONLINE"
            status_color = "#1de9b6"
        else:
            status_text = "OFFLINE"
            status_color = "#ff1744"
        self.status_label = self.status.create_text(30, 10, text=status_text, angle=270, anchor="w",
                                                    fill=status_color, font="Helvetica 20 bold")
        self.status.grid(column=0, row=0, padx=5, pady=5)
        if self.threshold == int(self.threshold): # If threshold is integer
            label_text = str(round(self.level,2))+"/"+str(int(self.threshold))
        else:
            label_text = str(round(self.level,2)) + "/" + str(self.threshold)
        self.gauge_label = tk.Label(self.plot_buttons, text=label_text,
                                    bg=self.main_color, borderwidth=1, fg="White")
        self.gauge_label.grid(column=0, row=2, padx=5, pady=5)
        self.plot_buttons.grid(column=4, row=0, sticky='s', rowspan=2)

    def refresh(self):
        # Refreshing Plot
        if self.plot_range == "plot_jump":  # if selected day
            self.plot_jump()
        elif self.plot_range == "day":  # if current day
            self.plot_day()
        elif self.plot_range == "week":  # if last week
            self.plot_7()
        elif self.plot_range == "month":  # if last month
            self.plot_30()
        # Refreshing Gauge
        self.get_status()  # getting online status and recent level of CPM
        x0, y0, x1, y1 = self.gauge.coords(self.fg_gauge)
        # Updating the right side canvas' rectangle
        self.gauge.delete("all")
        if self.level < self.threshold:
            level = self.level * self.gauge_size / self.threshold
            self.fg_gauge = self.gauge.create_rectangle(0, self.gauge_size - level, 60, self.gauge_size, fill="#1de9b6")
        else:
            self.fg_gauge = self.gauge.create_rectangle(0, 0, 60, self.gauge_size, fill="#ff1744")
        # Updating the right side label
        if self.online:
            status_text = "ONLINE"
            status_color = "#1de9b6"
        else:
            status_text = "OFFLINE"
            status_color = "#ff1744"
        self.status.itemconfig(self.status_label, text=status_text, fill=status_color)
        if self.threshold == int(self.threshold): # If threshold is integer
            label_text = str(round(self.level,2))+"/"+str(int(self.threshold))
        else:
            label_text = str(round(self.level,2)) + "/" + str(self.threshold)
        self.gauge_label.config(text=label_text)

    def get_status(self):  # Checks CPM levels and if the captor has sent anything in the last 10 minutes
        index = self.list_box.curselection()[0]
        captor = self.list_box.get(index)
        now = dt.datetime.now()
        minutes_10 = now - dt.timedelta(minutes=10)
        date_format = "%Y-%m-%d %H:%M:%S"
        # Loading selected captor's datafile
        try:
            df = pd.read_csv(os.path.join(os.path.join(self.data_path, captor + ".csv")))
        except FileNotFoundError: # if the datafile is non existent
            time = dt.datetime.strftime(now, date_format)
            df = {"time": np.array([time]), "CPM": np.array([0]), "dose": np.array([0])}
        # Converting the timeseries to datetime
        df["time"] = pd.to_datetime(df["time"], format=date_format)
        minutes_mask = (df["time"] > minutes_10)
        minutes = df.loc[minutes_mask]
        minutes = np.array(minutes["CPM"])
        if len(minutes) != 0:
            minutes = minutes[np.logical_not(np.isnan(minutes))]
        if len(minutes) == 0:
            minutes = np.array([0])
        # Getting the mean value for the last 10 minutes
        level = np.nanmean(minutes)
        if level == 0:  # No data sent in the last 10 minutes
            self.online = False
            self.level = 0
        else:
            self.online = True
            self.level = level

    def plot(self):  # Is called to refresh the center plot when a different date has not been selected
        index = self.list_box.curselection()[0]
        captor = self.list_box.get(index)
        today = dt.datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        date_format = "%Y-%m-%d %H:%M:%S"
        # Loading the selected captor datafile
        try:
            df = pd.read_csv(os.path.join(os.path.join(self.data_path, captor + ".csv")))
        except FileNotFoundError: # if datafile is non existent
            time = dt.datetime.strftime(today, date_format)
            df = {"time": np.array([time]), "CPM": np.array([0]), "dose": np.array([0])}
        plot_title = ""
        ###########################       DAY       ###########################
        if self.plot_range == "day":  # Plot of CPM values of today
            plot_title = "Today"
            next_day = today + dt.timedelta(days=1)
            # Converting to datetime
            df["time"] = pd.to_datetime(df["time"], format=date_format)
            # Selecting the selected day
            day_mask = (df["time"] > today)
            day = df.loc[day_mask]
            x = np.full(shape=(24,), fill_value=today)
            y = np.zeros(shape=(24,))
            # Need to calculate the mean values of each hour for the bar plot
            for j in range(24):
                x[j] = today + dt.timedelta(hours=j)
                next_hour = today + dt.timedelta(hours=j + 1)
                hour_mask = (day["time"] > x[j]) & (day["time"] < next_hour)
                hour = day.loc[hour_mask]
                hour = np.array(hour["CPM"])
                if len(hour) != 0:
                    hour = hour[np.logical_not(np.isnan(hour))]
                if len(hour) == 0:
                    hour = np.array([0])
                y[j] = np.nanmean(np.array(hour))
            x = np.append(x, today + dt.timedelta(days=1))
            width = np.full_like(y, 0.5)
            # Ticks and Labels
            x_ticks = np.linspace(0, 24, num=25)
            x_bars = np.linspace(0, 23, num=24) + 0.5
            x_tick_labels = []
            for i in range(len(x)):
                label = dt.datetime.strftime(x[i], date_format)
                x_tick_labels.append(label[11:16])
            # Colors
            colors = np.full_like(x[:-1], "#1de9b6")
            over_indices = y >= self.threshold
            colors[over_indices] = "#ff1744"

        ###########################       WEEK       ###########################
        elif self.plot_range == "week":  # Plot of CPM values for the last 7 days
            plot_title = "Last 7 Days"
            delta = dt.timedelta(days=6)
            last7 = today - delta
            # Converting to datetime
            df["time"] = pd.to_datetime(df["time"], format=date_format)
            # Selecting the selected day
            week_mask = (df["time"] > last7)
            week = df.loc[week_mask]
            x = np.full(shape=(7,), fill_value=today)
            y = np.zeros(shape=(7,))
            # Need to calculate the mean values of each day for the bar plot
            for j in range(7):
                x[j] = last7 + dt.timedelta(days=j)
                next_day = last7 + dt.timedelta(days=j + 1)
                day_mask = (week["time"] > x[j]) & (week["time"] < next_day)
                day = week.loc[day_mask]
                day = np.array(day["CPM"])
                if len(day) != 0:
                    day = day[np.logical_not(np.isnan(day))]
                if len(day) == 0:
                    day = np.array([0])
                y[j] = np.nanmean(np.array(day))
            # Widths
            width = np.full_like(y, 0.5)
            # Ticks and Labels
            x_ticks = np.linspace(0, 6, num=7)
            x_bars = x_ticks
            x_tick_labels = []
            for i in range(len(x)):
                label = dt.datetime.strftime(x[i], date_format)
                x_tick_labels.append(label[8:10] + "/" + label[5:7] + "/" + label[2:4])
            # Colors
            colors = np.full_like(x, "#1de9b6")
            over_indices = y >= self.threshold
            colors[over_indices] = "#ff1744"

        ###########################       MONTH       ###########################
        elif self.plot_range == "month":  # Plot of CPM values for the last 30 days
            plot_title = "Last 30 Days"
            delta = dt.timedelta(days=29)
            last30 = today - delta
            # Converting to datetime
            df["time"] = pd.to_datetime(df["time"], format=date_format)
            # Selecting the selected day
            month_mask = (df["time"] > last30)
            month = df.loc[month_mask]
            x = np.full(shape=(30,), fill_value=today)
            y = np.zeros(shape=(30,))
            # Need to calculate the mean values of each day for the bar plot
            for j in range(30):
                x[j] = last30 + dt.timedelta(days=j)
                next_day = last30 + dt.timedelta(days=j + 1)
                day_mask = (month["time"] > x[j]) & (month["time"] < next_day)
                day = month.loc[day_mask]
                day = np.array(day["CPM"])
                if len(day) != 0:
                    day = day[np.logical_not(np.isnan(day))]
                if len(day) == 0:
                    day = np.array([0])
                y[j] = np.nanmean(day)
            # Widths
            width = np.full_like(y, 0.5)
            # Ticks and Labels
            x_ticks = np.linspace(0, 29, num=30)
            x_bars = x_ticks
            x_tick_labels = []
            for i in range(len(x)):
                label = dt.datetime.strftime(x[i], date_format)
                x_tick_labels.append(label[8:10] + "/" + label[5:7] + "/" + label[2:4])
            # Colors
            colors = np.full_like(x, "#1de9b6")
            over_indices = y >= self.threshold
            colors[over_indices] = "#ff1744"

        ###########################       FIGURE       ###########################
        self.ax.clear()  # Clearing figure
        self.ax.bar(x_bars, y, width=width, color=colors[0:-1]) # Creating the bar plot
        self.ax.set_xticks(x_ticks)  # Putting the X axis coordinates
        self.ax.set_xticklabels(x_tick_labels, rotation=45)  # Putting the x axis labels
        # Setting up X axis range
        if self.plot_range == "day":
            self.ax.set_xlim(0, 24)
        if self.plot_range == "week":
            self.ax.set_xlim(-0.5, 6.5)
        if self.plot_range == "half_month":
            self.ax.set_xlim(-0.5, 13.5)
        if self.plot_range == "month":
            self.ax.set_xlim(-0.5, 29.5)
        # Setting up plot's colours
        self.figure.patch.set_facecolor("#282828")
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.set_facecolor("#282828")
        # Setting up grid
        self.ax.grid(axis='y', alpha=0.5, linestyle='--')
        self.ax.set_axisbelow(True)
        # Setting up legend
        self.ax.set_ylabel("CPM")
        # Changing axis' colours
        self.ax.yaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.xaxis.set_tick_params(labelsize=7)
        self.ax.yaxis.set_tick_params(labelsize=7)
        # Setting up Title
        title = self.ax.set_title(plot_title)
        plt.setp(title, color='white')

    def list_selection(self, event):
        # This method is called each time an item is called in the captors' list
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.selected_captor = index
            self.refresh()  # Refreshing the center plot, gauge and status

    def flip_range(self):
        if self.plot_range == "plot_jump":
            self.plot_day()
        elif self.plot_range == "day":
            self.plot_7()
        elif self.plot_range == "week":
            self.plot_30()
        elif self.plot_range == "month":
            self.plot_day()

    def adding_captor(self): # Opens the captor adding window
        # Setting up the window
        self.captor_window = tk.Toplevel(self)
        self.captor_window.grab_set()
        self.captor_window.title("Adding New Captor")
        self.captor_window.geometry("335x50")
        self.captor_window.config(bg=self.main_color)
        self.captor_window.resizable(width=False, height=False)
        # Placing widgets
        self.captor_entry = tk.Entry(self.captor_window)
        self.captor_entry.place(x=5, y=5, width=150, height=40)
        self.accept_captor = tk.Button(self.captor_window, text="Add", command=self.adding_finish,
                                       bg=self.secondary_color, borderwidth=1, fg="White")
        self.accept_captor.place(x=165, y=5, width=80, height=40)
        self.cancel_captor = tk.Button(self.captor_window, text="Cancel", command=self.captor_window.destroy,
                                       bg=self.secondary_color, borderwidth=1, fg="White")
        self.cancel_captor.place(x=250, y=5, width=80, height=40)

    def adding_finish(self):  # Is called when a captor is added
        new_captor = self.captor_entry.get()
        header = ['time', 'CPM', 'dose']
        if new_captor not in self.captors:  # if the captor does not already exists
            # Creating CSV File
            if os.path.exists(os.path.join(self.data_path, new_captor + ".csv")):  # File already exists
                response = tkinter.messagebox.askyesno('Warning', 'A file for this captor already exists, '
                                                                  'do you wish to overide it ?')
                if response:
                    with open(os.path.join(self.data_path, new_captor + ".csv"), "w") as file:
                        csv_writer = csv.writer(file)
                        csv_writer.writerow(header)
                    N = self.list_box.size()
                    # inserting into the captor's list
                    self.list_box.insert(N, new_captor)
                    self.list_box.itemconfig(N, {"selectbackground": "#828282"})
                    self.captors.insert(N, new_captor)
                    with open("Captors", "w") as file:
                        for i in range(len(self.captors)):
                            file.write(self.captors[i] + "\n")
                    self.captor_window.destroy()
            else:
                with open(os.path.join(self.data_path, new_captor + ".csv"), "w") as file:
                    csv_writer = csv.writer(file)
                    csv_writer.writerow(header)
                N = self.list_box.size()
                # inserting into the captor's list
                self.list_box.insert(N, new_captor)
                self.list_box.itemconfig(N, {"selectbackground": "#828282"})
                self.captors.insert(N, new_captor)
                with open("Captors", "w") as file:
                    for i in range(len(self.captors)):
                        file.write(self.captors[i] + "\n")
                self.captor_window.destroy()
        else:
            warning = tkinter.messagebox.showerror("Error", "This captor already exists !")

    def restore_captor(self): # opens the captor restoring window
        # Setting up the window
        self.restore_window = tk.Toplevel(self)
        self.restore_window.grab_set()
        self.restore_window.title("Restoring Captor")
        self.restore_window.geometry("380x85")
        self.restore_window.config(bg=self.main_color)
        self.restore_window.resizable(width=False, height=False)
        # Placing the widgets
        self.restore_entry = tk.Entry(self.restore_window)
        self.restore_entry.place(x=5, y=40, width=200, height=40)
        self.restore_accept = tk.Button(self.restore_window, text="Restore", command=self.restoring_finish,
                                        bg=self.secondary_color, borderwidth=1, fg="White")
        self.restore_accept.place(x=210, y=40, width=80, height=40)
        self.restore_cancel = tk.Button(self.restore_window, text="Cancel", command=self.restore_window.destroy,
                                        bg=self.secondary_color, borderwidth=1, fg="White")
        self.restore_cancel.place(x=295, y=40, width=80, height=40)
        self.import_button = tk.Button(self.restore_window, text="Import", command=self.import_file,
                                       bg=self.secondary_color, borderwidth=1, fg="White")
        self.import_button.place(x=260, y=5, width=65, height=30)
        self.restore_label = tk.Label(self.restore_window, text="Selected File : None", bg=self.main_color,
                                      borderwidth=1, fg="White")
        self.restore_label.place(x=5, y=5, width=250, height=30)

    def import_file(self):  # Is called to fetch the data backup for restoring a deleted captor
        self.imported_file = askopenfilename(filetypes=[("CSV Files", ".csv")], initialdir=self.backup_path)
        self.restore_label.config(text="Selected File : " + os.path.basename(self.imported_file))

    def restoring_finish(self):  # Is called when we want to restore a captor
        captor_name = self.restore_entry.get()
        if captor_name not in self.captors: # if the captor does not already exists
            # Moving CSV File
            old_path = self.imported_file
            new_path = os.path.join(self.data_path, captor_name + ".csv")
            shutil.move(old_path, new_path)
            # Adding to captors
            N = self.list_box.size()
            # inserting into the captor's list
            self.list_box.insert(N, captor_name)
            self.list_box.itemconfig(N, {"selectbackground": "#828282"})
            self.captors.insert(N, captor_name)
            with open("Captors", "w") as file:
                for i in range(len(self.captors)):
                    file.write(self.captors[i] + "\n")
            self.restore_window.destroy()
        else:
            warning = tkinter.messagebox.showerror("Error", "This captor already exists !")

    def move_up(self): # Is called to move a captor up a slot in the list
        index = self.list_box.curselection()[0]
        if index == 0:
            pass
        else:
            self.captors[index], self.captors[index - 1] = self.captors[index - 1], self.captors[index]
            with open("Captors", "w") as file:
                for i in range(len(self.captors)):
                    file.write(self.captors[i] + "\n")
            self.list_box.delete(0, 'end')
            for i in range(len(self.captors)):
                self.list_box.insert(i, self.captors[i])
                self.list_box.itemconfig(i, {"selectbackground": "#828282"})
            self.list_box.select_set(index - 1)

    def move_down(self):  # Is called to move a captor down a slot in the list
        index = self.list_box.curselection()[0]
        N = self.list_box.size()
        if index == N - 1:
            pass
        else:
            self.captors[index], self.captors[index + 1] = self.captors[index + 1], self.captors[index]
            with open("Captors", "w") as file:
                for i in range(len(self.captors)):
                    file.write(self.captors[i] + "\n")
            self.list_box.delete(0, 'end')
            for i in range(len(self.captors)):
                self.list_box.insert(i, self.captors[i])
                self.list_box.itemconfig(i, {"selectbackground": "#828282"})
            self.list_box.select_set(index + 1)

    def rename_captor(self):  # Opens the window to rename a captor
        # Setting up the window
        self.editing_window = tk.Toplevel(self)
        self.editing_window.grab_set()
        self.editing_window.title("Renaming Captor")
        self.editing_window.geometry("335x50")
        self.editing_window.config(bg=self.main_color)
        self.editing_window.resizable(width=False, height=False)
        self.editing_entry = tk.Entry(self.editing_window)
        index = self.list_box.curselection()[0]
        edited_captor = self.captors[index]
        # Placing the different widgets
        self.editing_entry.insert(tk.END, edited_captor)
        self.editing_entry.place(x=5, y=5, width=150, height=40)
        self.edit_captor = tk.Button(self.editing_window, text="Edit", command=self.renaming_finish,
                                     bg=self.secondary_color, borderwidth=1, fg="White")
        self.edit_captor.place(x=165, y=5, width=80, height=40)
        self.cancel_edit = tk.Button(self.editing_window, text="Cancel", command=self.editing_window.destroy,
                                     bg=self.secondary_color, borderwidth=1, fg="White")
        self.cancel_edit.place(x=250, y=5, width=80, height=40)

    def renaming_finish(self):  # Is called when a captor is renamed
        edited_captor = self.editing_entry.get()
        if edited_captor in self.captors and edited_captor != self.captors[self.selected_captor]:
            warning = tkinter.messagebox.showerror("Error", "This captor already exists !")
        else:
            index = self.selected_captor
            old_captor = self.captors[index]
            self.captors[index] = edited_captor
            self.list_box.delete(index)
            self.list_box.insert(index, edited_captor)
            self.list_box.itemconfig(index, {"selectbackground": "#828282"})
            with open("Captors", "w") as file:
                for i in range(len(self.captors)):
                    file.write(self.captors[i] + "\n")
            self.editing_window.destroy()
            self.list_box.select_set(index)
            # RENAMING CSV FILE TO NEW NAME
            old_name = os.path.join(self.data_path, old_captor + ".csv")
            new_name = os.path.join(self.data_path, edited_captor + ".csv")
            os.rename(old_name, new_name)

    def deleting_captor(self):  # Is called when we delete a captor
        # Messagebox for verification
        response = tkinter.messagebox.askyesno('Warning', 'Are you sure you want to remove this captor ?')
        if response:
            index = self.list_box.curselection()[0]
            name = self.captors[index]
            # CREATING BACKUP
            old_path = os.path.join(self.data_path, name + ".csv")
            new_path = os.path.join(self.backup_path, "backup_" + name + ".csv")
            shutil.move(old_path, new_path)
            # UPDATING CAPTOR LIST
            self.list_box.delete(index)
            self.captors.pop(index)
            with open("Captors", "w") as file:
                for i in range(len(self.captors)):
                    file.write(self.captors[i] + "\n")

    def set_threshold(self):
        # Setting up the window
        self.threshold_window = tk.Toplevel(self)
        self.threshold_window.grab_set()
        self.threshold_window.title("Setting Threshold")
        self.threshold_window.geometry("335x50")
        self.threshold_window.config(bg=self.main_color)
        self.threshold_window.resizable(width=False, height=False)
        self.threshold_entry = tk.Entry(self.threshold_window)
        previous_threshold = str(self.threshold)
        # Placing the widgets
        self.threshold_entry.insert(tk.END, previous_threshold)
        self.threshold_entry.place(x=5, y=5, width=150, height=40)
        self.set_button = tk.Button(self.threshold_window, text="Set", command=self.threshold_finish,
                                    bg=self.secondary_color, borderwidth=1, fg="White")
        self.set_button.place(x=165, y=5, width=80, height=40)
        self.cancel_threshold = tk.Button(self.threshold_window, text="Cancel", command=self.threshold_window.destroy,
                                          bg=self.secondary_color, borderwidth=1, fg="White")
        self.cancel_threshold.place(x=250, y=5, width=80, height=40)

    def threshold_finish(self):  # is called when threshold value needs to be changed
        new_threshold = self.threshold_entry.get()
        # Verifying if given value is float or integer
        if all([i.isnumeric() for i in new_threshold.split('.', 1)]):
            self.threshold = float(new_threshold)
            self.threshold_window.destroy()
            self.list_box.select_set(self.selected_captor)
            self.refresh()
            with open("parameters", "r") as file:
                lines = file.readlines()
            lines[0] = "THRESHOLD;" + str(self.threshold) + "\n"
            with open("parameters", "w") as file:
                for i in lines:
                    file.write(i)

        else:  # If the threshold entered value is not right
            warning = tkinter.messagebox.showerror("Setting Threshold", " Invalid value, must be integer or float.")

    def plot_30(self):  # Plots the data on a 30 days time range
        self.plot_range = "month"
        self.ax.clear()  # Clearing figure
        self.plot()  # plotting with current parameters
        self.figure_canvas.draw()

    def plot_7(self):  # Plots the data on a 7 days time range
        self.plot_range = "week"
        self.ax.clear()  # Clearing figure
        self.plot()  # plotting with current parameters
        self.figure_canvas.draw()

    def plot_day(self):  # Plots the data on a 1 day time range
        self.plot_range = "day"
        self.ax.clear()  # Clearing figure
        self.plot()  # plotting with current parameters
        self.figure_canvas.draw()

    def jump_to(self):  # Opens the Calendar Window to select a day you want data from
        # Setting up the window
        self.jump_window = tk.Toplevel(self)
        self.jump_window.grab_set()
        self.jump_window.title("Jump To")
        self.jump_window.geometry("335x380")
        self.jump_window.config(bg=self.main_color)
        self.jump_window.resizable(width=False, height=False)
        today = dt.datetime.now()
        # Placing widgets
        self.jump_calendar = Calendar(self.jump_window, selectmode='day', year=today.year,
                                      month=today.month, day=today.day, date_pattern='MM/dd/yyyy')
        self.jump_calendar.place(x=5, y=5, width=325, height=325)
        self.jump_accept = tk.Button(self.jump_window, text="Select", command=self.accept_jump,
                                     bg=self.secondary_color, borderwidth=1, fg="White")
        self.jump_accept.place(x=5, y=335, width=160, height=40)
        self.jump_cancel = tk.Button(self.jump_window, text="Cancel", command=self.jump_window.destroy,
                                     bg=self.secondary_color, borderwidth=1, fg="White")
        self.jump_cancel.place(x=170, y=335, width=160, height=40)

    def accept_jump(self):  # Is called when the date has been chosen in the calendar
        self.plot_range = "plot_jump"
        self.jump_date = dt.datetime.strptime(self.jump_calendar.get_date(), '%m/%d/%Y')
        self.refresh()  # Refreshes teh entire figure and gauge
        self.jump_window.destroy()

    def plot_jump(self):  # Is called when we want to plot data from a specific date chosen from a calendar widget
        index = self.list_box.curselection()[0]
        captor = self.list_box.get(index)
        date_format = "%Y-%m-%d %H:%M:%S"
        today = dt.datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        # Loading the data from the selected captor
        try:
            df = pd.read_csv(os.path.join(self.data_path, captor + ".csv"))
        except FileNotFoundError:  # creating a "false" datafile if the file is non existent
            time = dt.datetime.strftime(today, date_format)
            df = {"time": np.array([time]), "CPM": np.array([0]), "dose": np.array([0])}
        # Setting Up Title
        if self.jump_date == today:
            plot_title = "Today"
        else:
            plot_title = dt.datetime.strftime(self.jump_date, '%m/%d/%Y')
        next_day = self.jump_date + dt.timedelta(days=1)
        # Converting the time data into datetime format
        df["time"] = pd.to_datetime(df["time"], format=date_format)
        # Selecting the selected day in the data
        day_mask = (df["time"] > self.jump_date) & (df["time"] < next_day)
        day = df.loc[day_mask]
        x = np.full(shape=(24,), fill_value=self.jump_date)
        y = np.zeros(shape=(24,))
        # Need to calculate the mean values of each hour for the bar plot
        for j in range(24):
            x[j] = self.jump_date + dt.timedelta(hours=j)
            next_hour = self.jump_date + dt.timedelta(hours=j + 1)
            hour_mask = (day["time"] > x[j]) & (day["time"] < next_hour)
            hour = day.loc[hour_mask]
            hour = np.array(hour["CPM"])
            if len(hour) != 0:
                hour = hour[np.logical_not(np.isnan(hour))]
            if len(hour) == 0:
                hour = np.array([0])
            y[j] = np.nanmean(np.array(hour))
        x = np.append(x, self.jump_date + dt.timedelta(days=1))
        # Widths
        width = np.full_like(y, 0.5)
        # Ticks and Labels
        x_ticks = np.linspace(0, 24, num=25)
        x_bars = np.linspace(0, 23, num=24) + 0.5
        x_tick_labels = []
        for i in range(len(x)):
            label = dt.datetime.strftime(x[i], date_format)
            x_tick_labels.append(label[11:16])
        # Colors
        colors = np.full_like(x[:-1], "#1de9b6")
        over_indices = y >= self.threshold
        colors[over_indices] = "#ff1744"
        # Figure
        self.ax.clear()
        self.ax.bar(x_bars, y, width=width, color=colors[0:-1])
        self.ax.set_xlim(0, 24)
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(x_tick_labels, rotation=45)
        if np.all((y == 0.0)):  # If no data
            self.ax.set_ylim(0, 25)
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.set_facecolor("#282828")
        self.ax.grid(axis='y', alpha=0.5, linestyle='--')
        self.ax.set_axisbelow(True)
        self.ax.set_ylabel("CPM")
        self.ax.yaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.xaxis.set_tick_params(labelsize=6)
        self.ax.yaxis.set_tick_params(labelsize=6)
        title = self.ax.set_title(plot_title)
        plt.setp(title, color='white')
        # Updating the center plot
        self.figure_canvas.draw()

    def on_close(self):  # Is called when we want to exit the application
        # Creation of a message choice box
        response = tkinter.messagebox.askyesno('Exit', 'Are you sure you want to exit?')
        if response:
            self.destroy()

    def toggleFullScreen(self):  # Is called when we want to change into fullscreen or remove it.
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

