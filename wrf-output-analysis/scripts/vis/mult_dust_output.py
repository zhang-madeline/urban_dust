import glob
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
import cartopy.crs as ccrs
from netCDF4 import Dataset

filepath = "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/wrf_chem/ea_real/v2-domain/"
outdir   = "dust_plots"
os.makedirs(outdir, exist_ok=True)

files = sorted(glob.glob(os.path.join(filepath, "wrfout_d01_*")))
g = 9.81
dust_vars = ["DUST_1", "DUST_2", "DUST_3", "DUST_4", "DUST_5"]

def column_dust(ds, t):
    """Column-integrated dust (g/m2) for time index t."""
    # Total dust mixing ratio (ug/kg dry air), shape (bottom_top, sn, we)
    q = sum(ds.variables[v][t] for v in dust_vars)

    if "MU" in ds.variables and "MUB" in ds.variables and "DNW" in ds.variables:
        # Dry air mass per unit area in each layer (kg/m2):
        #   dp = -DNW * (MU + MUB)  [Pa],   mass = dp / g
        mu_total = ds.variables["MU"][t] + ds.variables["MUB"][t]      # (sn, we)
        dnw = ds.variables["DNW"][t][:, None, None]                    # (bottom_top, 1, 1)
        layer_mass = -dnw * mu_total[None, :, :] / g
    else:
        # Fallback: density from pressure and temperature, thickness from geopotential
        p = ds.variables["P"][t] + ds.variables["PB"][t]               # Pa
        theta = ds.variables["T"][t] + 300.0                           # K
        temp = theta * (p / 1.0e5) ** (287.04 / 1004.5)                # K
        rho = p / (287.04 * temp)                                      # kg/m3
        z_stag = (ds.variables["PH"][t] + ds.variables["PHB"][t]) / g
        dz = np.diff(z_stag, axis=0)                                   # m
        layer_mass = rho * dz

    # ug/kg * kg/m2 -> ug/m2, summed over layers, converted to g/m2
    return np.sum(q * layer_mass, axis=0) * 1e-6

# ---------- Load every time step from every file ----------
fields, tstrings = [], []
lats = lons = None

for f in files:
    with Dataset(f) as ds:
        if lats is None:
            lats = ds.variables["XLAT"][0]
            lons = ds.variables["XLONG"][0]
        times = ds.variables["Times"][:]
        for i in range(ds.dimensions["Time"].size):
            tstrings.append("".join(c.decode() for c in times[i]).replace("_", " "))
            fields.append(np.asarray(column_dust(ds, i)))

vmax = max(float(np.nanmax(d)) for d in fields)
# vmax = 5.0   # optionally fix manually (g/m2)
norm = mcolors.Normalize(vmin=0, vmax=vmax)
print(f"{len(fields)} frames, colour scale 0 to {vmax:.3f} g/m2")

# ---------- Set up the figure once ----------
fig = plt.figure(figsize=(9, 7))
ax = plt.axes(projection=ccrs.PlateCarree())

mesh = ax.pcolormesh(lons, lats, fields[0],
                     cmap="YlOrBr", norm=norm,
                     shading="gouraud",
                     transform=ccrs.PlateCarree())
ax.coastlines()
ax.gridlines(draw_labels=True, linewidth=0.3)

cbar = fig.colorbar(mesh, ax=ax, orientation="vertical", shrink=0.8, pad=0.05,
                    extend="max")
cbar.set_label("Column-integrated dust (g m$^{-2}$)")

title = ax.set_title(f"Total dust column burden\n{tstrings[0]}")


def update(k):
    mesh.set_array(fields[k].ravel())
    title.set_text(f"Total dust column burden\n{tstrings[k]}")
    return mesh, title


anim = FuncAnimation(fig, update, frames=len(fields), interval=200, blit=False)

# ---------- Save ----------
# MP4 (needs ffmpeg installed): smaller and smoother
try:
    anim.save(os.path.join(outdir, "dust_animation.mp4"),
              writer=FFMpegWriter(fps=5, bitrate=3000), dpi=150)
    print("Saved MP4")
except Exception as e:
    #print("MP4 failed (is ffmpeg installed?):", e)
    # GIF (no ffmpeg needed)
    anim.save(os.path.join(outdir, "dust_animation.gif"),
          writer=PillowWriter(fps=25), dpi=100)
    print("Saved GIF")

plt.close(fig)
