import vtk
import numpy as np


class Yarn:
    def __init__(self, yarn_id, yarn_type, column, layer, direction, spec, nodes, radii=0.2, color=(1,0,0),
                 renderer=None):
        self.yarn_id = yarn_id
        self.yarn_type = yarn_type
        self.column = column
        self.layer = layer
        self.direction = direction
        self.spec = spec

        self.nodes = nodes

        self.radii = radii
        self.color = color

        self.renderer = None
        self.spline_source = vtk.vtkParametricFunctionSource()
        self.tube_filter = vtk.vtkTubeFilter()
        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        self.handle_widgets = []

        self.visible = True
        self.interaction_enabled = True

        self._setup_pipeline()

    def split_at(self, idx):
        if idx <= 0 or idx >= len(self.nodes) - 1:
            return None, None
        pts1 = self.nodes[:idx].copy()
        pts2 = self.nodes[idx:].copy()

        y1 = Yarn(f"{self.yarn_id}_1", self.yarn_type, self.column, self.layer,
                  self.direction, self.spec, pts1, self.radii, self.color, self.renderer)
        y2 = Yarn(f"{self.yarn_id}_2", self.yarn_type, self.column, self.layer,
                  self.direction, self.spec, pts2, self.radii, self.color, self.renderer)
        return y1, y2

    def _setup_pipeline(self):
        pts = vtk.vtkPoints()
        for p in self.nodes:
            pts.InsertNextPoint(p)

        nni = len(self.nodes)
        line = vtk.vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(nni)
        for j in range(nni):
            line.GetPointIds().SetId(j, j)
        lines = vtk.vtkCellArray()
        lines.InsertNextCell(line)
        spline_poly = vtk.vtkPolyData()
        spline_poly.SetPoints(pts)
        spline_poly.SetLines(lines)

        spline = vtk.vtkParametricSpline()
        spline.SetPoints(pts)
        self.spline_source.SetParametricFunction(spline)
        self.spline_source.SetVResolution(0)
        self.spline_source.SetUResolution(0)
        self.spline_source.Update()
        #self.tube_filter.SetInputConnection(self.spline_source.GetOutputPort())
        self.tube_filter.SetInputData(spline_poly)
        self.tube_filter.SetRadius(self.radii)
        self.tube_filter.SetNumberOfSides(10)
        self.tube_filter.CappingOn()
        self.tube_filter.Update()
        self.mapper.SetInputConnection(self.tube_filter.GetOutputPort())
        # self.mapper.SetInputData(spline_poly)
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(self.color)
        self.actor.SetVisibility(self.visible)

    def add_to_renderer(self, renderer):
        self.renderer = renderer
        renderer.AddActor(self.actor)

    def fit_spline(self):
        if not self.interaction_enabled:
            return
        self._setup_pipeline()
        if self.renderer:
            self.renderer.GetRenderWindow().Render()

    def _translate_x(self,dx):
        pts2 = self.nodes.copy()
        pts2 = np.array(pts2)
        pts2[:, 0] += dx
        y = Yarn(f"{self.yarn_id}_1", self.yarn_type, self.column, self.layer,
                  self.direction, self.spec, pts2, self.radii, self.color, self.renderer)
        return y

    def reverse(self):
        self.nodes = self.nodes[::-1]
        if hasattr(self, 'nodes'):
            self.nodes = self.nodes[::-1]
        self.init_interaction(self.renderer.GetRenderWindow().GetInteractor())
        self.fit_spline()

    def _translate_y(self,dy):
        pts2 = self.nodes.copy()
        pts2 = np.array(pts2)
        pts2[:, 1] += dy
        y = Yarn(f"{self.yarn_id}_1", self.yarn_type, self.column, self.layer,
                 self.direction, self.spec, pts2, self.radii, self.color, self.renderer)
        return y

    def _translate_xy(self, dx, dy):
        pts1 = self.nodes.copy()
        pts1 = np.array(pts1)
        pts1[:, 2] += dx

        pts2 = pts1
        pts2[:, 1] += dy
        y = Yarn(f"{self.yarn_id}_1", self.yarn_type, self.column, self.layer,
                 self.direction, self.spec, pts2, self.radii, self.color, self.renderer)
        return y

    def _translate_Z(self, dx, dy, gap_x=0.0, gap_y=0.0):
        orig_pts = np.array(self.nodes, dtype=float)
        N = orig_pts.shape[0]
        if N < 2:
            new_pts = orig_pts + np.array([dx * (2 * self.radii + gap_x),
                                           dy * (2 * self.radii + gap_y),
                                           0.0])
            return Yarn(f"{self.yarn_id}_copy", self.yarn_type, self.column, self.layer,
                        self.direction, self.spec, new_pts,
                        self.radii, self.color, self.renderer)

        head = orig_pts[0]
        tail = orig_pts[-1]
        vec = tail - head
        norm_vec = np.linalg.norm(vec)
        if norm_vec < 1e-6:
            dir_unit = np.array([1.0, 0.0, 0.0])
        else:
            dir_unit = vec / norm_vec

        if abs(np.dot(dir_unit, np.array([0.0, 0.0, 1.0]))) < 0.99:
            ref = np.array([0.0, 0.0, 1.0])
        else:
            ref = np.array([0.0, 1.0, 0.0])

        local_x = np.cross(ref, dir_unit)
        lx_norm = np.linalg.norm(local_x)
        if lx_norm < 1e-6:
            local_x = np.array([1.0, 0.0, 0.0])
        else:
            local_x = local_x / lx_norm

        local_y = np.cross(dir_unit, local_x)
        ly_norm = np.linalg.norm(local_y)
        if ly_norm < 1e-6:
            local_y = np.array([0.0, 1.0, 0.0])
        else:
            local_y = local_y / ly_norm

        step_x = 2.0 * self.radii + gap_x
        step_y = 2.0 * self.radii + gap_y
        Tx = local_x * (dx * step_x)
        Ty = local_y * (dy * step_y)
        offset = Tx + Ty

        new_pts = orig_pts + offset[np.newaxis, :]

        new_id = f"{self.yarn_id}_x{dx}_y{dy}"
        y = Yarn(
            yarn_id=new_id,
            yarn_type=self.yarn_type,
            column=self.column,
            layer=self.layer,
            direction=self.direction,
            spec=self.spec,
            nodes=new_pts.tolist(),
            radii=self.radii,
            color=self.color,
            renderer=self.renderer
        )
        return y

    def splice_with_(self, other, idx_self=None, idx_other=None):
        if idx_self is None:
            idx_self = len(self.nodes) - 1
        if idx_other is None:
            idx_other = 0
        seg1 = self.nodes[:idx_self + 1]
        seg2 = other.nodes[idx_other + 1:]
        new_pts = np.vstack([seg1, seg2])
        self.nodes = new_pts
        self.init_interaction(self.renderer.GetRenderWindow().GetInteractor())
        self.fit_spline()

    def splice_general(self, other, idx_self, idx_other):
        A = np.array(self.nodes)
        B = np.array(other.nodes)

        lenA = A.shape[0]
        lenB = B.shape[0]

        if lenA < 1 or lenB < 1:
            return

        headA, tailA = 0, lenA - 1
        headB, tailB = 0, lenB - 1

        if idx_self == tailA and idx_other == headB:
            seg1 = A[:tailA + 1]
            seg2 = B[headB + 1:]
            new_nodes = np.vstack([seg1, seg2])

        elif idx_self == headA and idx_other == tailB:
            seg1 = B[:tailB + 1]
            seg2 = A[headA + 1:]
            new_nodes = np.vstack([seg1, seg2])

        elif idx_self == tailA and idx_other == tailB:
            B_rev = B[::-1]
            seg1 = A[:tailA + 1]
            seg2 = B_rev[1:]
            new_nodes = np.vstack([seg1, seg2])

        elif idx_self == headA and idx_other == headB:
            B_rev = B[::-1]
            seg1 = B_rev[:tailB + 1]
            seg2 = A[1:]
            new_nodes = np.vstack([seg1, seg2])
        else:
            seg1 = A[:idx_self + 1]
            seg2 = B[idx_other + 1:]
            new_nodes = np.vstack([seg1, seg2])

        self.nodes = new_nodes

        self.init_interaction(self.renderer.GetRenderWindow().GetInteractor())
        self.fit_spline()

    def init_interaction(self, interactor):
        for w in self.handle_widgets:
            w.EnabledOff()
        self.handle_widgets.clear()

        if not self.interaction_enabled:
            return

        N = len(self.nodes)
        for idx in range(N):
            pt = self.nodes[idx]
            rep = vtk.vtkPointHandleRepresentation3D()
            rep.SetWorldPosition(pt)
            rep.GetProperty().SetColor(1,1,0)
            rep.GetProperty().SetRepresentationToWireframe()
            rep.GetProperty().SetLineWidth(3.0)
            widget = vtk.vtkHandleWidget()
            widget.SetRepresentation(rep)
            widget.SetInteractor(interactor)

            def make_cb(i, r):
                def callback(obj, event):
                    new_pos = [0.0, 0.0, 0.0]
                    r.GetWorldPosition(new_pos)
                    new_pos = np.array(new_pos)
                    old_pos = self.nodes[i].copy()
                    delta = new_pos - old_pos

                    if self.manager.hotkey_H:
                        print("进入H模式")
                        if i == 0 or i == N-1:
                            self._cascade_move_gaussian(i, delta,decay='gaussian')
                        else:
                            self.nodes[i] = new_pos
                    else:
                        self.nodes[i] = new_pos

                    self.fit_spline()
                    if self.manager.hotkey_H:
                        self.manager.window.Render()
                return callback

            widget.AddObserver('InteractionEvent', make_cb(idx, rep))
            widget.EnabledOn()
            self.handle_widgets.append(widget)

    def _cascade_move(self, dragged_idx, delta):
        N = len(self.nodes)
        if dragged_idx == 0:
            for j in range(N):
                w = 1.0 - (j / (N-1))
                self.nodes[j] += delta * w
        else:
            for j in range(N):
                w = 1.0 - ((N-1 - j) / (N-1))
                self.nodes[j] += delta * w


    def set_visibility(self, visible):
        self.visible = visible
        self.actor.SetVisibility(visible)
        if self.renderer:
            self.renderer.GetRenderWindow().Render()

    def set_highlight_color(self, flag):
        if flag:
            self.actor.GetProperty().SetOpacity(0.5)
            if self.renderer:
                self.renderer.GetRenderWindow().Render()

    def enable_interaction(self, enable):
        self.interaction_enabled = enable
        if self.renderer:
            self.init_interaction(self.renderer.GetRenderWindow().GetInteractor())

    def highligth(self, on=True):
        if on:
            self.actor.GetProperty().SetColor(1, 1, 0)
        else:
            self.actor.GetProperty().SetColor(self.color)
        self.actor.GetProperty().Modified()

    def set_nodes(self, nodes):
        self.nodes = nodes
        self._setup_pipeline()
        if self.renderer:
            self.renderer.GetRenderWindow().Render()

    def split_at_PJ(self, idx1, idx2):
        if idx1 <= 0 or idx1 >= len(self.nodes) - 1:
            return None, None
        if idx2 <= 0 or idx2 >= len(self.nodes) - 1:
            return None, None
        start = min(idx1, idx2)
        end = max(idx1, idx2)
        pts1 = self.nodes[:start].copy()
        pts2 = self.nodes[end + 1:].copy()

        y1 = Yarn(f"{self.yarn_id}_1", self.yarn_type, self.column, self.layer,
                  self.direction, self.spec, pts1, self.radii, self.color, self.renderer)
        # y2 = Yarn(f"{self.yarn_id}_2", self.yarn_type, self.column, self.layer,
        #           self.direction, self.spec, pts2, self.radii, self.color, self.renderer)
        self.set_nodes(pts2)
        y2 = self
        return y1, y2

    def _cascade_move_2(self, dragged_idx, delta, power=2):
        N = len(self.nodes)
        if N < 2:
            self.nodes[dragged_idx] += delta
            return

        if dragged_idx == 0:
            for j in range(N):
                t = j / (N - 1)
                w = (1 - t) ** power
                self.nodes[j] += delta * w
        elif dragged_idx == N - 1:
            for j in range(N):
                t = (N - 1 - j) / (N - 1)
                w = (1 - t) ** power
                self.nodes[j] += delta * w
        else:
            self.nodes[dragged_idx] += delta

    def _cascade_move_gaussian(self, dragged_idx, delta, decay='gaussian', power=2):
        N = len(self.nodes)
        if N < 2:
            self.nodes[dragged_idx] += delta
            return

        sigma = (N - 1) / 3.0

        weights = np.zeros(N, dtype=float)

        if decay == 'gaussian':
            if dragged_idx == 0:
                mu = 0.0
            else:
                mu = float(N - 1)
            for j in range(N):
                diff = (j - mu)
                weights[j] = np.exp(- (diff * diff) / (2.0 * sigma * sigma))
            weights /= weights.max()

        elif decay == 'polynomial':
            if dragged_idx == 0:
                for j in range(N):
                    t = j / (N - 1)
                    weights[j] = (1.0 - t) ** power
            else:
                for j in range(N):
                    t = (N - 1 - j) / (N - 1)
                    weights[j] = (1.0 - t) ** power
        else:
            weights = np.zeros(N, dtype=float)
            weights[dragged_idx] = 1.0

        delta_x = np.array([delta[0], 0.0, 0.0])
        delta_y = np.array([0.0, delta[1], 0.0])
        delta_z = np.array([0.0, 0.0, delta[2]])
        for j in range(N):
            self.nodes[j] += delta_y * weights[j]

    def translate_along_fiber(self, orig_pts, radius, k=1, gap=0.0):

        pts = np.array(orig_pts, dtype=float)
        pts = np.array(pts)
        N = pts.shape[0]
        if N < 2:
            return pts.copy()

        head = pts[0]
        tail = pts[-1]
        vec = tail - head
        norm = np.linalg.norm(vec)
        norm2 = np.linalg.norm([1.0,0.0,0.0])
        if norm < 1e-6:
            dir_vec = np.array([1.0, 0.0, 0.0])
        else:
            dir_vec = vec / norm

        base_offset = 2.0 * radius + gap
        offset = dir_vec * (k * base_offset)
        control_pts_new = pts + offset

        y = Yarn(f"{self.yarn_id}_1", self.yarn_type, self.column, self.layer,
                 self.direction, self.spec, control_pts_new, self.radii, self.color, self.renderer)
        return y
