import numpy as np
import quaternion
from scipy.integrate import odeint
from .enviroment import Enviroment
from .rocket import Rocket

class TrajectorySolver:
    def __init__(
            self,
            rocket:Rocket,
            dt=0.05,
            max_t=1000.0):
        self.state = 1
        self.apogee_flag = False
        self.rocket = rocket
        self.dt = dt
        self.max_t = max_t
        self.t = np.r_[
                        np.arange(0.0,3.,self.dt/10),
                        np.arange(3., self.max_t, self.dt)
                        ]
    
    def solve(self):
        u0 = np.r_[
            self.rocket.x,
            self.rocket.v,
            quaternion.as_float_array(self.rocket.q),
            self.rocket.omega
        ]

        self.solution = odeint(self.__f_main, u0, self.t)
        return self.solution
    
    def __f_main(self, u, t):
        rocket = self.rocket
        env = rocket.enviroment
        air = rocket.air
        launcher = rocket.launcher

        if self.state == 5:
            return u*0.

        # --------------------------
        #   extract vectors
        # --------------------------
        x = u[0:3]
        v = u[3:6]
        q = quaternion.as_quat_array(u[6:10])
        omega = u[10:]

        rocket.t = t
        rocket.x = x
        rocket.v = v
        rocket.q = q
        rocket.omega = omega

        # ----------------------------
        #    Direction Cosine Matrix for input q
        # ----------------------------
        # Tbl = transform from local(fixed) coordinate to body coord.
        #     note: as_rotation_matrix is for vector rotation
        #         -> for coordinate rotation, input conj(q)
        Tbl = quaternion.as_rotation_matrix(np.conj(q))

        if self.state == 1 and launcher.is1stlugOff():
            print('------------------')
            print('1stlug off at t=', t, '[s]')
            self.state = 1.1
        elif self.state == 1.1 and launcher.is2ndlugOff():
            print('------------------')
            print('2ndlug off at t=', t, '[s]')
            self.state = 2
        elif self.state <= 2 and t >= rocket.engine.thrust_cutoff_time:
            print('------------------')
            print('MECO at t=', t, '[s]')
            if rocket.hasDroguechute():
                self.state = 3
            else:
                self.state = 3.5
        elif self.state == 3 and rocket.isDroguechuteDeployed():
            print('------------------')
            print('drogue chute deployed at t=', t, '[s]')
            self.state = 3.5
        elif self.state == 3.5 and rocket.isParachuteDeployed():
            print('------------------')
            print('main parachute deployed at t=', t, '[s]')
            self.state = 4
        elif self.state > 1 and self.state < 5 and x[2] < 0.0 and t > rocket.engine.thrust_startup_time:
            print('------------------')
            print('landing at t=', t, '[s]')
            self.state = 5
            return u*0

        # dx_dt:地球座標系での地球から見たロケットの速度
        # v:機体座標系なので地球座標系に変換
        dx_dt = np.dot(Tbl.T, v)

        if self.apogee_flag is False and dx_dt[2] < 0.0:
            print('------------------')
            print('apogee at t=', t, '[s]')
            print('altitude:', x[2], '[m]')
            rocket.t_apogee = t
            self.apogee_flag = True
        
        # 重量・重心・慣性モーメント計算
        mass = rocket.getMass(t)
        CG = rocket.getCG(t)
        MOI = rocket.getMOI(t)

        # 慣性モーメントの微分
        # 現在は次の推力サンプル点でのモーメントとの平均変化率で近似している
        # (モーメントの変化は推力サンプル間隔)
        dt = 1.0e-3
        MOI_next = rocket.getMOI(t + dt)
        dMOI_dt = (MOI_next - MOI)/dt

        # v_air: 機体座標系での相対風ベクトル
        v_air = -v + np.dot(Tbl, air.wind(x[2]))
        v_air_norm = np.linalg.norm(v_air)
        if v_air_norm == 0:
            alpha = 0.
        else:
            # v_air[0]: 地球から見た機体座標系での機軸方向速度
            alpha = np.arccos(np.abs(v_air[0])/v_air_norm)
        
        # ロール方向の風向
        phi = np.arctan2(-v_air[1], -v_air[2])
        _, _, rho, sound_speed = air.standard_air(x[2])
        mach = v_air_norm / sound_speed

        #Cd = air.getCd(mach, alpha)
        #Cl = air.getCl(mach, alpha)
        #CP = air.getCP(mach, alpha)
        Cd = rocket.getCd(mach, alpha)
        Cl = rocket.getCl(mach, alpha)
        CP = rocket.getCP(mach, alpha)

        cosa = np.cos(alpha)
        sina = np.sin(alpha)
        air_coeff = np.array(
                    [(-Cl*sina + Cd*cosa),
                    (Cl*cosa + Cd*sina)*np.sin(phi),
                    (Cl*cosa + Cd*sina)*np.cos(phi)]
                    )
        rocket_xarea = (rocket.diameter/2)**2 * np.pi
        air_force = 0.5 * rho * v_air_norm**2. * rocket_xarea * (-1 * air_coeff)
        air_moment_CG = np.cross(np.array([CG - CP, 0.0, 0.0]), air_force)
        l = np.array([rocket.diameter, rocket.height, rocket.height])
        air_moment_damping = 0.25 * rho * v_air_norm * rocket.Cm * (l**2) * rocket_xarea * omega
        air_moment = air_moment_CG + air_moment_damping
        
        # 重力加速度
        g = env.g(x[2])
        #print('F_coriolis', env.Coriolis(v, Tbl))

        if self.state <= 1.1:
            # state <= 1.1: ラグがランチャーに拘束されている時
            # 運動方向は機体x方向(機軸方向)のみ
            
            # 並進力のうち機体座標系で表現されているもの
            # TODO: 振動friction()関数の実装
            thrust_vec = np.array([rocket.engine.thrust(t), 0.0, 0.0])
            F_body = air_force + thrust_vec
            # 合計加速度
            dv_dt = -np.cross(omega, v) + np.dot(Tbl, g) + F_body/mass
            # 機軸方向以外の加速度をキャンセル
            dv_dt[1] = 0.
            dv_dt[2] = 0.
            # 機軸負方向の加速度をキャンセル
            if dv_dt[0] < 0.0:
                dv_dt[0] = 0.0

        elif self.state == 2:
            # ラグが2つともランチャーから離れており推力飛行をしている場合
            thrust_vec = np.array([rocket.engine.thrust(t), 0.0, 0.0])
            dv_dt = -np.cross(omega, v) + np.dot(Tbl, g) +\
                env.Coriolis(v, Tbl) + (air_force + thrust_vec)/mass

        elif self.state == 3 or self.state == 5:
            # 慣性飛行時orランディング
            dv_dt = -np.cross(omega, v) + np.dot(Tbl, g) +\
                env.Coriolis(v, Tbl) + air_force/mass
        elif self.state == 3.5:
            # ドローグシュート展開時
            dv_dt = np.dot(Tbl, g) + env.Coriolis(v, Tbl) +\
                rocket.droguechute.DragForce(v_air, rho)/mass
        elif self.state == 4:
            # メインパラシュート展開時
            dv_dt = np.dot(Tbl, g) + env.Coriolis(v, Tbl) +\
                rocket.parachute.DragForce(v_air, rho)/mass

        # ----------------------------
        #    3. Atitude
        # ----------------------------
        # パラシュート展開時は回転を無視
        if self.state == 3.5 or self.state == 4:
            omega *= 0.
        q_omega = quaternion.as_quat_array(np.r_[0.0, omega])
        dq_dt = quaternion.as_float_array(0.5*q*q_omega)

        # ----------------------------
        #    4. Angular velocity
        # ----------------------------
        if self.state == 1 or self.state == 3.5 or self.state == 4:
            # both lug on the rail /parachute deployed -> no angular velocity change
            domega_dt = np.zeros(3)
        else:
            if self.state == 1.1:
                # 2nd lug on the rail. rotate around this point. Add addtitonal moment
                lug2CG = np.array([rocket.lug_2nd - CG, 0., 0.])
                # aerodynamic moment correction: move center of rotation from CG > 2nd lug (currently ignore damping correction)
                air_moment_2ndlug = air_moment + np.cross(lug2CG, air_force)
                # gravitaional moment around CG
                grav_body = mass * np.dot(Tbl, env.g(x[2]))  # gravity in body coord.
                grav_moment_2ndlug = np.cross(lug2CG, grav_body)
                # overwrite air_moment
                air_moment = air_moment_2ndlug + grav_moment_2ndlug
                # convert moment of inertia using parallel axis foram
                MOI += mass * np.array( [0., rocket.lug_2nd - CG, rocket.lug_2nd - CG ])**2.
            # END IF

            domega_dt = (-np.cross(omega, MOI*omega) - dMOI_dt*omega + air_moment) / (MOI + np.array([1e-10, 1e-10, 1e-10]))
        # END IF

        du_dt = np.r_[dx_dt, dv_dt, dq_dt, domega_dt]
        
        return du_dt
    
