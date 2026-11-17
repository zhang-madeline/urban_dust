import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import find_peaks

folder_base = '/gucnas3/madeline/adnet/'
os.chdir(folder_base)

PPP = 'TKO'
start_date = pd.to_datetime('2023-01-01')
end_date   = pd.to_datetime('2023-12-31')

EXT_MAX      = 5e-3     # 1/m; extinction above this is treated as bad data
DAILY_AGG    = 'mean'   # 'mean', 'max', or 'median' of the 15-min AODs
MIN_VALID    = 8        # minimum valid profiles per day (8 = 2 h)
N_PEAKS      = 5        # extra peaks to label besides the annual max
MIN_SEP_DAYS = 5        # peaks must be at least this many days apart


def process_day(day, ppp):
    """Return one daily dust AOD (532 nm), or NaN if no file / too little data."""
    YY, MM, DD = day.strftime('%y'), day.strftime('%m'), day.strftime('%d')
    path = f'{folder_base}/{YY}{MM}/{ppp}{YY}{MM}{DD}.nc'
    if not os.path.exists(path):
        return np.nan

    with xr.open_dataset(path, decode_times=False) as ds:
        extd = ds['extd532'].load()          # (HEIGHT_E, TIME), 1/m
        height_km = ds['HEIGHT_E'].values    # km

    # mask flags (-9999, -999) and unphysically large values
    extd = extd.where((extd >= 0) & (extd <= EXT_MAX))

    dz_m = np.diff(height_km).mean() * 1000          # km -> m
    aod = np.nansum(extd.values, axis=0) * dz_m      # dimensionless, per 15-min profile
    aod[np.all(np.isnan(extd.values), axis=0)] = np.nan

    valid = aod[~np.isnan(aod)]
    if valid.size < MIN_VALID:
        return np.nan
    return getattr(np, DAILY_AGG)(valid)


# ---- loop over the year ----
days = pd.date_range(start_date, end_date, freq='D')
daily = pd.Series([process_day(d, PPP) for d in days], index=days,
                  name=f'dust_aod_{DAILY_AGG}')

if daily.isna().all():
    raise RuntimeError('No valid data; check folder_base / station / dates.')

daily.to_csv(f'{PPP}_dust_AOD_2023_daily.csv')

# ---- find maxima ----
t_max = daily.idxmax()
v_max = daily.max()

idx, _ = find_peaks(daily.fillna(0).values, distance=MIN_SEP_DAYS)
top = daily.iloc[idx].drop(t_max, errors='ignore').nlargest(N_PEAKS)

# ---- plot ----
fig, ax = plt.subplots(figsize=(14, 5))

ax.plot(daily.index, daily.values, lw=1.2, color='tab:blue',
        marker='.', ms=3, label=f'daily {DAILY_AGG}')

ax.axhline(v_max, color='crimson', ls='--', lw=0.8, alpha=0.7)
ax.plot(t_max, v_max, marker='*', ms=16, color='crimson', zorder=5,
        label=f'annual max: {v_max:.2f}')
ax.annotate(f'{t_max:%d %b}\nAOD = {v_max:.2f}',
            xy=(t_max, v_max), xytext=(15, -5), textcoords='offset points',
            color='crimson', fontsize=9, fontweight='bold', va='top')

for t, v in top.items():
    ax.plot(t, v, 'o', color='tab:orange', ms=6, zorder=4)
    ax.annotate(f'{t:%d %b}', xy=(t, v), xytext=(0, 8),
                textcoords='offset points', ha='center',
                fontsize=8, color='tab:orange')
ax.plot([], [], 'o', color='tab:orange', label=f'next {N_PEAKS} peaks')

ax.set_ylabel(f'Daily {DAILY_AGG} dust AOD (532 nm)')
ax.set_title(f'AD-Net dust optical depth, {PPP}, 2023')
ax.set_xlim(start_date, end_date)
ax.set_ylim(bottom=0)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.legend(loc='upper right')
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PPP}_dust_AOD_2023_daily.png', dpi=200)
plt.show()
