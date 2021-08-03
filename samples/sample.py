# %%]
from typing import Optional
import numpy as np
import rocketsimu.simulator as simu
import matplotlib.pyplot as plt
import pandas as pd
import argparse

from mpl_toolkits.mplot3d import Axes3D

def main(
        parameter_filename:str,
        output_filename:str,
        output_event_filename:Optional[str]=None,
        plot_tajectory:bool=True
    ):
    # シミュレーション
    result = simu.simulate(parameter_filename)
    t = result.t
    x = result.x
    v = result.v_body
    q = result.q
    omega = result.w

    trajec_record = {
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
        'wz': omega[2],
    }

    if output_event_filename is not None:
        result.events.to_json(output_event_filename)

    print('-'*10)
    events_dict = result.events.events()
    for name, record in events_dict.items():
        print(f' {name}:')
        for key, value in record.items():
            print(f'    {key}={value}')

    # print(result.events.events())
    record_df = pd.DataFrame.from_dict(trajec_record)
    record_df.to_csv(output_filename, index=False)

    if plot_tajectory:
        t_MECO = events_dict['MECO']['t']
        t_para = events_dict['para']['t']
        x_powered = x[:, t<t_MECO]
        # mask = t>=t_MECO and t<t_para
        t_coast = t[t>=t_MECO]
        x_coast = x[:, t>=t_MECO][:, t_coast<t_para]
        x_para = x[:, t>=t_para]

        fig = plt.figure(0)
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(x_powered[0], x_powered[1], x_powered[2], label='powered', color='red')
        ax.plot(x_coast[0], x_coast[1], x_coast[2], label='coast', color='green')
        ax.plot(x_para[0], x_para[1], x_para[2], label='para', color='blue')
        ax.legend()
        ax.set_title('Trajectory')
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('parameter')
    parser.add_argument('-o', '--output_path', default='result.csv')
    parser.add_argument('--output_event_path', default=None)
    parser.add_argument('--noplot', default=False)
    args = parser.parse_args()

    #input_filename = 'sample_parameters.json'
    #output_filename = 'result_trajectory.csv'

    main(args.parameter, args.output_path, args.output_event_path, ~args.noplot)