if __name__ == '__main__':
    from launcher import Launcher
    import rocket
    from engine import RocketEngine
    from air import Air
    import wind
    import parachute
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    
    rocket_parameters = {
        'height': 2.899,
        'diameter': 0.118,
        'mass_dry': 13.639,
        'CG_dry': 1.730,
        'MOI_dry': np.array([0.01, 17.06, 17.06]),
        'Cm': np.array([-0.0, -4.0, -4.0]),
        'lug_1st': 1.232,
        'lug_2nd': 2.230,
        'Cd0': 0.5,
        'Clalpha': 15.4,
        'CP': 2.243
    }

    engine_parameters = {
        'MOI_prop': np.array([0.001, 0.64, 0.64]),
        'mass_prop': 1.792
    }

    rocket = Rocket(rocket_parameters)
    engine = RocketEngine(engine_parameters)

    engine.loadThrust('Thrust_curve/20190218_Thrust.csv', 0.0001)

    drogue = parachute.Parachute(1.2, 0.215)
    para = parachute.Parachute(1.2, 3.39)
    drogue.setFallTimeTrigger(1.0)
    para.setAltitudeTrigger(250.0)

    rocket.joinDroguechute(drogue)
    rocket.joinParachute(para)

    rocket.joinEngine(engine, position=2.216)

    #wind = wind.WindConstant(np.array([7.,0.,0.]))
    wind = wind.WindPower(2.0, 4.5, [5.0, 0.0, 0.0])
    rocket.air = Air(wind)
    rocket.launcher = Launcher(5, 150.0, 75.0)
    rocket.enviroment = Enviroment(34.679730, 139.454987)
    rocket.setRocketOnLauncher()

    solver = TrajectorySolver(rocket, max_t=100.0)
    solution = solver.solve()
    
    v = solution[:, 3:6]
    v_norm = np.linalg.norm(v, axis=1)

    plt.figure(0)
    plt.plot(solver.t, v[:, 0], label='x')
    plt.plot(solver.t, v[:, 1], label='y')
    plt.plot(solver.t, v[:, 2], label='z')
    plt.plot(solver.t, v_norm, label='v norm')
    plt.legend()
    plt.show()
    fig = plt.figure(1)
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(solution[:,0], solution[:,1], solution[:,2])
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('alt')
    ax.set_title('trajectory')
    fig.show()

    plt.show()
    pass