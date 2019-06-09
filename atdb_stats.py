"""
    File name: atdb_plot.py
    version: 1.0.0 (28 mar 2019)
    Author: Copyright (C) 2019 - Nico Vermaas - ASTRON
    Description: Plot data from ATDB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import datetime

import plotly
import requests
import json
import psycopg2

import argparse
import plotly.graph_objs as go
from atdb_statistics import atdb_plot

#import numpy as np

# some constants
ATDB_API_DEV = "http://localhost:8000/atdb"
ATDB_API_TEST = "http://192.168.22.22/atdb"
ATDB_API_ACC = "http://195.169.22.25/atdb"
ATDB_API_PROD = "http://195.169.63.121/atdb"

ALTA_API_DEV = "http://localhost:8000/altapi"
ALTA_API_TEST = "http://alta-sys.astron.nl/altapi"
ALTA_API_ACC = "https://alta-acc.astron.nl/altapi"
ALTA_API_PROD = "https://alta.astron.nl/altapi"

TIME_FORMAT = "%Y-%m-%d %H:%M"

#--- common functions ---
def isCalibrator(name):
    """
    check if the provided name is in the (hardcoded) list of defined Apertif Calibrators
    :param: name, the name of a source.
    :return: True, if this is a calibrator
    """
    APERTIF_CALIBRATORS = ['3C48', '3C048', '3C138', '3C147', '3C196', '3C286', '3C295', 'CTD93']
    for calibrator in APERTIF_CALIBRATORS:
        if name.find(calibrator) >= 0:
            return True

    return False


def scp_filename(host, source, target):
    """ scp a file from a remote location to a local dir
        location: directory on the node where the source file is, and where the target file will be copied.
        from_name: file to copy
        to_name : the new file.
    """
    print('scp '+host+':/' + source+ ' to ' + target)
    cmd = 'scp ' + host + ':' + source + ' ' + target
    os.system(cmd)


def execute_remote_command(host, cmd):
    """ Run command on an ARTS node. Assumes ssh keys have been set up
        cmd: command to run
    """
    ssh_cmd = "ssh {} \"{}\"".format(host, cmd)
    print("Executing '{}'".format(ssh_cmd))
    return os.system(ssh_cmd)


# --- presentation functions ---

def do_ingest_sizes(args, starttime, endtime, plot_engine='plotly'):

    # connection parameters
    connection = None

    try:

        # connect to the PostgreSQL server
        connection = psycopg2.connect(host = args.atdb_database_host,
                                      port = args.atdb_database_port,
                                      database = args.atdb_database_name,
                                      user = args.atdb_database_user,
                                      password = args.atdb_database_password)

        # create a cursor
        cursor = connection.cursor()

        # input
        start_date = datetime.datetime.strptime(args.starttime, '%Y-%m-%d %H:%M')
        end_date = datetime.datetime.strptime(args.endtime, '%Y-%m-%d %H:%M')
        curr_date = start_date

        dates = []
        arts_list = []
        imaging_list = []

        print('DATE ARTS IMAGING')

        while curr_date <= end_date:

            datestr = datetime.datetime.strftime(curr_date, '%y%m%d')

            cursor.execute(
                "SELECT sum(size) FROM public.taskdatabase_dataproduct where filename like 'ARTS%s%%'" % datestr)
            arts = cursor.fetchone()

            cursor.execute(
                "SELECT sum(size) FROM public.taskdatabase_dataproduct where filename like 'WSRTA%s%%'" % datestr)
            imaging = cursor.fetchone()

            print(datestr, arts[0], imaging[0])
            dates.append(curr_date)

            if arts[0] != None:
                arts_list.append(float(arts[0]) / 1e12)
            else:
                arts_list.append(0)

            if imaging[0] != None:
                imaging_list.append(float(imaging[0]) / 1e12)
            else:
                imaging_list.append(0)

            curr_date = curr_date + datetime.timedelta(days=1)

        # Make cumulative
        arts_cumu = []
        imaging_cumu = []
        for i in range(0, len(dates)):
            j = sum(arts_list[0:i + 1])
            arts_cumu.append(j)
            j = sum(imaging_list[0:i + 1])
            imaging_cumu.append(j)

        print(arts_cumu[-1] / 134.40)
        # close the communication with the PostgreSQL
        cursor.close()

        # show the plot
        if ('IMAGING' in args.observing_mode.upper()):
            if (args.data_aggregation=='cumulative'):
                atdb_plot.do_plot(args.plot_engine, args.title, dates, imaging_cumu, args.plot_type, args.color, args.output_html, args.y_axis_title)
            else:
                atdb_plot.do_plot(args.plot_engine, args.title, dates, imaging_list, args.plot_type, args.color, args.output_html, args.y_axis_title)
        elif ('ARTS' in args.observing_mode.upper()):
            if (args.data_aggregation == 'cumulative'):
                atdb_plot.do_plot(args.plot_engine, args.title, dates, arts_cumu, args.plot_type, args.color, args.output_html, args.y_axis_title)
            else:
                atdb_plot.do_plot(args.plot_engine, args.title, dates, arts_list, args.plot_type, args.color, args.output_html, args.y_axis_title)
        #do_plot(args.title+' ARTS', dates, arts_list, args.type, args.output_html, args.y_axis_title)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()
            print('Database connection closed.')


def do_sky(args, starttime, endtime):
    """
    SELECT starttime, endtime, field_ra, field_dec
	FROM public.taskdatabase_observation
    WHERE starttime>'2019-01-01' and endtime<'2019-02-01';

    :param args:
    :param starttime:
    :param endtime:
    :return:
    """

    # init
    ra_list = []
    dec_list = []
    duration_list = []
    sizes_list = []
    # connection parameters
    connection = None

    # input parameters
    starttime = datetime.datetime.strptime(args.starttime, '%Y-%m-%d %H:%M')
    endtime = datetime.datetime.strptime(args.endtime, '%Y-%m-%d %H:%M')

    try:

        # connect to the PostgreSQL server
        connection = psycopg2.connect(host = args.atdb_database_host,
                                      port = args.atdb_database_port,
                                      database = args.atdb_database_name,
                                      user = args.atdb_database_user,
                                      password = args.atdb_database_password)

        # create a cursor
        cursor = connection.cursor()

        # define and execute a sql query
        query = "SELECT field_ra, field_dec, field_name, starttime, endtime FROM public.taskdatabase_observation WHERE "
        query += "starttime > '"+ str(starttime) + "' AND endtime < '"+ str(endtime)+"' "
        query += "AND field_ha IS NULL;"
        cursor.execute(query)

        # fetch all the data from the query

        records = cursor.fetchall()
        for record in records:
            # only plot information about the targets
            fieldname = record[2]
            if not isCalibrator(fieldname):
                t1 = record[3]
                t2 = record[4]

                duration = (t2 - t1).seconds
                duration_list.append(int(duration/3600))
                sizes_list.append(int(duration/360))
                ra = record[0]
                ra_list.append(ra)
                dec_list.append(record[1])


        # show the plot
        atdb_plot.do_sky_plot(args.plot_engine, args.title, ra_list, dec_list, duration_list, sizes_list, args.output_html, args.y_axis_title, args.colormap)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    finally:
        if connection:
            cursor.close()
            connection.close()
            print('Database connection closed.')


def do_ingest_speeds(args, starttime, endtime, plot_engine='plotly'):

    # The request header
    ATDB_HEADER = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'authorization': "Basic YWRtaW46YWRtaW4="
    }

    # input parameters
    starttime = datetime.datetime.strptime(args.starttime, '%Y-%m-%d %H:%M')
    endtime = datetime.datetime.strptime(args.endtime, '%Y-%m-%d %H:%M')


    url = args.atdb_host + "/times?" + str(args.query)

    # do the request to the ATDB backend
    print('request to '+url)
    response = requests.request("GET", url, headers=ATDB_HEADER)

    # parse the response
    try:
        json_response = json.loads(response.text)
        results = json_response["results"]

    except Exception as err:
        print("Exception : " + str(err))
        raise (Exception(
            "ERROR: " + str(response.status_code) + ", " + str(response.reason) + ', ' + str(response.content)))

    # analyse the results
    print('analyse the results.')
    datapoints = []
    for result in results:
        if result['write_speed'] > 0:
            datapoint = {}
            datapoint['taskid'] = result['taskID']
            timestamp = datetime.datetime.strptime(result['starttime'], '%Y-%m-%dT%H:%M:%SZ')
            datapoint['timestamp'] = timestamp
            datapoint['type'] = 'observing'
            #datapoint['duration'] = result['duration']
            datapoint['timestamp_end'] = timestamp + datetime.timedelta(seconds=result['duration'])
            datapoint['speed_bps'] = result['write_speed'] * 8 / 1000
            datapoints.append(datapoint)
            print(datapoint)

        if result['ingest_speed'] is not None:
            datapoint = {}
            datapoint['taskid'] = result['taskID']
            nofrag,frag = result['timestamp_ingesting'].split('.')
            timestamp = datetime.datetime.strptime(nofrag, '%Y-%m-%dT%H:%M:%S')
            datapoint['timestamp'] = timestamp
            datapoint['type'] = 'ingesting'
            datapoint['duration'] = result['ingest_duration']
            datapoint['timestamp_end'] = timestamp + datetime.timedelta(seconds=result['ingest_duration'])
            datapoint['speed_bps'] = result['ingest_speed'] * 8 / 1000
            datapoints.append(datapoint)
            # print(datapoint)

    sorted_datapoints = sorted(datapoints, key=lambda k: k['timestamp'])

    # plot the results
    atdb_plot.do_speed_plot(args.title, args.y_axis_title, args.query, sorted_datapoints)



def get_arguments(parser):
    """
    Gets the arguments with which this application is called and returns the parsed arguments.
    If a argfile is give as argument, the arguments will be overrided
    The args.argfile need to be an absolute path!
    :param parser: the argument parser.
    :return: Returns the arguments.
    """
    args = parser.parse_args()
    if args.argfile:
        args_file = args.argfile
        if os.path.exists(args_file):
            parse_args_params = ['@' + args_file]
            # First add argument file
            # Now add command-line arguments to allow override of settings from file.
            for arg in sys.argv[1:]:  # Ignore first argument, since it is the path to the python script itself
                parse_args_params.append(arg)
            args = parser.parse_args(parse_args_params)
        else:
            raise (Exception("Can not find argument file " + args_file))
    return args


def main():
    """
    The main module.
    """
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

   # IO parameters
    parser.add_argument("--atdb_database_host",
                        default="192.168.22.25",
                        help="database host")
    parser.add_argument("--atdb_database_port",
                        default="5432",
                        help="database port")
    parser.add_argument("--atdb_database_name",
                        default="atdb",
                        help="database name")
    parser.add_argument("--atdb_database_user",
                        default="atdbread",
                        help="database username")
    parser.add_argument("--atdb_database_password",
                        default="atdbread123",
                        help="database password")
    parser.add_argument("--atdb_api",
                        default="192.168.22.25/atdb",
                        help="ATDB ReST API")
    parser.add_argument("--plot_engine",
                        default="plotly",
                        help="options are: 'plotly' (for webpage)or 'mathplotlib")
    parser.add_argument("--filename",
                        default=None,
                        help="txt or qbx file to parse (when txt file parsing is used)")
    parser.add_argument("--dataset",
                        default=None,
                        help="dataset to parse (when qbackend is used). Possible options: gas, consumption, generation")
    parser.add_argument("--atdb_host",
                        default=None,
                        help="remote ssh/scp host where the files are stored (if None, then they are assumed to be local)")
    parser.add_argument("--remote_dir",
                        default=None,
                        help="remote directory where the files are stored")
    parser.add_argument("--remote_pre_command",
                        default=None,
                        help="execute this command on the remote host before downloading the data files")
    parser.add_argument("--remote_post_command",
                        default=None,
                        help="execute this command on the remote host after generating the html results.")
    parser.add_argument("--local_dir",
                        default='',
                        help="local directory where the data files are stored or read")

    # visualisation parameters
    parser.add_argument("--legends",
                        default="verbruik,teruglevering,totaal",
                        help="Legends for consumption, redelivery and totals.")
    parser.add_argument("--output_html",
                        default="atdb_plot.html",
                        help="output html file")
    parser.add_argument("--presentation",
                        default=None,
                        help="Possible options: ingest_sizes")
    parser.add_argument("--data_aggregation",
                        default="standard",
                        help="Possible options: cumulative, standard")
    parser.add_argument("--mode",
                        default=None,
                        help="Default modes. Possible options: today, this_week, this_month, this_year")
    parser.add_argument("--observing_mode",
                        default=None,
                        help="Observingmode")
    parser.add_argument("--starttime",
                        default=None,
                        help="Format like 2019-01-12 00:00")
    parser.add_argument("--endtime",
                        default=None,
                        help="Format like 2019-01-12 00:00")
    parser.add_argument("--query",
                        default=None,
                        help="query for the REST API, like 'taskID__contains=190607'")
    parser.add_argument("--interval",
                        default="day",
                        help="Shows bars per interval. Possible options: minute, hour, day, month")
    # plot parameters
    parser.add_argument("--title",
                        default="Title",
                        help="Title of the Plot")
    parser.add_argument("--y_axis_title",
                        default="y-axis",
                        help="Title on the Y axis")
    parser.add_argument("--plot_type",
                        default="bar",
                        help="Chart type. Possible options: bar, scatter")
    parser.add_argument("--color",
                        default="#0081C9",
                        help="Color of the plot in hex value")
    parser.add_argument("--colormap",
                        default="viridis",
                        help="see: https://matplotlib.org/examples/color/colormaps_reference.html")
    # All parameters in a file
    parser.add_argument('--argfile',
                        nargs='?',
                        type=str,
                        help='Parameter file containing all the parameters')
    parser.add_argument("--version",
                        default=False,
                        help="Show current version of this program.",
                        action="store_true")

    args = get_arguments(parser)

    # --------------------------------------------------------------------------------------------------------
    if (args.version):
        print('--- atdb_plot.py - version 1.0.0 - 28 mar 2019 ---')
        print('Copyright (C) 2019 - Nico Vermaas - ASTRON. This program comes with ABSOLUTELY NO WARRANTY;')
        return

    print('--- atdb_plot.py - version 1.0.0 - 28 mar 2019 ---')
    print('Copyright (C) 2019 - Nico Vermaas - ASTRON. This program comes with ABSOLUTELY NO WARRANTY;')
    if args.starttime != None:
        starttime = datetime.datetime.strptime(args.starttime, TIME_FORMAT)

    # if no endtime is specified, then the endtime is now
    if args.endtime != None:
        endtime = datetime.datetime.strptime(args.endtime, TIME_FORMAT)
    else:
        endtime = datetime.datetime.now()

    # some default modes
    # today
    if args.mode=='today':
        endtime = datetime.datetime.now()
        starttime = endtime.replace(hour=0, minute=0)

    # this_month
    if args.mode=='this_month':
        endtime = datetime.datetime.now()
        starttime = endtime.replace(day=1, hour=0, minute=0)

    # this_year
    if args.mode=='this_year':
        endtime = datetime.datetime.now()
        starttime = endtime.replace(month=1,day=1, hour=0, minute=0)

    if args.remote_pre_command != None:
        execute_remote_command(args.atdb_host, args.remote_pre_command)

    # determine the type of presentation
    presentation = args.presentation

    # for backward compatibility with version 1.0,
    # the presentation mode was interpreted from the definition of the datafiles

    # for a single dataset
    if presentation=="ingest_sizes":
       do_ingest_sizes(args, starttime, endtime)

    elif presentation=="sky":
       do_sky(args, starttime, endtime)

    elif presentation=="ingest_speed":
       do_ingest_speeds(args, starttime, endtime)

    if args.remote_post_command != None:
        execute_remote_command(args.atdb_host, args.remote_post_command)


if __name__ == "__main__":
        #try:
        main()
        #except Exception as error:
        #    print(str(error))

