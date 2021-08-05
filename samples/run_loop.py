from rocketsimu.judge_inside import InsideAreaJudgement
import rocketsimu.simulator as simu
import argparse
import multiprocessing
import os
import json
import numpy as np
import pandas as pd
import quaternion

from lib import kmlplot
from lib.numpy2json import NumpyEncoder

def run_simu(params:dict, idx, foldername='tmp'):
    print(f'[PID:{os.getpid()}] Start')

    # シミュレーション
    result = simu.simulate(params)
    log = result.events.events()

    print(f'[PID:{os.getpid()}] landing XYZ:', log['landing']['x'])
    log.update({'loop_id': idx})
    with open(os.path.join(foldername, str(idx)+'.json'), 'w') as f:
        json.dump(log, f, indent=2, cls=NumpyEncoder)

    t = result.t
    x = result.x
    v = result.v_body
    q = result.q
    omega = result.w

    # 結果を弾道履歴表(csv), パラメータ(json), 特異点ログ(json)に分けてファイル出力
    # q_float = quaternion.as_float_array(q)
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

    print(f'[PID:{os.getpid()}] End')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Parameter file path(json format)")
    parser.add_argument("azimuth", help="Number of azimuth of wind")
    parser.add_argument("speed", help="range of speed of wind. `start:end:step` i.e: 0:8:1")
    parser.add_argument("out", help="output directory")
    parser.add_argument("-k", "--kml", help="kml filename")
    parser.add_argument("-p", "--process", help="max number of processes to be used. laptop:4~8, desktop:8~16")
    args = parser.parse_args()

    # パラメータ読み込み
    print('Parmeter file:', args.config)
    with open(args.config) as f:
        params = json.load(f)

    # 出力先フォルダを作成
    if not os.path.exists(args.out):
        print('output directory:', args.out, 'was not found -> creating..')
        os.makedirs(args.out)

    # 出力フォルダにパラメータを保存
    with open(os.path.join(args.out, 'param_origin.json'), 'w') as f:
        json.dump(params, f, indent=2)

    # プロセス数
    if args.process:
        n_process = int(args.process)
    else:
        n_process = 1

    azimuth_array = np.linspace(0, 360, int(args.azimuth), endpoint=False)
    speed_range = np.array(args.speed.split(':'), dtype='int32')
    speed_array = np.arange(speed_range[0], speed_range[1], speed_range[2])
    print('azimuth arrray: ', azimuth_array)
    print('speed array:', speed_array)
    proc = []
    idx = 0
    for speed in speed_array:
        # 風向ごとにプロセス並列化して処理（ノートPCでは他のソフトの処理が重くなります）
        for azimuth in azimuth_array:
            azimuth_rad = np.deg2rad(azimuth)
            wind_std = [-speed * np.sin(azimuth_rad), -speed * np.cos(azimuth_rad), 0]
            params['wind_parameters']['wind_std'] = wind_std
            output_name = f'{speed:.2f}_{azimuth:.2f}'
            p = multiprocessing.Process(target=run_simu, args=(params, output_name, args.out))
            proc.append(p)
            p.start()
            idx += 1

            # 終了したプロセスは削除
            for i, _p in enumerate(proc):
                if not _p.is_alive():
                    proc.pop(i)

            # 使用プロセス数が上限に達したらプロセス終了を待つ
            if len(proc) >= n_process:
                # いずれかのプロセスの終了を待つ
                loopf=True
                while loopf:
                    for i, _p in enumerate(proc):
                        if not _p.is_alive():
                            proc.pop(i)
                            loopf=False
                            break

    # 全プロセスの処理終了を待つ
    for p in proc:
        p.join()
    proc = []

    # レギュレーション情報読み出し
    with open('location_parameters/noshiro.json') as f:
        regulations = json.load(f)['regulations']
    idx=0
    scatter = np.zeros((len(speed_array), len(azimuth_array)+1, 2))
    judge = InsideAreaJudgement(regulations)
    # judge_results = np.zeros((len(speed_array), len(azimuth_array)), dtype=bool)
    judge_results = {}
    for r, speed in enumerate(speed_array):
        speed_str = str(speed)
        judge_results[speed_str] = {}
        for theta, azimuth in enumerate(azimuth_array):
            output_name = f'{speed:.2f}_{azimuth:.2f}'
            with open(os.path.join(args.out, f'{output_name}.json')) as f:
                data = json.load(f)
            scatter[r, theta] = np.array(data['landing']['coord'])

            azimuth_str = f'{azimuth:.1f}'
            coord = data['landing']['coord']
            judge_results[speed_str][azimuth_str] = judge(coord[0], coord[1])
            idx += 1
        scatter[r, -1] = scatter[r, 0] # 楕円の始端と終端を結ぶ
    # print(judge_results)
    judge_result_df = pd.DataFrame.from_dict(judge_results)
    print(judge_result_df)

    if args.kml:
        kmlplot.output_kml(
            scatter,
            speed_array,
            azimuth_array,
            regulations,
            os.path.join(args.out, args.kml)
        )
