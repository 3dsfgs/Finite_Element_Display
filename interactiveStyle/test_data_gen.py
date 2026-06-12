import numpy as np

def generate_sin_cos_lines(N, output_nodes_file, output_lines_file):
    """
    在 xoy 和 zoy 平面生成 2 条 sin 曲线和 2 条 cos 曲线，并保存点和线信息。
    
    Args:
        N (int): 总采样点数。
        output_nodes_file (str): 保存节点坐标的文件路径。
        output_lines_file (str): 保存线条信息的文件路径。
    """
    # 每条曲线的采样点数
    num_curves = 8  # 4 条曲线在 xoy 平面，4 条曲线在 zoy 平面
    points_per_curve = N // num_curves

    # 存储所有点的坐标
    nodes = []
    # 存储每条线的第一个点索引
    lines = []

    # 生成 xoy 平面的曲线
    x = np.linspace(0, 2 * np.pi, points_per_curve)
    y_offsets = [-3, 0, 3, 6]  # y 坐标的偏移量
    for i, offset in enumerate(y_offsets):
        if i % 2 == 0:  # sin 曲线
            y = np.sin(x) + offset
        else:  # cos 曲线
            y = np.cos(x) + offset
        z = np.zeros_like(x)  # z 坐标为 0
        curve_points = np.column_stack((x, y, z))
        nodes.extend(curve_points)
        lines.append(len(nodes) - points_per_curve)  # 记录每条线的第一个点索引

    # 生成 zoy 平面的曲线
    z = np.linspace(0, 2 * np.pi, points_per_curve)
    y_offsets = [-3, 0, 3, 6]  # y 坐标的偏移量
    for i, offset in enumerate(y_offsets):
        if i % 2 == 0:  # sin 曲线
            y = np.sin(z) + offset
        else:  # cos 曲线
            y = np.cos(z) + offset
        x = np.zeros_like(z)  # x 坐标为 0
        curve_points = np.column_stack((x, y, z))
        nodes.extend(curve_points)
        lines.append(len(nodes) - points_per_curve)  # 记录每条线的第一个点索引

    # 保存节点坐标到文件
    with open(output_nodes_file, 'w') as f:
        f.write(f"{len(nodes)}\n")  # 第一行写入总节点数
        for node in nodes:
            f.write(f"{node[0]:.6f},{node[1]:.6f},{node[2]:.6f}\n")

    # 保存线条信息到文件
    with open(output_lines_file, 'w') as f:
        f.write(f"{num_curves//2},{num_curves//2}\n")
        f.write(f"###\n")
        for ind in range(len(lines)):
            line_start = lines[ind] + 1  # 从 1 开始
            f.write(f"{ind},{ind%2+1},0,0,0,24,{points_per_curve},{line_start}\n")

if __name__ == "__main__":
    N = 100  # 总采样点数
    output_nodes_file = "./data/yarn-nodes-100.dat"
    output_lines_file = "./data/yarn-lines-100.dat"

    generate_sin_cos_lines(N, output_nodes_file, output_lines_file)

    print(f"节点数据已保存到 {output_nodes_file}")
    print(f"线条数据已保存到 {output_lines_file}")