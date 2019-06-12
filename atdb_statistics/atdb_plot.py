"""
    File name: atdb_plot.py
    version: 1.0.0 (28 mar 2019)
    Author: Copyright (C) 2019 - Nico Vermaas - ASTRON
    Description: atdb plot module
"""

import plotly
import plotly.graph_objs as go

# https://matplotlib.org/tutorials/introductory/usage.html#sphx-glr-tutorials-introductory-usage-py
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches

import numpy as np

# --- plot functions  ---

def do_mathlib_plot():
    x = np.arange(0, 10, 0.2)
    y = np.sin(x)
    fig, ax = plt.subplots()
    ax.plot(x, y)
    plt.show()

def do_electricity_plots(title, xx,yy, legends, type, output_html,y_axis_title='verbruik'):
    """
    :param title: Title of Plot
    :param x: dict with data for x-axis (time)
    :param y: dict with data for y_axix (usage)
    :return:
    """
    print('do_electricity_plots()')

    line_consumption = go.Scatter(
        x=xx[0],
        y=yy[0],
        mode='lines',
        name=legends[0]
    )
    line_redelivery = go.Scatter(
        x=xx[1],
        y=yy[1],
        mode='lines',
        name = legends[1]
    )
    bar_totals = go.Bar(
        x=xx[2],
        y=yy[2],
        marker=dict(
            color='rgb(255,221,0)',
        ),
        name=legends[2]
    )

    layout = go.Layout(
        title=title,
        xaxis=dict(tickangle=-45),
        plot_bgcolor='rgb(230,230,230)',
        yaxis = dict(
            title=y_axis_title,
            titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'),
        ),
        barmode = 'group',

    )

    data = [bar_totals,line_consumption,line_redelivery]

    fig = go.Figure(data=data, layout=layout)
    plotly.offline.plot(fig,filename=output_html)


def do_plot(plot_engine, title, x,y, plot_type, color, output_html,y_axis_title='y-axis'):
    """

    :param title: Title of Plot
    :param x: dict with data for x-axis (time)
    :param y: dict with data for y_axix (usage)
    :return:
    """
    print('do_plot()')

    if plot_engine=='plotly':
        if plot_type == 'bar':
            trace = go.Bar(
                x=x,
                y=y,
                marker=dict(
                    color=color,
                ),
            )
            layout = go.Layout(
                title = title,
                xaxis=dict(
                    tickangle=-45,
                    #tickvals=x
                ),
                yaxis=dict(
                    title=y_axis_title,
                    titlefont=dict(
                        family='Courier New, monospace',
                        size=18,
                        color='#7f7f7f'),
                ),

                barmode='group',
                plot_bgcolor='rgb(230,230,230)'
            )

        elif plot_type == 'scatter':
            trace = go.Scatter(
                x=x,
                y=y,
                mode='lines',
                marker=dict(
                    size=10,
                    color=color,
                    line=dict(
                        width=2,
                    )
                )
            )
            layout = go.Layout(
                title=title,
                xaxis=dict(tickangle=-45),
                plot_bgcolor='rgb(230,230,230)'
            )

        # use plotly to generate a webpage
            data = [trace]
            fig = go.Figure(data=data, layout=layout)
            plotly.offline.plot(fig,filename=output_html)

    # use mathplotlib to generate a plot
    elif plot_engine=='mathplotlib':

        # fig, ax = plt.subplots()
        # ax.plot(x, y)
        plt.figure(figsize=(12,4))
        plt.title(title)
        plt.legend(loc=0)
        plt.xlabel('Time')
        plt.ylabel(y_axis_title)

        if plot_type == 'bar':
            # plt.bar(x,y,color='cornflowerblue')
            plt.bar(x, y, color=color)
        elif plot_type == 'scatter':
            plt.step(x,y,label='IMAGING',color=color,linewidth=2)

        plt.grid(True,alpha=0.3)
        plt.show()



