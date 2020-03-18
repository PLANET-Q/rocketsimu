import rocketsimu.simulator as simu
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse

# Jsonエンコーダクラス
import quaternion
import numpy as np
import json
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, quaternion.quaternion):
            return quaternion.as_float_array(obj)
        else:
            return super(NumpyEncoder, self).default(obj)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Parameter file path(json format)")
    parser.add_argument("-l", "--logout", help="output log filename")
    parser.add_argument("-s", "--showplot", help="whether show plot")
    args = parser.parse_args()

    # シミュレーション
    print('Parmeter file:', args.config)
    t, x, v, q, omega, log = simu.simulate(args.config)

    # ログ出力
    if args.logout:
        print('log file:', args.logout)
        with open(args.logout, 'w') as f:
            json.dump(log, f, indent=4, cls=NumpyEncoder)

    # プロット
    if args.showplot:
        # tを ~MECO, MECO~パラ展開, パラ展開~ランディング に切り分け
        t_1stlug = log['1stlug_off']['t']
        t_2ndlug = log['2ndlug_off']['t']
        t_meco = log['MECO']['t']

        if 'drogue' in log:
            t_drogue = log['drogue']['t']
        t_para = log['para']['t']
        t_landing = log['landing']['t']
        t_powered = t[t < t_meco]

        if 'drogue' in log:
            t_inertial = t[(t >= t_meco) & (t < t_drogue)]
            t_drogue_deployed = t[(t >= t_drogue) & (t < t_para)]
        else:
            t_inertial = t[(t >= t_meco) & (t < t_para)]
            t_drogue_deployed = None
        t_deployed = t[t >= t_para]

        # Show Trajectory
        x_powered = x.T[t < t_meco].T
        # x_inertial = x.T[(t >= t_meco) & (t < t_para)].T
        if 'drogue' in log:
            x_inertial = x.T[(t >= t_meco) & (t < t_drogue)].T
            x_drogue_deployed = x.T[(t >= t_drogue) & (t < t_para)].T
        else:
            x_inertial = x.T[(t >= t_meco) & (t < t_para)].T
        x_deployed = x.T[t >= t_para].T
        fig = plt.figure(0)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlabel('x(W2E) [m]')
        ax.set_ylabel('y(S2N) [m]')
        ax.set_zlabel('altitude [m]')
        ax.plot(x_powered[0], x_powered[1], x_powered[2], label='powered')
        ax.plot(x_inertial[0], x_inertial[1], x_inertial[2], label='inertia')
        if 'drogue' in log:
            ax.plot(x_drogue_deployed[0], x_drogue_deployed[1], x_drogue_deployed[2], label='drogue')
        ax.plot(x_deployed[0], x_deployed[1], x_deployed[2], label='para')
        ax.set_title('Trajectory')
        ax.legend()

        # Show XYZ vs time
        fig = plt.figure(1)
        ax = fig.add_subplot()
        ax.set_xlabel('t[s]')
        ax.set_ylabel('xyz [m]')
        ax.plot(t, x[0], label='x')
        ax.plot(t, x[1], label='y')
        ax.plot(t, x[2], label='z')
        ylim = ax.get_ylim()
        ax.vlines([t_1stlug, t_2ndlug, t_meco, t_para], ylim[0], ylim[1], linestyles='dashed')
        ax.legend()
        ax.set_title('XYZ vs. Time')
        ax.legend()

        # Show Velocity
        fig = plt.figure(2)
        v_speed = np.linalg.norm(v, axis=0)
        ax = fig.add_subplot()
        ax.set_xlabel('t[s]')
        ax.set_ylabel('velocity [m/s]')
        ax.plot(t, v[0], label='x')
        ax.plot(t, v[1], label='y')
        ax.plot(t, v[2], label='z')
        ax.plot(t, v_speed, label='speed')
        ylim = ax.get_ylim()
        ax.vlines([t_1stlug, t_2ndlug, t_meco, t_para], ylim[0], ylim[1], linestyles='dashed')
        ax.legend()
        ax.set_title('Velocity')

        # Angular Velocity
        fig = plt.figure(3)
        omega_speed = np.linalg.norm(omega, axis=0)
        ax = fig.add_subplot()
        ax.set_xlabel('t[s]')
        ax.set_ylabel('angular velocity [rad/s]')
        ax.plot(t, omega[0], label='x')
        ax.plot(t, omega[1], label='y')
        ax.plot(t, omega[2], label='z')
        ax.plot(t, omega_speed, label='speed')
        ylim = ax.get_ylim()
        ax.vlines([t_1stlug, t_2ndlug, t_meco, t_para], ylim[0], ylim[1], linestyles='dashed')
        ax.legend()
        ax.set_title('Angular Velocity')

        plt.show()