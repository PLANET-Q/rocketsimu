# %%
from os import TMP_MAX
from re import M

from numpy import result_type
from rocketsimu.solver import TrajectorySolver
import rocketsimu.simulator as simu
import matplotlib.pyplot as plt
import pandas as pd
import argparse

from mpl_toolkits.mplot3d import Axes3D

def main(
        parameter_filename:str,
        output_filename:str,
        plot_tajectory:bool=True
    ):
    # シミュレーション
    result = simu.simulate(parameter_filename)
    t = result.t
    x = result.x
    v = result.v
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

    print(result.events.dict())

    record_df = pd.DataFrame.from_dict(trajec_record)
    record_df.to_csv(output_filename, index=False)

    if plot_tajectory:
        fig = plt.figure(0)
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(x[0], x[1], x[2])
        ax.set_title('Trajectory')
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('parameter')
    parser.add_argument('-o', '--output_path', default='result.csv')
    parser.add_argument('--noplot', default=False)
    args = parser.parse_args()

    #input_filename = 'sample_parameters.json'
    #output_filename = 'result_trajectory.csv'

    main(args.parameter, args.output_path, ~args.noplot)
