#!/usr/bin/env python3
"""
AD-Net Tokyo (TKO): daily dust-mass heat maps for a year -> PNG frames -> animation.

Folder layout expected:  FOLDER_BASE/YYMM/TKOYYMMDD.nc   (variable: extd532, dims HEIGHT_E x TIME)
Frames are cached in FRAME_DIR, so a re-run only draws missing days.
"""
import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")                       # no GUI window per figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ------------------------------ settings ------------------------------------
FOLDER_BASE = '/gucnas3/madeline/adnet'
PPP = "TKO"
START, END = "2023-01-01", "2023-12-31"

CV, RHO = 0.75e-6, 2600.0                   # m, kg/m3
CMAP, VMIN, VMAX_PLOT = "plasma", 0, 300    # fixed colour scale: same for every frame
YMAX_KM = 300                                 # fixed height axis: same for every frame
FILL_THRESHOLD = -900                       # -9999 in cloud, -999 above cloud/rain -> masked
UTC_TO_JST = pd.Timedelta(hours=9)
FPS = 7                                     # 365 frames / 4 fps ~ 90 s
MAKE_GIF = False                            # mp4 is much smaller; GIF needs no ffmpeg

FRAME_DIR = os.path.join(FOLDER_BASE, f"frames_{PPP}_{START[:4]}")
OUT_BASE = os.path.join(FOLDER_BASE, f"dust_{PPP}_{START[:4]}")


# ------------------------------ functions -----------------------------------
def adnet_path(day):
    return os.path.join(FOLDER_BASE, day.strftime("%y%m"), f"{PPP}{day:%y%m%d}.nc")


def load_dust_mass(path, day):
    """Dust mass (ug/m3), dims (HEIGHT_E, TIME), TIME in JST (end-of-interval stamps)."""
    with xr.open_dataset(path, decode_times=False) as ds:
        ext = ds["extd532"].load()
    ext = ext.where(ext > FILL_THRESHOLD)   # cloud / above-cloud fill values -> NaN (not 0!)
    ext = ext.clip(min=0)                   # small negative noise -> 0
    mass = ext * CV * RHO * 1e9
    n = mass.sizes["TIME"]
    times = day + pd.to_timedelta((np.arange(n) + 1) * 15, unit="min") + UTC_TO_JST
    return mass.assign_coords(TIME=times)


def render_frame(mass, day, out_png):
    t0 = day + UTC_TO_JST
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_facecolor("lightgrey")           # masked (cloud/rain/missing) bins show grey
    mass.plot(x="TIME", y="HEIGHT_E", ax=ax, cmap=CMAP, vmin=VMIN, vmax=VMAX_PLOT,
              cbar_kwargs={"label": "Dust mass concentration (µg m$^{-3}$)"})
    ax.set_xlim(t0.to_pydatetime(), (t0 + pd.Timedelta(days=1)).to_pydatetime())
    ax.set_ylim(0, YMAX_KM)
    ax.set_ylabel("Height (km)")
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.set_xlabel(f"Time (JST)  [file day {day:%Y-%m-%d} UTC = "
                  f"{t0:%m-%d %H:%M} to {t0 + pd.Timedelta(days=1):%m-%d %H:%M} JST]")
    ax.set_title(f"{PPP}  AD-Net dust, {day:%Y-%m-%d} (UTC day)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=100)           # fixed size: 1200x400 px for every frame
    plt.close(fig)


def make_video(frames, out_path, fps=FPS):
    import imageio.v2 as imageio            # pip install imageio imageio-ffmpeg
    with imageio.get_writer(out_path, fps=fps, codec="libx264", quality=8) as w:
        for f in frames:
            w.append_data(imageio.imread(f)[..., :3])   # drop alpha channel


def make_gif(frames, out_path, fps=FPS):
    from PIL import Image
    imgs = [Image.open(f).convert("P", palette=Image.ADAPTIVE) for f in frames]
    imgs[0].save(out_path, save_all=True, append_images=imgs[1:],
                 duration=int(1000 / fps), loop=0, optimize=True)


# ------------------------------ main loop -----------------------------------
def main():
    os.makedirs(FRAME_DIR, exist_ok=True)
    frames, missing, failed = [], [], []

    for day in pd.date_range(START, END, freq="D"):
        png = os.path.join(FRAME_DIR, f"{day:%Y%m%d}.png")
        if os.path.exists(png):             # resume support
            frames.append(png)
            continue
        path = adnet_path(day)
        if not os.path.exists(path):
            missing.append(day)
            continue
        try:
            render_frame(load_dust_mass(path, day), day, png)
            frames.append(png)
        except Exception as e:              # one bad file should not stop the year
            failed.append((day, repr(e)))
            plt.close("all")

    print(f"frames: {len(frames)}   missing files: {len(missing)}   failed: {len(failed)}")
    for d, e in failed:
        print("  failed", d.date(), e)
    if not frames:
        return

    make_video(frames, OUT_BASE + ".mp4")
    print("wrote", OUT_BASE + ".mp4")
    if MAKE_GIF:
        make_gif(frames, OUT_BASE + ".gif")
        print("wrote", OUT_BASE + ".gif")


if __name__ == "__main__":
    main()
