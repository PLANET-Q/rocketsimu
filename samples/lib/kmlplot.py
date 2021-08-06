import simplekml
import numpy as np
import json
from rocketsimu.enviroment import xy_to_latlon


def getCirclePlot(center_coord, radius_meter):
    # delta_theta = 20./radius_meter
    # n_plots = int(2*np.pi / delta_theta)
    theta = np.linspace(0, 2*np.pi, 64, endpoint=True)
    x = np.cos(theta) * radius_meter
    y = np.sin(theta) * radius_meter
    points = np.c_[x, y]
    return xy_to_latlon(
        points,
        center_coord[1],
        center_coord[0],
        magnetic_declination_ccw_deg=0
    )


def setKmlCircle(
        kml,
        point_center,
        radius,
        name=None,
        plot_center=True,
        infill=False
        ):

    if plot_center:
        point = kml.newpoint(name=name, coords=[tuple(point_center)])
    else:
        point = None

    circleplots = getCirclePlot(
                    center_coord=point_center,
                    radius_meter=radius
                    )
    if infill:
        pol = kml.newpolygon(name=name)
        pol.outerboundaryis.coords = circleplots
    else:
        pol = kml.newlinestring(name=name)
        pol.coords = circleplots

    return point, pol


def setKmlByDicts(
        location_config:dict,
        kml=None,
    ):
    if kml is None:
        kml = simplekml.Kml()

    regulations = location_config['regulations']
    for dict in regulations:
        if 'name' in dict:
            name = dict['name']
        else:
            name = None

        if dict['type'] == 'point':
            point = dict['coord'][::-1]
            kml.newpoint(
                name=name,
                coords=[tuple(point)]
            )
        elif dict['type'] == 'circle':
            point = dict['center'][::-1]
            radius = dict['radius']

            is_plot_center = True
            if 'hide_center' in dict:
                if dict['hide_center'] is True:
                    is_plot_center = False

            is_infill = False
            if 'infill' in dict:
                if dict['infill'] is True:
                    is_infill = True

            point, pol = setKmlCircle(
                            kml,
                            point,
                            radius,
                            name=name,
                            plot_center=is_plot_center, infill=is_infill)

            pol.style.linestyle.width = 4
            pol.style.linestyle.color = '0045ff'

        elif dict['type'] == 'polygon':
            points = [tuple(p[::-1]) for p in dict['points']]
            line = kml.newlinestring(name=name)
            line.coords = points
            # Linecolor: Yellow
            line.style.linestyle.color = '00d7ff'
            line.style.linestyle.width = 4

        elif dict['type'] == 'line':
            point1 = tuple(dict['point1'][::-1])
            point2 = tuple(dict['point2'][::-1])
            line = kml.newlinestring(name=name)
            line.coords = [point1, point2]
            # Linecolor: Yellow
            line.style.linestyle.color = '00d7ff'
            line.style.linestyle.width = 4

        else:
            raise ValueError('The KML type: '+dict['type']+' is not available')

    return kml


def setKmlByJson(json_filename, kml=None, export_file=''):
    if kml is None:
        kml = simplekml.Kml()

    with open(json_filename, 'r') as f:
        dict_list = json.load(f)

    setKmlByDicts(dict_list, kml)

    if export_file != '':
        kml.save(export_file)

    return kml


def output_kml(
        drop_latlon:np.ndarray,
        wind_speeds:np.ndarray,
        wind_directions:np.ndarray,
        location_config:dict,
        filename:str
    ):
    '''
    Arguments:
        drop_latlon: ndarray (n_wind_speed, n_wind_directions, 2),
        wind_speeds: ndarray (n_wind_speed)
        wind_directions: @degree ndarray (n_wind_directions)
    '''
    # NOTE: 入力のdrop_latlonなどは[lat, lon]の順(TrajecSimu準拠)だが
    # kmlでは[lon, lat]の順なのでここでつかわれる関数はこの順です
    kml = simplekml.Kml()

    setKmlByDicts(location_config, kml)

    n_speeds = len(wind_speeds)
    for i, wind_speed in enumerate(wind_speeds):
        color_r = int(float(i / n_speeds) * 127) + 128

        for j, direction in enumerate(wind_directions):
            name = f'{direction:.1f}deg@{wind_speed:.1f}[m/s]'
            kml.newpoint(name=name, coords=[drop_latlon[i, j, ::-1]])

        line = kml.newlinestring(name=(str(wind_speed)+' [m/s]'))
        line.style.linestyle.color = simplekml.Color.rgb(color_r, 0, 0)
        line.style.linestyle.width = 2
        line.coords = drop_latlon[i, :, ::-1]

    kml.save(filename)
