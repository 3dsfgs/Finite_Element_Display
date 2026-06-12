import vtk
from .yarn_property import Yarn
import numpy as np
'''
此文件用于定义枚举值、放置一些公共函数
'''

class ControlMode:
    default_type = 0
    select_points = 1
    select_face = 2
    select_cell = 3
    select_model = 4
    inp_type = 5
    node_type = 6
    axis_show = 7
    cellID_show = 8
    cellNormal_show = 9
    yarn_type = 10


class ScalarValue:
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    red_normalization = (1.0, 0, 0)
    green_normalization = (0, 1.0, 0)
    blue_normalization = (0, 0, 1.0)
    black = (0, 0, 0)
    ori_ = (0.31*255, 0.51*255, 0.9*255)

def addPartID(polydata, part_id):
    """
    为每个 polydata 的所有 Cell 添加一个名为 "PartID" 的数组，
    所有 Cell 的值均为 part_id。
    """
    num_cells = polydata.GetNumberOfCells()
    partArray = vtk.vtkIntArray()
    partArray.SetName("PartID")
    partArray.SetNumberOfComponents(1)
    partArray.SetNumberOfTuples(num_cells)
    for i in range(num_cells):
        partArray.SetValue(i, part_id)
    polydata.GetCellData().AddArray(partArray)

def mergePolyData(polydata_list):
    """
    使用 vtkAppendPolyData 将所有子 PolyData 合并成一个 vtkPolyData。
    """
    appendFilter = vtk.vtkAppendPolyData()
    for i, pd in enumerate(polydata_list):
        addPartID(pd, i)
        appendFilter.AddInputData(pd)
    appendFilter.Update()
    return appendFilter.GetOutput()

def parse_inp_file(filepath):
    """
        nodes: list of (pid, x, y, z)
        elements: list of (id, pid1, pid2, pid3, pid4)
    """
    with open(filepath) as f:
        lines = f.readlines()
        Nodes = []
        ElementSets = []  # 存储多个点集
        node_index = [0, 0]
        mesh_index = []

        # 找到所有分段的索引位置
        for i in range(len(lines)):
            l = lines[i]
            if l.startswith("*NODE"):
                node_index[0] = i
            if l.startswith("*NSET"):
                node_index[1] = i
            if l.startswith("*ELEMENT") or l.startswith("*ELSET"):
                mesh_index.append(i)

        # 解析节点数据
        for index in range(node_index[0] + 1, node_index[1]):
            line = lines[index]
            data = line.strip().split(',')
            id = int(data[0])
            x = float(data[1])
            y = float(data[2])
            z = float(data[3])
            da = [x, y, z]
            Nodes.append(da)

        # 解析多个单元集
        for i in range(len(mesh_index) - 1):
            Triangles = []  # 每个单元集的三角形
            for index in range(mesh_index[i] + 1, mesh_index[i + 1]):
                line = lines[index]
                data = line.strip().split(',')
                if len(data) >= 5:  # 确保数据行包含足够的元素
                    id = int(data[0])
                    ids = [int(data[j]) - 1 for j in range(1, 5)]
                    Triangles.append([4, ids[0], ids[1], ids[2], ids[3]])
            if Triangles:  # 只添加非空的单元集
                ElementSets.append(Triangles)

    return Nodes, ElementSets


def read_Nodes(node_file):
    offset = -100
    Nodes = []
    uNodes = []
    offs = []
    with open(node_file) as f:
        lines = f.readlines()
        for line in lines:
            data = line.strip().split(',')
            id = int(data[0].split(".")[0])
            x = float(data[1])
            y = float(data[2])
            z = float(data[3])
            ux = float(data[4])
            uy = float(data[5])
            uz = float(data[6])
            da = [x, y, z]
            uda = [offset + x + ux, y + uy, z + uz]
            off = [ux, uy, uz]
            Nodes.append(da)
            uNodes.append(uda)
            offs.append(off)
    return Nodes, uNodes, offs


def read_Triangles(triangle_file):
    Triangles = []
    with open(triangle_file) as f:
        lines = f.readlines()
        for line in lines:
            data = line.strip().split(',')
            id = int(data[0].split(".")[0])
            ids = [int(data[i].split(".")[0]) - 1 for i in range(1, 9)]
            Triangles.extend([
                [4, ids[0], ids[1], ids[2], ids[3]],  # Bottom face
                [4, ids[0], ids[1], ids[5], ids[4]],  # Front face
                [4, ids[0], ids[3], ids[7], ids[4]],  # Left face
                [4, ids[1], ids[2], ids[6], ids[5]],  # Right face
                [4, ids[4], ids[5], ids[6], ids[7]],  # Top face
                [4, ids[3], ids[2], ids[6], ids[7]]  # Back face
            ])
            # ids = [int(data[i].split(".")[0]) - 1 for i in range(1, 5)]
            # Triangles.extend([
            #     [4, ids[0], ids[1], ids[2], ids[3]],  # Bottom face
            # ])
    return Triangles

