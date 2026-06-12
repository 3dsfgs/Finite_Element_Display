from .Tool_Definition import ScalarValue
import vtk


class RegionSelect:
    def __init__(self):
        self.regionVisible = False
        self.left_click_start = None
        self.right_click_start = None
        self.region = None
        self._create_region_()

    def __VisibilityOn__(self):
        self.region.VisibilityOn()

    def __VisibilityOff__(self):
        self.region.VisibilityOff()

    def set_left_click_start(self, val):
        self.left_click_start = val

    def set_right_click_start(self, val):
        self.right_click_start = val

    def _create_region_(self):
        self.points = vtk.vtkPoints()
        self.points.SetNumberOfPoints(4)
        for i in range(4):
            self.points.SetPoint(i, 0, 0, 0)
        polyLine = vtk.vtkPolyLine()
        polyLine.GetPointIds().SetNumberOfIds(5)
        for i, pid in enumerate([0, 1, 2, 3, 0]):
            polyLine.GetPointIds().SetId(i, pid)
        self.Lines = vtk.vtkCellArray()
        self.Lines.InsertNextCell(polyLine)
        self.polyData = vtk.vtkPolyData()
        self.polyData.SetPoints(self.points)
        self.polyData.SetLines(self.Lines)
        self.mapper = vtk.vtkPolyDataMapper2D()
        self.mapper.SetInputData(self.polyData)
        self.region = vtk.vtkActor2D()
        self.region.SetMapper(self.mapper)
        self.region.GetProperty().SetColor(ScalarValue.red_normalization)
        self.region.GetProperty().SetLineWidth(2)
        self.region.VisibilityOff()

    def update_region(self, _arg1, _arg2):
        x0, y0 = _arg1
        x1, y1 = _arg2
        pt0 = (min(x0, x1), max(y0, y1), 0)
        pt1 = (max(x0, x1), max(y0, y1), 0)
        pt2 = (max(x0, x1), min(y0, y1), 0)
        pt3 = (min(x0, x1), min(y0, y1), 0)
        self.points.SetPoint(0, pt0)
        self.points.SetPoint(1, pt1)
        self.points.SetPoint(2, pt2)
        self.points.SetPoint(3, pt3)
        self.points.Modified()
