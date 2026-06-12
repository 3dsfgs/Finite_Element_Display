import os
from PyQt6.QtWidgets import ( QDialog, QLineEdit, QLabel,
    QPushButton, QFormLayout, QHBoxLayout, QVBoxLayout, QMessageBox, QTextEdit
)


def writeparamforFortran(path_Preform, path_Hyper, filesave,
                         alpha, nodepreform, nodehyper, flag_plot):
    with open(os.path.join(path_Preform, "NodeData.dat"), 'r') as f:
        nnpreform = len(f.readlines())
    with open(os.path.join(path_Preform, "ElementData.dat"), 'r') as f:
        nepreform = len(f.readlines())

    with open(os.path.join(path_Hyper, "Hypermesh_NodeData.dat"), 'r') as f:
        nnhyper = len(f.readlines())
    with open(os.path.join(path_Hyper, "Hypermesh_ElementData.dat"), 'r') as f:
        nehyper = len(f.readlines())

    with open("input_param_fortran.dat", 'w') as f:
        f.write(path_Preform + "\n")
        f.write(path_Hyper + "\n")
        f.write(filesave + "\n")

        # flag_plot: 0 或 1
        if flag_plot == 1:
            f.write("0\n")
            print("compare hypermesh and preform")
            print("write data into input_param_fortran.dat")
        else:
            f.write("1\n")
            print("calculate hypermesh emat number")
            print("write data into input_param_fortran.dat")

        f.write(f"{alpha[0]:.6f},{alpha[1]:.6f},{alpha[2]:.6f}\n")
        f.write(f"{nepreform},{nnpreform}\n")
        f.write(f"{nehyper},{nnhyper}\n")
        f.write(f"{nodepreform},{nodehyper}\n")

    return


class ParamDialog(QDialog):
    def __init__(self, parent=None,
                 default_nodepreform=8,
                 default_nodehyper=8,
                 default_pathPre="inputdata",
                 default_pathHyper="inputdata",
                 default_filesave="outputdata",
                 default_alpha=(0.0, 0.0, 0.0)):
        super().__init__(parent)
        self.setWindowTitle("单元匹配参数设置")
        self.setModal(True)

        self.nodepreform = default_nodepreform
        self.nodehyper = default_nodehyper
        self.path_Preform = default_pathPre
        self.path_Hyper = default_pathHyper
        self.filesave = default_filesave
        self.alpha = list(default_alpha)
        self.flag_plot = 0

        self.le_pathPre = QLineEdit(default_pathPre)
        self.le_pathHyper = QLineEdit(default_pathHyper)
        self.le_filesave = QLineEdit(default_filesave)

        self.le_nodepre = QLineEdit(str(default_nodepreform))
        self.le_nodehyper = QLineEdit(str(default_nodehyper))

        self.le_alpha_x = QLineEdit(str(default_alpha[0]))
        self.le_alpha_y = QLineEdit(str(default_alpha[1]))
        self.le_alpha_z = QLineEdit(str(default_alpha[2]))

        form = QFormLayout()
        form.addRow("path_Preform:", self.le_pathPre)
        form.addRow("path_Hyper:", self.le_pathHyper)
        form.addRow("filesave:", self.le_filesave)
        form.addRow("nodepreform:", self.le_nodepre)
        form.addRow("nodehyper:", self.le_nodehyper)

        h_alpha = QHBoxLayout()
        h_alpha.addWidget(QLabel("alpha_x:"))
        h_alpha.addWidget(self.le_alpha_x)
        h_alpha.addWidget(QLabel(" alpha_y:"))
        h_alpha.addWidget(self.le_alpha_y)
        h_alpha.addWidget(QLabel(" alpha_z:"))
        h_alpha.addWidget(self.le_alpha_z)
        form.addRow("alpha:", h_alpha)

        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        h_buttons = QHBoxLayout()
        h_buttons.addStretch(1)
        h_buttons.addWidget(btn_ok)
        h_buttons.addWidget(btn_cancel)

        vbox = QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(h_buttons)
        self.setLayout(vbox)

    def accept(self):
        pathPre = self.le_pathPre.text().strip()
        pathHyper = self.le_pathHyper.text().strip()
        filesave = self.le_filesave.text().strip()

        try:
            nodepre = int(self.le_nodepre.text().strip())
            nodehyp = int(self.le_nodehyper.text().strip())
        except ValueError:
            QMessageBox.critical(self, "输入错误", "nodepreform/nodehyper 必须是整数")
            return

        try:
            ax = float(self.le_alpha_x.text().strip())
            ay = float(self.le_alpha_y.text().strip())
            az = float(self.le_alpha_z.text().strip())
        except ValueError:
            QMessageBox.critical(self, "输入错误", "alpha 必须是浮点数")
            return

        if not os.path.isdir(pathPre):
            QMessageBox.critical(self, "路径不存在", f"path_Preform 路径不存在：{pathPre}")
            return
        if not os.path.isdir(pathHyper):
            QMessageBox.critical(self, "路径不存在", f"path_Hyper 路径不存在：{pathHyper}")
            return

        self.path_Preform = pathPre
        self.path_Hyper = pathHyper
        self.filesave = filesave
        self.nodepreform = nodepre
        self.nodehyper = nodehyp
        self.alpha = [ax, ay, az]

        super().accept()

