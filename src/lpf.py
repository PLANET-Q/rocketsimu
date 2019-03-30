import numpy as np
from scipy.signal import firwin, lfilter
from scipy import fftpack

def LPF(x, dt, f_cutoff):
    tf = fftpack.fft(x)
    f = fftpack.fftfreq(len(x), dt)
    tf2 = np.copy(tf)
    tf2[np.abs(f) >= f_cutoff] = 0.
    y = np.real(fftpack.ifft(tf2))
    return y
