import rocketsimu.simulator as simu
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# シミュレーション
t, x, v, q, omega = simu.simulate('sample_parameters.json')

fig = plt.figure(0)
ax = fig.add_subplot(111, projection='3d')
ax.plot(x[0], x[1], x[2])
ax.set_title('Trajectory')
plt.show()
