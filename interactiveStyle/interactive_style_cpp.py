from .interactive_style_h import CustomInteractorStyle
from .Tool_Definition import ControlMode, ScalarValue
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QPushButton, QDialog, QLineEdit, QLabel, QGridLayout,QMenu,QInputDialog)
from PyQt6.QtCore import pyqtSignal, QObject,QPoint
from PyQt6 import QtGui
import numpy as np
import math
import vtk



# ---------------------------
# 自定义对话框：显示矩形区域和四个button
# ---------------------------
class CellInfoDialog(QDialog):

    selectionSubmitted = pyqtSignal(list)
    def __init__(self, cell_vertex_ids):
        super().__init__()
        self.cell_vertex_ids = cell_vertex_ids
        # self.polygon = polygon
        # self.default_renderer = renderer
        self.selected_buttons = []
        self.setup_ui()

    def selected_buttons_clear(self):
        self.selected_buttons.clear()
        # self.default_renderer.RemoveActor(self.axes_actor)

    def setup_ui(self):
        self.setWindowTitle("边界顶点所在单元格信息")
        self.setMinimumSize(200, 150)
        layout = QVBoxLayout(self)

        label = QLabel("请选择/确认单元格各顶点的id：")
        layout.addWidget(label)

        grid = QGridLayout()
        #   A   B
        #   D   C
        self.btn_A = QPushButton(str(list(self.cell_vertex_ids.keys())[0]), self)
        self.btn_B = QPushButton(str(list(self.cell_vertex_ids.keys())[1]), self)
        self.btn_C = QPushButton(str(list(self.cell_vertex_ids.keys())[2]), self)
        self.btn_D = QPushButton(str(list(self.cell_vertex_ids.keys())[3]), self)

        self.btn_A.clicked.connect(lambda: self.record_selection(self.btn_A))
        self.btn_B.clicked.connect(lambda: self.record_selection(self.btn_B))
        self.btn_C.clicked.connect(lambda: self.record_selection(self.btn_C))
        self.btn_D.clicked.connect(lambda: self.record_selection(self.btn_D))

        grid.addWidget(self.btn_A, 0, 0)
        grid.addWidget(self.btn_B, 0, 1)
        grid.addWidget(self.btn_D, 1, 0)
        grid.addWidget(self.btn_C, 1, 1)

        layout.addLayout(grid)

        # 添加一个提交按钮（后续接口）
        btn_submit = QPushButton("提交")
        btn_submit.clicked.connect(self.on_submit)
        layout.addWidget(btn_submit)

    def record_selection(self,button):
        #self.selected_buttons.add(button.text())
        if button.text() not in self.selected_buttons:
            self.selected_buttons.append(button.text())
        #print("当前选择顺序：", self.selected_buttons)

    def on_submit(self):
        # 后续提交的处理接口
        # print("提交按钮被点击，单元格顶点ID为：", self.cell_vertex_ids)
        # print("点击：当前选择顺序：", self.selected_buttons)
        self.selectionSubmitted.emit(self.selected_buttons)  # 发出信号
        self.accept()

