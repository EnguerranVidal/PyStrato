import tkinter as tk
import tkinter.messagebox
import tkinter.font
import tkinter.ttk

import os
import sys
from PIL import Image

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np
from sat_tracker.tracker import *
from sat_tracker.database import *


class PySat_GUI(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PySat")
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        ##################  PARAMETERS  ###################
        ##################  MENU  ##################
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        orbit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Orbit", menu=orbit_menu)
        propagate_menu = tk.Menu(orbit_menu, tearoff=0)
        orbit_menu.add_cascade(label="Propagated Recently", menu=propagate_menu)
        orbit_menu.add_separator()
        orbit_menu.add_command(label="New Orbit", command=self.new_orbit)
        orbit_menu.add_command(label="Open Orbit", command=self.open_orbit)
        orbit_menu.add_command(label="Save Orbit", command=self.save_orbit)
        orbit_menu.add_command(label="Save Orbit As", command=self.save_orbit_as)

        track_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tracker", menu=track_menu)
        tracked_menu = tk.Menu(orbit_menu, tearoff=0)
        track_menu.add_cascade(label="Tracked Recently", menu=tracked_menu)
        track_menu.add_separator()
        track_menu.add_command(label="Import TLE File", command=self.import_tle)
        track_menu.add_command(label="Preferences", command=self.tracker_preferences_open)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)

        ##################  VARIABLES  ##################
        # ENGINE
        self.database = None
        self.database_toggle = []
        self.database_categories = []
        self.database_sources = []
        self.database_supp = []
        self.trackable_names = None
        self.trackable_numbers = None
        self.tracker = None
        # COLORS
        self.main_color = "#282828"
        self.secondary_color = "#484848"
        self.text_color = "white"
        self.config(bg=self.main_color)
        # WINDOWS
        # Tracker Preferences
        self.tracker_preferences_window = None
        # WIDGETS
        # Search Bar
        self.search_frame = None
        self.search_var = None
        self.search_entry = None
        self.search_list_box = None
        self.select_button = None
        # Selection Bar
        self.selected_frame = None
        self.tracked_satellites = []
        self.selected_list_box = None
        self.delete_button = None
        # Notebooks
        self.frame_notebook = None
        # Tracking Tab
        self.tracking_tab = None
        self.tracking_figure = None
        self.tracking_ax = None
        self.night_shade = None
        self.tracking_canvas = None
        self.tracking_lines = []
        self.tracking_points = []
        # 3D View Tab
        self.view_3D_tab = None
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.data_path = os.path.join(self.data_dir, "NORAD.txt")

        ##################  INITIALIZATION  ##################
        self.initialize_UI()
        ################# REFRESHING LOOP ##################
        self.refresh()

    def initialize_UI(self):
        #### SATELLITES DATABASE ####
        self.database = TLE_Database(self.data_path, load_online=True)
        self.tracker = Tracker(self.database)

        #### MAIN TABS ####
        self.frame_notebook = tk.ttk.Notebook(self, width=1000, height=500)
        self.tracking_tab = tk.Frame(self.frame_notebook, bg=self.main_color)
        self.view_3D_tab = tk.Frame(self.frame_notebook, bg=self.main_color)
        self.frame_notebook.add(self.tracking_tab, text="Live Tracking")
        self.frame_notebook.add(self.view_3D_tab, text="3D View")
        self.frame_notebook.grid(column=0, row=0, rowspan=2)

        #### SEARCH BAR ####
        self.search_frame = tk.Frame(self)
        self.trackable_names = self.database.deconstructed_data[0]
        self.trackable_numbers = self.database.deconstructed_data[1]
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_search_list)
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_list_box = tk.Listbox(self.search_frame, selectmode=tk.MULTIPLE, width=40, height=12)
        self.search_entry.grid(row=0, column=0, padx=10, pady=3)
        self.search_list_box.grid(row=1, column=0, padx=10, columnspan=2)
        self.select_button = tk.Button(self.search_frame, text="+", command=self.search_select, width=3)
        self.select_button.grid(column=1, row=0, sticky="w")
        self.update_search_list()
        self.search_frame.grid(column=1, row=0, sticky="ne")

        #### SELECTED BAR ####
        self.selected_frame = tk.Frame(self)
        self.tracked_satellites = []
        self.selected_list_box = tk.Listbox(self.selected_frame, selectmode=tk.MULTIPLE, width=40, height=12)
        self.selected_list_box.bind("<<ListboxSelect>>", self.satellite_selected)
        self.delete_button = tk.Button(self.selected_frame, text="-", command=self.selection_list_delete, width=3)
        self.selected_list_box.grid(row=1, column=0)
        self.delete_button.grid(row=0, column=0)
        self.update_selection_list()
        self.selected_frame.grid(column=1, row=1, sticky="new")

        #### LIVE TRACKING TAB ####
        self.tracking_figure = Figure(dpi=100)
        self.tracking_ax = self.tracking_figure.add_subplot(111, projection=ccrs.PlateCarree())
        self.tracking_ax.set_extent([-180, 180, -90, 90])
        self.tracking_ax.stock_img()
        self.tracking_ax.coastlines()
        current_time = datetime.datetime.utcnow()
        self.night_shade = self.tracking_ax.add_feature(Nightshade(current_time, alpha=0.4))
        self.tracking_ax.gridlines(draw_labels=False, linewidth=1, color='blue', alpha=0.3, linestyle='--')
        self.live_tracking_plot()
        self.tracking_canvas = FigureCanvasTkAgg(self.tracking_figure, master=self.tracking_tab)
        self.tracking_canvas.draw()
        self.tracking_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", rowspan=2)

        #### 3D VIEW TAB ####

        #### COLUMN CONFIGURATION ####
        self.grid_columnconfigure(0, weight=1)
        self.tracking_tab.grid_columnconfigure(0, weight=1)

        #### ROW CONFIGURATION ####
        self.grid_rowconfigure(0, weight=1)
        self.tracking_tab.grid_rowconfigure(0, weight=1)

    def load_configuration(self):
        with open("configuration", "r") as file:
            lines = file.readlines()
        # DATABASE = LINE 1
        self.database_toggle = []
        self.database_categories = []
        line_1 = lines[0].replace("{", " ").replace("}", " ").split()[1].split(";")
        for i in range(len(line_1)):
            self.database_toggle.append(tk.BooleanVar(self, bool(int(line_1[i][-1]))))
            line_1[i] = line_1[i].split("=")
            self.database_categories.append(line_1[i][0].replace("_", " "))
        # LINKS = LINE 2
        line_2 = lines[1].replace("{", " ").replace("}", " ").split()[1].split(";")
        self.database_sources = [None] * len(self.database_categories)
        for i in range(len(self.database_sources)):
            line_2[i] = line_2[i].split("=")
            index = self.database_categories.index(line_2[i][0].replace("_", " "))
            self.database_sources[index] = line_2[i][1]
        # SUPP LINKS = LINE 3
        self.database_supp = []
        line_3 = lines[2].replace("{", " ").replace("}", " ").split()
        if len(line_3) != 1:
            line_3 = line_3[1].split(";")
            for i in range(len(line_3)):
                self.database_supp.append(line_3[i].split("="))

    def save_configuration(self):
        with open("configuration", "r") as file:
            lines = file.readlines()
        file = open("configuration", "w")
        # UPDATING DATABASE TOGGLE
        file.write(lines[0])
        file.write(lines[1])
        # UPDATING SUPPLEMENTARY SOURCES
        file.write("SUPP_SOURCES{")
        name = self.database_supp[0][0]
        link = self.database_supp[0][1]
        file.write(name + "=" + link)
        for i in range(len(self.database_supp) - 1):
            name = self.database_supp[i][0]
            link = self.database_supp[i][1]
            file.write(";" + name + "=" + link)
        file.write("}\n")
        # CLOSING FILE
        file.close()

    def live_tracking_plot(self):
        # Removing past Nightshade and adding current
        self.night_shade.remove()
        current_time = datetime.datetime.utcnow()
        self.night_shade = self.tracking_ax.add_feature(Nightshade(current_time, alpha=0.4))
        # Removing past Ground-Tracks
        if len(self.tracking_lines) != 0:
            for i in self.tracking_lines:
                self.tracking_ax.lines.pop(0)
            self.tracking_lines = []
        # Removing past Nadirs
        if len(self.tracking_points) != 0:
            for i in self.tracking_points:
                i.remove()
            self.tracking_points = []
        # Getting Estimations from Tracker
        t0 = time.time()
        N = 241
        times = np.linspace(t0 - 3600, t0 + 3600, num=241)
        if len(self.tracked_satellites) != 0:
            Long, Lat, H = self.tracker.sub_points(times)
            Long = np.degrees(Long)
            Lat = np.degrees(Lat)
        # Plotting Ground Tracks and current Nadir Positions
        selection = self.selected_list_box.curselection()
        middle = int(N/2)
        for i in range(len(self.tracked_satellites)):
            if i in selection:
                line = self.tracking_ax.plot(Long[i, :], Lat[i, :], transform=ccrs.Geodetic(), color="red", zorder=1)
                point = self.tracking_ax.scatter(Long[i, middle], Lat[i, middle], color="white", s=25,
                                                 alpha=1, transform=ccrs.PlateCarree(), zorder=2, edgecolors='black')
                self.tracking_lines.append(line)
            else:
                point = self.tracking_ax.scatter(Long[i, middle], Lat[i, middle], color="white", s=25,
                                                 alpha=1, transform=ccrs.PlateCarree(), zorder=2, edgecolors='black')
            self.tracking_points.append(point)

    def update_search_list(self, *args):
        search_term = self.search_var.get()
        self.search_list_box.delete(0, tk.END)
        for i in range(len(self.trackable_names)):
            sat_name = self.trackable_names[i]
            sat_number = self.trackable_numbers[i]
            if search_term.lower() in sat_name.lower() or search_term in str(sat_number):
                self.search_list_box.insert(tk.END, sat_name)

    def search_select(self):
        selection = self.search_list_box.curselection()
        for i in selection:
            entered = self.search_list_box.get(i)
            if entered not in self.tracked_satellites:
                self.tracked_satellites.append(self.trackable_names[i])
                self.tracked_satellites.sort()
        self.update_selection_list()
        # Updating Tracker
        self.tracker.update_objects(self.tracked_satellites)
        # Updating Plots
        self.update_plots()

    def update_selection_list(self, *args):
        self.selected_list_box.delete(0, tk.END)
        for item in self.tracked_satellites:
            self.selected_list_box.insert(tk.END, item)

    def satellite_selected(self, *args):
        self.update_plots()

    def delete_all(self, *args):
        self.tracked_satellites = []
        self.update_selection_list()
        # Updating Tracker
        self.tracker.update_objects(self.tracked_satellites)
        # Updating Plots
        self.update_plots()

    def selection_list_delete(self):
        selection = self.selected_list_box.curselection()
        selection = list(selection)
        for i in selection[::-1]:
            self.tracked_satellites.pop(i)
        self.update_selection_list()
        # Updating Tracker
        self.tracker.update_objects(self.tracked_satellites)
        # Updating Plots
        self.update_plots()

    def find_current_tab(self, *args):
        name = self.frame_notebook.tab(self.frame_notebook.select(), "text")
        return name

    def update_plots(self):
        if self.find_current_tab() == "Live Tracking":
            self.live_tracking_plot()
            self.tracking_canvas.draw()
        if self.find_current_tab() == "3D View":
            pass

    def refresh(self):
        ### ADD HERE : CONTINUOUS UPDATES NEEDED ###
        self.update_plots()
        self.after(500, self.refresh)

    def new_orbit(self):
        pass

    def save_orbit(self):
        pass

    def open_orbit(self):
        pass

    def save_orbit_as(self):
        pass

    def import_tle(self):
        pass

    def tracker_preferences_open(self):
        self.tracker_preferences_window = tk.Toplevel(self)
        self.tracker_preferences_window.grab_set()
        self.tracker_preferences_window.title("Tracker Preferences")
        self.tracker_preferences_window.geometry("500x500")
        pass

    def tracker_preferences_accept(self):
        pass

    def tracker_preferences_cancel(self):
        pass

    def on_close(self):  # Is called when we want to exit the application
        # Creation of a message choice box
        response = tkinter.messagebox.askyesno('Exit', 'Are you sure you want to exit?')
        if response:
            self.destroy()

    def toggleFullScreen(self):  # Is called when we want to change into fullscreen or remove it.
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))
