import sys
import os
import shutil
import time
from PyQt6 import QtCore, QtGui, QtWidgets
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk


#########################################################################
# 先定义一个简易的“可折叠区域”类，前面示例已有，这里直接复用
#########################################################################
class CollapsibleSection(QtWidgets.QWidget):
    """
    一个简易“可折叠区”实现。点击标题会展开/收起内部内容。
    """
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        # 1. 标题按钮
        self.toggle_button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        #self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setStyleSheet("QToolButton { border: none; padding: 2px; background-color: #cdcdcd; }")
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self.toggle_button.clicked.connect(self.on_toggled)

        # 2. 内容区（用 QScrollArea 包裹，方便折叠时高度能自动收缩）
        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        # 布局：标题在上，内容在下
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

        # 用一个内层 QWidget + VBoxLayout 来放真正的子控件
        self.inner_widget = QtWidgets.QWidget()
        self.inner_layout = QtWidgets.QVBoxLayout(self.inner_widget)
        self.inner_layout.setContentsMargins(20, 5, 5, 5)
        self.inner_layout.setSpacing(5)
        self.content_area.setWidget(self.inner_widget)
        self.content_area.setWidgetResizable(True)

    def on_toggled(self):
        """展开或折叠 content_area"""
        checked = self.toggle_button.isChecked()
        if checked:
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
            # 展开：把最大高度设成 inner_widget 的 sizeHint
            content_height = self.inner_widget.sizeHint().height()
            self.content_area.setMaximumHeight(content_height)
        else:
            self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            # 收起：把最大高度设为 0
            self.content_area.setMaximumHeight(0)

    def addWidget(self, widget: QtWidgets.QWidget):
        """向折叠区内部的布局添加一个控件"""
        self.inner_layout.addWidget(widget)


#########################################################################
# 左侧下拉框的图标设置
#########################################################################
class IconCollapsibleSection(QtWidgets.QWidget):
    def __init__(self, title: str, icon_path: str = None, parent=None):
        super().__init__(parent)
        self.toggle_button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        #self.toggle_button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        # 无边框、留一点 padding
        self.toggle_button.setStyleSheet("QToolButton { border: none; padding: 2px; background-color: #E8F4FF; }")
        # 如果图标文件存在，就加载
        if icon_path and os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
            print("图标加载：",icon_path)
        else:
            icon = QtGui.QIcon()
        self.toggle_button.setIcon(icon)
        self.toggle_button.setIconSize(QtCore.QSize(16, 16))
        self.toggle_button.clicked.connect(self.on_toggled)


        # 内容区
        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        # 布局：标题、内容
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

#########################################################################
# 自定义的“参数对话框”示例，供“展平/示迹/厚度 设置”使用
#########################################################################
class FlattenParamDialog(QtWidgets.QDialog):
    """
    展平参数对话框示例。用户可以在这里填写展平所需的参数。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("展平参数设置")
        self.setModal(True)
        self.resize(300, 200)

        main_layout = QtWidgets.QVBoxLayout(self)

        # 1) 网格间距
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("网格间距 (mm):"))
        self.dist_edit = QtWidgets.QLineEdit()
        self.dist_edit.setPlaceholderText("例如 1.0")
        h1.addWidget(self.dist_edit)
        main_layout.addLayout(h1)

        # # 2) 保留孔洞复选框
        # h2 = QtWidgets.QHBoxLayout()
        # self.check_keep_holes = QtWidgets.QCheckBox("保留孔洞")
        # h2.addWidget(self.check_keep_holes)
        # h2.addStretch()
        # main_layout.addLayout(h2)

        # 3) 按钮：确定 / 取消
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    def get_parameters(self):
        """返回用户填写的参数，未填写或格式错误时为 None"""
        try:
            dist = float(self.dist_edit.text())
        except (ValueError, TypeError):
            dist = None
        keep_holes = self.check_keep_holes.isChecked()
        return {"distance": dist, "keep_holes": keep_holes}


class TraceParamDialog(FlattenParamDialog):
    """示迹参数对话框。示例中复用同一个父类，仅修改标题。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("示迹参数设置")


