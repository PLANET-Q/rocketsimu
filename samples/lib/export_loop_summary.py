import json
from typing import Iterable
import pandas as pd


def export_loop_summary(
        writer:pd.ExcelWriter,
        events_data:dict,
        event_names_fmt:str,
        speed_array:Iterable,
        direction_array:Iterable
    ):

    max_alt = {}
    max_v = {}
    max_mach = {}
    launch_clear_v = {}
    drogue_v = {}
    parachute_v = {}
    max_q = {}
    # max_accelation = {}
    for s, speed in enumerate(speed_array):
        speed_str = str(speed)
        max_alt[speed_str] = {}
        max_v[speed_str] = {}
        max_mach[speed_str] = {}
        launch_clear_v[speed_str] = {}
        drogue_v[speed_str] = {}
        parachute_v[speed_str] = {}
        max_q[speed_str] = {}
        # max_accelation[speed_str] = {}
        for d, direction in  enumerate(direction_array):
            direction_str = f'{direction:.1f}'
            event_data = events_data[event_names_fmt.format(speed, direction)]
            max_alt[speed_str][direction_str] = event_data['apogee']['x'][2]
            max_v[speed_str][direction_str] = event_data['max_air_speed']['air_speed']
            max_mach[speed_str][direction_str] = event_data['max_mach']['mach']
            launch_clear_v[speed_str][direction_str] = event_data['2ndlug_off']['v_air']

            if 'drogue' in event_data:
                drogue_v[speed_str][direction_str] = event_data['drogue']['v_air']
            else:
                drogue_v[speed_str][direction_str] = None

            if 'para' in event_data:
                parachute_v[speed_str][direction_str] = event_data['para']['v_air']
            else:
                parachute_v[speed_str][direction_str] = None

            max_q[speed_str][direction_str] = event_data['max_Q']['Q']

    alt_df = pd.DataFrame.from_dict(max_alt, orient='index')
    v_df = pd.DataFrame.from_dict(max_v, orient='index')
    mach_df = pd.DataFrame.from_dict(max_mach, orient='index')
    launch_clear_v_df = pd.DataFrame.from_dict(launch_clear_v, orient='index')
    drogue_df = pd.DataFrame.from_dict(drogue_v, orient='index')
    para_df = pd.DataFrame.from_dict(parachute_v, orient='index')
    q_df = pd.DataFrame.from_dict(max_q, orient='index')

    # write to sheets
    alt_df.to_excel(writer, '最高高度', na_rep='-')
    v_df.to_excel(writer, '最大対気速度', na_rep='-')
    mach_df.to_excel(writer, '最大マッハ数', na_rep='-')
    launch_clear_v_df.to_excel(writer, 'ランチクリア対気速度', na_rep='-')
    drogue_df.to_excel(writer, 'ドローグ展開時対気速度', na_rep='-')
    para_df.to_excel(writer, 'パラ展開時対気速度', na_rep='-')
    q_df.to_excel(writer, '最大動圧', na_rep='-')
