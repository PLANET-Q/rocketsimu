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
            max_t=1000.0,
            cons_out=True):
        self.state = 1
        self.apogee_flag = False
        self.rocket = rocket
        self.dt = dt
        self.max_t = max_t
        self.cons = cons_out
        self.solver_log = {}
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

        self.solver_log = {}
        self.solution = odeint(self.__f_main, u0, self.t)
        return self.solution
    
    def add_solver_log(self, name:str, **kwargs):
        self.solver_log[name] = kwargs
    
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
            if self.cons:
                print('------------------')
                print('1stlug off at t=', t, '[s]')
                print('altitude:', x[2], '[m]')

            self.add_solver_log('1stlug_off', t=t, x=x, v=v, q=q, omega=omega)
            self.state = 1.1
        elif self.state == 1.1 and launcher.is2ndlugOff():
            if self.cons:
                print('------------------')
                print('2ndlug off at t=', t, '[s]')
                print('altitude:', x[2], '[m]')

            self.add_solver_log('2ndlug_off', t=t, x=x, v=v, q=q, omega=omega)
            self.state = 2
        elif self.state <= 2 and t >= rocket.engine.thrust_cutoff_time:
            if self.cons:
                print('------------------')
                print('MECO at t=', t, '[s]')
                print('altitude:', x[2], '[m]')

            self.add_solver_log('MECO', t=t, x=x, v=v, q=q, omega=omega)
            self.state = 3
        elif self.state == 3:
            if rocket.hasDroguechute():
                if rocket.isDroguechuteDeployed():
                    if self.cons:
                        print('------------------')
                        print('drogue chute deployed at t=', t, '[s]')
                        print('altitude:', x[2], '[m]')

                    self.add_solver_log('drogue', t=t, x=x, v=v, q=q, omega=omega)
                    self.state = 3.5 # ドローグ展開
            else:
                if rocket.isParachuteDeployed():
                    if self.cons:
                        print('------------------')
                        print('main parachute deployed at t=', t, '[s]')
                        print('altitude:', x[2], '[m]')

                    self.add_solver_log('para', t=t, x=x, v=v, q=q, omega=omega)
                    self.state = 4
        elif self.state == 3.5 and rocket.isParachuteDeployed():
            if self.cons:
                print('------------------')
                print('main parachute deployed at t=', t, '[s]')
                print('altitude:', x[2], '[m]')

            self.add_solver_log('para', t=t, x=x, v=v, q=q, omega=omega)
            self.state = 4
        elif self.state > 1 and self.state < 5 and x[2] < 0.0 and t > rocket.engine.thrust_startup_time:
            if self.cons:
                print('------------------')
                print('landing at t=', t, '[s]')
                print('x:', x)

            self.add_solver_log('landing', t=t, x=x, v=v, q=q, omega=omega)
            self.state = 5
            return u*0

        # dx_dt:地球座標系での地球から見たロケットの速度
        # v:機体座標系なので地球座標系に変換
        dx_dt = np.dot(Tbl.T, v)

        if self.apogee_flag is False and dx_dt[2] < 0.0:
            if self.cons:
                print('------------------')
                print('apogee at t=', t, '[s]')
                print('altitude:', x[2], '[m]')
            rocket.t_apogee = t

            self.add_solver_log('apogee', t=t, x=x, v=v, q=q, omega=omega)
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
        air_force = 0.5 * rho * v_air_norm**2.0 * rocket_xarea * (-1 * air_coeff)

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