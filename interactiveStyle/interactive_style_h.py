from .region_select import RegionSelect
from .coordinate_axis import Axis,LabelOverlay
from .Tool_Definition import ControlMode
import vtk


class CustomInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        super().__init__()
        # 鼠标左键按下交互事件
        self.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        # 鼠标右键按下交互事件
        self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        # 鼠标中键按下事件
        self.AddObserver("MiddleButtonPressEvent", self.middle_button_press_event)

        # 鼠标左键释放事件
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_release_event)
        # 鼠标右键释放事件
        self.AddObserver("RightButtonReleaseEvent", self.right_button_release_event)
        # 鼠标中键释放事件
        self.AddObserver("MiddleButtonReleaseEvent", self.middle_button_release_event)

        # 鼠标移动事件
        self.AddObserver("MouseMoveEvent", self.mouse_move_event)

        # 监听键盘等一些快捷建
        self.AddObserver("KeyPressEvent",self.keyboard_callback)
        # 鼠标滚轮 向前
        #self.AddObserver("MouseWheelForwardEvent", self.mouse_wheel_forward_event)
        # 鼠标滚轮 向后
        #self.AddObserver("MouseWheelBackwardEvent", self.mouse_wheel_backward_event)

        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.01)

        self.default_renderer = None
        self.selected_actor = None
        self.assembly = None
        self.dragging = False
        self.region_select = RegionSelect()
        self.axis_show = Axis()
        self.text_label = None
        self.silhouette = None
        self.box_selecting = None
        self.start_pos = None
        self.select_control = 0
        self.axis_set_type = 0
        self.actor_to_polygon = {}
        self.original_actor_color = {}
        self.selected_point_indices = {}
        self.region_point_indices = {}
        self.selected_cell_actors = set()
        self.boundary_map = set()
        self.boundary_points = vtk.vtkPolyData()
        self.temp_actor = None
        self.glyph_actor = vtk.vtkActor()

        self.marker_to_cell = None
        self.current_dialog = None

        self.xMouseMoveFactor = 4.0
        self.yMouseMoveFactor = 2.5
        self.StartPos = (0, 0)
        self.center = None
        self.StartWorld = None
        self.ActorInitialPosition = None
        self.MiddleButtonDown = False
        self.polyhedron_cell_ids = []
        self.polyhedron_cell_ids_release = []
        self.temp_point_box = None
        self.unique_point_ids = set()
        self.view_actor_type = 0
        self.center_list = []
        self.axes_actor = None
        self.current_cell_vertex_ids = None
        self.actor_x = None
        self.actor_y = None
        self.actor_z = None
        self.plane_ = None
        self.click_point = []
        self.cell_shell = set()

        self.iren = None
        self.model_normal = None
        self.id_list = vtk.vtkIdTypeArray()
        self.bill_text = []
        self.merge_queue = []
        self.click_id = None
        self.cellID_show = 0
        self.cellNormal_show = 0
        self._last_box = None
        self.yarn_mgr = None
        self._debug = False


    def view_actor_file(self, val):
        self.view_actor_type = val

    def set_default_renderer(self, val):
        self.default_renderer = val
        self.text_label = LabelOverlay(self.default_renderer, self.default_renderer.GetRenderWindow())

    def set_marker_to_cell(self, val):
        self.marker_to_cell = val

    def set_model_normal(self, val):
        self.model_normal = val

    def set_cellID_switch(self, val):
        self.cellID_show = val
        if len(self.bill_text) == 0 and self.click_id is not None:
            self.visualize_label()
            if self.default_renderer:
                self.default_renderer.GetRenderWindow().Render()
        elif len(self.bill_text) != 0:
            self.text_label.clear()
            self.bill_text.clear()
            if self.default_renderer:
                self.default_renderer.GetRenderWindow().Render()

    def set_normal_switch(self, val):
        self.cellNormal_show = val

    def set_controlmode(self, val):
        self.select_control = val
        if self.select_control == ControlMode.select_face:
            self.reset_face_selections()
        else:
            self.reset_all_selections()

    def select_finish(self):
        self.select_control = ControlMode.default_type
        self.click_id = None
        self.polyhedron_cell_ids.clear()
        self.unique_point_ids.clear()
        self.cell_shell.clear()

    def set_axis_type(self, val):
        self.axis_set_type = val
        self.click_point.clear()

    def set_boundary_map(self, val):
        self.boundary_map = val

    def set_boundary_points(self, val):
        self.boundary_points = val

    def set_assembly(self, val, axis):
        self.assembly = val
        self.temp_actor = axis
        self.temp_actor.PickableOff()

        actors = vtk.vtkPropCollection()
        self.assembly.GetActors(actors)
        actors.InitTraversal()
        actor = actors.GetNextProp()
        while actor:
            actor.GetProperty().SetEdgeColor(0, 0, 0)
            actor.GetProperty().EdgeVisibilityOn()
            actor = actors.GetNextProp()

        self.default_renderer.AddActor(self.assembly)
        self.default_renderer.AddActor(self.temp_actor)

    def set_region_renderer(self):
        self.default_renderer.AddActor2D(self.region_select.region)

    def register_actor_polydata(self, val1, val2):
        self.actor_to_polygon[val1] = val2
        self.original_actor_color[val1] = val1.GetProperty().GetColor()
        self.selected_point_indices[val1] = set()
        self.region_point_indices[val1] = set()

    def OnLeftButtonDown(self):
        interactor = self.GetInteractor()
        if interactor.GetControlKey():
            self.StopState()
            self.StartPan()
        return

    def OnLeftButtonUp(self):
        interactor = self.GetInteractor()
        if interactor.GetControlKey():
            self.EndPan()
        return

    def OnRightButtonDown(self):
        self.StopState()
        interactor = self.GetInteractor()
        if interactor.GetControlKey():
            self.StopState()
            self.StartRotate()
        return

    def OnRightButtonUp(self):
        self.StopState()
        interactor = self.GetInteractor()
        if interactor.GetControlKey():
            self.EndRotate()
        return

    def OnMiddleButtonDown(self):
        self.StopState()
        return

    def OnMiddleButtonUp(self):
        self.StopState()
        return

    def left_button_press_event(self, obj, event):
        pass

    def right_button_press_event(self, obj, event):
        pass

    def middle_button_press_event(self, obj, event, key=False):
        pass

    def mouse_move_event(self, obj, event):
        pass

    def left_button_release_event(self, obj, event):
        pass

    def right_button_release_event(self, obj, event):
        pass

    def middle_button_release_event(self, obj, event, key=False):
        pass

    def keyboard_callback(self, obj, event):
        pass

    def set_scalar(self, actor=None, data=None, index=None, uv=None, flag=0, multi_select=False, alt_key=False):
        pass

    def control_selection(self, _arg1, _arg2, flag=0):
        pass

    def locator_point(self, data, _arg):
        pass

    def reset_all_selections(self):
        pass

    def reset_face_selections(self):
        pass

    def update_cell_selection(self, actor, multi_select=False):
        pass

    def update_face_selection(self, actor, multi_select=False):
        pass

    def region_control_selection(self, _arg1, _arg2, flag=0, multi_select=False):
        pass

    def world_to_display(self, pt):
        pass

    def compute_face_coordinate_system(self, selected_ids, cell_vertex_ids):
        pass

    def handle_selection_result(self, selected_ids):
        pass

    def build_face_axes_from_selection(self, selected_ids):
        pass

    def remove_actor(self):
        pass

    def click_to_plane(self):
        pass

    def click_to_face_plane(self, polygon, pt):
        pass

    def build_boundary_shell(self,data,cell_to_color):
        pass

    def visualize_normals(self, scale_factor=0.1):
        pass

    def visualize_label(self):
        pass

    def visualize_boundary(self, polydata, angle_threshold_deg=80.0):
        pass

    def compute_2d_convex_hull(self, points2d):
        pass

    def build_screen_outline(self, contour: vtk.vtkPolyData,
                             renderer: vtk.vtkRenderer):
        pass

    def extract_view_silhouette(self, poly: vtk.vtkPolyData, cam: vtk.vtkCamera):
        pass