# https://plot.ly/python/line-and-scatter/
def do_sky_plot(plot_engine, title, x,y, duration, sizes, output_html,y_axis_title='y-axis',colormap='viridis'):
    """
    :param title: Title of Plot
    :param x: dict with data for x-axis (time)
    :param y: dict with data for y_axis (usage)
    :return:
    """

    print('do_sky_plot()')
    if plot_engine=='plotly':
        trace = go.Scatter(
            x=x,
            y=y,
            mode='markers',
            marker = dict(
                size = 10,
                color = duration,
                colorscale='Viridis',
                showscale=True
            ),

        )
        layout = go.Layout(
            title=title,
            xaxis=dict(tickangle=0),
            plot_bgcolor='rgb(150,150,150)'
        )

        data = [trace]

        fig = go.Figure(data=data, layout=layout)
        plotly.offline.plot(fig,filename=output_html)

    # use mathplotlib to generate a plot
    elif plot_engine=='mathplotlib':

        # fig, ax = plt.subplots()
        # ax.plot(x, y)
        plt.style.use('dark_background')
        plt.figure(figsize=(12,6))
        plt.title(title)
        plt.suptitle("ATDB Sky Map")
        #import matplotlib.patches as mpatches
        #red_patch = mpatches.Patch(color='red', label='The red data')
        #plt.legend(handles=[red_patch])
        plt.xlabel('Right Ascension (degrees)')
        plt.ylabel('Declination')

        # https://matplotlib.org/examples/color/colormaps_reference.html
        plt.scatter(x,y,c=duration,s=sizes,cmap=colormap,alpha=1.0)
        plt.colorbar()

        plt.grid(True,alpha=0.3)
        plt.show()


def do_speed_plot(title, y_axis_title, subtitle, annotate, datapoints):
    """
    :param title: Title of Plot
    :param x: dict with data for x-axis (time)
    :param y: dict with data for y_axix (usage)
    :return:
    """

    #print('do_speed_plot()')

    fig = plt.figure(figsize=(12,6))
    #fig, ax = plt.subplots()

    plt.text(x=0.5, y=0.94, s=title, fontsize=14, ha="center", transform=fig.transFigure)
    plt.text(x=0.5, y=0.90, s='query: '+subtitle, fontsize=10, ha="center", transform=fig.transFigure)

    #plt.title(title)
    #plt.suptitle(subtitle)

    plt.xlabel('Timestamp')
    plt.ylabel(y_axis_title)

    plt.grid(True,alpha=0.3)

    observing_x = []
    observing_y = []
    ingesting_x = []
    ingesting_y = []
    ingest_error_x = []
    ingest_error_y = []
    i = 0
    for datapoint in datapoints:

        if datapoint['type'] == 'observing':
            observing_x.append(datapoint['timestamp'])
            observing_y.append(datapoint['speed_bps'])
            observing_x.append(datapoint['timestamp_end'])
            observing_y.append(datapoint['speed_bps'])

            # plot start and end points
            plt.plot(datapoint['timestamp'], datapoint['speed_bps'], 'b.',
                     datapoint['timestamp_end'], datapoint['speed_bps'], 'b.')
            if annotate is not None:
                plt.text(datapoint['timestamp'], datapoint['speed_bps'], datapoint[annotate]+'...',
                         rotation='vertical', fontsize=8)

        if datapoint['type']=='ingesting':
            ingesting_x.append(datapoint['timestamp'])
            ingesting_y.append(datapoint['speed_bps'])
            ingesting_x.append(datapoint['timestamp_end'])
            ingesting_y.append(datapoint['speed_bps'])

            plt.plot(datapoint['timestamp'], datapoint['speed_bps'], 'g.',
                     datapoint['timestamp_end'], datapoint['speed_bps'], 'g.')
            if annotate is not None:
                plt.text(datapoint['timestamp'], datapoint['speed_bps'], datapoint[annotate]+'...',
                          rotation='vertical', fontsize=8)

        if datapoint['type'] == 'ingest_error':
            ingest_error_x.append(datapoint['timestamp'])
            ingest_error_x.append(datapoint['speed_bps'])

            plt.plot(datapoint['timestamp'], datapoint['speed_bps'], 'r.')
            if annotate is not None:
                plt.text(datapoint['timestamp'], datapoint['speed_bps'], datapoint[annotate] + '...',
                         rotation='vertical', fontsize=8)

    # plot lines
    # connect a line
    for i in range(0,len(observing_x),2):
        plt.plot(observing_x[i:i + 2], observing_y[i:i + 2], 'b:')

    for i in range(0,len(ingesting_x),2):
        plt.plot(ingesting_x[i:i + 2], ingesting_y[i:i + 2], 'g-')

    # legend
    plt.plot(observing_x[i:i + 2], observing_y[i:i + 2], 'b:',label='Observing')
    plt.plot(ingesting_x[i:i + 2], ingesting_y[i:i + 2], 'g-',label='Ingesting')
    #plt.plot(ingest_error_x[i:i], 'r.',label='ingest error')
    plt.legend(loc='upper right')

    plt.show()