# region 纱线属性解析函数
def read_yarn_info(lines_file, nodes_file):
    yarns = []
    yarns_by_type = {1: [], 2: []}
    with open(lines_file, 'r') as f:
        lines = f.readlines()
    weft_count, warp_count = map(int, lines[0].strip().split(','))
    yarn_data = lines[2:]
    with open(nodes_file, 'r') as f:
        node_lines = f.readlines()
    total_nodes = int(node_lines[0].strip())
    coords = [list(map(float, ln.strip().split(','))) for ln in node_lines[1:]]
    if len(coords) != total_nodes:
        raise ValueError('Node count mismatch')

    for i,ln in enumerate(yarn_data):
        parts = ln.strip().split(',')
        yid = int(parts[0]); ytype = int(parts[1])
        col = int(parts[2]); lay = int(parts[3])
        direc = parts[4]; spec = parts[5]
        cnt = int(parts[6])
        _lines = [list(map(float, l.strip().split(','))) for l in yarn_data]
        lines_node = [list(range(int(idx - 1), int(idx + n - 1))) for *_, n, idx in _lines]
        nodes = [coords[j] for j in lines_node[i]]
        y = Yarn(yid, ytype, col, lay, direc, spec, nodes)
        yarns.append(y)
        yarns_by_type[ytype].append(y)
    return yarns, yarns_by_type
# endregion


def read_yarn(lines_file, nodes_file):
    yarns = []
    yarns_by_type = {1: [], 2: []}

    # 常量参数
    df = 5.12e-3  # 单根碳纤维丝直径 (mm)
    vf1k = 0.9
    ak = 0
    drota = 0.0
    nx, ny = 1, 2
    drota *= 360.0  # 将圈数转换为度数 (1圈 = 360°)
    r0 = 0.5 * df  # 单纤维半径
    r1k = r0 * np.sqrt(1000.0 / vf1k)

    # ==================== 读取关键点坐标 ====================
    with open(nodes_file, 'r') as f:
        nkp = int(f.readline().strip())  # 关键点总数
        COORDKP = np.zeros((nkp, 3), dtype=float)
        for i in range(nkp):
            COORDKP[i, :] = np.array(f.readline().split(','), dtype=float)

    # ==================== 读取纱线拓扑信息 ====================
    with open(lines_file, 'r') as f:
        nweft, nwarp = map(int, f.readline().split(','))
        nyarn = nweft + nwarp
        print(f"纱线数量、纬纱数量、经纱数量：{nyarn}, {nweft}, {nwarp}")

        # 初始化
        NX_NY = np.zeros((nyarn, 2), dtype=int)  # 每根纱线在 X/Y 方向的纤维数
        KP_OF_YARN = np.zeros((nyarn, 2), dtype=int)  # 每根纱线端点关键点索引 (1-based)
        SIZE_YARN0 = np.zeros(nyarn, dtype=float)  # 初始纱线规格

        f.readline()  # 跳过标题行
        metadata = []  # 暂存每根纱线的 metadata 和索引信息
        for i in range(nyarn):
            line_parts = f.readline().strip().split(',')[0:8]
            iyarn, itype, irow, klayer, idirection = map(int, line_parts[0:5])
            sizei = float(line_parts[5])
            nn1, k1 = map(int, line_parts[6:8])
            # 记录端点的关键点索引 (假设文件里是 1-based)
            KP_OF_YARN[i, :] = [k1, k1 + nn1 - 1]
            SIZE_YARN0[i] = sizei
            metadata.append((iyarn, itype, irow, klayer, idirection, sizei))

    SIZE_YARN = SIZE_YARN0.copy()

    # ==================== 计算每根纱线在 X/Y 方向的排列数 ====================
    iflag = 0
    if nx == 0 or ny == 0:
        iflag = 1

    for iyarn in range(nyarn):
        sizei = SIZE_YARN[iyarn]
        if iflag == 1:
            nx = int((1 + np.sqrt(1 + 2 * sizei * ak)) / 2)
            ny = max(1, nx - 1)
            print(sizei, nx, ny)
        NX_NY[iyarn, 0] = nx
        NX_NY[iyarn, 1] = ny

    # ==================== 显示基本信息 ====================
    nn = 0
    nfiber = 0
    iflag = 0
    for iyarn in range(nyarn):
        sizei = SIZE_YARN[iyarn]
        nx = NX_NY[iyarn, 0]
        ny = NX_NY[iyarn, 1]
        nfiber += nx * ny
        n1, n2 = KP_OF_YARN[iyarn]
        nn += nx * ny * (n2 - n1 + 1)
        print(f"纱线 {iyarn + 1:5d}，规格 {sizei:5.1f}，纤维排列：{nx:2d} x {ny:2d}")

    print(f"纤维总数：{nfiber}")
    print(f"节点总数：{nn}")
    ne = nn - nfiber
    print(f"单元总数：{ne}")
    numemin = np.min(KP_OF_YARN[:, 1] - KP_OF_YARN[:, 0]) + 1
    print(f"最短纱线（纤维）单元数：{numemin}")

    # ==================== 生成 Yarn 实例 ====================
    for i in range(nyarn):
        iyarn, itype, irow, klayer, idirection, sizei = metadata[i]
        k1, k2 = KP_OF_YARN[i]  # 1-based 关键点索引
        # 提取从 k1 到 k2(包含)的控制点 (转换为 0-based)
        nodes = COORDKP[k1 - 1:k2, :].tolist()

        # 构造 Yarn，nodes 传入为 list of [x,y,z]
        y = Yarn(
            yarn_id=iyarn,
            yarn_type=itype,
            column=irow,
            layer=klayer,
            direction=idirection,
            spec=sizei,
            nodes=nodes
        )
        yarns.append(y)
        yarns_by_type[itype].append(y)

    return yarns, yarns_by_type,NX_NY, SIZE_YARN, KP_OF_YARN, COORDKP, r1k, drota