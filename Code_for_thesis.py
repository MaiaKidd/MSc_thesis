#! /usr/bin/env python3

#############################################################
#############################################################

# These variables can be edited to change the output of the graphs 


# This list maps each code to a rgb color 
# with colors values in the range [0,255]
code_colors = [
    ("Q1ta", (130, 130, 130)),
    ("Q3a", (130, 130, 130)),
    ("Q7u", (43, 133, 161)),
    ("Q8i",  (194, 158, 215)),
    ("Q8c",  (255, 207, 255)),
    ("Q9w",  (79, 122, 56)),
    ("eQw", (255, 127, 127)),
]

# These control the axis labels of the generated graph
x_axis_label = "Distance, East-West (m)"
y_axis_label = "Elevation (m)"

# Specify the axis limits 
x_min = 0
x_max = 20250

y_min = 120
y_max = 530

#############################################################
#############################################################


import csv
import collections
import itertools
import os
import tkinter as tk
from tkinter import filedialog
from tkinter.messagebox import showerror

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import xlrd

#############################################################
#############################################################

# Convert the color_code rgb values from [0,255] to the [0,1] range 
# matplotlib expects and store them in an ordered dictionary so the 
# order is presered in the legend 
code_colors = [(code, [i/255. for i in colors]) for code, colors in code_colors]

# Wrap colors in this class to make accessing it safe 
class Colors():
    def __init__(self, colors):
        self._colors = collections.OrderedDict(colors)
        self._keys = tuple(self._colors)

    def error(self, code):
        raise PlottingError(f"Could not find code: {code}, you may need to add it to 'code_colors'")

    def __getitem__(self, code):
        try:
            return self._colors[code]
        except:
            self.error(code)

    def index(self, code):
        try:
            return self._keys.index(code)
        except:
            self.error(code)

code_colors = Colors(code_colors)


#############################################################
#                                                           #
#             Data Extraction and Formating                 #
#                                                           #
#############################################################

class PlottingError(Exception):
    def __init__(self, message):
        self.message = message

# Extract that data from the file and return it a a list 
# of 3 element lists 
# [distance, elevation, code]
def read_file(filename):
    extension = os.path.splitext(filename)[1]
    try:
        if extension == ".csv":
            return read_file_csv(filename)
        elif extension == ".xls":
            return read_file_xls(filename)
        else:
            raise PlottingError(f"Filetype: {extension} is not supported")
    except:
        raise PlottingError(f"Could not read file: {filename}")

def read_file_csv(filename):
    try:
        with open(filename) as csv_file:
            reader = csv.reader(csv_file, delimiter=",")
            data = list(reader)
            # Exclude the first line, which is the headers 
            data = data[1:]
            # Casting the values to floats 
            data = [[float(x), float(y), code] for (x,y,code) in data]
            return data
    except:
        raise PlottingError(f"Could not read file: {filename}")

def read_file_xls(filename):
    workbook = xlrd.open_workbook(filename)
    sheet = workbook.sheet_by_index(0)
    data = []

    # Deliberatly skip the first row since it has the column headers 
    for row_index in range(1, sheet.nrows):
        row = sheet.row(row_index)
        data.append([entry.value for entry in row])

    return data

# Take the data and sort it into contigous data series 
# This function returns a list of data series
# Each series is a tuple: (code, <list of data points>)
def make_series(data):
    groups = itertools.groupby(data, lambda point: point[2])

    # Expand all the iterators into lists and remove the code from each 
    # individual point 
    groups = [(code, [point[:2] for point in data]) for (code, data) in groups]
    return groups

#############################################################
#                                                           #
#                      Plotting                             #
#                                                           #
#############################################################

class PlotData(object):
    def __init__(self, input_file):
        self.data = read_file(input_file)

        # Setup the inital plot that can be mainpulated from the gui 
        self.fig, self.ax = plt.subplot(111)

def plot_data(data_series, legend_position, output=""):
    fig, ax = plt.subplots()
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    for series in data_series:
        plot_series(series)
    make_legend(data_series, ax, location=legend_position)
    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_label)

    if output != "":
        plt.savefig(output)

