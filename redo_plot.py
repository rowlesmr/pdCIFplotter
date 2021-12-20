import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib as mpl
from matplotlib.figure import Figure


class PlotData:
    def __init__(self, m_canvas_x, m_canvas_y):
        self.canvas_x = m_canvas_x
        self.canvas_y = m_canvas_y\

    def plot(self, x, y, fig):
        if fig:
            fig.clear()
        fig = Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot()
        fig.set_tight_layout(True)
        ax.margins(x=0)
        ax.plot(x, y, label="a legend entry")
        ax.set_xlabel("X ordinate")
        ax.set_ylabel("Y ordinate")
        ax.set_title("Title", loc="left")

        return fig


# sg.set_options(dpi_awareness=True)

canvas_x = 600
canvas_y = 300

plot = PlotData(canvas_x, canvas_y)
figure = None

x_data = [1, 2, 3, 4, 5]
y_data = [[2, 6, 4, 7, 9], [7, 3, 7, 3, 5]]



# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
# https://github.com/PySimpleGUI/PySimpleGUI/issues/3989#issuecomment-794005240
def draw_figure_w_toolbar(canvas, figure, toolbar_canvas):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if toolbar_canvas.children:
        for child in toolbar_canvas.winfo_children():
            child.destroy()
    figure_canvas = FigureCanvasTkAgg(figure, master=canvas)
    figure_canvas.draw()
    toolbar = NavigationToolbar2Tk(figure_canvas, toolbar_canvas)
    toolbar.update()
    figure_canvas.get_tk_widget().pack(side='right', fill='both', expand=1)



layout = \
    [
        [sg.Button("Plot", key="plot_data"), sg.Button("Exit", key="exit")],
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="figure", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Sizer(v_pixels=60), sg.Canvas(key="toolbar")]
    ]


def gui() -> None:
    global figure
    window = sg.Window("Data plotter", layout, finalize=True, resizable=True)
    print(f"{mpl.__version__=}")
    i = 0
    while True:
        event, values = window.read()
        i += 1
        print(f"{i=}")
        if event in (None, "exit"):
            break
        elif event == "plot_data":
            figure = plot.plot(x_data, y_data[i % 2], figure)
            draw_figure_w_toolbar(window["figure"].TKCanvas, figure, window["toolbar"].TKCanvas)



if __name__ == "__main__":
    gui()
