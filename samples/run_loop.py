from typing import Dict
from rocketsimu.judge_inside import InsideAreaJudgement
import rocketsimu.simulator as simu
import argparse
from multiprocessing import Pool
import os
import json
import numpy as np
import pandas as pd
import time
from copy import deepcopy

from lib import kmlplot
from lib.numpy2json import NumpyEncoder
from lib.export_loop_summary import export_loop_summary

def run_simu(params:dict, idx, foldername='tmp'):
    t_start = time.time()
    print(f'[PID:{os.getpid()}] Start')

    # シミュレーション
    result = simu.simulate(params)
    log = result.events.events()

    print(f'[PID:{os.getpid()}] landing XYZ:', log['landing']['x'])
    log.update({'loop_id': idx})
    # with open(os.path.join(foldername, str(idx)+'.json'), 'w') as f:
    #     json.dump(log, f, indent=2, cls=NumpyEncoder)

    t = result.t
    x = result.x
    v = result.v_body
    q = result.q
    omega = result.w

    # 結果を弾道履歴表(csv), パラメータ(json), 特異点ログ(json)に分けてファイル出力
    trajectory = {
        't': t,
        'x': x[0],
        'y': x[1],
        'z': x[2],
        'vx': v[0],
        'vy': v[1],
        'vz': v[2],
        'qx': q[0],
        'qy': q[1],
        'qz': q[2],
        'qw': q[3],
        'wx': omega[0],
        'wy': omega[1],
        'wz': omega[2]
    }
    df = pd.DataFrame(trajectory)
    df = df.set_index('t')
    df.to_csv(os.path.join(foldername, str(idx)+'.csv')) #弾道表

    t_end = time.time()
    print(f'[PID:{os.getpid()}] End. {t_end - t_start}[s]')
    return {
        'name': idx,
        'events': log,
        'trajectory': df
    }


def simulate_for_all_params(
    all_params:Dict[str, Dict],
    output_dir:str,
    n_workers:int=2
):
    arguments = []
    for name, params in all_params.items():
        arguments.append((params, name, output_dir))

    with Pool(n_workers) as pool:
        results = pool.starmap(run_simu, arguments)

    ret = {}
    for result in results:
        ret[result['name']] = result['events']

    return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Parameter file path(json format)")
    parser.add_argument("azimuth", help="Number of azimuth of wind")
    parser.add_argument("speed", help="range of speed of wind. `start:end:step` i.e: 0:8:1")
    parser.add_argument("out", help="output directory")
    # parser.add_argument("-k", "--kml", help="kml filename. default=`result.kml`")
    parser.add_argument("-p", "--process", help="max number of processes to be used. typ. laptop:4~8, desktop:8~16. default=2")
    args = parser.parse_args()

    # パラメータ読み込み
    print('Parmeter file:', args.config)
    with open(args.config) as f:
        base_params = json.load(f)

    # 出力先フォルダを作成
    if not os.path.exists(args.out):
        print('output directory:', args.out, 'was not found -> creating..')
        os.makedirs(args.out)

    # 出力フォルダにパラメータを保存
    with open(os.path.join(args.out, 'param_origin.json'), 'w') as f:
        json.dump(base_params, f, indent=2)

    # プロセス数
    if args.process:
        n_process = int(args.process)
    else:
        n_process = 2

    t_start = time.time()
    azimuth_array = np.linspace(0, 360, int(args.azimuth), endpoint=False)
    speed_range = np.array(args.speed.split(':'), dtype='int32')
    speed_array = np.arange(speed_range[0], speed_range[1]+1, speed_range[2])
    print('azimuth arrray: ', azimuth_array)
    print('speed array:', speed_array)
    loop_params = {}
    for speed in speed_array:
        for azimuth in azimuth_array:
            azimuth_rad = np.deg2rad(azimuth)
            wind_std = [-speed * np.sin(azimuth_rad), -speed * np.cos(azimuth_rad), 0]
            for mode in ['para', 'bal']:
                output_name = f'{speed:.2f}_{azimuth:.2f}_{mode}'
                params = deepcopy(base_params)
                params['wind_parameters']['wind_std'] = wind_std
                if mode == 'bal':
                    params['parachutes']['para']['enable'] = False
                    params['parachutes']['drogue']['enable'] = False
                loop_params[output_name] = params

    # プロセス並列化して処理（ノートPCでは他のソフトの処理が重くなります）
    simulation_output_dir = os.path.join(args.out, 'all')
    os.makedirs(simulation_output_dir, exist_ok=True)
    results = simulate_for_all_params(loop_params, simulation_output_dir, n_workers=n_process)
    t_end = time.time()

    print(f'process end: {t_end - t_start}[s]')

    # レギュレーション情報読み出し
    location_filename = params['environment']['location_filename']
    with open(location_filename) as f:
        location_config = json.load(f)

    scatter = np.zeros((len(speed_array), len(azimuth_array)+1, 2, 2))
    judge = InsideAreaJudgement(location_config['regulations'])
    judge_results = np.zeros((len(speed_array), len(azimuth_array), 2))
    for r, speed in enumerate(speed_array):
        for theta, azimuth in enumerate(azimuth_array):
            for i, mode in enumerate(['para', 'bal']):
                name = f'{speed:.2f}_{azimuth:.2f}_{mode}'
                coord = results[name]['landing']['coord']
                scatter[r, theta, i] = np.array(coord)
                judge_results[r, theta, i] = int(judge(coord[0], coord[1]))
        scatter[r, -1] = scatter[r, 0] # 落下分散円の始端と終端を結ぶ

    para_judge_df = pd.DataFrame(judge_results[:, :, 0], index=speed_array, columns=azimuth_array)
    bal_judge_df = pd.DataFrame(judge_results[:, :, 1], index=speed_array, columns=azimuth_array)

    all_judge_results = np.where(judge_results[:, :, 0] * judge_results[:, :, 1] == 1, 'Go', 'Nogo')
    all_judge_df = pd.DataFrame(all_judge_results[:, :], index=speed_array, columns=azimuth_array)
    print(all_judge_df)

    # output Go/Nogo judgement and other flight summaries to excel file
    with pd.ExcelWriter(os.path.join(args.out, 'result.xlsx')) as writer:
        all_judge_df.to_excel(writer, 'Go_NoGo')
        event_names_fmt ='{:.2f}_{:.2f}_para'
        # print(event_files_fmt)
        export_loop_summary(
            writer,
            results,
            event_names_fmt=event_names_fmt,
            speed_array=speed_array,
            direction_array=azimuth_array
        )
        bal_judge_df.to_excel(writer, '弾道判定')
        para_judge_df.to_excel(writer, 'パラ判定')

    # Output kml
    kmlplot.output_kml(
        scatter[:, :, 0],
        speed_array,
        azimuth_array,
        location_config,
        os.path.join(args.out, 'result_para.kml')
    )
    kmlplot.output_kml(
        scatter[:, :, 1],
        speed_array,
        azimuth_array,
        location_config,
        os.path.join(args.out, 'result_bal.kml')
    )

    t_export_end = time.time()
    print(f'export: {t_export_end - t_end}[s]')
