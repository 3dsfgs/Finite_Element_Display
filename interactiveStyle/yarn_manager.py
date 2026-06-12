import vtk
import numpy as np
from .Tool_Definition import read_yarn_info,read_yarn
from .yarn_property import Yarn
from PyQt6.QtWidgets import QMenu
from PyQt6 import QtGui


class YarnManager:
    def __init__(self, parent_widget=None, renderer=None, window=None):
        self.parent_widget = parent_widget
        self.picker = vtk.vtkPropPicker()
        self.renderer = renderer
        self.interactor = self.renderer.GetRenderWindow().GetInteractor()

        # self.parent_widget = parent_widget
        # self.picker = vtk.vtkPropPicker()
        # self.renderer = vtk.vtkRenderer()
        # self.window = vtk.vtkRenderWindow()
        # self.window.AddRenderer(self.renderer)
        # self.interactor = vtk.vtkRenderWindowInteractor()
        # self.interactor.SetRenderWindow(self.window)
        # self.interactor.Initialize()
        # self.window.Render()

        self.yarns = []
        self.select_yarn_tuple = []
        self.selected_points = []
        self.select_split = set()
        self.merge_queue = []
        self.hotkey_H = False
        self.nyarn = len(self.yarns)
        self.NX_NY = None       # 从 read_yarn 取得的二维数组
        self.SIZE_YARN = None  # 从 read_yarn 取得的大小数组
        self.KP_OF_YARN = None  # 端点关键点索引数组
        self.COORDKP = None     # 关键点坐标数组
        self.r1k = None        # 计算半径的标量
        self.drota = None      # 扭转角度

    def load_from_files(self, lines_file, nodes_file):
        self.renderer.RemoveAllViewProps()
        self.yarns.clear()
        yarns, by_type,NX_NY, SIZE_YARN, KP_OF_YARN, COORDKP, r1k, drota = read_yarn(lines_file, nodes_file)
        self.NX_NY = NX_NY
        self.SIZE_YARN = SIZE_YARN
        self.KP_OF_YARN = KP_OF_YARN
        self.COORDKP = COORDKP
        self.r1k = r1k
        self.drota = drota
        color_map = {1: (1,0,0), 2: (0,1,0)}
        for y in yarns:
            y.color = color_map.get(y.yarn_type, (0,0,1))
            y.radii = 0.05 + 0.05 * (y.yarn_type)
            y._setup_pipeline()
            y.add_to_renderer(self.renderer)
            #y.enable_interaction(False)
            y.init_interaction(self.interactor)
            y.manager = self
            self.yarns.append(y)

    def sub_step1_2_copyfiber(self, index=None):
        # 确保我们已经在 load_from_files 里存了这些数组
        NX_NY = self.NX_NY
        SIZE_YARN = self.SIZE_YARN
        KP_OF_YARN = self.KP_OF_YARN
        COORDKP = self.COORDKP
        r1k = self.r1k
        drota = self.drota

        nyarn = len(self.yarns)
        # 先计算 nfiber, nn, ne
        nfiber = int(np.sum(NX_NY[:, 0] * NX_NY[:, 1]))
        nn = 0
        for iy in range(nyarn):
            n1, n2 = KP_OF_YARN[iy] - 1
            nodewi = (n2 - n1 + 1)
            nx, ny = NX_NY[iy]
            nn += nx * ny * nodewi
        ne = nn - nfiber

        # 分配输出数组
        COORDN = np.zeros((nn, 3))
        SIZE_FIBER = np.zeros(nfiber)
        NODE_ON_FIBER = np.zeros((nfiber, 2), dtype=int)
        IFIBER_OF_YARN = np.zeros((nyarn, 2), dtype=int)
        ELEMFIBER = np.zeros(ne, dtype=int)
        ELEMATTR = np.zeros((ne, 2), dtype=int)

        drota_1mm = drota / 1000.0
        deg2arc = np.arccos(-1.0) / 180.0
        scaleinitial = 1.0
        n1c0 = 0
        ie = -1
        ifiber0 = 0

        # 日志文件（可选）
        # file_dof = os.path.join(pathin, 'user-1-yarn-const.dat')
        # file_rotation = open(f"{data/yarn}/log_InitialYarnRotation.dat", "w")
        # file_rotation.write(f"单位长度的旋转角度（度/mm）= {drota_1mm:.2f}\n")

        # 如果给定了 index，则只处理该 yarn_id，否则处理所有
        if index is None:
            yarn_indices = range(nyarn)
        else:
            # 找出对应 yarn_id 的下标
            idx0 = None
            for ii, y in enumerate(self.yarns):
                if y.yarn_id == index:
                    idx0 = ii
                    break
            if idx0 is None:
                raise ValueError(f"找不到 ID={index} 的纱线")
            yarn_indices = [idx0]

        total_ifiber = 0
        total_nodes = 0
        total_elems = 0

        # Step 1.2: 计算纤维单元信息，每根纤维的节点编号
        for iyarn in yarn_indices:
            # 获取当前纱线的节点数量和节点索引
            nx, ny = NX_NY[iyarn, :]
            n1, n2 = KP_OF_YARN[iyarn, :] - 1  # 调整为从0开始的索引

            # 计算纤维2方向
            e2_ref = np.zeros(3)
            dx = np.max(COORDKP[n1:n2 + 1, 0]) - np.min(COORDKP[n1:n2 + 1, 0])  # x方向长度
            dy = np.max(COORDKP[n1:n2 + 1, 1]) - np.min(COORDKP[n1:n2 + 1, 1])  # y方向长度
            dz = np.max(COORDKP[n1:n2 + 1, 2]) - np.min(COORDKP[n1:n2 + 1, 2])  # z方向长度
            d_xyz = np.array([dx, dy, dz])  # 纤维轮廓在三个方向的长度
            id2 = np.argmin(d_xyz)  # 选择最短的方向作为纤维的第二方向
            if id2 == 0:
                e2_ref[0] = 1.0  # x方向
            elif id2 == 1:
                e2_ref[1] = 1.0  # y方向
            else:
                e2_ref[2] = 1.0  # z方向

            nodewi = n2 - n1 + 1  # 节点数
            rfiyarn = np.sqrt(SIZE_YARN[iyarn] / nx / ny) * r1k  # 计算纱线半径
            SIZE_YARN[iyarn] = rfiyarn  # 更新纱线大小为纤维半径

            # 遍历每个节点，计算节点的旋转和坐标
            for ik in range(nodewi):
                ik0 = n1 + ik
                if ik == 0:
                    e1 = COORDKP[ik0 + 1, :] - COORDKP[ik0, :]  # 第一根纤维方向e1
                else:
                    e1 = COORDKP[ik0, :] - COORDKP[ik0 - 1, :]  # 后续纤维方向e1

                sab = np.sqrt(np.dot(e1, e1))  # 当前点的弧长（单位：mm）
                if sab < 1.0e-5:
                    print(f"error, unit length is 0, iyarn, ik, ik0 = {iyarn}, {ik}, {ik0}")
                    #file_rotation.write(f"Unit length is 0, returning, iyarn, ik, ik0 = {iyarn}, {ik}, {ik0}\n")
                    return

                # 计算局部坐标系
                e_z = np.cross(e1, e2_ref)  # 计算e1和e2的叉积，得到z方向
                e_y = np.cross(e_z, e1)  # 计算e_z和e1的叉积，得到y方向
                s2 = np.sqrt(np.dot(e_y, e_y))  # 叉积的长度
                e3, flagerr1 = self.unitvector(e_z)  # 归一化e_z
                e2, flagerr2 = self.unitvector(e_y)  # 归一化e_y
                if flagerr1 == 1 or flagerr2 == 1:
                    print('error, flagerr1 = 1 or flagerr2 = 1')
                    return

                # 计算节点的旋转角度
                if ik == 0:
                    s0 = 0.0  # 初始弧长为0
                else:
                    s0 += sab  # 累加弧长
                thetai = s0 * drota_1mm * deg2arc  # 计算当前节点的旋转角度（单位：弧度）
                e_y = np.cos(thetai) * e2 + np.sin(thetai) * e3  # 旋转后的y方向
                e_z = -np.sin(thetai) * e2 + np.cos(thetai) * e3  # 旋转后的z方向

                # 计算纤维节点的位置
                for j in range(ny):
                    for i in range(nx):
                        ifiber = j * nx + i  # 计算当前纤维索引
                        nicij = n1c0 + ifiber * nodewi + ik  # 计算新的节点索引
                        dx = -0.5 * (nx - 1) * 2 * rfiyarn + 2 * rfiyarn * i + 0.1 * rfiyarn * j
                        dy = -0.5 * (ny - 1) * 2 * rfiyarn + 2 * rfiyarn * j
                        COORDN[nicij, :] = COORDKP[ik0, :] + scaleinitial * (dx * e_y + dy * e_z)  # 更新节点坐标

            # 记录每根纱线的统计信息
            #file_rotation.write(f"Yarn {iyarn}, total length(mm) = {s0:.1f}, twist angle = {s0 * drota_1mm:.1f}(°)\n")

            n1c = n1c0 + 1
            for j in range(ny):
                for i in range(nx):
                    ifiber = ifiber0 + j * nx + i  # 计算纤维的索引
                    n2c = n1c + nodewi - 1  # 计算当前纤维的最后一个节点
                    NODE_ON_FIBER[ifiber, :] = [n1c, n2c]  # 设置纤维的节点索引
                    SIZE_FIBER[ifiber] = rfiyarn  # 设置纤维半径

                    for ii in range(nodewi - 1):
                        ie += 1
                        ELEMFIBER[ie] = n1c + ii  # 设置单元的节点
                        ELEMATTR[ie, 0] = iyarn  # 设置纱线编号
                        ELEMATTR[ie, 1] = ifiber  # 设置纤维编号

                    n1c = n2c + 1

            IFIBER_OF_YARN[iyarn, 0] = ifiber0 + 1  # 记录当前纱线的第一根纤维索引
            IFIBER_OF_YARN[iyarn, 1] = ifiber0 + nx * ny  # 记录当前纱线的最后一根纤维索引
            n1c0 = n2c
            ifiber0 += nx * ny

        # 输出纤维统计信息
        nfiberw = ifiber
        print(f"Total number of fibers: {nfiberw}")
        print(f"Total number of fibers: {nfiber}")

        # 返回相关数据
        return IFIBER_OF_YARN, SIZE_FIBER, COORDN, NODE_ON_FIBER, ELEMFIBER, ELEMATTR

    def sub_step1_2_copyfiber_new(self, index=None):
        NX_NY = self.NX_NY
        SIZE_YARN = self.SIZE_YARN
        KP_OF_YARN = self.KP_OF_YARN
        COORDKP = self.COORDKP
        r1k = self.r1k
        drota = self.drota

        nyarn = len(self.yarns)
        # 先计算 nfiber, nn, ne
        nfiber = int(np.sum(NX_NY[:, 0] * NX_NY[:, 1]))
        nn = 0
        for iy in range(nyarn):
            n1, n2 = KP_OF_YARN[iy] - 1
            nodewi = (n2 - n1 + 1)
            nx, ny = NX_NY[iy]
            nn += nx * ny * nodewi
        ne = nn - nfiber

        COORDN = np.zeros((nn, 3))
        SIZE_FIBER = np.zeros(nfiber)
        NODE_ON_FIBER = np.zeros((nfiber, 2), dtype=int)
        IFIBER_OF_YARN = np.zeros((nyarn, 2), dtype=int)
        ELEMFIBER = np.zeros(ne, dtype=int)
        ELEMATTR = np.zeros((ne, 2), dtype=int)

        drota_1mm = drota / 1000.0
        deg2arc = np.arccos(-1.0) / 180.0
        scaleinitial = 1.0
        n1c0 = 0
        ie = -1
        ifiber0 = 0

        # 先根据 index 决定到底处理哪些 yarn
        if index is None:
            yarn_indices = range(nyarn)
        else:
            idx0 = None
            for ii, y in enumerate(self.yarns):
                if y.yarn_id == index:
                    idx0 = ii
                    break
            if idx0 is None:
                raise ValueError(f"找不到 ID={index} 的纱线")
            yarn_indices = [idx0]

        total_ifiber = 0
        total_nodes = 0
        total_elems = 0

        # --------- 关键改动：循环改成 yarn_indices，而不是 range(nyarn) ---------
        for iyarn in yarn_indices:
            nx, ny = NX_NY[iyarn, :]
            n1, n2 = KP_OF_YARN[iyarn, :] - 1
            nodewi = (n2 - n1 + 1)
            rfiyarn = np.sqrt(SIZE_YARN[iyarn] / nx / ny) * r1k
            SIZE_YARN[iyarn] = rfiyarn

            # … 剩下逻辑保持不变，只处理这一根纱线 …
            s0 = 0.0
            for ik in range(nodewi):
                ik0 = n1 + ik
                if ik == 0:
                    e1 = COORDKP[ik0 + 1] - COORDKP[ik0]
                else:
                    e1 = COORDKP[ik0] - COORDKP[ik0 - 1]
                sab = np.linalg.norm(e1)
                if sab < 1e-5:
                    print(f"error: 单位长度为 0, iyarn={iyarn}, ik={ik}, ik0={ik0}")
                    return
                dx_ = np.max(COORDKP[n1:n2 + 1, 0]) - np.min(COORDKP[n1:n2 + 1, 0])
                dy_ = np.max(COORDKP[n1:n2 + 1, 1]) - np.min(COORDKP[n1:n2 + 1, 1])
                dz_ = np.max(COORDKP[n1:n2 + 1, 2]) - np.min(COORDKP[n1:n2 + 1, 2])
                d_xyz = np.array([dx_, dy_, dz_])
                id2 = np.argmin(d_xyz)
                e2_ref = np.zeros(3)
                e2_ref[id2] = 1.0

                if ik == 0:
                    s0 = 0.0
                else:
                    s0 += sab
                thetai = s0 * drota_1mm * deg2arc

                e_z = np.cross(e1, e2_ref)
                e_y = np.cross(e_z, e1)
                e3, flagerr1 = self.unitvector(e_z)
                e2, flagerr2 = self.unitvector(e_y)
                if flagerr1 == 1 or flagerr2 == 1:
                    print('error: 归一化失败')
                    return

                e_y_rot = np.cos(thetai) * e2 + np.sin(thetai) * e3
                e_z_rot = -np.sin(thetai) * e2 + np.cos(thetai) * e3

                for j in range(ny):
                    for i in range(nx):
                        if index is None:
                            ifiber = ifiber0 + j * nx + i
                        else:
                            ifiber = total_ifiber + j * nx + i
                        nicij = n1c0 + (j * nx + i) * nodewi + ik
                        dx2 = -0.5 * (nx - 1) * 2 * rfiyarn + 2 * rfiyarn * i + 0.1 * rfiyarn * j
                        dy2 = -0.5 * (ny - 1) * 2 * rfiyarn + 2 * rfiyarn * j
                        COORDN[nicij, :] = COORDKP[ik0, :] + scaleinitial * (dx2 * e_y_rot + dy2 * e_z_rot)

            n1c = n1c0 + 1
            for j in range(ny):
                for i in range(nx):
                    if index is None:
                        ifiber = ifiber0 + j * nx + i
                    else:
                        ifiber = total_ifiber + j * nx + i
                    n2c = n1c + nodewi - 1
                    NODE_ON_FIBER[ifiber, :] = [n1c, n2c]
                    SIZE_FIBER[ifiber] = rfiyarn
                    for ii in range(nodewi - 1):
                        ie += 1
                        ELEMFIBER[ie] = n1c + ii
                        ELEMATTR[ie, 0] = iyarn
                        ELEMATTR[ie, 1] = ifiber
                    n1c = n2c + 1

            IFIBER_OF_YARN[iyarn, 0] = ifiber0 + 1
            IFIBER_OF_YARN[iyarn, 1] = ifiber0 + nx * ny
            ifiber0 += nx * ny
            total_ifiber += nx * ny
            total_nodes = n1c0

        return IFIBER_OF_YARN, SIZE_FIBER, COORDN, NODE_ON_FIBER, ELEMFIBER, ELEMATTR

    def unitvector(self, v):
        """将一个3D向量v归一化，返回单位向量及状态标志"""
        result = v * 0.0  # 初始化一个与v同样大小的零向量
        mag = np.sqrt(np.dot(v, v))  # 计算向量v的模长（magnitude）

        # 如果模长小于非常小的阈值，说明是零向量
        if mag < 1.0e-5:
            return (result, 1)  # 错误：零向量，无法归一化
        result[:] = v / mag  # 归一化向量
        return (result, 0)  # 返回单位向量和成功标志


    def generate_fibers_for_yarn(self, parent_yarn_id):
        try:
            IFIBER_OF_YARN, SIZE_FIBER, COORDN, NODE_ON_FIBER, ELEMFIBER, ELEMATTR = \
                self.sub_step1_2_copyfiber(index=parent_yarn_id)
        except ValueError as e:
            print(f"错误：{e}")
            return

        parent_idx = None
        for idx, yarn in enumerate(self.yarns):
            if yarn.yarn_id == parent_yarn_id:
                parent_idx = idx
                break
        if parent_idx is None:
            print(f"找不到 yarn_id={parent_yarn_id} 的 Yarn")
            return
        parent_yarn = self.yarns[parent_idx]

        fiber_start, fiber_end = IFIBER_OF_YARN[parent_idx]
        fiber_start -= 1
        fiber_end -= 1

        for f in range(fiber_start, fiber_end + 1):
            n_start, n_end = NODE_ON_FIBER[f]
            fiber_nodes = COORDN[n_start : n_end + 1, :].tolist()
            fiber_radius = float(SIZE_FIBER[f])

            new_yarn_id = f"{parent_yarn_id}_fiber{f - fiber_start + 1}"

            new_yarn = Yarn(
                yarn_id=new_yarn_id,
                yarn_type=parent_yarn.yarn_type,
                column=parent_yarn.column,
                layer=parent_yarn.layer,
                direction=parent_yarn.direction,
                spec=parent_yarn.spec,
                nodes=fiber_nodes,
                radii=fiber_radius,
                color=parent_yarn.color,
                renderer=self.renderer
            )

            new_yarn.manager = self
            new_yarn.enable_interaction(False)

            new_yarn.add_to_renderer(self.renderer)
            self.yarns.append(new_yarn)

        print(f"成功为 Yarn {parent_yarn_id} 生成了 {fiber_end - fiber_start + 1} 根微观纤维并添加到管理器中。")

    def generate_fiber_matrix_for_one(self, parent_yarn_id):
        parent_idx = None
        for idx, y in enumerate(self.yarns):
            if y.yarn_id == parent_yarn_id:
                parent_idx = idx
                break
        if parent_idx is None:
            print(f"[Error] 找不到 yarn_id={parent_yarn_id}")
            return

        parent_yarn = self.yarns[parent_idx]

        try:
            IFIBER_OF_YARN, SIZE_FIBER, COORDN, NODE_ON_FIBER, ELEMFIBER, ELEMATTR = \
                self.sub_step1_2_copyfiber(index=parent_yarn_id)
        except ValueError as e:
            print(f"[Error] {e}")
            return

        fiber_start_1b, fiber_end_1b = IFIBER_OF_YARN[parent_idx]
        fiber_start = fiber_start_1b - 1
        fiber_end = fiber_end_1b - 1


        new_list = []

        for f in range(fiber_start, fiber_end + 1):
            n_start, n_end = NODE_ON_FIBER[f]
            fiber_nodes = COORDN[n_start:(n_end + 1), :].tolist()
            fiber_radius = float(SIZE_FIBER[f])

            local_index = f - fiber_start + 1
            new_yarn_id = f"{parent_yarn_id}_fiber{local_index}"

            new_yarn = Yarn(
                yarn_id=new_yarn_id,
                yarn_type=parent_yarn.yarn_type,
                column=parent_yarn.column,
                layer=parent_yarn.layer,
                direction=parent_yarn.direction,
                spec=parent_yarn.spec,
                nodes=fiber_nodes,
                radii=fiber_radius,
                color=parent_yarn.color,
                renderer=self.renderer
            )

            new_yarn.manager = self
            new_yarn.add_to_renderer(self.renderer)
            new_yarn.init_interaction(self.interactor)

            new_list.append(new_yarn)

        self.yarns.extend(new_list)

        print(f"Yarn {parent_yarn_id} 已生成 {len(new_list)} 根微观纤维，并重新渲染自身。")

    def translate_(self, id_a, num_x=3, num_y=0):
        a = next((y for y in self.yarns if y.yarn_id == id_a),None)
        dx = 2*a.radii
        dy = 0.15 + a.radii

        for k in range(0, num_x+1):
            for L in range(0, num_y+1):
                if k == 0 and L == 0:
                    continue
                y_a = a._translate_xy(k * dx, L * dy)
                y_a.add_to_renderer(self.renderer)
                y_a.init_interaction(self.interactor)
                y_a.manager = self
                self.yarns.append(y_a)

    def translate_offset(self, id_a, num_x=3, num_y=0):
        a = next((y for y in self.yarns if y.yarn_id == id_a),None)
        dx = 2*a.radii
        dy = 0.15 + a.radii

        orig_pts = a.nodes  # (N,3) 数组
        r = 2*a.radii  # 纱线半径
        gap = 2*a.radii  # 不留额外间隙
        num_copies = 3
        for k in range(1, num_copies + 1):
            y_a = a.translate_along_fiber(orig_pts, radius=r, k=k, gap=gap)
            y_a.add_to_renderer(self.renderer)
            y_a.init_interaction(self.interactor)
            y_a.manager = self
            self.yarns.append(y_a)

    def translate_o(self, id_a, num_x=3, num_y=3, gap_x=0.0, gap_y=0.0):
        a = next((y for y in self.yarns if y.yarn_id == id_a), None)
        if not a:
            return
        a.manager = self
        for k in range(0, int(num_x) ):
            for l in range(0, int(num_y)):
                if k == 0 and l == 0:
                    continue
                new_yarn = a._translate_Z(dx=k, dy=l, gap_x=gap_x, gap_y=gap_y)
                new_yarn.manager = self
                new_yarn.enable_interaction(False)
                # new_yarn.init_interaction(self.interactor)
                new_yarn.add_to_renderer(self.renderer)
                self.yarns.append(new_yarn)

    def splice_yarns(self, id_a, id_b, idx_a=None, idx_b=None):
        a = next((y for y in self.yarns if y.yarn_id == id_a), None)
        b = next((y for y in self.yarns if y.yarn_id == id_b), None)
        if not a or not b:
            return
        a.splice_with_(b, idx_self=idx_a, idx_other=idx_b)
        b.set_visibility(False)
        b.enable_interaction(False)

    def filter(self, yarn_type=None, column=None, layer=None, on=True):
        for y in self.yarns:
            ok = True
            if yarn_type is not None and y.yarn_type != yarn_type: ok = False
            if column is not None and y.column != column: ok = False
            if layer is not None and y.layer != layer: ok = False
            y.set_highlight_color(ok)
            if not on:
                y.enable_interaction(False)

    def operate_on(self, yarn_id, enable_interaction=False):
        for y in self.yarns:
            y.enable_interaction(False)
        target = next((y for y in self.yarns if y.yarn_id == yarn_id), None)
        if target:
            target.enable_interaction(enable_interaction)

    def split_yarn(self, yarn_id, idx):
        orig = next((y for y in self.yarns if y.yarn_id == yarn_id), None)
        if not orig:
            print(f"Yarn {yarn_id} not found")
            return
        y1, y2 = orig.split_at(idx)
        if y1 and y2:
            orig.set_visibility(False)
            orig.enable_interaction(False)
            y1.add_to_renderer(self.renderer)
            y1.init_interaction(self.interactor)
            y1.manager = self
            y2.add_to_renderer(self.renderer)
            y2.init_interaction(self.interactor)
            y2.manager = self
            self.yarns.append(y1)
            self.yarns.append(y2)
            self.yarns.remove(orig)
        else:
            print("Split index out of range or invalid")

    def splice_yarns2(self, id_a, id_b, idx_a, idx_b):

        a = next((y for y in self.yarns if y.yarn_id == id_a), None)
        b = next((y for y in self.yarns if y.yarn_id == id_b), None)
        if not a or not b:
            return
        a.splice_general(b, idx_a, idx_b)
        b.set_visibility(False)
        b.enable_interaction(False)

    def toggle_selection(self, yarn):
        if yarn in self.select_yarn_tuple:
            self.select_yarn_tuple.remove(yarn)
            yarn.highligth(False)
        else:
            self.select_yarn_tuple.append(yarn)
            yarn.highligth(True)

    def toggle_interactive(self, yarn, flag):
        yarn.enable_interaction(flag)
        yarn.add_to_renderer(self.renderer)
        yarn.init_interaction(self.interactor)

    def toggle_selection_pt(self, yarn, idx):
        key = (yarn, idx)
        rep = yarn.handle_widgets[idx].GetRepresentation()
        prop = rep.GetProperty()
        if key in self.selected_points:
            prop.SetColor(1,1,0)
            self.selected_points.remove(key)
        else:
            prop.SetColor(1,0,1)
            self.selected_points.append(key)
        prop.Modified()
        self.window.Render()

    def split_button(self, yid, idx):
        global_pos = QtGui.QCursor.pos()
        menu = QMenu(self.parent_widget)
        act_split = menu.addAction("断开")
        chosen = menu.exec(global_pos)
        if chosen == act_split:
            self.split_yarn(yid, idx)

    def split_button_pj(self, yid, idx, idy):
        global_pos = QtGui.QCursor.pos()
        menu = QMenu(self.parent_widget)
        act_split = menu.addAction("断开")
        chosen = menu.exec(global_pos)
        if chosen == act_split:
            self.split_yarn_PJ(yid, idx,idy)

    def split_yarn_PJ(self, yarn_id, idx1, idx2):
        orig = next((y for y in self.yarns if y.yarn_id == yarn_id), None)
        if not orig:
            return
        y1, y2 = orig.split_at_PJ(idx1, idx2)
        if y1 and y2:
            y1.add_to_renderer(self.renderer)
            y1.init_interaction(self.interactor)
            y2.add_to_renderer(self.renderer)
            y2.init_interaction(self.interactor)
            self.yarns.append(y1)
            self.yarns.append(y2)
        else:
            print("Split index out of range or invalid")

    def start(self):
        style = vtk.vtkInteractorStyleTrackballCamera()

        def on_key_press(obj, evt):
            key = obj.GetKeySym()
            if key.lower() == "h":
                self.hotkey_H = True
                print("on_key_press true")

        def on_key_release(obj, evt):
            key = obj.GetKeySym()
            if key.lower() == "h":
                self.hotkey_H = False
                print("on_key_press False")

        def on_left_click(obj, evt):
            x, y = obj.GetEventPosition()
            if self.picker.Pick(x, y, 0, self.renderer):
                picked_actor = self.picker.GetViewProp()
                for yarn in self.yarns:
                    if yarn.interaction_enabled:
                        continue
                    if yarn.actor is picked_actor:
                        self.toggle_selection(yarn)
                        break
            self.window.Render()

        # def on_right_click(obj, evt):
        #     x, y = obj.GetEventPosition()
        #     if self.picker.Pick(x, y, 0, self.renderer):
        #         pick_pos = np.array(self.picker.GetPickPosition())
        #         for yarn in self.yarns:
        #             for idx, widget in enumerate(yarn.handle_widgets):
        #                 rep = widget.GetRepresentation()
        #                 handle_pos = np.array(rep.GetWorldPosition())
        #                 # print(np.linalg.norm(pick_pos - handle_pos))
        #                 if np.linalg.norm(pick_pos - handle_pos) < 2.0:
        #                     if idx > 0 and idx < len(yarn.nodes) - 1:
        #                         global_pos = QtGui.QCursor.pos()
        #                         menu = QMenu(self.parent_widget)
        #                         act_split = menu.addAction("断开")
        #                         chosen = menu.exec(global_pos)
        #                         if chosen == act_split:
        #                             self.split_yarn(yarn.yarn_id, idx)
        #                     break
        #     self.window.Render()
        # ----------------------------------------------
        # def on_right_click(obj, evt):
        #     x, y = obj.GetEventPosition()
        #     if self.picker.Pick(x, y, 0, self.renderer):
        #         picked_actor = self.picker.GetViewProp()
        #
        #         target_yarn = next((y for y in self.yarns if y.actor is picked_actor), None)
        #         if target_yarn:
        #             print("actor is true")
        #             pick_pos = np.array(self.picker.GetPickPosition())
        #
        #             for idx, widget in enumerate(target_yarn.handle_widgets):
        #                 rep = widget.GetRepresentation()
        #                 handle_pos = np.array(rep.GetWorldPosition())
        #                 # print("当前计算的距离：", np.linalg.norm(pick_pos - handle_pos))
        #                 #if np.linalg.norm(pick_pos - handle_pos) < 2.2:
        #                 if np.linalg.norm(pick_pos - handle_pos) < 0.2:
        #                     print("接近控制点：")
        #                     global_pos = QtGui.QCursor.pos()
        #                     menu = QMenu(self.parent_widget)
        #
        #                     # print("当前的索引值为：", idx)
        #                     # print("len(target_yarn.nodes) - 1：", len(target_yarn.nodes) - 1)
        #                     is_end = idx == 0 or idx == len(target_yarn.nodes) - 1
        #                     #if idx > 1 and idx < len(target_yarn.nodes) - 1:
        #                     #if not is_end:
        #                         # self.split_button(target_yarn.yarn_id, idx)
        #                         # print("当前的索引值为：", idx)
        #                         # act_split = menu.addAction("断开")
        #                         # chosen = menu.exec(global_pos)
        #                         # if chosen == act_split:
        #                         #     self.split_yarn(target_yarn.yarn_id, idx)
        #                         #     print("断开的索引：",idx)
        #                             # y1, y2 = self.split_yarn(target_yarn.yarn_id, idx)
        #                             # if y1 and y2:
        #                             #     # Highlight split points
        #                             #     self.toggle_selection(y1, len(y1.control_pts) - 1)
        #                             #     self.toggle_selection(y2, 0)
        #
        #                     # if idx > 1 and idx < len(target_yarn.nodes) - 1:
        #                     #     self.select_split.add(idx)
        #                     #     # for other in self.yarns:
        #                     #     #     if other is target_yarn:
        #                     #     #         continue
        #                     #     #     for other_idx in [0, len(other.nodes) - 1]:
        #                     #     #         other_pos = np.array(other.nodes[other_idx])
        #                     #     #         if np.linalg.norm(handle_pos - other_pos) < 2.0:
        #                     #     #             # print("other_idx= ",other_idx)
        #                     #     #             if len(merge_targets) == 2:
        #                     #     #                 break
        #                     #     #             merge_targets.append((target_yarn, other_idx))
        #                     #     print("self.select_split: ", self.select_split)
        #                     #     if len(self.select_split) == 2:
        #                     #         self.select_split = list(self.select_split)
        #                     #         print("target_yarn.yarn_id=",target_yarn.yarn_id)
        #                     #         self.split_button_pj(target_yarn.yarn_id,self.select_split[0], self.select_split[1])
        #                     #         self.select_split.clear()
        #                     # *********** ***************
        #                     if idx == 0 or idx == len(target_yarn.nodes) - 1:
        #                         merge_targets = []
        #                         for other in self.yarns:
        #                             if other is target_yarn:
        #                                 continue
        #                             for other_idx in [0, len(other.nodes) - 1]:
        #                                 other_pos = np.array(other.nodes[other_idx])
        #                                 if np.linalg.norm(handle_pos - other_pos) < 0.1:
        #                                     print("other_idx= ",other_idx)
        #                                     if len(merge_targets) == 2:
        #                                         break
        #                                     merge_targets.append((other, other_idx))
        #
        #                         print("merge_targets = ", merge_targets)
        #                         if len(merge_targets) == 2:
        #                             act_merge = menu.addAction("合并")
        #                             chosen = menu.exec(global_pos)
        #                             if chosen == act_merge:
        #                                 other, other_idx = merge_targets[1]
        #                                 idx_self = idx
        #                                 idx_other = other_idx
        #                                 # print("target_yarn.yarn_id=",target_yarn.yarn_id,"\t",
        #                                 #      "other.yarn_id=", other.yarn_id,"\t",
        #                                 #       "idx_self=",idx_self,"\t",
        #                                 #       "idx_other=",idx_other)
        #                                 if other_idx == len(other.nodes) - 1:
        #                                     idx_other = 0
        #                                 self.splice_yarns(other.yarn_id,target_yarn.yarn_id)
        #                                                   #idx_a=idx_self, idx_b=idx_other)
        #                     break
        #     self.window.Render()

        # 第一次测试
        # def on_right_click(obj, evt):
        #     x, y = obj.GetEventPosition()
        #     if self.picker.Pick(x, y, 0, self.renderer):
        #         picked_actor = self.picker.GetViewProp()
        #         target_yarn = next((y for y in self.yarns if y.actor is picked_actor), None)
        #
        #         if target_yarn:
        #             pick_pos = np.array(self.picker.GetPickPosition())
        #
        #             for idx, widget in enumerate(target_yarn.handle_widgets):
        #                 rep = widget.GetRepresentation()
        #                 handle_pos = np.array(rep.GetWorldPosition())
        #
        #                 if np.linalg.norm(pick_pos - handle_pos) < 0.2:
        #                     if idx == 0 or idx == len(target_yarn.nodes) - 1:
        #                         print(f"右键点击了纱线 {target_yarn.yarn_id} 的 {'头部' if idx == 0 else '尾部'} 控制点")
        #
        #                         if not hasattr(self, 'merge_queue'):
        #                             self.merge_queue = []
        #                             # self.id_list = []
        #                         self.merge_queue.append((target_yarn, idx))
        #
        #                         if len(self.merge_queue) == 2:
        #                             yarn1, idx1 = self.merge_queue[0]
        #                             yarn2, idx2 = self.merge_queue[1]
        #
        #                             if yarn1 != yarn2:
        #                                 global_pos = QtGui.QCursor.pos()
        #                                 menu = QMenu(self.parent_widget)
        #                                 act_merge = menu.addAction("合并")
        #                                 chosen = menu.exec(global_pos)
        #
        #                                 if chosen == act_merge:
        #                                     print(f"合并纱线 {yarn1.yarn_id} 和 {yarn2.yarn_id}")
        #                                     self.splice_yarns(yarn1.yarn_id, yarn2.yarn_id,idx_a= idx1,idx_b= idx2,index=idx1)
        #                             else:
        #                                 print("不能合并同一条纱线")
        #
        #                             # 不管有没有合并成功，都清空
        #                             self.merge_queue.clear()
        #                     break
        #     self.window.Render()
        def on_right_click(obj, evt):
            x, y = obj.GetEventPosition()
            if self.picker.Pick(x, y, 0, self.renderer):
                picked_actor = self.picker.GetViewProp()
                target_yarn = next((y for y in self.yarns if y.actor is picked_actor), None)
                if target_yarn:
                    pick_pos = np.array(self.picker.GetPickPosition())

                    for idx, widget in enumerate(target_yarn.handle_widgets):
                        rep = widget.GetRepresentation()
                        handle_pos = np.array(rep.GetWorldPosition())
                        if np.linalg.norm(pick_pos - handle_pos) < 0.2:
                            if idx == 0 or idx == len(target_yarn.nodes) - 1:
                                if not hasattr(self, 'merge_queue'):
                                    self.merge_queue = []
                                self.merge_queue.append((target_yarn, idx))

                                if len(self.merge_queue) == 2:
                                    yarn1, idx1 = self.merge_queue[0]
                                    yarn2, idx2 = self.merge_queue[1]
                                    if yarn1 != yarn2:
                                        global_pos = QtGui.QCursor.pos()
                                        menu = QMenu(self.parent_widget)
                                        act_merge = menu.addAction("合并")
                                        chosen = menu.exec(global_pos)
                                        if chosen == act_merge:
                                            self.splice_yarns2(yarn1.yarn_id, yarn2.yarn_id, idx1, idx2)
                                    self.merge_queue.clear()
                            break
            self.window.Render()

        self.interactor.AddObserver('LeftButtonPressEvent', on_left_click)
        self.interactor.AddObserver('RightButtonPressEvent', on_right_click)
        self.interactor.AddObserver("KeyPressEvent",on_key_press)
        self.interactor.AddObserver("KeyReleaseEvent",on_key_release)
        self.interactor.Start()