class ThickParamDialog(FlattenParamDialog):
    """厚度参数对话框。示例中复用同一个父类，仅修改标题。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("厚度参数设置")


#########################################################################
# 主窗口：左侧“项目” → 四个折叠区；右侧 3D/2D 切换
#########################################################################
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("三维编织软件")
        self.resize(1200, 800)

        # 定义一个“工作区”根目录，后面所有模型、展平、示迹、厚度的文件夹都在这里
        self.workspace_root = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
        # models 根目录：workspace/models
        self.models_root = os.path.join(self.workspace_root, "models")
        # 确保工作区存在
        os.makedirs(self.models_root, exist_ok=True)

        # 1. 菜单栏
        self._create_menu_bar()
        # 2. 工具栏
        self._create_tool_bar()
        # 3. 左侧面板 & 右侧面板
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        # 1. 先创建一个 QScrollArea
        left_scroll = QtWidgets.QScrollArea()
        # 2. 把我们原来的 left_panel 设为 scroll area 的内容
        left_scroll.setWidget(left_panel)
        # 3. 开启 widget 自动调整大小，让它跟滚动区域尺寸配合
        left_scroll.setWidgetResizable(True)
        # 4. （可选）去掉滚动区自带的边框
        left_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        # 5. 然后把 left_scroll 而不是 left_panel 本身，加入到中央布局
        central = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(central)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        # 这里原来是 left_panel，现在改成 left_scroll
        left_scroll.setMaximumWidth(260)  # 或者 setFixedWidth(260) 看你想要的宽度
        h_layout.addWidget(left_scroll)
        h_layout.addWidget(right_panel, 1)
        self.setCentralWidget(central)

        # # 4. 中央区域布局：左右
        # central_widget = QtWidgets.QWidget()
        # h_layout = QtWidgets.QHBoxLayout(central_widget)
        # h_layout.setContentsMargins(0, 0, 0, 0)
        # h_layout.setSpacing(0)
        # left_panel.setMaximumWidth(260)
        # left_panel.setMinimumWidth(200)
        # h_layout.addWidget(left_panel)
        # h_layout.addWidget(right_panel, 1)
        # self.setCentralWidget(central_widget)

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

        # import os
        # if os.path.exists("./icon/元素-坐标轴.png"):
        #     pixmap = QtGui.QPixmap("./icon/元素-坐标轴.png")
        #     if not pixmap.isNull():
        #         print(f"警告：文件加载")
        #     else:
        #         print(f"警告：文件存在但无法加载")
        # else:
        #     print(f"错误：图标文件不存在")

        for text, filename in actions:
            icon_path = os.path.join(icon_dir, filename)
            if os.path.exists(icon_path):
                icon = QtGui.QIcon(icon_path)
            else:
                # icon = QtGui.QIcon()  # 文件不存在时给一个空图标，防止错误
                icon = QtGui.QIcon.fromTheme(filename)
            action = QtGui.QAction(icon, text, self)
            action.setToolTip(text)
            toolbar.addAction(action)

        # for text, icon_name in actions:
        #     if icon_name:
        #         print("icon_name=",icon_name)
        #         action = QtGui.QAction(QtGui.QIcon.fromTheme(icon_name), text, self)
        #     else:
        #         print("text=",text)
        #         action = QtGui.QAction(text, self)
        #     toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addWidget(QtWidgets.QLabel("？"))
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        self.addToolBar(toolbar)

    def _create_left_panel(self) -> QtWidgets.QWidget:
        """
        构造左侧“项目”面板，包含：模型管理器、展平、示迹、厚度 四个折叠区
        """
        left_container = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(left_container)
        v_layout.setContentsMargins(5, 5, 5, 5)
        v_layout.setSpacing(8)

        # —— 最上方 “项目” 大标题
        title_proj = QtWidgets.QLabel("项目", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        font0 = title_proj.font()
        font0.setPointSize(14)
        font0.setBold(True)
        title_proj.setFont(font0)
        title_proj.setFixedHeight(30)
        v_layout.addWidget(title_proj)
        base_dir = os.path.abspath(os.path.dirname(__file__))
        icon_dir = os.path.join(base_dir, "icon")

        # ================== 1. 模型管理器 ==================
        section_model_mgr = CollapsibleSection("模型管理器")
        # section_model_mgr = IconCollapsibleSection(
        #     title="模型管理器",
        #     icon_path=os.path.join(icon_dir, "模型管理.png")
        # )

        # 1.1) 模型列表，用于显示已导入的模型名称
        self.model_listwidget = QtWidgets.QListWidget()
        self.model_listwidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        section_model_mgr.addWidget(self.model_listwidget)

        # 1.2) 导入模型按钮
        btn_import_model = QtWidgets.QPushButton("导入模型")
        ic_import = QtGui.QIcon(os.path.join(icon_dir, "模型管理.png"))
        btn_import_model.setIcon(ic_import)
        btn_import_model.setIconSize(QtCore.QSize(16, 16))

        btn_import_model.clicked.connect(self.on_import_model)
        section_model_mgr.addWidget(btn_import_model)

        v_layout.addWidget(section_model_mgr)

        # ================== 2. 展平 ==================
        section_flat = CollapsibleSection("展平")

        # 2.1) 导入展平数据
        btn_import_flat = QtWidgets.QPushButton("导入展平数据")
        btn_import_flat.clicked.connect(self.on_import_flatten_data)
        section_flat.addWidget(btn_import_flat)

        # 2.2) 展平设置
        btn_flat_settings = QtWidgets.QPushButton("展平设置")
        btn_flat_settings.clicked.connect(self.on_flatten_settings)
        section_flat.addWidget(btn_flat_settings)

        # 2.3) 展平结果列表
        section_flat.addWidget(QtWidgets.QLabel("展平结果列表："))
        self.flat_result_list = QtWidgets.QListWidget()
        self.flat_result_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        section_flat.addWidget(self.flat_result_list)

        v_layout.addWidget(section_flat)

        if 0:
            # ================== 3. 示迹 ==================
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

            # ================== 4. 厚度 ==================
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

            # ================== 4. 云图 ==================
            # cloud_picture = CollapsibleSection("云图")
            # btn_import_picture = QtWidgets.QPushButton("导入云图数据")
            # btn_import_picture.clicked.connect(self.on_import_cloud_data())
            # cloud_picture.addWidget(btn_import_picture)
            #
            # btn_cloud_settings = QtWidgets.QPushButton("厚度计算设置")
            # btn_cloud_settings.clicked.connect(self.on_thick_settings)
            # cloud_picture.addWidget(btn_cloud_settings)
            #
            # section_thick.addWidget(QtWidgets.QLabel("厚度计算结果列表："))
            # self.thick_result_list = QtWidgets.QListWidget()
            # self.thick_result_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
            # section_thick.addWidget(self.thick_result_list)
            #
            # v_layout.addWidget(section_thick)

        # 底部拉伸，让上面内容靠上排列
        v_layout.addStretch()

        # 2. 现在把 left_container 包在一个 QScrollArea 里
        # left_scroll = QtWidgets.QScrollArea()
        # left_scroll.setWidget(left_container)
        # left_scroll.setWidgetResizable(True)
        # left_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        return left_container

    def _create_right_panel(self) -> QtWidgets.QWidget:
        """
        右侧：上面两个单选按钮用于 3D/2D 切换，下面放 QStackedLayout
        """
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 1) 切换按钮区
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

        # 2) 中间的 QStackedLayout：Page0=VTK 3D，Page1=2D 占位
        self.stacked = QtWidgets.QStackedLayout()
        self.stacked.setContentsMargins(0, 0, 0, 0)

        # 2.1) 3D 渲染区
        vtk_frame = QtWidgets.QFrame()
        vtk_layout = QtWidgets.QVBoxLayout(vtk_frame)
        vtk_layout.setContentsMargins(0, 0, 0, 0)
        vtk_layout.setSpacing(0)
        self.vtk_widget = QVTKRenderWindowInteractor(vtk_frame)
        vtk_layout.addWidget(self.vtk_widget)
        self._init_vtk_scene()
        self.stacked.addWidget(vtk_frame)

        # 2.2) 2D 设计区占位
        design2d = QtWidgets.QFrame()
        design2d.setStyleSheet("background-color: #F5F5F5;")
        d2_layout = QtWidgets.QVBoxLayout(design2d)
        label2d = QtWidgets.QLabel("这里是二维设计区（示例占位）", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        label2d.setFont(QtGui.QFont("", 16))
        d2_layout.addWidget(label2d)
        self.stacked.addWidget(design2d)

        right_layout.addLayout(self.stacked, 1)

        # 3) 切换信号
        self.btn_3d.toggled.connect(lambda checked: self.stacked.setCurrentIndex(0 if checked else 1))

        return right_container

    def _init_vtk_scene(self):
        """
        用一个简单的 VTK 场景示例：一个球体和坐标轴
        """
        iren = self.vtk_widget
        self.vtk_renderer = vtk.vtkRenderer()
        iren.GetRenderWindow().AddRenderer(self.vtk_renderer)


        vtk_read = vtk.vtkPLYReader()
        vtk_read.SetFileName("D:/git_test/simulationprogram/test.ply")
        vtk_read.Update()
        # sphere_source = vtk.vtkSphereSource()
        sphere_source = vtk.vtkCubeSource()
        #sphere_source.SetRadius(5.0)
        #sphere_source.SetThetaResolution(30)
        #sphere_source.SetPhiResolution(30)
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

    #########################################################################
    # —— 以下是左侧各个按钮的回调槽函数，重点是“导入模型”、“导入展平/示迹/厚度”以及“展平/示迹/厚度 设置”
    #########################################################################

    def on_import_model(self):
        """
        用户点击“导入模型”按钮：
        1. 弹出文件对话框，让用户选一个本地三维模型文件（*.stl, *.obj, *.ply 等）。
        2. 若用户选择了文件，则创建对应的模型文件夹：
             workspace/models/<模型名称>/original/
           并把选中的文件 copy 到 original 目录下。
        3. 在 QListWidget 中插入一行：“<模型名称>”，同时把它的模型目录路径作为 item.data(Qt.UserRole) 存起来。
        """
        file_dialog = QtWidgets.QFileDialog(self, "选择三维模型文件")
        file_dialog.setNameFilter("3D 模型文件 (*.stl *.obj *.ply *.vtk);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if not selected_files:
                return
            src_path = selected_files[0]
            # 提取文件名（不含扩展名）作为模型名称
            base_name = os.path.splitext(os.path.basename(src_path))[0]
            model_name = base_name

            # 在 workspace/models 下创建 <model_name>/original 目录
            model_folder = os.path.join(self.models_root, model_name)
            original_folder = os.path.join(model_folder, "original")
            try:
                os.makedirs(original_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建模型文件夹失败", f"无法创建目录：{original_folder}\n{e}")
                return

            # 把选择的文件复制到 original_folder
            try:
                dst_file = os.path.join(original_folder, os.path.basename(src_path))
                shutil.copy(src_path, dst_file)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制模型文件失败", f"无法复制文件到 {original_folder}\n{e}")
                return

            # 在 QListWidget 中添加一个条目，显示 model_name，并把 model_folder 路径存在 Qt.UserRole
            item = QtWidgets.QListWidgetItem(model_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, model_folder)
            self.model_listwidget.addItem(item)

            # 自动展开“模型管理器”折叠区（如果折叠的话）
            # 这里假设用户已经手动展开，也可以像下面这样强制展开：
            # section 不是直接属性，为了演示简单，我们不强制展开
            QtWidgets.QMessageBox.information(self, "导入成功", f"模型 [{model_name}] 已导入，文件存储在：\n{original_folder}")

    def on_import_flatten_data(self):
        """
        用户点击“导入展平数据”：
        1. 先检查“模型管理器”是否选中一个模型；如果没有选中，则弹出警告并返回。
        2. 如果选中了，就弹出文件对话框让用户选一个已有的展平结果文件。
        3. 把选中的文件复制到：
             workspace/models/<模型名称>/flatten/<模型名称>_外部展平_<timestamp>/
        4. 在 self.flat_result_list 中插入一行：“<模型名称>_外部展平_<timestamp>”，并把该结果子文件夹路径存在 item.data(Qt.UserRole)
        """
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再导入展平数据。")
            return

        # 获取所选模型的文件夹路径
        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        # 确保 model_folder/original 下至少有一个文件，才算模型已导入
        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 的 original 文件夹不存在或为空，请先成功导入模型文件。")
            return

        # 弹出文件对话框，让用户选一个已有的展平结果文件
        file_dialog = QtWidgets.QFileDialog(self, "选择已有的展平结果文件")
        file_dialog.setNameFilter("展平文件 (*.vtp *.txt *.csv *.stl *.obj);;所有文件 (*)")
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            sel_flat_files = file_dialog.selectedFiles()
            if not sel_flat_files:
                return
            src_flat_path = sel_flat_files[0]

            # 在 model_folder 下创建 flatten/<模型名称>_外部展平_<timestamp> 子文件夹
            timestamp = int(time.time())
            out_folder_name = f"{model_name}_外部展平_{timestamp}"
            flatten_root = os.path.join(model_folder, "flatten")
            target_folder = os.path.join(flatten_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建展平结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            # 复制用户选的展平文件到 target_folder
            try:
                dst_flat = os.path.join(target_folder, os.path.basename(src_flat_path))
                shutil.copy(src_flat_path, dst_flat)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "复制展平文件失败", f"无法复制文件到 {target_folder}\n{e}")
                return

            # 在 flat_result_list 中插入一行
            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.flat_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "导入展平成功", f"展平结果已导入到：\n{target_folder}")

    def on_flatten_settings(self):
        """
        用户点击“展平设置”：
        1. 检查是否选中模型，且模型 original 目录中有文件；
        2. 如果条件满足，则弹出 FlattenParamDialog 让用户填写参数；
        3. 用户点击确定后，模拟“调用子程序”生成结果（这里会在 model_folder/flatten/<模型名称>_展平_<timestamp>/ 下创建一个 dummy_flatten_result.txt），
           并在 flat_result_list 中插入一行。
        """
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再进行展平设置。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        # 确保 original 文件夹中有模型文件
        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        # 弹出参数对话框
        dlg = FlattenParamDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            params = dlg.get_parameters()
            if params["distance"] is None:
                QtWidgets.QMessageBox.warning(self, "参数错误", "请填写合法的网格间距(例如1.0)。")
                return

            # 模拟调用子程序：在模型目录下创建一个 flatten/<model_name>_展平_<timestamp> 目录，
            # 并在里面写一个 dummy_flatten_result.txt 作为示例结果文件
            timestamp = int(time.time())
            out_folder_name = f"{model_name}_展平_{timestamp}"
            flatten_root = os.path.join(model_folder, "flatten")
            target_folder = os.path.join(flatten_root, out_folder_name)
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "创建展平结果目录失败", f"无法创建目录：{target_folder}\n{e}")
                return

            # 在 target_folder 下生成一个“dummy_flatten_result.txt”来模拟展平输出
            dummy_file = os.path.join(target_folder, "dummy_flatten_result.txt")
            try:
                with open(dummy_file, "w", encoding="utf-8") as fp:
                    fp.write(f"模型 {model_name} 的展平结果示例\n")
                    fp.write(f"顶点id: {params['distance']}\n")
                    fp.write(f"面片id: {'是' if params['keep_holes'] else '否'}\n")
                    fp.write("…后续加入真实的展平数据格式…\n")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "写入展平结果失败", f"无法在 {target_folder} 创建展平结果文件\n{e}")
                return

            # 在列表中插入一行
            item = QtWidgets.QListWidgetItem(out_folder_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, target_folder)
            self.flat_result_list.addItem(item)

            QtWidgets.QMessageBox.information(self, "展平完成", f"模型 [{model_name}] 展平完成，结果已存储在：\n{target_folder}")

    def on_import_trace_data(self):
        """
        用户点击“导入示迹数据”：流程与“导入展平数据”类似，
        只是放到 <model_folder>/trace/<model_name>_外部示迹_<timestamp>/
        """
        sel_items = self.model_listwidget.selectedItems()
        if not sel_items:
            QtWidgets.QMessageBox.warning(self, "没有选中模型", "请先在“模型管理器”中选择一个模型，然后再导入示迹数据。")
            return

        model_item = sel_items[0]
        model_name = model_item.text()
        model_folder = model_item.data(QtCore.Qt.ItemDataRole.UserRole)

        # original 文件夹检查
        original_folder = os.path.join(model_folder, "original")
        if not os.path.isdir(original_folder) or not os.listdir(original_folder):
            QtWidgets.QMessageBox.critical(self, "模型文件缺失", f"模型 [{model_name}] 尚未导入模型文件或 original 文件夹为空。")
            return

        # 选择示迹文件
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
        """
        用户点击“示迹设置”：流程与“展平设置”类似，
        只是目录变成 <model_folder>/trace/<model_name>_示迹_<timestamp>/
        """
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

            # 生成一个 dummy_trace_result.txt 作为示例
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
        """
        用户点击“导入厚度数据”：流程与“导入展平数据”类似，
        只是目录变成 <model_folder>/thick/<model_name>_外部厚度_<timestamp>/
        """
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
        """
        用户点击“导入厚度数据”：流程与“导入展平数据”类似，
        只是目录变成 <model_folder>/thick/<model_name>_外部厚度_<timestamp>/
        """
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
        """
        用户点击“厚度设置”：流程与“展平/示迹 设置”类似，
        只不过目录是 <model_folder>/thick/<model_name>_厚度_<timestamp>/
        """
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

            # 生成 dummy_thick_result.txt 作为示例
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
