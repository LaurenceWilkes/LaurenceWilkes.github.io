import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

N, ell = 20, 0.10
rng = np.random.default_rng(6)
k = 2*np.pi*np.fft.fftfreq(N, d=1/N)
kx, ky = np.meshgrid(k, k, indexing='ij')
s = np.exp(-0.5*ell**2*(kx**2 + ky**2))
u, v = [np.fft.fft2(rng.normal(size=(N,N)))*s for _ in range(2)]
k2, dot = kx**2 + ky**2, kx*u + ky*v
gx = np.divide(kx*dot, k2, out=np.zeros_like(u), where=k2 != 0)
gy = np.divide(ky*dot, k2, out=np.zeros_like(v), where=k2 != 0)
fields = [('original', u, v), ('divergence_free', u-gx, v-gy), ('gradient', gx, gy)]

for name, a, b in fields:
    a, b = np.fft.ifft2(a).real, np.fft.ifft2(b).real
    needles = []
    for i, j in np.ndindex(N, N):
        d = np.array([a[i,j], b[i,j]])
        d *= 0.8/N / (np.linalg.norm(d) + 1e-12)
        p = (np.array([i,j]) + 0.5)/N
        n = 0.07*np.array([-d[1], d[0]])
        needles.append([p-d/2-n, p-d/2+n, p+d/2])
    fig, ax = plt.subplots(figsize=(4,4))
    ax.add_collection(PolyCollection(needles, facecolor='#344c43', edgecolor='none'))
    ax.set(xlim=(0,1), ylim=(0,1), aspect='equal')
    ax.axis('off')
    fig.savefig(name+'.svg', bbox_inches='tight')
    plt.close(fig)
