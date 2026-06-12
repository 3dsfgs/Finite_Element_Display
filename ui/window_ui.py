import sys
import os
import shutil
import time
from PyQt6 import QtCore, QtGui, QtWidgets
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk


class CollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        self.toggle_button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        
        self.toggle_button.setStyleSheet("QToolButton { border: none; padding: 2px; background-color: #cdcdcd; }")
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self.toggle_button.clicked.connect(self.on_toggled)

        
        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        
        self.inner_widget = QtWidgets.QWidget()
        self.inner_layout = QtWidgets.QVBoxLayout(self.inner_widget)
        self.inner_layout.setContentsMargins(20, 5, 5, 5)
        self.inner_layout.setSpacing(5)
        self.content_area.setWidget(self.inner_widget)
        self.content_area.setWidgetResizable(True)

    def on_toggled(self):
        checked = self.toggle_button.isChecked()
        if checked:
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
            
            content_height = self.inner_widget.sizeHint().height()
            self.content_area.setMaximumHeight(content_height)
        else:
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            
            self.content_area.setMaximumHeight(0)

    def addWidget(self, widget: QtWidgets.QWidget):
        self.inner_layout.addWidget(widget)





class IconCollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title: str, icon_path: str = None, parent=None):
        super().__init__(parent)
        self.toggle_button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        
        self.toggle_button.setStyleSheet("QToolButton { border: none; padding: 2px; background-color: #E8F4FF; }")
        
        if icon_path and os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
            print("图标加载：",icon_path)
        else:
            icon = QtGui.QIcon()
        self.toggle_button.setIcon(icon)
        self.toggle_button.setIconSize(QtCore.QSize(16, 16))
        self.toggle_button.clicked.connect(self.on_toggled)

        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        self.inner_widget = QtWidgets.QWidget()
        self.inner_layout = QtWidgets.QVBoxLayout(self.inner_widget)
        self.inner_layout.setContentsMargins(20, 5, 5, 5)
        self.inner_layout.setSpacing(5)
        self.content_area.setWidget(self.inner_widget)
        self.content_area.setWidgetResizable(True)

    def on_toggled(self):
        expanded = self.toggle_button.isChecked()
        if expanded:
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
            content_height = self.inner_widget.sizeHint().height()
            self.content_area.setMaximumHeight(content_height)
        else:
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            self.content_area.setMaximumHeight(0)

    def addWidget(self, widget: QtWidgets.QWidget):
        self.inner_layout.addWidget(widget)


class FlattenParamDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("展平参数设置")
        self.setModal(True)
        self.resize(300, 200)

        main_layout = QtWidgets.QVBoxLayout(self)

        
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("网格间距 (mm):"))
        self.dist_edit = QtWidgets.QLineEdit()
        self.dist_edit.setPlaceholderText("例如 1.0")
        h1.addWidget(self.dist_edit)
        main_layout.addLayout(h1)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    def get_parameters(self):
        try:
            dist = float(self.dist_edit.text())
        except (ValueError, TypeError):
            dist = None
        # keep_holes = self.check_keep_holes.isChecked()
        return {"distance": 0, "keep_holes": 1}


