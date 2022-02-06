import tkinter as tk
import tkinter.messagebox
import tkinter.font
import tkinter.ttk as ttk
from ttkthemes import ThemedStyle

import os
import sys
from PIL import Image

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np


class GUI(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Ground Station")
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.resizable(True, True)
        ##################  PARAMETERS  ###################
        # self.geometry('200x200')
        self.set_style = ttk.Style(self)
        self.tk.call('source', 'azure dark/azure dark.tcl')
        self.set_style.theme_use('azure')
        self.set_style.configure("Accentbutton", foreground='white')
        self.set_style.configure("Togglebutton", foreground='white')

        ##################  MENU  ##################
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        ##################  VARIABLES  ##################
        self.balloons_notebook = None
        self.A_tab = None
        self.B_tab = None
        ##################  INITIALIZATION  ##################
        self.initialize_UI()

    def initialize_UI(self):
        self.balloons_notebook = tk.ttk.Notebook(self, width=1000, height=500)
        self.A_tab = tk.Frame(self.balloons_notebook)
        self.B_tab = tk.Frame(self.balloons_notebook)
        self.balloons_notebook.add(self.A_tab, text="Balloon A")
        self.balloons_notebook.add(self.B_tab, text="Balloon B")
        self.balloons_notebook.grid(column=0, row=0)

    def dark_style(self):
        self.set_style = ttk.Style(self)
        self.tk.call('source', 'azure dark/azure dark.tcl')
        self.set_style.theme_use('azure')
        self.set_style.configure("Accentbutton", foreground='white')
        self.set_style.configure("Togglebutton", foreground='white')

    def find_current_tab(self, *args):
        name = self.frame_notebook.tab(self.frame_notebook.select(), "text")
        return name

    def on_close(self):  # Is called when we want to exit the application
        # Creation of a message choice box
        response = tkinter.messagebox.askyesno('Exit', 'Are you sure you want to exit?')
        if response:
            self.destroy()

    def toggleFullScreen(self):  # Is called when we want to change into fullscreen or remove it.
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))