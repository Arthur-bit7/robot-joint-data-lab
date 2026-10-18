# 机器人关节数据处理实验（学习路线第 4 步）

这是一个可直接运行的 Python / NumPy / Matplotlib 练习仓库。它读取网上公开的仿真机器人 CSV，分析一个关节的目标与实际轨迹，计算统计指标，并输出图片与结果文件。

## 先看数据

| 文件 | 内容 | 用途 |
| --- | --- | --- |
| `data/raw/demo_trajectory.csv` | 网上公开的原始参考轨迹，2,000 行，包含 `time,q1,q2,q1_dot,q2_dot` | 练习读取时间、位置与速度；画参考位置和速度图 |
| `data/raw/tracking_results.csv` | 同一项目已验证的跟踪结果前 500 行，包含时间、目标位置、实际位置等 | 比较关节 1 的目标与实际，计算误差 |
| `data/processed/joint1_tracking_with_estimated_velocity.csv` | 本仓库脚本生成 | 含关节 1 目标/实际位置、估算速度和误差 |

原始来源：

- [参考轨迹 CSV](https://github.com/mhfakouri/ros2-planar-robot-trajectory-tracking/blob/main/config/demo_trajectory.csv)
- [跟踪结果 CSV](https://github.com/mhfakouri/ros2-planar-robot-trajectory-tracking/blob/main/results/verified_tuning/tracking_results.csv)
- [原项目说明](https://github.com/mhfakouri/ros2-planar-robot-trajectory-tracking)

数据由原项目的 **ROS 2 双关节机器人仿真**生成，并非真实机器人实测。本仓库仅截取跟踪结果前 500 行（从 CSV 表头后的第一行开始），方便初学者观察启动阶段的误差如何收敛。原项目采用 MIT 许可证，许可证副本见 `data/raw/UPSTREAM_LICENSE.txt`。

两个 CSV 的时间起点与采样频率不同，因此脚本**不会按行号把它们拼接**。处理后的速度是从跟踪 CSV 的位置与时间通过 `numpy.gradient` 估算，列名带 `_est`；它不是传感器直接测得的速度。参考轨迹 CSV 中的 `q1_dot/q2_dot` 是来源文件已有的速度列。

## 运行

需要 Python 3.10 或更新版本。在仓库目录执行：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe analyze.py
```

Ubuntu / Linux：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python analyze.py
```

运行后应生成：

- `data/processed/joint1_tracking_with_estimated_velocity.csv`：清洗后的单关节数据
- `results/metrics.json`：最大值、平均值、平均绝对误差、最大绝对误差、均方根误差
- `results/joint1_target_vs_actual.png`：目标与实际位置及误差
- `results/reference_position_velocity.png`：原始参考位置与速度
- `results/*.svg`：同一图表的矢量版本，便于在 GitHub 查看和下载

## 每一步在做什么

1. `csv.DictReader` 按列名读取两个文件。脚本检查列是否存在、数字是否有效、时间是否递增。
2. 用 `np.gradient(position, time)` 估算跟踪数据中的速度。真实实验中优先使用设备直接提供的速度列。
3. 定义位置误差：`error = target - actual`。正值表示目标角度大于实际角度。
4. 计算 `mean(abs(error))`（平均绝对误差）、`max(abs(error))`（最大绝对误差）及 RMSE。位置单位为弧度，速度单位为弧度/秒。
5. 用 Matplotlib 画目标与实际曲线，并把原始数据、处理后数据、指标和图都保存在仓库中。

**注意速度平均值的含义：**带符号平均速度会让正反方向互相抵消；如果关心关节平均运动快慢，看 `actual_velocity_mean_abs_est_rad_s`。

## 自己继续练习

- 将分析从关节 1 扩展到关节 2。
- 用完整的网上跟踪 CSV 替换目前的 500 行摘录，重新运行，比较统计指标变化。
- 选另一份 CSV，修改 `read_csv(...)` 的列名映射，保留来源和单位说明。
- 在 README 记录你观察到的：起始误差多大、何时减小、是否有持续偏差。

## 提交到 GitHub

该目录已是本地 Git 仓库。创建**私有** GitHub 仓库后，在本目录执行：

```bash
git remote add origin <你的仓库地址>
git push -u origin main
```

`results/` 中的图片和指标已作为本次可核对的运行产出提交。以后重新运行脚本后，检查 `git diff`，再提交改动。

