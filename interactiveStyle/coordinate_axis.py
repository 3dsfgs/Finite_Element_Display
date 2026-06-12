import vtk
import math


class Axis:

    def __init__(self):
        pass
    # 增加一个传入顶点位置信息记录的 显示坐标轴

    def circle_axis(self, center, norm, radius, color):
        polygon = vtk.vtkRegularPolygonSource()
        polygon.SetCenter(0,0,0)
        polygon.SetNormal(norm)
        polygon.SetRadius(radius)
        polygon.SetNumberOfSides(50)
        polygon.SetGeneratePolyline(1)
        polygon.SetGeneratePolygon(0)
        tubeFilter = vtk.vtkTubeFilter()
        tubeFilter.SetInputConnection(polygon.GetOutputPort())
        tubeFilter.SetRadius(0.25)
        tubeFilter.SetNumberOfSides(50)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(tubeFilter.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetLineWidth(5)
        actor.GetProperty().SetOpacity(0.8)
        return actor

    def line_axis(self,p1,p2,color):
        lineSource = vtk.vtkLineSource()
        lineSource.SetPoint1(p1)
        lineSource.SetPoint2(p2)
        lineSource.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetLineWidth(3)
        actor.GetProperty().SetOpacity(0.8)
        return actor

    def create_axis_actor(self,origin, vector, color, scale=1.0):
        """
        创建一条从原点延伸至 origin+vector*scale 的线段，用于显示坐标轴
        """
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
        actor.GetProperty().SetOpacity(0.8)

        return actor

    def sphere(self, center, radius, color):
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(0,0,0)
        sphereSource.SetRadius(radius)
        sphereSource.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetOpacity(0.8)

        return actor

    def show_coordinate_system(self, arg1):
        assembly = vtk.vtkAssembly()
        if arg1 is None:
            return
        bounds = arg1.GetBounds()
        # center = [
        #     (bounds[0] + bounds[1]) / 2.0,
        #     (bounds[2] + bounds[3]) / 2.0,
        #     (bounds[4] + bounds[5]) / 2.0
        # ]
        center = [0,0,0]
        dx = bounds[1] - bounds[0]
        dy = bounds[3] - bounds[2]
        dz = bounds[5] - bounds[4]
        diag = math.sqrt(dx * dx + dy * dy + dz * dz)
        sphere_radius = diag * 0.005

        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(0,0,0)
        sphereSource.SetRadius(sphere_radius)
        sphereSource.Update()
        sphereMapper = vtk.vtkPolyDataMapper()
        sphereMapper.SetInputConnection(sphereSource.GetOutputPort())
        cenActor = vtk.vtkActor()
        cenActor.SetMapper(sphereMapper)
        cenActor.GetProperty().SetColor(1, 0, 0)
        cenActor.PickableOff()

        rot_radius = diag / 4.0
        rotX = self.circle_axis(center, (1, 0, 0), rot_radius, (1, 0, 0))
        rotY = self.circle_axis(center, (0, 1, 0), rot_radius, (0, 1, 0))
        rotZ = self.circle_axis(center, (0, 0, 1), rot_radius, (0, 0, 1))

        move_len = diag / 2.0
        moveX = self.line_axis(center, [center[0] + move_len, center[1], center[2]], (1, 0, 0))
        moveY = self.line_axis(center, [center[0], center[1] + move_len, center[2]], (0, 1, 0))
        moveZ = self.line_axis(center, [center[0], center[1], center[2] + move_len], (0, 0, 1))
        moveX.PickableOff()
        moveY.PickableOff()
        moveZ.PickableOff()

        moveXEnd = self.sphere([center[0] + move_len, center[1], center[2]], sphere_radius, (1, 0, 0))
        moveYEnd = self.sphere([center[0], center[1] + move_len, center[2]], sphere_radius, (0, 1, 0))
        moveZEnd = self.sphere([center[0], center[1], center[2] + move_len], sphere_radius, (0, 0, 1))
        moveXEnd.PickableOff()
        moveYEnd.PickableOff()
        moveZEnd.PickableOff()

        assembly.AddPart(cenActor)
        # assembly.AddPart(rotX)
        # assembly.AddPart(rotY)
        # assembly.AddPart(rotZ)
        assembly.AddPart(moveX)
        assembly.AddPart(moveY)
        assembly.AddPart(moveZ)
        assembly.AddPart(moveXEnd)
        assembly.AddPart(moveYEnd)
        assembly.AddPart(moveZEnd)
        assembly.PickableOff()

        return assembly

    def create_plane_actor(self, origin, x_axis, y_axis):
        half_width = 10.0
        half_height = 10.0

        p0 = origin - half_width * x_axis - half_height * y_axis
        p1 = origin + half_width * x_axis - half_height * y_axis
        p2 = origin + half_width * x_axis + half_height * y_axis
        p3 = origin - half_width * x_axis + half_height * y_axis

        points = vtk.vtkPoints()
        points.InsertNextPoint(p0.tolist())
        points.InsertNextPoint(p1.tolist())
        points.InsertNextPoint(p2.tolist())
        points.InsertNextPoint(p3.tolist())

        quad = vtk.vtkPolygon()
        quad.GetPointIds().SetNumberOfIds(4)
        for i in range(4):
            quad.GetPointIds().SetId(i, i)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(quad)

        planePolyData = vtk.vtkPolyData()
        planePolyData.SetPoints(points)
        planePolyData.SetPolys(cells)

        planeColors = vtk.vtkUnsignedCharArray()
        planeColors.SetNumberOfComponents(3)
        planeColors.InsertNextTuple3(200, 200, 200)  # RGB：浅灰色
        planePolyData.GetCellData().SetScalars(planeColors)

        planeMapper = vtk.vtkPolyDataMapper()
        planeMapper.SetInputData(planePolyData)
        planeActor = vtk.vtkActor()
        planeActor.SetMapper(planeMapper)
        planeActor.GetProperty().SetOpacity(0.5)

        return planeActor


class LabelOverlay:
    def __init__(self, renderer, render_window):
        self.renderer = renderer
        self.ren_win = render_window
        self.text_actors = []

        self.ren_win.AddObserver("RenderEvent", self._update_positions)

    def clear(self):
        for ta in self.text_actors:
            self.renderer.RemoveActor2D(ta[0])
        self.text_actors.clear()

    def label_point_ids(self, points3d, ids):

        self.clear()
        for (x,y,z), pid in zip(points3d, ids):
            ta = vtk.vtkTextActor()
            ta.SetInput(str(pid))
            prop = ta.GetTextProperty()
            prop.SetFontSize(14)
            prop.SetColor(1,1,1)
            prop.SetJustificationToCentered()
            prop.SetVerticalJustificationToCentered()
            ta.GetPositionCoordinate().SetCoordinateSystemToDisplay()
            ta.SetPosition(0,0)
            self.renderer.AddActor2D(ta)
            self.text_actors.append((ta, (x,y,z)))
        self.ren_win.Render()

    def _update_positions(self, caller, event):
        for ta, world_pt in self.text_actors:
            xw, yw, zw = world_pt
            self.renderer.SetWorldPoint(xw, yw, zw, 1.0)
            self.renderer.WorldToDisplay()
            disp = self.renderer.GetDisplayPoint()
            ta.SetPosition(int(disp[0]), int(disp[1]))