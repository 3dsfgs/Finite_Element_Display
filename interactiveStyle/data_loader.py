import numpy as np

# region 有限元相关
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
    return Triangles
# endregion

# region 纱线相关
class Yarn:
    def __init__(self, yarn_id, yarn_type, column, layer, direction, spec, node_count, nodes):
        self.yarn_id = yarn_id
        self.yarn_type = yarn_type  # 1: 经纱, 2: 纬纱
        self.column = column
        self.layer = layer
        self.direction = direction
        self.spec = spec
        self.node_count = node_count
        self.nodes = nodes  # 节点的三维坐标列表

    def __repr__(self):
        return f"Yarn(id={self.yarn_id}, type={self.yarn_type}, column={self.column}, layer={self.layer}, direction={self.direction}, spec={self.spec}, nodes={self.nodes})"

def read_yarn_info(lines_file, nodes_file):
    yarns = []  # 所有纱线实例集合
    yarns_by_type = {1: [], 2: []}  # 按纱线类别分类的集合

    # 读取 lines_file
    with open(lines_file, 'r') as f:
        lines = f.readlines()

    # 解析纬纱数量和经纱数量
    weft_count, warp_count = map(int, lines[0].strip().split(','))
    
    # 跳过第二行注释信息
    yarn_data = lines[2:]

    # 读取 nodes_file
    with open(nodes_file, 'r') as f:
        nodes_lines = f.readlines()

    total_nodes = int(nodes_lines[0].strip())  # 总节点个数
    node_coordinates = [list(map(float, line.strip().split(','))) for line in nodes_lines[1:]]

    if len(node_coordinates) != total_nodes:
        raise ValueError("节点数量与文件中提供的总节点个数不匹配！")

    # 解析纱线信息
    for line in yarn_data:
        parts = line.strip().split(',')
        yarn_id = int(parts[0])
        yarn_type = int(parts[1])  # 1: 经纱, 2: 纬纱
        column = int(parts[2])
        layer = int(parts[3])
        direction = parts[4]
        spec = parts[5]
        node_count = int(parts[6])
        node_indices = list(map(int, parts[7:7 + node_count]))

        # 根据节点索引获取三维坐标
        nodes = [node_coordinates[idx] for idx in node_indices]

        # 创建纱线实例
        yarn = Yarn(yarn_id, yarn_type, column, layer, direction, spec, node_count, nodes)
        yarns.append(yarn)
        yarns_by_type[yarn_type].append(yarn)

    return yarns, yarns_by_type
# endregion

if __name__ == "__main__":
    lines_file = "./data/yarn/user-1-yarn-lines.dat"
    nodes_file = "./data/yarn/user-1-yarn-nodes.dat"
    yarns, yarns_by_type = read_yarn_info(lines_file, nodes_file)

    print("所有纱线实例：", yarns)
    print("经纱集合：", yarns_by_type[1])
    print("纬纱集合：", yarns_by_type[2])