#!/usr/bin/env python3
"""
N01 CE201 - Flight Evaluation Plot Generator
Generates high-resolution publication-quality plots from mission timeseries CSVs.
"""

from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

LOGS_DIR = Path('/workspace/sim/evidence/flight_logs')

def plot_hover(run_id='20261108_133915'):
    hover_csv = LOGS_DIR / f'hover_{run_id}.csv'
    if not hover_csv.exists():
        print(f"File not found: {hover_csv}")
        return
    
    with open(hover_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    t = [float(r['t_rel_s']) for r in rows]
    ex = [float(r['est_x']) for r in rows]
    ey = [float(r['est_y']) for r in rows]
    ez = [float(r['est_z']) for r in rows]
    err_xy = [float(r['err_xy']) for r in rows]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    
    ax1.plot(t, ex, 'b-', label='Est X (North)')
    ax1.plot(t, ey, 'g-', label='Est Y (East)')
    ax1.axhline(0.5, color='r', linestyle='--', label='KPI Threshold (+0.5m)')
    ax1.axhline(-0.5, color='r', linestyle='--', label='KPI Threshold (-0.5m)')
    ax1.set_ylabel('Position (m)')
    ax1.set_title('N01 CE201 - Non-GPS 30s Hover Position Hold (Altitude 1.0m)')
    ax1.grid(True, linestyle=':')
    ax1.legend(loc='upper right')
    
    ax2.plot(t, err_xy, 'k-', linewidth=1.8, label='Horizontal Error e_xy')
    ax2.plot(t, [-z for z in ez], 'm--', label='Height AGL (-z)')
    ax2.axhline(0.5, color='r', linestyle='--', label='Max Error Bound (0.5m)')
    ax2.axhline(1.0, color='c', linestyle=':', label='Target Height (1.0m)')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Error / Height (m)')
    ax2.grid(True, linestyle=':')
    ax2.legend(loc='upper right')
    
    plt.tight_layout()
    out1 = LOGS_DIR / f'hover_plot_{run_id}.png'
    plt.savefig(out1, dpi=200)
    plt.close()
    print(f"Generated hover plot: {out1}")

def plot_square():
    square_csv = LOGS_DIR / 'square_20261107_101837.csv'
    if not square_csv.exists():
        print(f"File not found: {square_csv}")
        return
    
    with open(square_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    est_x = [float(r['est_x']) for r in rows]
    est_y = [float(r['est_y']) for r in rows]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Square corridor reference
    sq_x = [0.0, 2.0, 2.0, 0.0, 0.0]
    sq_y = [0.0, 0.0, 2.0, 2.0, 0.0]
    ax.plot(sq_y, sq_x, 'r--', linewidth=2.0, label='Target Waypoint Path (2x2m)')
    
    # Drone estimated trajectory (East on X-axis, North on Y-axis)
    ax.plot(est_y, est_x, 'b-', linewidth=2.2, label='EKF2 Optical Flow Trajectory')
    
    # Mark waypoints
    ax.scatter([0, 0, 2, 2], [0, 2, 2, 0], color='red', s=70, zorder=5)
    ax.text(0.05, -0.08, 'WP0/WP4 (0,0)', fontsize=10, fontweight='bold')
    ax.text(-0.08, 2.05, 'WP1 (2,0)', fontsize=10, fontweight='bold')
    ax.text(1.95, 2.05, 'WP2 (2,2)', fontsize=10, fontweight='bold')
    ax.text(2.05, -0.08, 'WP3 (0,2)', fontsize=10, fontweight='bold')
    
    ax.set_xlabel('East [Y] (m)')
    ax.set_ylabel('North [X] (m)')
    ax.set_title('N01 CE201 - Non-GPS 2x2m Square Trajectory Following (1.0m AGL)')
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(-0.5, 2.5)
    ax.set_aspect('equal', 'box')
    ax.grid(True, linestyle=':')
    ax.legend(loc='center')
    
    plt.tight_layout()
    out2 = LOGS_DIR / 'square_plot_20261107_101837.png'
    plt.savefig(out2, dpi=200)
    plt.close()
    print(f"Generated square plot: {out2}")

if __name__ == '__main__':
    plot_hover()
    plot_square()
