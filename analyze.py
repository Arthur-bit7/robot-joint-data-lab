"""第四步实验：读取网上的机器人关节 CSV，计算指标并绘图。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def read_csv(path: Path, required: tuple[str, ...]) -> dict[str, np.ndarray]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or any(name not in reader.fieldnames for name in required):
            raise ValueError(f"{path.name} 缺少列；需要 {required}")
        columns: dict[str, list[float]] = {name: [] for name in required}
        for row_number, row in enumerate(reader, start=2):
            for name in required:
                try:
                    value = float(row[name])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{path.name} 第 {row_number} 行的 {name} 不是数字") from exc
                if not np.isfinite(value):
                    raise ValueError(f"{path.name} 第 {row_number} 行的 {name} 非有限数")
                columns[name].append(value)
    if len(next(iter(columns.values()))) < 3:
        raise ValueError(f"{path.name} 至少需要 3 行数据")
    return {name: np.asarray(values, dtype=float) for name, values in columns.items()}


def validate_time(time_s: np.ndarray, filename: str) -> None:
    if np.any(np.diff(time_s) <= 0):
        raise ValueError(f"{filename} 的时间必须严格递增")


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    reference = read_csv(
        RAW / "demo_trajectory.csv",
        ("time", "q1", "q2", "q1_dot", "q2_dot"),
    )
    tracking = read_csv(
        RAW / "tracking_results.csv",
        ("time", "desired_q1", "actual_q1"),
    )
    validate_time(reference["time"], "demo_trajectory.csv")
    validate_time(tracking["time"], "tracking_results.csv")

    # 两个原始文件采样频率不同，不能按行号拼接；在跟踪数据自己的时间轴上估算速度。
    t = tracking["time"] - tracking["time"][0]
    target = tracking["desired_q1"]
    actual = tracking["actual_q1"]
    target_velocity_est = np.gradient(target, t)
    actual_velocity_est = np.gradient(actual, t)
    error = target - actual
    absolute_error = np.abs(error)

    processed_path = PROCESSED / "joint1_tracking_with_estimated_velocity.csv"
    with processed_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow((
            "time_s", "target_position_rad", "actual_position_rad",
            "target_velocity_est_rad_s", "actual_velocity_est_rad_s",
            "position_error_rad",
        ))
        for row in zip(t, target, actual, target_velocity_est, actual_velocity_est, error):
            writer.writerow(f"{value:.8f}" for value in row)

    metrics = {
        "source_rows_reference": int(len(reference["time"])),
        "source_rows_tracking_excerpt": int(len(t)),
        "tracking_duration_s": float(t[-1]),
        "target_position_max_rad": float(np.max(target)),
        "actual_position_max_rad": float(np.max(actual)),
        "actual_position_mean_rad": float(np.mean(actual)),
        "actual_velocity_max_abs_est_rad_s": float(np.max(np.abs(actual_velocity_est))),
        "actual_velocity_mean_signed_est_rad_s": float(np.mean(actual_velocity_est)),
        "actual_velocity_mean_abs_est_rad_s": float(np.mean(np.abs(actual_velocity_est))),
        "position_error_mean_abs_rad": float(np.mean(absolute_error)),
        "position_error_max_abs_rad": float(np.max(absolute_error)),
        "position_error_rmse_rad": float(np.sqrt(np.mean(error**2))),
    }
    (RESULTS / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, layout="constrained")
    axes[0].plot(t, target, label="Target position")
    axes[0].plot(t, actual, label="Actual position")
    axes[0].set_ylabel("Joint 1 position (rad)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    axes[1].plot(t, error, color="#b45309", label="Target - actual")
    axes[1].axhline(0, color="gray", linewidth=0.8)
    axes[1].set_xlabel("Time since excerpt start (s)")
    axes[1].set_ylabel("Position error (rad)")
    axes[1].grid(alpha=0.25)
    fig.savefig(RESULTS / "joint1_target_vs_actual.png", dpi=160)
    fig.savefig(RESULTS / "joint1_target_vs_actual.svg")
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, layout="constrained")
    axes[0].plot(reference["time"], reference["q1"], label="q1")
    axes[0].plot(reference["time"], reference["q2"], label="q2")
    axes[0].set_ylabel("Reference position (rad)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)
    axes[1].plot(reference["time"], reference["q1_dot"], label="q1_dot")
    axes[1].plot(reference["time"], reference["q2_dot"], label="q2_dot")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Reference velocity (rad/s)")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    fig.savefig(RESULTS / "reference_position_velocity.png", dpi=160)
    fig.savefig(RESULTS / "reference_position_velocity.svg")
    plt.close(fig)

    for name, value in metrics.items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()