# Plots a single series 
def plot_series(series):
    [code, data] = series
    color = code_colors[code]
    x_data, y_data = zip(*data)
    plt.plot(x_data, y_data, color=color)

# Make a single line in the legend for each unique code
def make_legend(data_series, ax, location="best"):
    unique_codes = set([group[0] for group in data_series])

    # Get the codes in the ordered specified buy code_colors
    unique_codes = [code for code in unique_codes]
    unique_codes = sorted(unique_codes, key = code_colors.index)

    custom_lines = [Line2D([0], [0], color=code_colors[code]) for code in unique_codes]
    ax.legend(custom_lines, unique_codes, loc=location)

def do_plot(input, legend_position, output=""):
    data = read_file(input)
    series = make_series(data)
    plot_data(series, legend_position, output)
    plt.show()

#############################################################
#                                                           #
#                         GUI                               #
#                                                           #
#############################################################

legend_positions = {"Best", "Upper Right", "Upper Left", "Lower Left", "Lower Right",
                    "Center Left", "Center Right", "Lower Center", "Upper Center",
                    "Center"}

class View(tk.Frame):

    def __init__(self, root):
        tk.Frame.__init__(self, root)

        # Defining variables 
        self.selected_file = ""
        self.output_file = ""
        self.input_dialog = tk.StringVar()
        self.output_dialog = tk.StringVar()
        self.working_dir = os.getcwd()
        self.legend_position = tk.StringVar(root)
        self.legend_position.set("Best")

        # Setting initial state 
        self.input_dialog.set("You haven't selected an input file")
        self.output_dialog.set("You haven't named an output file")

        # Creating widgets 
        self.pack_widgets()

    def plot(self):
        # Wrap this in an exception, an error in plotting shouldn't 
        # bring down the GUI 
        try:
            position = self.legend_position.get().lower()
            do_plot(self.selected_file, position, self.output_file)
        except PlottingError as err:
            showerror(message=err.message)
        except Exception as err:
            showerror(message="Something unexpected went wrong, make sure your input file is formated correctly")
            print(err)


    def select_input_file(self):
        path = filedialog.askopenfilename(filetypes = [("spreadsheet files","*.csv *.xls")],
                                          initialdir = self.working_dir)
        self.selected_file = path
        self.working_dir = os.path.dirname(path)

        if not self.selected_file in ["", ()]:
            self.input_dialog.set(f"You've selected: {self.selected_file}")
        else:
            self.input_dialog.set("You haven't selected an input file")

    def select_output_file(self):
        path = filedialog.asksaveasfilename(filetypes = [("png files", "*png")],
                                            initialdir = self.working_dir)
        self.working_dir = os.path.dirname(path)

        # Remove any extension on the path 
        path = os.path.splitext(path)[0]
        self.output_file = path

        if self.output_file != "":
            self.output_dialog.set(f"Plot will be saved to: {self.output_file}.png")
        else:
            self.output_dialog.set("You haven't named an output file")

    def pack_widgets(self):
        # Creating widgets 
        tk.Label(self, text="Select input file:").grid()
        tk.Button(self, text="Select File", command=self.select_input_file).grid(row=0, column=1)
        tk.Label(self, text = "Select output file:").grid()
        tk.Button(self, text="Select File", command=self.select_output_file).grid(row=1, column=1)

        # Empty row=2 for spacing 
        self.rowconfigure(2, minsize=10)

        tk.Label(self, textvariable=self.input_dialog).grid(row=3, columnspan=2, padx=50)
        tk.Label(self, textvariable=self.output_dialog).grid(row=4, columnspan=2)

        # Empty row=5 for spacing 
        self.rowconfigure(5, minsize=10)

        tk.Label(self, text="Set Legend Position:").grid(row=6)
        tk.OptionMenu(self, self.legend_position, *legend_positions).grid(row=6, column=1)

        self.rowconfigure(7, minsize=10)

        tk.Button(self, text="Plot", command=self.plot).grid(row=8, column=0, columnspan=2)



def make_gui():
    window = tk.Tk()
    window.title("Plotting")
    plotter = View(window)
    plotter.grid(padx=20, pady=20)
    return window

make_gui().mainloop()