class InteractorStyle(CustomInteractorStyle):

    def left_button_press_event(self, obj, event):
        click_pos = self.GetInteractor().GetEventPosition()
        ctrl = self.GetInteractor().GetControlKey()
        shift = self.GetInteractor().GetShiftKey()
        alt = self.GetInteractor().GetAltKey()

        if self._debug:
            print(f"鼠标左键按下")

        print("self.view_actor_type = ", self.view_actor_type)

        if ctrl:
            self.OnLeftButtonDown()
            return

        if self.current_dialog:
            self.current_dialog.selected_buttons_clear()
            self.current_dialog.close()
        if self.actor_x or self.actor_y or self.actor_z:
            self.remove_actor()

        if self.cellID_show == 0 and self.text_label:
            self.text_label.clear()
            self.bill_text.clear()

        if self.default_renderer:
            self.GetInteractor().SetPicker(self.picker)
            self.GetInteractor().GetPicker().Pick(click_pos[0], click_pos[1], 0, self.default_renderer)
            path = self.picker.GetPath()
            if path:
                actor = vtk.vtkActor.SafeDownCast(path.GetLastNode().GetViewProp())
                if self.select_control == ControlMode.select_model and self.assembly:
                    self.set_scalar(uv=ScalarValue.red_normalization, flag=ControlMode.select_model)
                    self.default_renderer.GetRenderWindow().Render()
                    return
                if actor:
                    if actor in self.marker_to_cell:
                        cell_vertex_ids = self.marker_to_cell[actor]
                        # 弹出对话框显示单元格顶点信息
                        # self.current_dialog = CellInfoDialog(cell_vertex_ids)
                        # self.current_dialog.setWindowTitle("顶点信息")
                        # self.current_dialog.show()
                    # elif self.view_actor_type == ControlMode.yarn_type:
                    if self.yarn_mgr.yarns:
                        for yarn in self.yarn_mgr.yarns:
                            # if yarn.interaction_enabled:
                            #     continue
                            print("颜色修改：")
                            if yarn.actor is actor:
                                self.yarn_mgr.toggle_selection(yarn)
                                break

                    polygon = self.actor_to_polygon.get(actor, None)
                    pt = self.control_selection(actor, click_pos, self.select_control)
                    if pt:
                        # 点击当前单元网格的形式，确立面的方向
                        # if self.select_control == ControlMode.select_points:
                        #     face_id = pt["selected_face_id"]
                        #     cell_vertex_ids = {}
                        #     for i in range(polygon.GetCell(face_id).GetPointIds().GetNumberOfIds()):
                        #         pt0 = polygon.GetPoints().GetPoint(polygon.GetCell(face_id).GetPointIds().GetId(i))
                        #         # cell_vertex_ids.append(polygon.GetCell(face_id).GetPointIds().GetId(i))
                        #         cell_vertex_ids[polygon.GetCell(face_id).GetPointIds().GetId(i)] = pt0
                        #     self.current_cell_vertex_ids = cell_vertex_ids
                        #     self.current_dialog = CellInfoDialog(cell_vertex_ids)
                        #     self.current_dialog.setWindowTitle("顶点信息")
                        #     self.current_dialog.selectionSubmitted.connect(self.handle_selection_result)
                        #     self.current_dialog.show()
                        self.set_scalar(actor, polygon, pt, ScalarValue.red, self.select_control, ctrl, alt)
                        polygon.Modified()
                        self.click_to_plane()
                    if self.select_control == ControlMode.select_cell:
                        self.update_cell_selection2(actor, click_pos, ctrl)
                    if not ctrl and self.selected_actor and self.selected_actor != actor:
                        pass
                    self.selected_actor = actor
                else:
                    self.center = None
                    self.selected_actor = None
            if self.select_control == ControlMode.select_points or self.select_control == ControlMode.select_face\
                    or self.select_control == ControlMode.select_cell:
                self.dragging = True
                self.region_select.update_region(click_pos, click_pos)
                self.region_select.set_left_click_start(click_pos)
                self.region_select.__VisibilityOn__()
            self.GetInteractor().GetRenderWindow().Render()
        return

    def right_button_press_event(self, obj, event):
        if self.GetInteractor().GetControlKey():
            self.OnRightButtonDown()
            return

        if self._debug:
            print(f"鼠标右键按下")

        click_pos = self.GetInteractor().GetEventPosition()
        # 执行拾取
        self.GetInteractor().SetPicker(self.picker)
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.default_renderer)
        path = self.picker.GetPath()


        if path:
            actor = vtk.vtkActor.SafeDownCast(path.GetLastNode().GetViewProp())
            if self.view_actor_type == ControlMode.yarn_type:
                self.handle_yarn_context_menu(path)

            # if self.view_actor_type == ControlMode.yarn_type:
            #     target_yarn = next((y for y in self.yarn_mgr.yarns if y.actor is actor), None)
            #
            #     if target_yarn:
            #         global_pos = QtGui.QCursor.pos()
            #         menu = QMenu()
            #         act_merge = menu.addAction("阵列")
            #         chosen = menu.exec(global_pos)
            #         if chosen == act_merge:
            #             tmpe_yarn = []
            #             tmpe_yarn.extend(self.yarn_mgr.yarns)
            #             for yarn in tmpe_yarn:
            #                 print("id=",yarn.yarn_id)
            #                 self.yarn_mgr.translate_o(yarn.yarn_id,2,2)
            #
            #     if target_yarn:
            #         pick_pos = np.array(self.picker.GetPickPosition())
            #         for idx, widget in enumerate(target_yarn.handle_widgets):
            #             rep = widget.GetRepresentation()
            #             handle_pos = np.array(rep.GetWorldPosition())
            #             print("距离：",np.linalg.norm(pick_pos - handle_pos))
            #             if np.linalg.norm(pick_pos - handle_pos) < 0.2:
            #                 if idx == 0 or idx == len(target_yarn.nodes) - 1:
            #                     if not hasattr(self, 'merge_queue'):
            #                         self.merge_queue = []
            #                     self.merge_queue.append((target_yarn, idx))
            #                     print("self.merge_queue=", self.merge_queue)
            #                     if len(self.merge_queue) == 2:
            #                         yarn1, idx1 = self.merge_queue[0]
            #                         yarn2, idx2 = self.merge_queue[1]
            #                         if yarn1 != yarn2:
            #                             global_pos = QtGui.QCursor.pos()
            #                             menu = QMenu()
            #                             act_merge = menu.addAction("合并")
            #                             chosen = menu.exec(global_pos)
            #                             if chosen == act_merge:
            #                                 self.yarn_mgr.splice_yarns2(yarn1.yarn_id, yarn2.yarn_id, idx1, idx2)
            #                         self.merge_queue.clear()
            #                 break
            #     target_yarn = next((y for y in self.yarn_mgr.yarns if y.actor is actor), None)
            #     if target_yarn:
            #         print("actor is true")
            #         pick_pos = np.array(self.picker.GetPickPosition())
            #         for idx, widget in enumerate(target_yarn.handle_widgets):
            #             rep = widget.GetRepresentation()
            #             handle_pos = np.array(rep.GetWorldPosition())
            #             #if np.linalg.norm(pick_pos - handle_pos) < 2.2:
            #             if np.linalg.norm(pick_pos - handle_pos) < 0.2:
            #                 print("接近控制点：")
            #                 if idx > 1 and idx < len(target_yarn.nodes) - 1:
            #                     self.yarn_mgr.split_button(target_yarn.yarn_id, idx)
            #                     # self.yarn_mgr.split_yarn(target_yarn.yarn_id, idx)
            #     return
            if (actor and self.select_control == ControlMode.select_model and self.assembly) or self.select_control == ControlMode.default_type:
                global_pos = QtGui.QCursor.pos()
                menu = QMenu()
                act_center = menu.addAction("居中")
                act_set_pivot = menu.addAction("设置旋转中心")
                act_split = ...;act_copy=...
                # if self.view_actor_type == ControlMode.yarn_type:
                #     #act_split = menu.addAction("断开")
                #     # act_splice = menu.addAction("合并")
                #     act_copy = menu.addAction("阵列")
                chosen = menu.exec(global_pos)
                cam = self.default_renderer.GetActiveCamera()

                if chosen == act_center:
                    self.default_renderer.ResetCamera()
                    self.default_renderer.ResetCameraClippingRange()
                    self.GetInteractor().GetRenderWindow().Render()

                elif chosen == act_set_pivot:
                    pick_pt = self.picker.GetPickPosition()
                    old_fp = cam.GetFocalPoint()
                    old_pos = cam.GetPosition()
                    vec = [old_pos[i] - old_fp[i] for i in range(3)]
                    new_pos = [pick_pt[i] + vec[i] for i in range(3)]

                    cam.SetFocalPoint(*pick_pt)
                    cam.SetPosition(*new_pos)
                    self.default_renderer.ResetCameraClippingRange()
                    self.GetInteractor().GetRenderWindow().Render()
                elif chosen == act_copy:
                    pass
                return

        interactor = self.GetInteractor()
        self.box_selecting = True
        self.region_select.update_region(click_pos, click_pos)
        self.region_select.set_right_click_start(click_pos)
        self.region_select.__VisibilityOn__()
        self.start_pos = interactor.GetEventPosition()
        self.OnRightButtonDown()
        return

    def middle_button_press_event(self, obj, event, key=False):
        interactor = self.GetInteractor()
        ctrl = interactor.GetControlKey()
        self.StartPos = interactor.GetEventPosition()
        if self.view_actor_type == ControlMode.inp_type:
            if self.selected_actor is not None and self.select_control == ControlMode.select_cell:
                if ctrl:
                    x, y = self.StartPos[0], self.StartPos[1]
                    render = self.default_renderer
                    render.SetDisplayPoint(x,y,0)
                    render.DisplayToWorld()
                    worldPt = render.GetWorldPoint()
                    w = worldPt[3] if worldPt[3] != 0 else 1.0
                    self.StartWorld = [worldPt[0] / w, worldPt[1] / w, worldPt[2] / w]
                    self.ActorInitialPosition = self.selected_actor.GetPosition()
                else:
                    pass
                self.MiddleButtonDown = True
                self.default_renderer.GetRenderWindow().Render()
                return
            if ctrl:
                self.default_renderer.GetRenderWindow().Render()
                self.OnMiddleButtonDown()
            else:
                self.dragging = True
                self.default_renderer.GetRenderWindow().Render()
            return
        elif self.view_actor_type == ControlMode.node_type:
            self.select_finish()
            if self.selected_actor is not None and self.select_control == ControlMode.select_cell:
                if ctrl:
                    x, y = self.StartPos[0], self.StartPos[1]
                    render = self.default_renderer
                    render.SetDisplayPoint(x,y,0)
                    render.DisplayToWorld()
                    worldPt = render.GetWorldPoint()
                    w = worldPt[3] if worldPt[3] != 0 else 1.0
                    self.StartWorld = [worldPt[0] / w, worldPt[1] / w, worldPt[2] / w]
                    self.ActorInitialPosition = self.selected_actor.GetPosition()
                else:
                    pass
                self.MiddleButtonDown = True
                self.default_renderer.GetRenderWindow().Render()
                return
            if key:
                return
            if ctrl:
                self.default_renderer.GetRenderWindow().Render()
                self.OnMiddleButtonDown()
            else:
                self.dragging = True
                self.default_renderer.GetRenderWindow().Render()
            return

    def mouse_move_event(self, obj, event):
        if self.GetInteractor().GetControlKey():
            self.OnMouseMove()
            return
        if self.dragging and self.region_select.left_click_start is not None and self.selected_actor:
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            self.region_select.update_region(self.region_select.left_click_start, pos)
            self.GetInteractor().Render()
            self.default_renderer.GetRenderWindow().Render()
        elif self.box_selecting and self.region_select.right_click_start is not None:
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            self.region_select.update_region(self.region_select.right_click_start, pos)
            self.GetInteractor().Render()
            self.default_renderer.GetRenderWindow().Render()

        if self.MiddleButtonDown and self.selected_actor is not None and \
                self.select_control == ControlMode.select_cell:
            interactor = self.GetInteractor()
            currPos = interactor.GetEventPosition()
            if interactor.GetControlKey():
                x, y = currPos[0], currPos[1]
                renderer = self.default_renderer
                renderer.SetDisplayPoint(x, y, 0)
                renderer.DisplayToWorld()
                worldPt = renderer.GetWorldPoint()
                w = worldPt[3] if worldPt[3] != 0 else 1.0
                currWorld = [worldPt[0] / w, worldPt[1] / w, worldPt[2] / w]
                delta = [currWorld[i] - self.StartWorld[i] for i in range(3)]

                polygon = self.selected_actor.GetMapper().GetInput()
                points_vtk = polygon.GetPoints()
                if polygon is not None:
                    unique_point_ids = set()
                    for cell_id in self.polyhedron_cell_ids:
                        cell = polygon.GetCell(cell_id)
                        npts = cell.GetNumberOfPoints()
                        for j in range(npts):
                            pid = cell.GetPointId(j)
                            unique_point_ids.add(pid)
                    for pid in self.unique_point_ids:
                        pt = list(points_vtk.GetPoint(pid))
                        new_pt = [pt[i] + delta[i] for i in range(3)]
                        points_vtk.SetPoint(pid, new_pt)
                    points_vtk.Modified()
                    polygon.Modified()

                    mapper = self.selected_actor.GetMapper()
                    mapper.SetInputData(polygon)
                    mapper.Update()
                    parts = vtk.vtkPropCollection()
                    self.assembly.GetParts()
                    parts.InitTraversal()
                    for i in range(parts.GetNumberOfItems()):
                        actor = parts.GetNextProp()
                        if actor is not None:
                            actor.Modified()
                            if actor.GetMapper():
                                actor.GetMapper().Modified()
                    self.assembly.Modified()
                    self.GetInteractor().GetRenderWindow().Render()
            else:
                dx = currPos[0] - self.StartPos[0]
                dy = currPos[1] - self.StartPos[1]
                angleY = dx * 0.5
                angleX = dy * 0.5

                polygon = self.actor_to_polygon.get(self.selected_actor, None)
                if self.selected_actor.GetMapper().GetInput() is not None:
                    center = self.center
                    transform = vtk.vtkTransform()
                    transform.PostMultiply()
                    transform.Translate([-c for c in center])
                    transform.RotateY(angleY)
                    transform.RotateX(angleX)
                    transform.Translate(center)

                    unique_point_ids = set()
                    for cell_id in self.polyhedron_cell_ids:
                        cell = self.selected_actor.GetMapper().GetInput().GetCell(cell_id)
                        npts = cell.GetNumberOfPoints()
                        for j in range(npts):
                            pid = cell.GetPointId(j)
                            unique_point_ids.add(pid)

                    polydata = self.selected_actor.GetMapper().GetInput()
                    points_vtk = polydata.GetPoints()
                    for pid in self.unique_point_ids:
                        pt = list(points_vtk.GetPoint(pid))
                        new_pt = transform.TransformPoint(pt)
                        points_vtk.SetPoint(pid, new_pt)
                    points_vtk.Modified()
                    polydata.Modified()

                    mapper = self.selected_actor.GetMapper()
                    mapper.SetInputData(polydata)
                    mapper.Update()

                    parts = vtk.vtkPropCollection()
                    self.assembly.GetParts()
                    parts.InitTraversal()
                    for i in range(parts.GetNumberOfItems()):
                        actor = parts.GetNextProp()
                        if actor is not None:
                            actor.Modified()
                            if actor.GetMapper():
                                actor.GetMapper().Modified()
                    self.assembly.Modified()

                    self.GetInteractor().GetRenderWindow().Render()

            self.StartPos = currPos
            self.default_renderer.GetRenderWindow().Render()
            interactor.GetRenderWindow().Render()

        self.OnMouseMove()
        # print("执行：self.OnMouseMove()")
        return

    def left_button_release_event(self, obj, event):
        ctrl = self.GetInteractor().GetControlKey()
        if ctrl:
            self.dragging = False
            self.region_select.__VisibilityOff__()
            self.OnLeftButtonUp()
            return

        if self._debug:
            print(f"鼠标左键抬起")

        if self.region_select.left_click_start is not None and self.selected_actor:
            interactor = self.GetInteractor()
            pos = interactor.GetEventPosition()
            ctrl = self.GetInteractor().GetControlKey()
            self.region_control_selection(self.selected_actor, pos, self.select_control, ctrl)
        self.dragging = False
        self.region_select.__VisibilityOff__()
        self.OnLeftButtonUp()
        self.GetInteractor().GetRenderWindow().Render()
        return

    def right_button_release_event(self, obj, event):

        if self._debug:
            print(f"鼠标右键抬起")

        interactor = self.GetInteractor()
        if self.box_selecting and self.start_pos:
            end_pos = interactor.GetEventPosition()
            dx = end_pos[0] - self.start_pos[0]
            dy = end_pos[1] - self.start_pos[1]
            factor = 1.0 + (abs(dx) + abs(dy)) / 300.0
            camera = self.default_renderer.GetActiveCamera()
            if dx > 0 and dy < 0:
                camera.Zoom(factor)
            elif dx < 0 and dy > 0:
                camera.Zoom(1.0 / factor)
            self.default_renderer.GetRenderWindow().Render()

        self.box_selecting = False
        self.region_select.__VisibilityOff__()
        self.start_pos = None
        self.OnRightButtonUp()
        self.GetInteractor().GetRenderWindow().Render()
        return

    def middle_button_release_event(self, obj, event, key=False):
        if key:
            self.OnLeftButtonUp()
        if self.MiddleButtonDown:
            self.MiddleButtonDown = False
        self.dragging = False
        if self.select_control == ControlMode.select_cell:
            pass
        else:
            self.OnMiddleButtonUp()
        self.default_renderer.GetRenderWindow().Render()
        return

    def keyboard_callback(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == "Escape":
            if self.select_control == ControlMode.select_face:
                self.reset_face_selections()
                # print("ESC : reset_face_selections")
            else:
                self.reset_all_selections()
                # print("ESC : reset_all_selections")


    def set_scalar(self, actor=None, data=None, index=None, uv=None, flag=0, multi_select=False, alt_key=False):
        if flag == ControlMode.select_face:
            key = self.GetInteractor().GetKeySym()
            self.click_id = index
            if key == "Alt_L":
                locator = vtk.vtkPointLocator()
                locator.SetDataSet(data)
                locator.BuildLocator()

                bounds = [0] * 6
                data.GetBounds(bounds)
                diag = math.sqrt(sum((bounds[i * 2 + 1] - bounds[i * 2]) ** 2 for i in range(3)))
                diag = diag * 1e-3

                hit_pids = set()
                id_list = vtk.vtkIdList()
                for i in range(self.boundary_points.GetNumberOfPoints()):
                    pt = self.boundary_points.GetPoints().GetPoint(i)
                    locator.FindPointsWithinRadius(diag, pt, id_list)
                    for i in range(id_list.GetNumberOfIds()):
                        hit_pids.add(id_list.GetId(i))

                cell_to_color = set()
                for pid in hit_pids:
                    cell_ids = vtk.vtkIdList()
                    data.GetPointCells(pid, cell_ids)
                    for j in range(cell_ids.GetNumberOfIds()):
                        cell_one = data.GetCell(cell_ids.GetId(j))
                        on_surface = True
                        for i in range(cell_one.GetNumberOfPoints()):
                            pid = cell_one.GetPointId(i)
                            if pid not in hit_pids:
                                on_surface = False
                                break
                        if on_surface:
                            cell_to_color.add(cell_ids.GetId(j))

                scalars = data.GetCellData().GetScalars()
                for cid in range(data.GetNumberOfCells()):
                    if cid in cell_to_color:
                        scalars.SetTuple3(cid, *uv)

                data.GetCellData().SetScalars(scalars)
                self.selected_point_indices[actor] = cell_to_color
                self.cell_shell = cell_to_color
                self.build_boundary_shell(data, cell_to_color)
            else:
                if data.GetCell(index) is None:
                    return
                if self.cellID_show == ControlMode.cellID_show:
                    self.bill_text.clear()
                cell_scalars = data.GetCellData().GetScalars()

                cell_scalars.SetTuple3(index, *uv)

                self.update_face_selection(actor, multi_select)

                self.selected_point_indices[actor].add(index)
                if self.cellID_show == ControlMode.cellID_show:
                    self.visualize_label()
        elif flag == ControlMode.select_points:
            selected_point = index["selected_point"]
            face_id = index["selected_face_id"]
            cell = data.GetCell(face_id)
            min_distance = float('inf')
            closest_pid = None
            for i in range(cell.GetNumberOfPoints()):
                pid = cell.GetPointId(i)
                pt = data.GetPoints().GetPoint(pid)
                distance = math.sqrt((pt[0] - selected_point[0]) ** 2 +
                                     (pt[1] - selected_point[1]) ** 2 +
                                     (pt[2] - selected_point[2]) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_pid = pid
            if closest_pid is not None:
                data.GetPointData().GetScalars().SetTuple3(closest_pid, *uv)
                self.click_point.append(data.GetPoints().GetPoint(closest_pid))
            self.update_face_selection(actor, multi_select)
            self.selected_point_indices[actor].add(closest_pid)
        elif flag == ControlMode.select_model:
            actors = vtk.vtkPropCollection()
            self.assembly.GetActors(actors)
            actors.InitTraversal()
            actor = actors.GetNextProp()
            while actor:
                actor.GetProperty().SetColor(uv[0], uv[1], uv[2])
                actor = actors.GetNextProp()

    def control_selection(self, _arg1, _arg2, flag=0):
        polygon = self.actor_to_polygon.get(_arg1, None)
        if polygon is None:
            return None

        obb = vtk.vtkOBBTree()
        obb.SetDataSet(polygon)
        obb.BuildLocator()

        renderer = self.default_renderer
        renderer.SetDisplayPoint(_arg2[0], _arg2[1], 0)
        renderer.DisplayToWorld()
        point_1 = renderer.GetWorldPoint()[:3]

        renderer.SetDisplayPoint(_arg2[0], _arg2[1], 1)
        renderer.DisplayToWorld()
        point_2 = renderer.GetWorldPoint()[:3]

        if flag == ControlMode.select_points:
            points = vtk.vtkPoints()
            idlist = vtk.vtkIdList()
            if obb.IntersectWithLine(point_1, point_2, points, idlist):
                if points.GetNumberOfPoints() > 0 and idlist.GetNumberOfIds() > 0:
                    selected_point = points.GetPoint(0)
                    selected_face_id = idlist.GetId(0)
                    return {"selected_point": selected_point, "selected_face_id": selected_face_id}
            return None
        elif flag == ControlMode.select_face:
            points = vtk.vtkPoints()
            idlist = vtk.vtkIdList()
            if obb.IntersectWithLine(point_1, point_2, points, idlist):
                if idlist.GetNumberOfIds() > 0:
                    return idlist.GetId(0)
            return None
        return None

    def locator_point(self, data, _arg):
        locator = vtk.vtkStaticPointLocator()
        locator.SetDataSet(data)
        locator.BuildLocator()
        return locator.FindClosestPoint(_arg)

    def reset_all_selections(self):
        for actor, polydata in self.actor_to_polygon.items():
            if polydata is None:
                continue
            scalars = polydata.GetPointData().GetScalars()
            if scalars is None:
                continue
            orig_color = self.original_actor_color.get(actor, None)
            numPts = polydata.GetNumberOfPoints()
            for i in range(numPts):
                scalars.SetTuple3(i, orig_color[0]*255, orig_color[1]*255, orig_color[2]*255)
            scalars.Modified()
            self.selected_point_indices[actor].clear()
            self.region_point_indices[actor].clear()
        for actor in self.selected_cell_actors:
            pass

        self.selected_cell_actors.clear()
        self.id_list.Reset()
        self.polyhedron_cell_ids.clear()
        self.unique_point_ids.clear()
        self.cell_shell.clear()

        actors = vtk.vtkPropCollection()
        self.assembly.GetActors(actors)
        actors.InitTraversal()
        actor = actors.GetNextProp()
        while actor:
            actor.GetProperty().SetColor(ScalarValue.green_normalization[0],
                                         ScalarValue.green_normalization[1], ScalarValue.green_normalization[2])
            actor.GetMapper().SetScalarModeToUsePointData()
            actor = actors.GetNextProp()

        if self.default_renderer:
            self.default_renderer.GetRenderWindow().Render()

    def reset_face_selections(self):
        for actor, polydata in self.actor_to_polygon.items():
            if polydata is None:
                continue
            cell_scalars = polydata.GetCellData().GetScalars()
            if cell_scalars is None:
                continue
            orig_color = self.original_actor_color.get(actor, None)
            numCells = polydata.GetNumberOfCells()
            for i in range(numCells):
                cell_scalars.SetTuple3(i,
                                       orig_color[0] * 255,
                                       orig_color[1] * 255,
                                       orig_color[2] * 255)
            cell_scalars.Modified()

            self.selected_point_indices[actor].clear()
            self.region_point_indices[actor].clear()

        self.id_list.Reset()
        for actor in self.selected_cell_actors:
            pass
        self.selected_cell_actors.clear()

        actors = vtk.vtkPropCollection()
        self.assembly.GetActors(actors)
        actors.InitTraversal()
        actor = actors.GetNextProp()
        while actor:
            actor.GetProperty().SetColor(ScalarValue.green_normalization[0],
                                         ScalarValue.green_normalization[1],
                                         ScalarValue.green_normalization[2])
            actor.GetMapper().SetScalarModeToUseCellData()
            actor = actors.GetNextProp()

        if self.default_renderer:
            self.default_renderer.GetRenderWindow().Render()

    def update_cell_selection(self, actor, multi_select=False):
        if not multi_select:
            for a in self.selected_cell_actors:
                pass
            self.selected_cell_actors.clear()
        actor.GetProperty().SetEdgeColor(ScalarValue.red_normalization[0],
                                         ScalarValue.red_normalization[1], ScalarValue.red_normalization[2])
        self.selected_cell_actors.add(actor)

    def update_cell_selection2(self, actor, click_pos, multi_select=False):
        polygon = self.actor_to_polygon.get(actor, None)
        if polygon is None:
            return

        cellID = self.control_selection(actor, click_pos, ControlMode.select_face)
        if cellID is None:
            return
        if cellID < 0:
            return

        partArray = polygon.GetCellData().GetArray("PartID")
        selected_part_id = partArray.GetValue(cellID)
        num_cells = polygon.GetNumberOfCells()

        current_polyhedron_cell_ids = []
        for i in range(num_cells):
            if partArray.GetValue(i) == selected_part_id:
                if i not in self.polyhedron_cell_ids:
                    current_polyhedron_cell_ids.append(i)
                    self.polyhedron_cell_ids.append(i)

        for cell_id in current_polyhedron_cell_ids:
            cell = polygon.GetCell(cell_id)
            npts = cell.GetNumberOfPoints()
            for j in range(npts):
                pid = cell.GetPointId(j)
                polygon.GetPointData().GetScalars().SetTuple3(pid, *ScalarValue.red)

        current_unique_point_ids = set()
        for cell_id in current_polyhedron_cell_ids:
            cell = polygon.GetCell(cell_id)
            npts = cell.GetNumberOfPoints()
            for j in range(npts):
                pid = cell.GetPointId(j)
                current_unique_point_ids.add(pid)

        self.unique_point_ids = self.unique_point_ids.union(current_unique_point_ids)

        self.temp_point_box = vtk.vtkPoints()
        for pid in current_unique_point_ids:
            self.temp_point_box.InsertNextPoint(polygon.GetPoints().GetPoint(pid))
        bounds = self.temp_point_box.GetBounds()
        self.center = [
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0
        ]
        self.center_list.append(self.center)

        polygon.Modified()

    def update_face_selection(self, actor, multi_select=False):
        if not multi_select:
            for a in self.selected_cell_actors:
                pass
            self.selected_cell_actors.clear()
        actor.GetProperty().SetEdgeColor(ScalarValue.black[0], ScalarValue.black[1], ScalarValue.black[2])
        # actor.GetProperty().EdgeVisibilityOn()
        self.selected_cell_actors.add(actor)

    def update_point_selection(self, actor, multi_select=False):
        if not multi_select:
            for a in self.selected_cell_actors:
                # a.GetProperty().EdgeVisibilityOff()
                pass
            self.selected_cell_actors.clear()
        actor.GetProperty().SetPointColor(ScalarValue.green[0], ScalarValue.green[1], ScalarValue.green[2])
        actor.GetProperty().PointsVisibilityOn()
        self.selected_cell_actors.add(actor)

    def region_control_selection(self, _arg1, _arg2, flag=0, multi_select=False):
        x0, y0 = self.region_select.left_click_start
        x1, y1 = _arg2
        dx_ = x1 - x0
        dy_ = y1 - y0

        x_min, x_max = sorted([x0, x1])
        y_min, y_max = sorted([y0, y1])
        self._last_box = (x_min, x_max, y_min, y_max)

        for actor in self.actor_to_polygon.keys():
            poly = self.actor_to_polygon.get(actor, None)
            if poly is None:
                continue
            if flag == ControlMode.select_points:
                num_pts = poly.GetNumberOfPoints()
                for i in range(num_pts):
                    xy = self.world_to_display(poly.GetPoint(i))
                    dx, dy = xy[0], xy[1]
                    if x_min <= dx <= x_max and y_min <= dy <= y_max:
                        if dx_ > 0 and dy_ < 0:
                            poly.GetPointData().GetScalars().SetTuple3(i, *ScalarValue.red)
                            self.region_point_indices[actor].add(i)
                        elif dx_ < 0 and dy_ > 0:
                            poly.GetPointData().GetScalars().SetTuple3(i, *ScalarValue.ori_)
                            self.region_point_indices[actor].discard(i)

                poly.Modified()

            elif flag == ControlMode.select_face:
                cell_scalars = poly.GetCellData().GetScalars()
                num_cells = poly.GetNumberOfCells()

                for cid in range(num_cells):
                    cell = poly.GetCell(cid)
                    inside = False
                    for j in range(cell.GetNumberOfPoints()):
                        dx, dy = self.world_to_display(poly.GetPoint(cell.GetPointId(j)))[:2]
                        if x_min <= dx <= x_max and y_min <= dy <= y_max:
                            inside = True
                            break

                    if inside:
                        if dx_ > 0 and dy_ < 0:
                            cell_scalars.SetTuple3(cid, *ScalarValue.red)
                            self.selected_cell_actors.add(actor)
                        elif dx_ < 0 and dy_ > 0:
                            cell_scalars.SetTuple3(cid, *ScalarValue.ori_)
                            self.selected_cell_actors.discard(actor)

                actor.GetProperty().SetEdgeColor(*ScalarValue.black)
                poly.Modified()

            elif flag == ControlMode.select_cell:
                partArray = poly.GetCellData().GetArray("PartID")
                num_cells = poly.GetNumberOfCells()

                for cid in range(num_cells):
                    cell = poly.GetCell(cid)
                    inside = any(
                        (x_min <= self.world_to_display(poly.GetPoint(cell.GetPointId(j)))[0] <= x_max and
                         y_min <= self.world_to_display(poly.GetPoint(cell.GetPointId(j)))[1] <= y_max)
                        for j in range(cell.GetNumberOfPoints())
                    )

                    if inside:
                        pid_part = partArray.GetValue(cid)

                        if dx_ > 0 and dy_ < 0:
                            for k in range(num_cells):
                                if partArray.GetValue(k) == pid_part:
                                    self.polyhedron_cell_ids.append(k)
                                    for j in range(poly.GetCell(k).GetNumberOfPoints()):
                                        pid = poly.GetCell(k).GetPointId(j)
                                        poly.GetPointData().GetScalars().SetTuple3(pid, *ScalarValue.red)
                            pts = {
                                poly.GetCell(k).GetPointId(j)
                                for k in range(num_cells) if partArray.GetValue(k) == pid_part
                                for j in range(poly.GetCell(k).GetNumberOfPoints())
                            }
                            self.unique_point_ids |= pts
                            temp = vtk.vtkPoints()
                            for pid in pts:
                                temp.InsertNextPoint(poly.GetPoints().GetPoint(pid))
                            bounds = temp.GetBounds()
                            center = [
                                (bounds[0] + bounds[1]) / 2.0,
                                (bounds[2] + bounds[3]) / 2.0,
                                (bounds[4] + bounds[5]) / 2.0
                            ]
                            self.center_list.append(center)

                        elif dx_ < 0 and dy_ > 0:
                            for k in range(num_cells):
                                if partArray.GetValue(k) == pid_part:
                                    for j in range(poly.GetCell(k).GetNumberOfPoints()):
                                        pid = poly.GetCell(k).GetPointId(j)
                                        poly.GetPointData().GetScalars().SetTuple3(pid, *ScalarValue.ori_)
                                    if k in self.polyhedron_cell_ids:
                                        self.polyhedron_cell_ids.remove(k)
                            self.unique_point_ids = {
                                pid for pid in self.unique_point_ids
                                if all(partArray.GetValue(cellId) != pid_part
                                       for cellId in range(num_cells)
                                       for pid in [poly.GetCell(cellId).GetPointId(j) for j in
                                                   range(poly.GetCell(cellId).GetNumberOfPoints())])
                            }

                poly.Modified()

    def world_to_display(self, pt):
        import numpy as np
        self.default_renderer.SetWorldPoint(pt[0], pt[1], pt[2], 1.0)
        self.default_renderer.WorldToDisplay()
        display_coord = self.default_renderer.GetDisplayPoint()
        return np.array(display_coord)

    def Rotate(self):
        if not self.GetCurrentRenderer():
            return

        rwi = self.GetInteractor()
        dx = rwi.GetEventPosition()[0] - rwi.GetLastEventPosition()[0]
        dy = rwi.GetEventPosition()[1] - rwi.GetLastEventPosition()[1]

        size = self.GetCurrentRenderer().GetRenderWindow().GetSize()
        delta_elevation = -20.0 / size[1]
        delta_azimuth = -20.0 / size[0]

        rxf = dx * delta_azimuth * self.GetMotionFactor() * self.xMouseMoveFactor
        ryf = dy * delta_elevation * self.GetMotionFactor() * self.yMouseMoveFactor


        if ryf > 90:
            ryf = 80
        elif ryf < -90:
            ryf = -80

        camera = self.GetCurrentRenderer().GetActiveCamera()
        focalPoint = camera.GetFocalPoint()
        viewUp = camera.GetViewUp()
        position = camera.GetPosition()

        viewTransformMat = camera.GetViewTransformMatrix()
        axis = [
            -viewTransformMat.GetElement(0, 0),
            -viewTransformMat.GetElement(0, 1),
            -viewTransformMat.GetElement(0, 2)
        ]

        # 始终根据选中 actor 计算中心
        center = self.assembly.GetCenter()
        transform = vtk.vtkTransform()
        transform.Identity()
        transform.Translate(center[0], center[1], center[2])
        transform.RotateWXYZ(rxf, viewUp)  # 绕 viewUp 方向旋转（水平旋转）
        transform.RotateWXYZ(ryf, axis)  # 绕 axis 方向旋转（垂直旋转）
        transform.Translate(-center[0], -center[1], -center[2])

        newPosition = [0, 0, 0]
        newFocalPoint = [0, 0, 0]
        transform.TransformPoint(position, newPosition)
        transform.TransformPoint(focalPoint, newFocalPoint)
        camera.SetPosition(newPosition)
        camera.SetFocalPoint(newFocalPoint)
        camera.OrthogonalizeViewUp()

        if self.GetAutoAdjustCameraClippingRange():
            self.GetCurrentRenderer().ResetCameraClippingRange()

        if rwi.GetLightFollowCamera():
            self.GetCurrentRenderer().UpdateLightsGeometryToFollowCamera()

        rwi.Render()

    def compute_face_coordinate_system(self, selected_ids, cell_vertex_ids):
        origin = np.array(cell_vertex_ids[int(selected_ids[0])])

        pt1 = np.array(cell_vertex_ids[int(selected_ids[1])])
        x_axis = pt1 - origin
        norm_x = np.linalg.norm(x_axis)
        if norm_x == 0:
            raise ValueError("选中顶点退化，不能构造 x 轴")
        x_axis = x_axis / norm_x

        pt2 = np.array(cell_vertex_ids[int(selected_ids[2])])

        vec1 = pt1 - origin
        vec2 = pt2 - origin
        normal = np.cross(vec1, vec2)
        norm_normal = np.linalg.norm(normal)
        if norm_normal == 0:
            raise ValueError("无法计算面的法向量")
        z_axis = normal / norm_normal

        y_axis = np.cross(z_axis, x_axis)
        norm_y = np.linalg.norm(y_axis)
        if norm_y == 0:
            raise ValueError("无法计算 y 轴")
        y_axis = y_axis / norm_y

        return origin, x_axis, y_axis, z_axis

    def handle_selection_result(self, selected_ids):
        origin, x_axis, y_axis, z_axis = self.compute_face_coordinate_system(selected_ids,
                                                                                 self.current_cell_vertex_ids)

        if self.actor_x or self.actor_y or self.actor_z:
            self.remove_actor()

        self.actor_x = self.axis_show.create_axis_actor(origin, x_axis, color=(1, 0, 0), scale=1.0)  # 红色 X
        self.actor_y = self.axis_show.create_axis_actor(origin, y_axis, color=(0, 1, 0), scale=1.0)  # 绿色 Y
        self.actor_z = self.axis_show.create_axis_actor(origin, z_axis, color=(0, 0, 1), scale=1.0)  # 蓝色 Z

        self.default_renderer.AddActor(self.actor_x)
        self.default_renderer.AddActor(self.actor_y)
        self.default_renderer.AddActor(self.actor_z)

        # 刷新渲染窗口
        self.default_renderer.GetRenderWindow().Render()

        # with open("face_coordinate_system.txt", "w") as f:
        #     f.write("Origin: {}\n".format(origin.tolist()))
        #     f.write("X-axis: {}\n".format(x_axis.tolist()))
        #     f.write("Y-axis: {}\n".format(y_axis.tolist()))
        #     f.write("Z-axis: {}\n".format(z_axis.tolist()))
        # print("当前面的坐标系已保存。")

    def remove_actor(self):
        if self.actor_x:
            self.default_renderer.RemoveActor(self.actor_x)
            self.actor_x = None
        if self.actor_y:
            self.default_renderer.RemoveActor(self.actor_y)
            self.actor_y = None
        if self.actor_z:
            self.default_renderer.RemoveActor(self.actor_z)
            self.actor_z = None
        if self.plane_:
            self.default_renderer.RemoveActor(self.plane_)
            self.plane_ = None

    def create_axis_actor(self, origin, vector, color, scale=1.0):
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(origin.tolist())
        end_point = (origin + vector * scale).tolist()
        lineSource.SetPoint2(end_point)
        lineSource.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetLineWidth(3)
        return actor

    def click_to_plane(self):
        if self.axis_set_type == ControlMode.axis_show:

            if len(self.click_point) == 3:

                selected_ids = self.click_point

                origin = np.array(selected_ids[0])
                pt2 = np.array(selected_ids[1])
                pt3 = np.array(selected_ids[2])

                x_axis = pt2 - origin
                norm_x = np.linalg.norm(x_axis)
                if norm_x < 1e-6:
                    self.click_point.clear()
                else:
                    x_axis = x_axis / norm_x

                    vec = pt3 - origin
                    normal = np.cross(x_axis, vec)
                    norm_normal = np.linalg.norm(normal)
                    if norm_normal < 1e-6:
                        self.click_point.clear()
                    else:
                        z_axis = normal / norm_normal
                        y_axis = np.cross(z_axis, x_axis)
                        norm_y = np.linalg.norm(y_axis)
                        if norm_y < 1e-6:
                            self.click_point.clear()
                        else:
                            y_axis = y_axis / norm_y

                            self.actor_x = self.create_axis_actor(origin, x_axis, color=(1, 0, 0),
                                                                  scale=1.0)
                            self.actor_y = self.create_axis_actor(origin, y_axis, color=(0, 1, 0),
                                                                  scale=1.0)
                            self.actor_z = self.create_axis_actor(origin, z_axis, color=(0, 0, 1),
                                                                  scale=1.0)

                            self.plane_ = self.axis_show.create_plane_actor(origin, x_axis, y_axis)
                            self.default_renderer.AddActor(self.actor_x)
                            self.default_renderer.AddActor(self.actor_y)
                            self.default_renderer.AddActor(self.actor_z)
                            self.default_renderer.AddActor(self.plane_)
                            self.click_point.clear()


    def click_to_face_plane(self, polygon, pt):
        if self.select_control == ControlMode.select_points:
            face_id = pt["selected_face_id"]
            cell_vertex_ids = {}
            for i in range(polygon.GetCell(face_id).GetPointIds().GetNumberOfIds()):
                pt0 = polygon.GetPoints().GetPoint(polygon.GetCell(face_id).GetPointIds().GetId(i))
                # cell_vertex_ids.append(polygon.GetCell(face_id).GetPointIds().GetId(i))
                cell_vertex_ids[polygon.GetCell(face_id).GetPointIds().GetId(i)] = pt0
            self.current_cell_vertex_ids = cell_vertex_ids
            self.current_dialog = CellInfoDialog(cell_vertex_ids)
            self.current_dialog.setWindowTitle("顶点信息")
            # print("进入信号链接")
            self.current_dialog.selectionSubmitted.connect(self.handle_selection_result)
            self.current_dialog.show()

    def build_boundary_shell(self,data,cell_to_color):
        pts = data.GetPoints()
        normalsArr = self.model_normal.GetCellData().GetNormals()
        shellPts = vtk.vtkPoints()
        shellCells = vtk.vtkCellArray()
        origIdArr = vtk.vtkIntArray()
        origIdArr.SetName("OriginalCellId")

        pt_map = {}

        def get_ccw_order(cell_id):
            cell = data.GetCell(cell_id)
            pids = [cell.GetPointId(i) for i in range(cell.GetNumberOfPoints())]
            coords = [pts.GetPoint(pid) for pid in pids]

            N = normalsArr.GetTuple(cell_id)
            cx = sum(x for x, y, z in coords) / len(coords)
            cy = sum(y for x, y, z in coords) / len(coords)
            cz = sum(z for x, y, z in coords) / len(coords)

            def normalize(v):
                l = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
                return (v[0] / l, v[1] / l, v[2] / l)

            e = (coords[1][0] - coords[0][0],
                 coords[1][1] - coords[0][1],
                 coords[1][2] - coords[0][2])
            u = normalize(e)
            v = (N[1] * u[2] - N[2] * u[1],
                 N[2] * u[0] - N[0] * u[2],
                 N[0] * u[1] - N[1] * u[0])

            angles = []
            for pid, (x, y, z) in zip(pids, coords):
                dx, dy, dz = x - cx, y - cy, z - cz
                ux = dx * u[0] + dy * u[1] + dz * u[2]
                vx = dx * v[0] + dy * v[1] + dz * v[2]
                ang = math.atan2(vx, ux)
                angles.append((ang, pid))
            angles.sort()
            return [pid for ang, pid in angles]

        for orig_cid in cell_to_color:
            ccw_pids = get_ccw_order(orig_cid)

            newIds = vtk.vtkIdList()
            for pid in ccw_pids:
                if pid not in pt_map:
                    new_id = shellPts.InsertNextPoint(pts.GetPoint(pid))
                    pt_map[pid] = new_id
                newIds.InsertNextId(pt_map[pid])

            shellCells.InsertNextCell(newIds)
            origIdArr.InsertNextValue(orig_cid)

        shell = vtk.vtkPolyData()
        shell.SetPoints(shellPts)
        shell.SetPolys(shellCells)
        shell.GetCellData().AddArray(origIdArr)

        newCells = vtk.vtkCellArray()
        shellCells.InitTraversal()
        idList = vtk.vtkIdList()
        while shellCells.GetNextCell(idList):
            flipped = vtk.vtkIdList()
            n = idList.GetNumberOfIds()

            for i in range(n - 1, -1, -1):
                flipped.InsertNextId(idList.GetId(i))
            newCells.InsertNextCell(flipped)

        shell.SetPolys(newCells)
        shell.Modified()

        normalsGen = vtk.vtkPolyDataNormals()
        normalsGen.SetInputData(shell)
        normalsGen.ConsistencyOn()
        normalsGen.SplittingOff()
        normalsGen.Update()

        clearn = vtk.vtkCleanPolyData()
        clearn.SetInputData(normalsGen.GetOutput())
        clearn.Update()

        temp_polygon = clearn.GetOutput()
        self.write_NodeData(temp_polygon,"data/NodeData_w.dat")
        self.write_ElementData(temp_polygon,"data/ElementData_w.dat")

        # 静态轮廓方法
        # self.extract_view_silhouette(clearn.GetOutput(),self.default_renderer.GetActiveCamera())

    def visualize_normals(self, scale_factor: float = 0.5):

        if not self.selected_actor:
            return
        polygon = self.selected_actor.GetMapper().GetInput()
        if not polygon:
            return
        if not self.cell_shell:
            locator = vtk.vtkPointLocator()
            locator.SetDataSet(polygon)
            locator.BuildLocator()

            bounds = [0] * 6
            polygon.GetBounds(bounds)
            diag = math.sqrt(sum((bounds[i * 2 + 1] - bounds[i * 2]) ** 2 for i in range(3)))
            diag = diag * 1e-3

            hit_pids = set()
            id_list = vtk.vtkIdList()
            for i in range(self.boundary_points.GetNumberOfPoints()):
                pt = self.boundary_points.GetPoints().GetPoint(i)
                locator.FindPointsWithinRadius(diag, pt, id_list)
                for i in range(id_list.GetNumberOfIds()):
                    hit_pids.add(id_list.GetId(i))

            cell_to_color = set()
            for pid in hit_pids:
                cell_ids = vtk.vtkIdList()
                polygon.GetPointCells(pid, cell_ids)
                for j in range(cell_ids.GetNumberOfIds()):
                    cell_one = polygon.GetCell(cell_ids.GetId(j))
                    on_surface = True
                    for i in range(cell_one.GetNumberOfPoints()):
                        pid = cell_one.GetPointId(i)
                        if pid not in hit_pids:
                            on_surface = False
                            break
                    if on_surface:
                        cell_to_color.add(cell_ids.GetId(j))
            self.cell_shell = cell_to_color
        if self.glyph_actor:
            self.default_renderer.RemoveActor(self.glyph_actor)
            self.glyph_actor = None

        centroids = vtk.vtkPoints()
        normalsArr = self.model_normal.GetCellData().GetNormals()
        normals = vtk.vtkFloatArray()
        normals.SetNumberOfComponents(3)
        normals.SetName("Normals")

        for cid in self.cell_shell:
            cell = polygon.GetCell(cid)
            pts = cell.GetPoints()
            npts = pts.GetNumberOfPoints()
            cx = sum(pts.GetPoint(i)[0] for i in range(npts)) / npts
            cy = sum(pts.GetPoint(i)[1] for i in range(npts)) / npts
            cz = sum(pts.GetPoint(i)[2] for i in range(npts)) / npts
            centroids.InsertNextPoint(cx, cy, cz)
            nx, ny, nz = normalsArr.GetTuple(cid)
            normals.InsertNextTuple([nx, ny, nz])

        centroidPD = vtk.vtkPolyData()
        centroidPD.SetPoints(centroids)
        centroidPD.GetPointData().SetNormals(normals)

        arrow = vtk.vtkArrowSource()
        arrow.Update()
        try:
            glyphMapper = vtk.vtkGlyph3DMapper()
            glyphMapper.SetInputData(centroidPD)
            glyphMapper.SetSourceConnection(arrow.GetOutputPort())
            glyphMapper.SetOrientationArray("Normals")
            glyphMapper.SetOrientationModeToUseVector()
            glyphMapper.SetScaleModeToScaleByVector()
            glyphMapper.SetScaleFactor(scale_factor)
        except AttributeError:
            glyph = vtk.vtkGlyph3D()
            glyph.SetInputData(centroidPD)
            glyph.SetSourceConnection(arrow.GetOutputPort())
            glyph.SetVectorModeToUseNormal()
            glyph.SetScaleModeToScaleByVector()
            glyph.SetScaleFactor(scale_factor)
            glyph.Update()
            glyphMapper = vtk.vtkPolyDataMapper()
            glyphMapper.SetInputConnection(glyph.GetOutputPort())

        pointmapper = vtk.vtkPolyDataMapper()
        pointmapper.SetInputData(centroidPD)

        glyph_actor = vtk.vtkActor()
        # glyph_actor.SetMapper(pointmapper)
        glyph_actor.SetMapper(glyphMapper)
        glyph_actor.GetProperty().SetAmbient(0.5)
        glyph_actor.GetProperty().SetDiffuse(0.5)
        glyph_actor.PickableOff()
        glyph_actor.GetProperty().SetColor(0.0, 1.0, 0.0)
        # self.default_renderer.AddActor(self.glyph_actor)
        # self.default_renderer.GetRenderWindow().Render()
        return glyph_actor

    def visualize_label(self):
        if not self.selected_actor:
            return
        polygon = self.selected_actor.GetMapper().GetInput()
        if not polygon or self.click_id is None:
            return

        cell = polygon.GetCell(self.click_id)
        pts = polygon.GetPoints()

        pts3d = []
        for i in range(cell.GetNumberOfPoints()):
            pid = cell.GetPointId(i)
            pts3d.append(pts.GetPoint(pid))
            self.bill_text.append(pid)

        self.text_label.label_point_ids(pts3d, self.bill_text )
        return

    def extract_view_silhouette(self, poly: vtk.vtkPolyData, cam: vtk.vtkCamera):

        normalsF = vtk.vtkPolyDataNormals()
        normalsF.SetInputData(poly)
        normalsF.ComputeCellNormalsOn()
        normalsF.ComputePointNormalsOff()
        normalsF.SplittingOff()
        normalsF.Update()
        poly_n = normalsF.GetOutput()
        cell_normals = poly_n.GetCellData().GetNormals()

        edge2faces = {}
        for cid in range(poly_n.GetNumberOfCells()):
            cell = poly_n.GetCell(cid)
            ids = [cell.GetPointId(i) for i in range(cell.GetNumberOfPoints())]
            for i in range(len(ids)):
                e = tuple(sorted((ids[i], ids[(i + 1) % len(ids)])))
                edge2faces.setdefault(e, []).append(cid)

        pts = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        pid_map = {}
        for (v1, v2), faces in edge2faces.items():
            if len(faces) != 2:
                continue

            p1 = poly_n.GetPoint(v1)
            p2 = poly_n.GetPoint(v2)
            mid = [(p1[i] + p2[i]) * 0.5 for i in range(3)]
            cam_pos = cam.GetPosition()
            view_vec = [cam_pos[i] - mid[i] for i in range(3)]
            n1 = cell_normals.GetTuple(faces[0])
            n2 = cell_normals.GetTuple(faces[1])
            s1 = sum(n1[i] * view_vec[i] for i in range(3)) >= 0
            s2 = sum(n2[i] * view_vec[i] for i in range(3)) >= 0
            if s1 != s2:
                for v in (v1, v2):
                    if v not in pid_map:
                        pid_map[v] = pts.InsertNextPoint(poly.GetPoint(v))
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, pid_map[v1])
                line.GetPointIds().SetId(1, pid_map[v2])
                lines.InsertNextCell(line)

        out = vtk.vtkPolyData()
        out.SetPoints(pts)
        out.SetLines(lines)

        contour_mapper = vtk.vtkPolyDataMapper()
        contour_mapper.SetInputData(out)

        contour_actor = vtk.vtkActor()
        contour_actor.SetMapper(contour_mapper)
        contour_actor.GetProperty().SetColor(1, 0, 0)
        contour_actor.GetProperty().SetLineWidth(2)
        contour_actor.PickableOff()

    def write_NodeData(self,polydata,output_filename):

        points = polydata.GetPoints()
        npoints = points.GetNumberOfPoints()
        with open(output_filename, 'w') as f:
            for i in range(npoints):
                x, y, z = points.GetPoint(i)
                ux = uy = uz = 0.0
                line = "%d, %.5E, %.5E, %.5E, %.5E, %.5E, %.5E\n" % (
                    i + 1, x, y, z, ux, uy, uz
                )
                f.write(line)
        print(f"Wrote {npoints} nodes to '{output_filename}'")

    def write_ElementData(self,polydata, output_filename):
        n_cells = polydata.GetNumberOfCells()
        eid = 1
        with open(output_filename, 'w') as f:
            for cid in range(n_cells):
                cell = polydata.GetCell(cid)
                if cell.GetCellType() != vtk.VTK_QUAD:
                    continue
                npts = cell.GetNumberOfPoints()
                if npts != 4:
                    continue
                ids = [cell.GetPointId(i) + 1 for i in range(4)]
                line = f"{eid}, " + ", ".join(str(v) for v in ids) + "\n"
                f.write(line)
                eid += 1
        print(f"Wrote {eid - 1} quadrilateral elements to '{output_filename}'")

    def get_build_boundary_shell(self):
        data = self.selected_actor.GetMapper().GetInput()
        locator = vtk.vtkPointLocator()
        locator.SetDataSet(data)
        locator.BuildLocator()

        bounds = [0] * 6
        data.GetBounds(bounds)
        diag = math.sqrt(sum((bounds[i * 2 + 1] - bounds[i * 2]) ** 2 for i in range(3)))
        diag = diag * 1e-3

        hit_pids = set()
        id_list = vtk.vtkIdList()
        for i in range(self.boundary_points.GetNumberOfPoints()):
            pt = self.boundary_points.GetPoints().GetPoint(i)
            locator.FindPointsWithinRadius(diag, pt, id_list)
            for i in range(id_list.GetNumberOfIds()):
                hit_pids.add(id_list.GetId(i))

        cell_to_color = set()
        for pid in hit_pids:
            cell_ids = vtk.vtkIdList()
            data.GetPointCells(pid, cell_ids)
            for j in range(cell_ids.GetNumberOfIds()):
                cell_one = data.GetCell(cell_ids.GetId(j))
                on_surface = True
                for i in range(cell_one.GetNumberOfPoints()):
                    pid = cell_one.GetPointId(i)
                    if pid not in hit_pids:
                        on_surface = False
                        break
                if on_surface:
                    cell_to_color.add(cell_ids.GetId(j))
        scalars = data.GetCellData().GetScalars()
        data.GetCellData().SetScalars(scalars)
        self.build_boundary_shell(data, cell_to_color)

    def handle_yarn_context_menu(self, path):
        if not path:
            return
        actor = vtk.vtkActor.SafeDownCast(path.GetLastNode().GetViewProp())
        if self.view_actor_type != ControlMode.yarn_type or actor is None:
            return
        target_yarn = next((y for y in self.yarn_mgr.yarns if y.actor is actor), None)
        if target_yarn is None:
            return
        pick_pos = np.array(self.picker.GetPickPosition())
        clicked_handle_idx = None
        for idx, widget in enumerate(target_yarn.handle_widgets):
            rep = widget.GetRepresentation()
            handle_pos = np.array(rep.GetWorldPosition())
            dist = np.linalg.norm(pick_pos - handle_pos)
            if dist < 0.2:
                clicked_handle_idx = idx
                break

        menu = QMenu()
        act_array = menu.addAction("阵列")
        show_merge_action = False
        if clicked_handle_idx is not None and (
            clicked_handle_idx == 0 or clicked_handle_idx == len(target_yarn.nodes) - 1
        ):
            if not any((y is target_yarn and i == clicked_handle_idx) for (y, i) in self.merge_queue):
                self.merge_queue.append((target_yarn, clicked_handle_idx))

            if len(self.merge_queue) == 2:
                y1, i1 = self.merge_queue[0]
                y2, i2 = self.merge_queue[1]
                if y1 is not y2:
                    show_merge_action = True

        act_merge = None
        if show_merge_action:
            act_merge = menu.addAction("合并")

        act_split = None
        if clicked_handle_idx is not None and 0 < clicked_handle_idx < len(target_yarn.nodes) - 1:
            act_split = menu.addAction("分裂")

        global_pos = QtGui.QCursor.pos()
        chosen = menu.exec(global_pos)

        if chosen == act_array:
            dx, ok1 = QInputDialog.getDouble(
                None,
                "阵列 - X 偏移",
                "请输入 X 方向平移量：",
                2.0,
                -1e6,
                1e6,
                4
            )
            if not ok1:
                return

            dy, ok2 = QInputDialog.getDouble(
                None,
                "阵列 - Y 偏移",
                "请输入 Y 方向平移量：",
                2.0,
                -1e6,
                1e6,
                4
            )
            if not ok2:
                return

            self.yarn_mgr.translate_o(target_yarn.yarn_id, dx, dy)
            return

        if show_merge_action and chosen == act_merge:
            y1, i1 = self.merge_queue[0]
            y2, i2 = self.merge_queue[1]
            self.yarn_mgr.splice_yarns2(y1.yarn_id, y2.yarn_id, i1, i2)
            self.merge_queue.clear()
            return

        if act_split is not None and chosen == act_split:
            self.yarn_mgr.split_button(target_yarn.yarn_id, clicked_handle_idx)
            return
        return

    def set_yarn_interactive(self, flag):
        if self.yarn_mgr.yarns:
            for yarn in self.yarn_mgr.yarns:
                if yarn.actor is self.selected_actor:
                    self.yarn_mgr.toggle_interactive(yarn,flag)
                    break
            self.default_renderer.GetRenderWindow().Render()

    def set_yarn_show(self,flag):
        if self.yarn_mgr is not None and self.yarn_mgr.yarns is not None:
            for yarn in self.yarn_mgr.yarns:
                if yarn.actor:
                    yarn.actor.SetVisibility(flag)
            self.default_renderer.GetRenderWindow().Render()

    def set_structural_show(self,flag):
        if self.assembly is not None:
            parts = vtk.vtkPropCollection()
            self.assembly.GetParts()
            parts.InitTraversal()
            for i in range(parts.GetNumberOfItems()):
                actor = parts.GetNextProp()
                if actor is not None:
                    actor.SetVisibility(flag)
            self.assembly.SetVisibility(flag)
            self.GetInteractor().GetRenderWindow().Render()

