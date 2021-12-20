import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib as mpl


class PlotData:
    def __init__(self, m_canvas_x, m_canvas_y):
        self.canvas_x = m_canvas_x
        self.canvas_y = m_canvas_y

    def plot(self, x, y, fig):
        dpi = plt.gcf().get_dpi()
        print(f"{dpi=}")

        if fig:
            plt.close(fig)
        fig, ax = plt.subplots(1, 1)
        fig = plt.gcf()
        fig.set_size_inches(self.canvas_x / float(dpi), self.canvas_y / float(dpi))
        print(f"{fig.get_size_inches()=}")
        fig.set_tight_layout(True)
        plt.margins(x=0)

        ax.plot(x, y, label="a legend entry")
        ax.set_xlabel("X ordinate")
        ax.set_ylabel("Y ordinate")
        plt.title("Title", loc="left")

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
def draw_figure_w_toolbar(canvas, figure, canvas_toolbar):
    print(f"{canvas.winfo_width()=}, {canvas.winfo_height()=}")
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(figure, master=canvas)
    figure_canvas_agg.draw()
    toolbar = NavigationToolbar2Tk(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)


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
            draw_figure_w_toolbar(window["figure"].TKCanvas, figure,
                                  window["toolbar"].TKCanvas)


if __name__ == "__main__":
    gui()
