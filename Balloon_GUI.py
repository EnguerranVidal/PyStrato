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


class GUI(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("PySat")
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        ##################  PARAMETERS  ###################
        ##################  MENU  ##################
        menubar = tk.Menu(self)
        self.config(menu=menubar)