class TraceParamDialog(FlattenParamDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("示迹参数设置")


class ThickParamDialog(FlattenParamDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("厚度参数设置")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("三维编织软件")
        self.resize(1200, 800)

        self.workspace_root = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
        
        self.models_root = os.path.join(self.workspace_root, "models")
        
        os.makedirs(self.models_root, exist_ok=True)

        
        self._create_menu_bar()
        
        self._create_tool_bar()
        
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        
        left_scroll = QtWidgets.QScrollArea()
        
        left_scroll.setWidget(left_panel)
        
        left_scroll.setWidgetResizable(True)
        
        left_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        central = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(central)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        left_scroll.setMaximumWidth(260)  
        h_layout.addWidget(left_scroll)
        h_layout.addWidget(right_panel, 1)
        self.setCentralWidget(central)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        menus = ["文件", "编辑", "搜索", "视图", "窗口", "语言", "设置", "工具", "帮助", "其他"]
        for m in menus:
            menu_bar.addMenu(m)

    def _create_tool_bar(self):
        toolbar = QtWidgets.QToolBar("主工具栏")
        toolbar.setIconSize(QtCore.QSize(24, 24))

        base_dir = os.path.abspath(os.path.dirname(__file__))
        icon_dir = os.path.join(base_dir, "icon")
        print("icon_dir=",icon_dir)
        actions = [
            ("打开", "folder-open"), ("保存", "document-save"),
            ("坐标", "元素-坐标轴.png"), ("放大", "zoom-in"), ("缩小", "zoom-out"),
            ("左视", "左视图-01.png"), ("俯视", "俯视图-01.png"), ("正视", "正视图.png"), ("透视", "透视图-01.png"),
            ("模式", "选择模式.png"), ("法向", "法向视图.png"), ("网格", "网格.png")
        ]

        for text, filename in actions:
            icon_path = os.path.join(icon_dir, filename)
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
            else:
                
                icon = QtGui.QIcon.fromTheme(filename)
            action = QtGui.QAction(icon, text, self)
            action.setToolTip(text)
            toolbar.addAction(action)

        toolbar.addSeparator()
        toolbar.addWidget(QtWidgets.QLabel("？"))
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.addToolBar(toolbar)

    def _create_left_panel(self) -> QtWidgets.QWidget:
        left_container = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(left_container)
        v_layout.setContentsMargins(5, 5, 5, 5)
        v_layout.setSpacing(8)

        title_proj = QtWidgets.QLabel("项目", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        font0 = title_proj.font()
        font0.setPointSize(14)
        font0.setBold(True)
        title_proj.setFont(font0)
        title_proj.setFixedHeight(30)
        v_layout.addWidget(title_proj)
        base_dir = os.path.abspath(os.path.dirname(__file__))
        icon_dir = os.path.join(base_dir, "icon")

        section_model_mgr = CollapsibleSection("模型管理器")

        self.model_listwidget = QtWidgets.QListWidget()
        self.model_listwidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        section_model_mgr.addWidget(self.model_listwidget)

        btn_import_model = QtWidgets.QPushButton("导入模型")
        ic_import = QtGui.QIcon(os.path.join(icon_dir, "模型管理.png"))
        btn_import_model.setIcon(ic_import)
        btn_import_model.setIconSize(QtCore.QSize(16, 16))

        btn_import_model.clicked.connect(self.on_import_model)
        section_model_mgr.addWidget(btn_import_model)

        v_layout.addWidget(section_model_mgr)

        section_flat = CollapsibleSection("展平")

        btn_import_flat = QtWidgets.QPushButton("导入展平数据")
        btn_import_flat.clicked.connect(self.on_import_flatten_data)
        section_flat.addWidget(btn_import_flat)
        
        btn_flat_settings = QtWidgets.QPushButton("展平设置")
        btn_flat_settings.clicked.connect(self.on_flatten_settings)
        section_flat.addWidget(btn_flat_settings)

        section_flat.addWidget(QtWidgets.QLabel("展平结果列表："))
        self.flat_result_list = QtWidgets.QListWidget()
        self.flat_result_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        section_flat.addWidget(self.flat_result_list)

        v_layout.addWidget(section_flat)

        if 0:
            
            section_trace = CollapsibleSection("示迹线")

            btn_import_trace = QtWidgets.QPushButton("导入示迹线数据")
            btn_import_trace.clicked.connect(self.on_import_trace_data)
            section_trace.addWidget(btn_import_trace)

            btn_trace_settings = QtWidgets.QPushButton("示迹线设置")
            btn_trace_settings.clicked.connect(self.on_trace_settings)
            section_trace.addWidget(btn_trace_settings)

            section_trace.addWidget(QtWidgets.QLabel("示迹线结果列表："))
            self.trace_result_list = QtWidgets.QListWidget()
            self.trace_result_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
            section_trace.addWidget(self.trace_result_list)

            v_layout.addWidget(section_trace)

            
            section_thick = CollapsibleSection("厚度计算")

            btn_import_thick = QtWidgets.QPushButton("导入厚度数据")
            btn_import_thick.clicked.connect(self.on_import_thick_data)
            section_thick.addWidget(btn_import_thick)

            btn_thick_settings = QtWidgets.QPushButton("厚度计算设置")
            btn_thick_settings.clicked.connect(self.on_thick_settings)
            section_thick.addWidget(btn_thick_settings)

            section_thick.addWidget(QtWidgets.QLabel("厚度计算结果列表："))
            self.thick_result_list = QtWidgets.QListWidget()
            self.thick_result_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
            section_thick.addWidget(self.thick_result_list)

            v_layout.addWidget(section_thick)

        v_layout.addStretch()
        return left_container

    def _create_right_panel(self) -> QtWidgets.QWidget:
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        switch_layout = QtWidgets.QHBoxLayout()
        switch_layout.setContentsMargins(5, 5, 5, 5)
        switch_layout.setSpacing(10)
        self.btn_3d = QtWidgets.QRadioButton("三维显示")
        self.btn_2d = QtWidgets.QRadioButton("二维显示")
        self.btn_3d.setChecked(True)
        switch_layout.addWidget(self.btn_3d)
        switch_layout.addWidget(self.btn_2d)
        switch_layout.addStretch()
        right_layout.addLayout(switch_layout)

        self.stacked = QtWidgets.QStackedLayout()
        self.stacked.setContentsMargins(0, 0, 0, 0)

        vtk_frame = QtWidgets.QFrame()
        vtk_layout = QtWidgets.QVBoxLayout(vtk_frame)
        vtk_layout.setContentsMargins(0, 0, 0, 0)
        vtk_layout.setSpacing(0)
        self.vtk_widget = QVTKRenderWindowInteractor(vtk_frame)
        vtk_layout.addWidget(self.vtk_widget)
        self._init_vtk_scene()
        self.stacked.addWidget(vtk_frame)

        design2d = QtWidgets.QFrame()
        design2d.setStyleSheet("background-color: #F5F5F5;")
        d2_layout = QtWidgets.QVBoxLayout(design2d)
        label2d = QtWidgets.QLabel("这里是二维设计区（示例占位）", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        label2d.setFont(QtGui.QFont("", 16))
        d2_layout.addWidget(label2d)
        self.stacked.addWidget(design2d)

        right_layout.addLayout(self.stacked, 1)

        self.btn_3d.toggled.connect(lambda checked: self.stacked.setCurrentIndex(0 if checked else 1))

        return right_container

    def _init_vtk_scene(self):
        iren = self.vtk_widget
        self.vtk_renderer = vtk.vtkRenderer()
        iren.GetRenderWindow().AddRenderer(self.vtk_renderer)
        vtk_read = vtk.vtkPLYReader()
        vtk_read.SetFileName("D:/git_test/simulationprogram/test.ply")
        vtk_read.Update()
        sphere_source = vtk.vtkCubeSource()
        sphere_source.Update()
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetInputConnection(sphere_source.GetOutputPort())
        sphere_actor = vtk.vtkActor()
        sphere_actor.SetMapper(sphere_mapper)
        self.vtk_renderer.AddActor(sphere_actor)

        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(3, 3, 3)
        self.vtk_renderer.AddActor(axes)

        self.vtk_renderer.SetBackground(0.2, 0.3, 0.4)
        camera = self.vtk_renderer.GetActiveCamera()
        camera.SetPosition(20, 20, 20)
        camera.SetFocalPoint(0, 0, 0)

        iren.Initialize()
        iren.Start()

    def on_import_model(self):
        file_dialog = QtWidgets.QFileDialog(self, "选择三维模型文件")
        file_dialog.setNameFilter("3D 模型文件 (*.stl *.obj *.ply *.vtk);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if not selected_files:
                return
            src_path = selected_files[0]
            
            base_name = os.path.splitext(os.path.basename(src_path))[0]
            model_name = base_name

            
            model_folder = os.path.join(self.models_root, model_name)
            original_folder = os.path.join(model_folder, "original")
            try:
                os.makedirs(original_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建模型文件夹失败", f"无法创建目录：{original_folder}\n{e}")
                return
            try:
                dst_file = os.path.join(original_folder, os.path.basename(src_path))
                shutil.copy(src_path, dst_file)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制模型文件失败", f"无法复制文件到 {original_folder}\n{e}")
                return
            item = QtWidgets.QListWidgetItem(model_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, model_folder)
            self.model_listwidget.addItem(item)
            QtWidgets.QMessageBox.information(self, "导入成功", f"模型 [{model_name}] 已导入，文件存储在：\n{original_folder}")

    def on_import_flatten_data(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再导入展平数据。")
            return
        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 的 original 文件夹不存在或为空，请先成功导入模型文件。")
            return
        
        file_dialog = QtWidgets.QFileDialog(self, "选择已有的展平结果文件")
        file_dialog.setNameFilter("展平文件 (*.vtp *.txt *.csv *.stl *.obj);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sel_flat_files = file_dialog.selectedFiles()
            if not sel_flat_files:
                return
            src_flat_path = sel_flat_files[0]
            timestamp = int(time.time())
            out_folder_name = f"{model_name}_外部展平_{timestamp}"
            flatten_root = os.path.join(model_folder, "flatten")
            target_folder = os.path.join(flatten_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建展平结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            try:
                dst_flat = os.path.join(target_folder, os.path.basename(src_flat_path))
                shutil.copy(src_flat_path, dst_flat)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制展平文件失败", f"无法复制文件到 {target_folder}\n{e}")
                return
            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.flat_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "导入展平成功", f"展平结果已导入到：\n{target_folder}")

    def on_flatten_settings(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再进行展平设置。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)
        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return
        
        dlg = FlattenParamDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            params = dlg.get_parameters()
            if params["distance"] is None:
                QtWidgets.QMessageBox.warning(self, "参数错误", "请填写合法的网格间距(例如1.0)。")
                return
            timestamp = int(time.time())
            out_folder_name = f"{model_name}_展平_{timestamp}"
            flatten_root = os.path.join(model_folder, "flatten")
            target_folder = os.path.join(flatten_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建展平结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            dummy_file = os.path.join(target_folder, "dummy_flatten_result.txt")
            try:
                with open(dummy_file, "w", encoding="utf-8") as fp:
                    fp.write(f"模型 {model_name} 的展平结果:\n")
                    fp.write(f"顶点id: {params['distance']}\n")
                    fp.write(f"面片id: {'0' if params['keep_holes'] else '1'}\n")
                    fp.write("…后续加入真实的展平数据格式…\n")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "写入展平结果失败", f"无法在 {target_folder} 创建展平结果文件\n{e}")
                return
            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.flat_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "展平完成", f"模型 [{model_name}] 展平完成，结果已存储在：\n{target_folder}")

    def on_import_trace_data(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再导入示迹数据。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        file_dialog = QtWidgets.QFileDialog(self, "选择已有的示迹结果文件")
        file_dialog.setNameFilter("示迹文件 (*.vtp *.txt *.csv *.stl *.obj);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sel_trace_files = file_dialog.selectedFiles()
            if not sel_trace_files:
                return
            src_trace_path = sel_trace_files[0]

            timestamp = int(time.time())
            out_folder_name = f"{model_name}_外部示迹_{timestamp}"
            trace_root = os.path.join(model_folder, "trace")
            target_folder = os.path.join(trace_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建示迹结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            try:
                dst_trace = os.path.join(target_folder, os.path.basename(src_trace_path))
                shutil.copy(src_trace_path, dst_trace)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制示迹文件失败", f"无法复制文件到 {target_folder}\n{e}")
                return

            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.trace_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "导入示迹成功", f"示迹结果已导入到：\n{target_folder}")

    def on_trace_settings(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再进行示迹设置。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        dlg = TraceParamDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            params = dlg.get_parameters()
            if params["distance"] is None:
                QtWidgets.QMessageBox.warning(self, "参数错误", "请填写合法的网格间距(例如1.0)。")
                return

            timestamp = int(time.time())
            out_folder_name = f"{model_name}_示迹_{timestamp}"
            trace_root = os.path.join(model_folder, "trace")
            target_folder = os.path.join(trace_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建示迹结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            
            dummy_file = os.path.join(target_folder, "dummy_trace_result.txt")
            try:
                with open(dummy_file, "w", encoding="utf-8") as fp:
                    fp.write(f"模型 {model_name} 的示迹结果示例\n")
                    fp.write(f"网格间距: {params['distance']}\n")
                    fp.write(f"保留孔洞: {'是' if params['keep_holes'] else '否'}\n")
                    fp.write("…这里可以写真实的示迹数据格式…\n")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "写入示迹结果失败", f"无法在 {target_folder} 创建示迹结果文件\n{e}")
                return

            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.trace_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "示迹完成", f"模型 [{model_name}] 示迹完成，结果已存储在：\n{target_folder}")

    def on_import_thick_data(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再导入厚度数据。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        file_dialog = QtWidgets.QFileDialog(self, "选择已有的厚度结果文件")
        file_dialog.setNameFilter("厚度文件 (*.vtp *.txt *.csv *.stl *.obj);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sel_thick_files = file_dialog.selectedFiles()
            if not sel_thick_files:
                return
            src_thick_path = sel_thick_files[0]

            timestamp = int(time.time())
            out_folder_name = f"{model_name}_外部厚度_{timestamp}"
            thick_root = os.path.join(model_folder, "thick")
            target_folder = os.path.join(thick_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建厚度结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            try:
                dst_thick = os.path.join(target_folder, os.path.basename(src_thick_path))
                shutil.copy(src_thick_path, dst_thick)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制厚度文件失败", f"无法复制文件到 {target_folder}\n{e}")
                return

            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.thick_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "导入厚度成功", f"厚度结果已导入到：\n{target_folder}")

    def on_import_cloud_data(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再导入云图数据。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        file_dialog = QtWidgets.QFileDialog(self, "选择已有的云图结果文件")
        file_dialog.setNameFilter("云图文件 (*.vtp *.txt *.csv *.stl *.obj);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sel_thick_files = file_dialog.selectedFiles()
            if not sel_thick_files:
                return
            src_thick_path = sel_thick_files[0]

            timestamp = int(time.time())
            out_folder_name = f"{model_name}_外部云图_{timestamp}"
            thick_root = os.path.join(model_folder, "cloud_picture")
            target_folder = os.path.join(thick_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建云图结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            try:
                dst_thick = os.path.join(target_folder, os.path.basename(src_thick_path))
                shutil.copy(src_thick_path, dst_thick)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制云图文件失败", f"无法复制文件到 {target_folder}\n{e}")
                return

            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.thick_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "导入云图成功", f"厚度结果已导入到：\n{target_folder}")

    def on_thick_settings(self):
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再进行厚度设置。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        dlg = ThickParamDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            params = dlg.get_parameters()
            if params["distance"] is None:
                QtWidgets.QMessageBox.warning(self, "参数错误", "请填写合法的网格间距(例如1.0)。")
                return

            timestamp = int(time.time())
            out_folder_name = f"{model_name}_厚度_{timestamp}"
            thick_root = os.path.join(model_folder, "thick")
            target_folder = os.path.join(thick_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建厚度结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            
            dummy_file = os.path.join(target_folder, "dummy_thick_result.txt")
            try:
                with open(dummy_file, "w", encoding="utf-8") as fp:
                    fp.write(f"模型 {model_name} 的厚度结果示例\n")
                    fp.write(f"网格间距: {params['distance']}\n")
                    fp.write(f"保留孔洞: {'是' if params['keep_holes'] else '否'}\n")
                    fp.write("…这里可以写真实的厚度数据格式…\n")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "写入厚度结果失败", f"无法在 {target_folder} 创建厚度结果文件\n{e}")
                return

            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.thick_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "厚度计算完成", f"模型 [{model_name}] 厚度计算完成，结果已存储在：\n{target_folder}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
