import sys
from yarn_manager import YarnManager
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


'''
目前初步实现基础的鼠标交互、后续会将鼠标交互的相关内容、移入到interactive_style_cpp中
后续使用继承的方式重写交互逻辑 以及交互策略
'''
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.frame = QWidget()
        self.vl = QVBoxLayout()
        self.vtk_widget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtk_widget)
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        self.mgr = YarnManager(parent_widget=self.vtk_widget)
        lines_file = "D:/Pycharm_project/interaction Fiber/data/yarn/user-1-yarn-lines.dat"
        nodes_file = "D:/Pycharm_project/interaction Fiber/data/yarn/user-1-yarn-nodes.dat"
        # lines_file = "D:/Pycharm_project/interaction Fiber/data/yarn/yarn-lines-100.dat"
        # nodes_file = "D:/Pycharm_project/interaction Fiber/data/yarn/yarn-nodes-100.dat"
        self.mgr.load_from_files(lines_file, nodes_file)
        self.mgr.filter(yarn_type=2,on=True)
        # self.mgr.translate_o(0,10,10)
        # self.mgr.translate_o(1,10,10)
        # self.mgr.translate_o(2,10,10)
        # self.mgr.translate_o(3,10,10)
        # self.mgr.translate_o(4,10,10)
        # self.mgr.translate_o(5,10,10)
        # self.mgr.translate_o(6,10,10)
        # self.mgr.translate_o(7,10,10)
        self.mgr.start()


if __name__ == "__main__":
    '''
    该文件为独立运行的纱线交互demo，目前的功能有:
    1. 通过属性选择纱线
    2. 纱线集合: 支持增加、删除不同属性的纱线 单击选中
    3. 通过点击纱线上的节点 改变纱线的形状
    4. 新增断开纱线接口、目前存在渲染的问题
    5. 增加纱线的右键 断开的 交互逻辑以及相关功能
    6. 增加纱线的右键合并 交互逻辑以及相关功能
    备注：关于断开接口修改，目前沿用之前的接口
    '''
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    w.vtk_widget.Initialize()
    # sys.exit(app.exec())
