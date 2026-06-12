from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    QPushButton, QDialog, QLineEdit, QLabel, QHBoxLayout, QFileDialog, QScrollArea,
    QInputDialog,QGraphicsView,QGraphicsRectItem,QGraphicsScene,QSizePolicy,
    QGraphicsEllipseItem, QGraphicsTextItem, QFormLayout,QGridLayout,QMessageBox,QTextEdit
)
from ui.main_window import Ui_MainWindow
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow
)
from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLPolyDataMapper
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkCommonTransforms import vtkTransform
import vtk
import os
import sys
import subprocess
sys.path.append("modules")
from modules.FindEnumV1_2.ParamDialog import writeparamforFortran,ParamDialog
import numpy as np
from interactiveStyle.Tool_Definition import ControlMode, mergePolyData
from interactiveStyle.interactive_style_cpp import InteractorStyle
from interactiveStyle.Tool_Definition import read_Nodes, read_Triangles, parse_inp_file
from interactiveStyle.coordinate_axis import Axis
from interactiveStyle.yarn_manager import YarnManager
from interactiveStyle.yarn_property import Yarn

# ---------------------------
# 主窗口
# ---------------------------
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # 搭建基础UI
        self.setupUi(self)
        self.horizontalLayoutWidget.updateGeometry()
        self.vtkwidget.updateGeometry()

        # 构建 vtkUI 及其渲染器、绑定事件设置
        self.vtk_widget = QVTKRenderWindowInteractor(self.vtkwidget)
        self.horizontalLayout_2.addWidget(self.vtk_widget)

        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()

        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        self.assembly = vtk.vtkAssembly()
        self.interactor_style = InteractorStyle()
        self.interactor_style.set_default_renderer(self.renderer)
        self.interactor_style.set_region_renderer()
        self.iren.SetInteractorStyle(self.interactor_style)

        self.axis_actor = vtk.vtkAxesActor()
        self.axis_actor.SetPosition(0, 0, 0)
        self.axis_actor.SetTotalLength(2, 2, 2)
        self.axis_actor.SetShaftType(0)
        self.axis_actor.SetCylinderRadius(0.02)

        self.widget = vtk.vtkOrientationMarkerWidget()
        self.widget.SetOrientationMarker(self.axis_actor)
        self.widget.SetInteractor(self.iren)
        self.widget.SetEnabled(1)
        self.widget.InteractiveOff()

        self.iren.Initialize()
        self.iren.Start()

        # 用于存储选中mesh和边界 marker 对应的单元格信息
        self.marker_to_cell = {}

        self.edge_flag = True
        self.axis_flag = True
        self.normal_flag = True
        self.cellID_flag = True
        self.silhouette_flag = True
        self.yarn_flag = True
        self.yarnview = True
        self.structuralview = True

        self.Position = None
        self.focal_point = None
        self.view_up = None

        self.temp_Position = None
        self.temp_focal_point = None
        self.temp_view_up = None

        self.temp_actor = None
        self.normal_actor = None
        self.label_actor = None


        # 动态绑定 UI 事件
        self.actionImport.triggered.connect(self.open_piece_data)
        self.actionOpen.triggered.connect(self.open_node_data)
        self.yarn_open.triggered.connect(self.open_yarn_data)
        self.zp_btn.clicked.connect(self.flatten)
        self.heatmap_btn.clicked.connect(self.create_heatmap)
        # 创建四个按钮选项的动态链接 add by pxt 20250328
        self.select_points.triggered.connect(self.set_controlmode_points)
        self.select_face.triggered.connect(self.set_controlmode_face)
        self.select_cell.triggered.connect(self.set_controlmode_cell)
        self.select_model.triggered.connect(self.set_controlmode_mode)
        self.zp_btn.clicked.connect(self.flatten)
        self.heatmap_btn.clicked.connect(self.create_heatmap)
        # 创建坐标轴显示
        self.axis_button.triggered.connect(self.set_axis_show)

        # 创建投影方式按钮
        self.perspective_projection.triggered.connect(self.set_perspective_projection)
        self.rectangular_projection.triggered.connect(self.set_rectangular_projection)
        # 创建视图按钮
        self.Front_view.triggered.connect(self.set_front_view)
        self.top_view.triggered.connect(self.set_top_view)
        self.side_view.triggered.connect(self.set_side_view)
        # 自定义视角
        self.set_view.triggered.connect(self.set_view_style)
        self.switchover_view.triggered.connect(self.get_switchover_view)
        self.edge_button.triggered.connect(self.edge_switch)
        self.axis_view.triggered.connect(self.axis_switch)
        self.normal_reversal.triggered.connect(self.reversal_normal)
        # 显示网格ID
        self.show_cellID.triggered.connect(self.show_cellID_switch)
        # 显示轮廓线
        # self.show_silhouette.triggered.connect(self.show_silhouette_switch)
        # 反向选择
        # self.reverse_selection.triggered.connect(self.reverse_selection_switch)
        self.exported_shell.triggered.connect(self.exported_shell_switch)
        self.unit_matching.triggered.connect(self.unit_matching_switch)
        # self.unit_matching.triggered.connect()
        self.yarn_move.triggered.connect(self.yarn_move_switch)
        self.yarn_view.triggered.connect(self.yarn_view_switch)
        self.structural_view.triggered.connect(self.structural_view_switch)

        self.design_btn.clicked.connect(self.adaptiveDesign)
        self.light_btn.clicked.connect(self.thickness)


    def resizeEvent(self, event):
        self.vtk_widget.setGeometry(self.vtkwidget.rect())
        self.horizontalLayoutWidget.setGeometry(self.vtkwidget.rect())
        super().resizeEvent(event)

    def showEvent(self, event):
        self.vtk_widget.setGeometry(self.vtkwidget.rect())
        self.horizontalLayoutWidget.setGeometry(self.vtkwidget.rect())
        super(MainWindow, self).showEvent(event)

    def adaptiveDesign(self):
        self.parameter_input_widget = AdaptiveDesignWidget()
        self.parameter_input_widget.show()
        self.parameter_input_widget.submit_button.clicked.connect(self.open_design_window)

    def open_design_window(self):
        self.design_window = InterDesignWindow()
        self.design_window.show()
        self.parameter_input_widget.close()
        self.close()

    def open_piece_data(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*);;Text Files (*.txt)")
        if len(files) == 1:
            Nodes, ElementSets = parse_inp_file(files[0])
            for i, triangles in enumerate(ElementSets):
                self.create_mesh(Nodes, triangles, color=[0.31, 0.51, 0.9], bounding=False, num=i)
            self.interactor_style.view_actor_file(ControlMode.inp_type)
            self.interactor_style.set_marker_to_cell(self.marker_to_cell)
            self.temp_actor = Axis().show_coordinate_system(self.assembly)
            self.temp_actor.PickableOff()
            self.interactor_style.set_assembly(self.assembly, self.temp_actor)
            # self.interactor_style.locality_axis(self.iren)
            self.renderer.ResetCamera()
            self.set_ori_camera()

    def open_node_data(self):
        # options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*);;Text Files (*.txt)")
        if len(files) == 2:
            self.points, self.uPoints, self.heatmaps = read_Nodes(files[0] if "Node" in files[0] else files[1])
            self.cells = read_Triangles(files[0] if "Element" in files[0] else files[1])

            polydata_list = []
            num_hex = len(self.cells) // 6
            for i in range(num_hex):
                hex_faces = self.cells[i * 6:(i + 1) * 6]
                vertex_indices = set()
                for face in hex_faces:
                    vertex_indices.update(face[1:])
                local_indices = sorted(vertex_indices)
                mapping = {old: new for new, old in enumerate(local_indices)}
                local_points = [self.points[j] for j in local_indices]
                local_faces = []
                for face in hex_faces:
                    local_face = [face[0]] + [mapping[idx] for idx in face[1:]]
                    local_faces.append(local_face)
                polydata_ = self.create_mesh2(local_points, local_faces, color=[0.31, 0.51, 0.9], bounding=False)
                polydata_list.append(polydata_)
            merge_polygon = mergePolyData(polydata_list)

            ids = vtk.vtkIntArray()
            ids.SetName("OriginalIds")
            ids.SetNumberOfComponents(1)
            numc = merge_polygon.GetNumberOfCells()
            ids.SetNumberOfTuples(numc)
            for i in range(numc):
                ids.SetValue(i, i)
            merge_polygon.GetCellData().AddArray(ids)
            if True:
                ugrid = vtk.vtkUnstructuredGrid()
                pts = vtk.vtkPoints()
                for p in self.points:
                    pts.InsertNextPoint(p)
                ugrid.SetPoints(pts)

                ptIdsArr = vtk.vtkIntArray()
                ptIdsArr.SetName("OriginalPointIds")
                ptIdsArr.SetNumberOfComponents(1)
                ptIdsArr.SetNumberOfTuples(len(self.points))
                for i in range(len(self.points)):
                    ptIdsArr.SetValue(i, i)
                ugrid.GetPointData().AddArray(ptIdsArr)

                for hid, hex_verts in enumerate(self.cells):
                    hexCell = vtk.vtkHexahedron()
                    for j, pid in enumerate(hex_verts):
                        hexCell.GetPointIds().SetId(j, pid)
                    ugrid.InsertNextCell(hexCell.GetCellType(), hexCell.GetPointIds())

                surfFilter = vtk.vtkDataSetSurfaceFilter()
                surfFilter.SetInputData(ugrid)
                surfFilter.Update()
                boundaryPoly = surfFilter.GetOutput()

                pts = vtk.vtkPoints()
                for i in range(boundaryPoly.GetNumberOfPoints()):
                    pts.InsertNextPoint(boundaryPoly.GetPoints().GetPoint(i))
                    boundaryPoly.GetPointData().GetArray("OriginalPointIds").GetValue(i)
                origPtIds = boundaryPoly.GetPointData().GetArray("OriginalPointIds")

                pt_polgon = vtk.vtkPolyData()
                pt_polgon.SetPoints(pts)

            normalsF = vtk.vtkPolyDataNormals()
            normalsF.AutoOrientNormalsOn()
            normalsF.ComputeCellNormalsOn()
            normalsF.SetInputData(merge_polygon)
            normalsF.Update()

            self.interactor_style.set_model_normal(normalsF.GetOutput())
            self.interactor_style.set_boundary_points(pt_polgon)
            # 创建网格actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(merge_polygon)
            mapper.SetColorModeToDirectScalars()
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.31, 0.51, 0.9)
            self.interactor_style.view_actor_file(ControlMode.node_type)
            self.interactor_style.register_actor_polydata(actor, merge_polygon)
            self.assembly.AddPart(actor)
            # self.renderer.AddActor(self.assembly)
            self.interactor_style.set_marker_to_cell(self.marker_to_cell)
            self.temp_actor = Axis().show_coordinate_system(self.assembly)
            self.temp_actor.PickableOff()
            self.interactor_style.set_assembly(self.assembly, self.temp_actor)
            # self.interactor_style.locality_axis(self.iren)
            self.renderer.ResetCamera()
            self.renderer.GetActiveCamera().SetParallelProjection(True)
            self.set_ori_camera()
        else:
            print("Please select exactly two files.")

    def open_yarn_data(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*);;Text Files (*.txt)")
        print("one:", files[0])
        print("two:", files[1])
        print("len:",len(files))
        if len(files) == 2:
            self.interactor_style.yarn_mgr = YarnManager(parent_widget=self.vtk_widget,renderer=self.renderer)
            self.interactor_style.yarn_mgr.load_from_files(files[0] if "lines" in files[0] else files[1], files[0] if "nodes" in files[0] else files[1])
            self.interactor_style.yarn_mgr.filter(yarn_type=2,on=False)
            self.interactor_style.view_actor_file(ControlMode.yarn_type)
            self.interactor_style.set_marker_to_cell(self.marker_to_cell)
            self.renderer.ResetCamera()
            self.renderer.GetActiveCamera().SetParallelProjection(True)
            self.set_ori_camera()
        else:
            print("Please select exactly two files.")

    def set_controlmode_points(self):
        self.interactor_style.set_controlmode(ControlMode.select_points)
        print("ControlMode.select_points")

    def set_controlmode_face(self):
        self.interactor_style.set_controlmode(ControlMode.select_face)
        print("ControlMode.select_face")

    def set_controlmode_cell(self):
        self.interactor_style.set_controlmode(ControlMode.select_cell)
        print("ControlMode.select_cell")

    def set_controlmode_mode(self):
        self.interactor_style.set_controlmode(ControlMode.select_model)
        print("ControlMode.select_model")

    def set_axis_show(self):
        self.interactor_style.set_axis_type(ControlMode.axis_show)
        print("ControlMode.axis_show")

    def set_perspective_projection(self):
        self.renderer.ResetCamera()
        camera = self.renderer.GetActiveCamera()
        camera.SetParallelProjection(False)
        #camera.SetViewAngle(30)  # 设置视角（角度制）
        #camera.SetClippingRange(0.1, 100)  # 设置近/远裁剪面
        self.renderer.GetRenderWindow().Render()

    def set_rectangular_projection(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetParallelProjection(True)
        #camera.SetParallelScale(10)  # 设置正交投影的缩放范围（类似视口高度）
        #camera.SetClippingRange(0.1, 100)
        self.renderer.GetRenderWindow().Render()

    def set_front_view(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.Position)
        camera.SetFocalPoint(self.focal_point)
        camera.SetViewUp(self.view_up)
        self.renderer.GetRenderWindow().Render()

    def set_top_view(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.Position)
        camera.SetFocalPoint(self.focal_point)
        camera.SetViewUp(self.view_up)
        camera.Azimuth(90)
        self.renderer.GetRenderWindow().Render()

    def set_side_view(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.Position)
        camera.SetFocalPoint(self.focal_point)
        camera.SetViewUp(self.view_up)
        direction = camera.GetDirectionOfProjection()
        original_viewup = camera.GetViewUp()
        new_viewup = [0.0, 0.0, 0.0]
        vtk.vtkMath.Cross(direction, original_viewup, new_viewup)
        camera.SetViewUp(new_viewup)
        camera.Azimuth(-90)
        self.renderer.GetRenderWindow().Render()

    def set_view_style(self):
        self.temp_Position = self.renderer.GetActiveCamera().GetPosition()
        self.temp_focal_point = self.renderer.GetActiveCamera().GetFocalPoint()
        self.temp_view_up = self.renderer.GetActiveCamera().GetViewUp()

    def get_switchover_view(self):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.temp_Position)
        camera.SetFocalPoint(self.temp_focal_point)
        camera.SetViewUp(self.temp_view_up)
        self.renderer.GetRenderWindow().Render()


    def set_ori_camera(self):
        self.Position = self.renderer.GetActiveCamera().GetPosition()
        self.focal_point = self.renderer.GetActiveCamera().GetFocalPoint()
        self.view_up = self.renderer.GetActiveCamera().GetViewUp()

    def edge_switch(self):
        if self.edge_flag:
            self.edge_flag = False
            actors = vtk.vtkPropCollection()
            self.assembly.GetActors(actors)
            actors.InitTraversal()
            actor = actors.GetNextProp()
            while actor:
                actor.GetProperty().SetEdgeColor(0, 0, 0)
                actor.GetProperty().EdgeVisibilityOff()
                actor = actors.GetNextProp()
            self.renderer.GetRenderWindow().Render()
        else:
            self.edge_flag = True
            actors = vtk.vtkPropCollection()
            self.assembly.GetActors(actors)
            actors.InitTraversal()
            actor = actors.GetNextProp()
            while actor:
                actor.GetProperty().SetEdgeColor(0, 0, 0)
                actor.GetProperty().EdgeVisibilityOn()
                actor = actors.GetNextProp()
            self.renderer.GetRenderWindow().Render()

    def axis_switch(self):
        if self.axis_flag:
            self.axis_flag = False
            self.renderer.RemoveActor(self.temp_actor)
            self.renderer.GetRenderWindow().Render()
        else:
            self.axis_flag = True
            self.temp_actor.PickableOff()
            self.renderer.AddActor(self.temp_actor)
            self.renderer.GetRenderWindow().Render()

    def reversal_normal(self):
        if self.normal_flag:
            self.normal_flag = False
            # self.interactor_style.set_normal_switch(ControlMode.cellNormal_show)
            self.normal_actor = self.interactor_style.visualize_normals()
            self.renderer.AddActor(self.normal_actor)
            self.renderer.GetRenderWindow().Render()
        else:
            self.normal_flag = True
            # self.interactor_style.set_normal_switch(0)
            self.renderer.RemoveActor(self.normal_actor)
            self.renderer.GetRenderWindow().Render()

    def show_cellID_switch(self):
        if self.cellID_flag:
            self.cellID_flag = False
            self.interactor_style.set_cellID_switch(ControlMode.cellID_show)
        else:
            self.cellID_flag = True
            self.interactor_style.set_cellID_switch(0)

    def show_silhouette_switch(self):
        if self.silhouette_flag:
            self.silhouette_flag = False
            pass
        else:
            self.silhouette_flag = True
            pass

    def exported_shell_switch(self):
        if self.interactor_style:
            self.interactor_style.get_build_boundary_shell()

    def unit_matching_switch(self):
        dlg = ParamDialog(self,
                          default_nodepreform=8,
                          default_nodehyper=8,
                          default_pathPre="modules/FindEnumV1_2/inputdata",
                          default_pathHyper="modules/FindEnumV1_2/inputdata",
                          default_filesave="modules/FindEnumV1_2/outputdata",
                          default_alpha=(0.0, 0.0, 0.0))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        path_Preform = dlg.path_Preform
        path_Hyper = dlg.path_Hyper
        filesave = dlg.filesave
        nodepreform = dlg.nodepreform
        nodehyper = dlg.nodehyper
        alpha = dlg.alpha
        flag_plot = dlg.flag_plot

        try:
            writeparamforFortran(path_Preform, path_Hyper, filesave,
                                 alpha, nodepreform, nodehyper, flag_plot)
        except Exception as e:
            QMessageBox.critical(self, "写参数失败", f"写入 input_param_fortran.dat 时出错：\n{e}")
            return

        try:
            result = subprocess.run(
                ["modules/FindEnumV1_2/FindEnum.exe"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
        except FileNotFoundError:
            QMessageBox.critical(self, "找不到可执行文件",
                                 "无法找到 FindEnum.exe，请确认它在当前目录或 PATH 中。")
            return
        out_text = ""
        if result.stdout:
            out_text += "=== 标准输出 ===\n" + result.stdout + "\n"
        if result.stderr:
            out_text += "=== 错误输出 ===\n" + result.stderr + "\n"
        if not out_text:
            out_text = "FindEnum.exe 执行完毕，未产生任何输出。"

        dlg_out = QDialog(self)
        dlg_out.setWindowTitle("FindEnum.exe 运行结果")
        dlg_out.resize(600, 400)
        layout = QVBoxLayout()
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(out_text)
        layout.addWidget(txt)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dlg_out.accept)
        hb = QHBoxLayout()
        hb.addStretch(1)
        hb.addWidget(btn_close)
        layout.addLayout(hb)
        dlg_out.setLayout(layout)
        dlg_out.exec()
        return

    def yarn_move_switch(self):
        if self.yarn_flag:
            self.interactor_style.set_yarn_interactive(self.yarn_flag)
            self.yarn_flag = False
        else:
            self.interactor_style.set_yarn_interactive(self.yarn_flag)
            self.yarn_flag = True

        # self.interactor_style.yarn_mgr
    def yarn_view_switch(self):
        if self.yarnview:
            self.yarnview = False
            self.interactor_style.set_yarn_show(self.yarnview)
        else:
            self.yarnview = True
            self.interactor_style.set_yarn_show(self.yarnview)

    def structural_view_switch(self):
        if self.structuralview:
            self.structuralview = False
            self.interactor_style.set_structural_show(self.structuralview)
        else:
            self.structuralview = True
            self.interactor_style.set_structural_show(self.structuralview)

    def reverse_selection_switch(self):
        pass

    def flatten(self):
        self.create_mesh(self.uPoints, self.cells, color=[0.31, 0.51, 0.9], bounding=False, num=0)

    def create_mesh2(self, points, cells, color, bounding=False, num=0):
        # 创建网格polydata
        points_vtk = vtk.vtkPoints()
        for point in points:
            points_vtk.InsertNextPoint(point)

        cells_vtk = vtk.vtkCellArray()
        for cell in cells:
            cells_vtk.InsertNextCell(4, cell[1:])

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points_vtk)
        polydata.SetPolys(cells_vtk)

        # 增加 PartID 数组，每连续 6 个 cell 对应一个六面体
        # 只有节点数据时，用到这个
        num_cells = polydata.GetNumberOfCells()
        partArray = vtk.vtkIntArray()
        partArray.SetName("PartID")
        partArray.SetNumberOfComponents(1)
        partArray.SetNumberOfTuples(num_cells)
        for i in range(num_cells):
            # 计算当前 cell 属于哪个六面体（每六个 cell 为一组）
            part_id = i // 6
            partArray.SetValue(i, part_id)
        polydata.GetCellData().AddArray(partArray)

        pointColors = vtk.vtkUnsignedCharArray()
        pointColors.SetNumberOfComponents(3)
        pointColors.SetName("PointColors")
        numPts = polydata.GetNumberOfPoints()
        szColor = [0, 0, 0, 0]

        for i in range(numPts):
            pointColors.InsertNextTuple3(color[0]*255,color[1]*255,color[2]*255)
        polydata.GetPointData().SetScalars(pointColors)

        cellcolors = vtk.vtkUnsignedCharArray()
        cellcolors.SetNumberOfComponents(3)
        cellcolors.SetName("CellColors")
        numc = polydata.GetNumberOfCells()
        for i in range(numc):
            cellcolors.InsertNextTuple3(color[0]*255,color[1]*255,color[2]*255)
        polydata.GetCellData().SetScalars(cellcolors)  # 面渲染

        return polydata

    def create_mesh(self, points, cells, color, bounding=False, num=0):
        # 创建网格polydata
        points_vtk = vtk.vtkPoints()
        for point in points:
            points_vtk.InsertNextPoint(point)

        cells_vtk = vtk.vtkCellArray()
        for cell in cells:
            cells_vtk.InsertNextCell(4, cell[1:])

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points_vtk)
        polydata.SetPolys(cells_vtk)

        # 增加 PartID 数组，每连续 6 个 cell 对应一个六面体
        # 只有节点数据时，用到这个
        num_cells = polydata.GetNumberOfCells()
        partArray = vtk.vtkIntArray()
        partArray.SetName("PartID")
        partArray.SetNumberOfComponents(1)
        partArray.SetNumberOfTuples(num_cells)
        for i in range(num_cells):
            # 计算当前 cell 属于哪个六面体（每六个 cell 为一组）
            part_id = i // 6
            partArray.SetValue(i, part_id)
        polydata.GetCellData().AddArray(partArray)

        pointColors = vtk.vtkUnsignedCharArray()
        pointColors.SetNumberOfComponents(3)
        pointColors.SetName("PointColors")
        numPts = polydata.GetNumberOfPoints()
        for i in range(numPts):
            pointColors.InsertNextTuple3(color[0]*255,color[1]*255,color[2]*255)
        polydata.GetPointData().SetScalars(pointColors)

        # 创建网格actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        self.interactor_style.register_actor_polydata(actor, polydata)
        self.assembly.AddPart(actor)

        if bounding:
            self.create_bounding_box(points, color=[1, 0, 0], n=4, p=4)

        self.renderer.AddActor(self.assembly)

    def create_bounding_box(self, points, color, n, p):
        points_np = np.array(points)
        x_min, y_min, z_min = points_np.min(axis=0)
        x_max, y_max, z_max = points_np.max(axis=0)
        # 外部包围框
        # Create the grid lines
        grid_lines = vtk.vtkPolyData()
        points_vtk = vtk.vtkPoints()
        lines_vtk = vtk.vtkCellArray()

        # Horizontal lines (parallel to x-axis)
        for i in range(n + 1):
            z = z_min + i * (z_max - z_min) / n
            points_vtk.InsertNextPoint(x_min, y_max, z)
            points_vtk.InsertNextPoint(x_max, y_max, z)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, 2 * i)
            line.GetPointIds().SetId(1, 2 * i + 1)
            lines_vtk.InsertNextCell(line)

        # Vertical lines (parallel to z-axis)
        for j in range(p + 1):
            x = x_min + j * (x_max - x_min) / p
            points_vtk.InsertNextPoint(x, y_max, z_min)
            points_vtk.InsertNextPoint(x, y_max, z_max)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, 2 * (n + 1) + 2 * j)
            line.GetPointIds().SetId(1, 2 * (n + 1) + 2 * j + 1)
            lines_vtk.InsertNextCell(line)

        grid_lines.SetPoints(points_vtk)
        grid_lines.SetLines(lines_vtk)

        grid_mapper = vtk.vtkPolyDataMapper()
        grid_mapper.SetInputData(grid_lines)

        grid_actor = vtk.vtkActor()
        grid_actor.SetMapper(grid_mapper)
        grid_actor.GetProperty().SetColor((0, 0, 1))  # RGB
        grid_actor.GetProperty().SetOpacity(0.5)

        self.assembly.AddPart(grid_actor)

        # 内部包围框
        # Create the grid lines
        grid_lines = vtk.vtkPolyData()
        points_vtk = vtk.vtkPoints()
        lines_vtk = vtk.vtkCellArray()

        # Horizontal lines (parallel to x-axis)
        for i in range(n):
            z = z_min + (2 * i + 1) * (z_max - z_min) / (2 * n)
            mid_x_min = x_min + (x_max - x_min) / (2 * p)
            mid_x_max = x_min + (x_max - x_min) / (2 * p) * (2 * p - 1)
            points_vtk.InsertNextPoint(mid_x_min, y_max, z)
            points_vtk.InsertNextPoint(mid_x_max, y_max, z)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, 2 * i)
            line.GetPointIds().SetId(1, 2 * i + 1)
            lines_vtk.InsertNextCell(line)

        # Vertical lines (parallel to z-axis)
        for j in range(p):
            x = x_min + (2 * j + 1) * (x_max - x_min) / (2 * p)
            mid_z_min = z_min + (z_max - z_min) / (2 * n)
            mid_z_max = z_min + (z_max - z_min) / (2 * n) * (2 * n - 1)
            points_vtk.InsertNextPoint(x, y_max, mid_z_min)
            points_vtk.InsertNextPoint(x, y_max, mid_z_max)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, 2 * (n) + 2 * j)
            line.GetPointIds().SetId(1, 2 * (n) + 2 * j + 1)
            lines_vtk.InsertNextCell(line)

        grid_lines.SetPoints(points_vtk)
        grid_lines.SetLines(lines_vtk)

        grid_mapper = vtk.vtkPolyDataMapper()
        grid_mapper.SetInputData(grid_lines)

        grid_actor = vtk.vtkActor()
        grid_actor.SetMapper(grid_mapper)
        grid_actor.GetProperty().SetColor(color)
        grid_actor.GetProperty().SetOpacity(0.5)

        self.assembly.AddPart(grid_actor)

    def thickness(self):
        # 该方法弹出一个对话框，通过两个输入框允许用户输入经纬的数量，输入框旁边有上下按钮可以点击实现数字加减，并且动态绘制一个蓝色网格，被经纬向的数量平均分割
        from widgets.main_window import ThickDialog
        from modules.PyModule_Thickness.BladeThickness_main import thinckness_calu
        dialog = ThickDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            jing_count, wei_count, grid_points, mid_points = dialog.get_values()
            print(f"经数量: {jing_count}, 纬数量: {wei_count}")
            print(f"蓝色网格每个点的坐标: {grid_points}")
            print(f"中点网格每个点的坐标: {mid_points}")
            self.create_bounding_box(self.uPoints, color=[1, 0, 0], n=jing_count, p=wei_count)
            thinckness_calu(jing_count, wei_count)

    def create_heatmap(self):
        points, heatmaps, cells = self.uPoints, self.heatmaps, self.cells

        # Convert heatmaps to numpy array for faster operations
        heatmaps_np = np.array(heatmaps)

        # Pre-calculate min and max values
        mins = heatmaps_np.min(axis=0)
        maxs = heatmaps_np.max(axis=0)
        ranges = maxs - mins

        # Normalize colors using vectorized operations
        normalized_colors = (heatmaps_np - mins) / ranges

        # Create VTK points
        points_vtk = vtk.vtkPoints()
        for point in points:
            points_vtk.InsertNextPoint(point)

        # Create VTK cells
        cells_vtk = vtk.vtkCellArray()
        for cell in cells:
            cells_vtk.InsertNextCell(4, cell[1:])

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points_vtk)
        polydata.SetPolys(cells_vtk)

        # Create color scalars
        scalars = vtk.vtkFloatArray()
        scalars.SetNumberOfComponents(3)
        scalars.SetName("Colors")

        # Add normalized colors to scalars
        for color in normalized_colors:
            scalars.InsertNextTuple3(color[0], color[1], color[2])

        polydata.GetPointData().SetScalars(scalars)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        mapper.SetScalarModeToUsePointData()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self.assembly.AddPart(actor)
        self.renderer.AddActor(self.assembly)

# ---------------------------
# 主程序入口
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
