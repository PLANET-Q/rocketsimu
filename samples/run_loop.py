import rocketsimu.simulator as simu
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import multiprocessing
import os
import json
import numpy as np

from lib import kmlplot
from lib.numpy2json import NumpyEncoder

def run_simu(params, idx, foldername='tmp'):
    # シミュレーション
    print(f'start {os.getpid()}')
    t, x, v, q, omega, log = simu.simulate(params, cons_out=False)
    res = {
        'simu_id': idx,
        'params': params,
        't': t,
        'x': x,
        'v': v,
        'q': q,
        'omega': omega
    }
    res.update(log)

    with open(os.path.join(foldername, str(idx)+'.json'), 'w') as f:
        json.dump(res, f, indent=4, cls=NumpyEncoder)
    print(f'end {os.getpid()}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Parameter file path(json format)")
    parser.add_argument("azimuth", help="Number of azimuth of wind")
    parser.add_argument("speed", help="range of speed of wind. [start:end:step] i.e: [0:8:1]")
    parser.add_argument("out", help="output directory")
    parser.add_argument("-k", "--kml", help="kml filename")
    args = parser.parse_args()

    # パラメータ読み込み
    print('Parmeter file:', args.config)
    with open(args.config) as f:
        params = json.load(f)

    # 出力先フォルダを作成
    if not os.path.exists(args.out):
        print('output directory:', args.out, 'was not found -> creating..')
        os.makedirs(args.out)

    azimuth_array = np.linspace(0, 2*np.pi, int(args.azimuth), endpoint=False)
    speed_range = np.array(args.speed.split(':'), dtype='int32')
    speed_array = np.arange(speed_range[0], speed_range[1], speed_range[2])
    print('azimuth arrray: ', azimuth_array)
    print('speed array:', speed_array)
    proc = []
    idx = 0
    for speed in speed_array:
        # 風向ごとにプロセス並列化して処理（ノートPCでは他のソフトの処理が重くなります）
        for azimuth in azimuth_array:
            wind_std = [-speed * np.sin(azimuth), -speed * np.cos(azimuth), 0]
            print(wind_std)
            params['wind_parameters']['wind_std'] = wind_std
            p = multiprocessing.Process(target=run_simu, args=(params, idx, args.out))
            proc.append(p)
            p.start()
            idx += 1
        
        # 全プロセスの処理終了を待つ
        for p in proc:
            p.join()
        proc = []

    if args.kml:
        
        # 伊豆レギュレーション情報読み出し
        with open('location_parameters/izu.json') as f:
            regulations = json.load(f)
        
        idx=0
        scatter = np.zeros((len(speed_array), len(azimuth_array), 2))
        for r, speed in enumerate(speed_array):
            for theta, azimuth in enumerate(azimuth_array):
                wind_std = [-speed * np.sin(azimuth), -speed * np.cos(azimuth), 0]
                with open(os.path.join(args.out, str(idx)+'.json')) as f:
                    data = json.load(f)
                scatter[r, theta] = np.array(data['landing']['x'])[:2]
                idx += 1

        print('scatter:', scatter)
        for item in regulations:
            if item['name'] == 'rail':
                latlon = item['center']
        print('lat lon:', latlon)
        kmlplot.output_kml(scatter, latlon, speed_array, regulations, os.path.join(args.out, args.kml))