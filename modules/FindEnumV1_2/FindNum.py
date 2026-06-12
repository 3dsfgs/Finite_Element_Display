# -*- coding: utf-8 -*-
"""
# 参数文件：input_param_fortran.dat
inputdata     # data2.展平模型单元、节点信息存放路径
inputdata     # data3.空间模型单元、节点信息存放路径
outputdata    # 输出数据保存位置
1             # 是否查找单元编号
0.0,0.0,0.0   # 空间模型坐标系分别绕x\y\z旋转的角度，模型不动，坐标系动
10088,13230   # 展平模型单元数量、节点数量
10088,15489   # 空间模型单元数量、节点数量
8,8           # 展平模型节点数量、空间模型节点数量
"""

"""
输出文件：res_Enum_Mapping.mac
格式：空间模型单元编号, 展平模型单元编号
"""

import os 
import numpy as np
import matplotlib.pyplot as plt
def writeparamforFortran(path_Preform,path_Hyper,filesave,alpha,flag_plot):
    # 将参数写入到参数文件中，提供给Fortran计算    
    # 提取预制体节点、单元数量
    fileopen  = open(path_Preform+r"\NodeData.dat", 'r');
    lines = fileopen.readlines()
    nnpreform = len(lines)
    fileopen.close()
    
    fileopen  = open(path_Preform+r"\ElementData.dat", 'r');
    lines = fileopen.readlines()
    nepreform = len(lines)
    fileopen.close()
    
    # 提取Hypermesh节点、单元数量
    fileopen  = open(path_Hyper+r"\Hypermesh_NodeData.dat", 'r');
    lines = fileopen.readlines()
    nnhyper = len(lines)
    fileopen.close()
    
    fileopen  = open(path_Hyper+r"\Hypermesh_ElementData.dat", 'r');
    lines = fileopen.readlines()
    nehyper = len(lines)
    fileopen.close()
    
    filewrite = open('input_param_fortran.dat', 'w')
    filewrite.write(path_Preform+'\n')
    filewrite.write(path_Hyper+'\n')
    filewrite.write(filesave+'\n')
    if(flag_plot==1):
        filewrite.write('0'+'\n')
        print ('compare hypermesh and preform')
        print('write data into input_param_fortran.dat')
    else:
        print ('calculate hypermesh emat number')
        print('write data into input_param_fortran.dat')
        filewrite.write('1'+'\n')
    
    filewrite.write(str(alpha[0])+','+str(alpha[1])+','+str(alpha[2])+'\n')
    filewrite.write(str(nepreform)+','+str(nnpreform) +'\n')
    filewrite.write(str(nehyper)+','+str(nnhyper) +'\n')
    filewrite.write(str(nodepreform)+','+str(nodehyper) +'\n')
    filewrite.close()
    return 
    
def compareHyper_Preform(path_Preform,pathsave):
    # 对比两个模型的空间位置是否重合，暂时不用
    coord0=np.loadtxt(path_Preform+r"\\NodeData.dat");
    coord1=np.loadtxt(pathsave+r"\\Hypermesh_NodeData_transfered.dat");
    nd = 3
    plt.figure(1)
    plt.plot(coord0[0:-1:nd,1], coord0[0:-1:nd,2],'k.', coord1[0:-1:nd,1],coord1[0:-1:nd,2],'ro')
    plt.legend(['Preform', 'Composite'])                
    plt.figure(2)
    plt.plot(coord0[0:-1:nd,1], coord0[0:-1:nd,3],'k.', coord1[0:-1:nd,1],coord1[0:-1:nd,3],'ro')
    plt.legend(['Preform', 'Composite'])
    plt.figure(3)
    plt.plot(coord0[0:-1:nd,2], coord0[0:-1:nd,3],'k.', coord1[0:-1:nd,2],coord1[0:-1:nd,3],'ro')
    plt.legend(['Preform', 'Composite'])
    plt.show()
    return
    
nodepreform = 8
nodehyper = 8
path_Preform = "inputdata"
path_Hyper = "inputdata"
filesave = "outputdata"
alpha = [0.0,0.0,0.0]

flag_plot = 0  # 0-直接计算单元编号；1-不直接计算单元编号，先计算空间模型选择alpha后的节点坐标
writeparamforFortran(path_Preform,path_Hyper,filesave,alpha,flag_plot)
os.system('FindEnum.exe')
