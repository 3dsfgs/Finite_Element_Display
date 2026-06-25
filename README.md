## Language

- [English](#english)
- [中文](#中文)

- # Demo Example
![image1](https://github.com/3dsfgs/Finite_Element_Display/blob/master/1.png)
![image2](https://github.com/3dsfgs/Finite_Element_Display/blob/master/2.png)
![image3](https://github.com/3dsfgs/Finite_Element_Display/blob/master/3.png)
![image4](https://github.com/3dsfgs/Finite_Element_Display/blob/master/4.png)

### 中文
# 背景

- 这个项目的发展历史更加的黑暗，也是让我明白了，重新认识到，这个社会的运行规则 —— 技术在资源以及权力面前什么都不是；
- 该项目全由个人独自完成，以后不要乱接外包！
- 估计已经烂尾了，开源希望能有些启示；


# 代码目录
- three-dimensional braided composite material\  **根目录**
    - interactiveStyle\   **交互工具类**
        - coordinate_axis.py
        - interactive_style_cpp.py
        - interactive_style_h.py
        - region_select.py
        - Tool_Definition.py
    - ui\  **界面ui**
        - icon\
            - 各类 *.jpg 图标文件
        - main_window.py
    - MainMaindow.py   **主程序接口**
    - ElementData.dat  **数据文件（需与NodeData.dat同时选中加载）**
    - NodeData.dat
    - README

# 总结
该项目使用可用于 有限元模型的 抽壳 以及一些其他的计算；
同时支持 纱线模型 的合并 拼接 阵列 等

# 环境配置 

请参考 Pip freeze > requirements.txt 中的第三方库

# ui
本来准备新加ui的，后续有时间再弄吧


### English
# Background
This project went through a rather grim development journey, which gave me a brand-new, sobering understanding of how society really operates: technology means nothing in the face of resources and power.
I completed the entire project single-handedly. A hard lesson learned—never take random freelance outsourcing work again!
The project is likely permanently stalled. I’m open-sourcing it in hopes that others can draw some insights from it.

# Code Directory
- three-dimensional braided composite material\  **Root Directory**
  - interactiveStyle\  *Interactive Utility Classes*
    - coordinate_axis.py
    - interactive_style_cpp.py
    - interactive_style_h.py
    - region_select.py
    - Tool_Definition.py
  - ui\  *GUI Interface Module*
    - icon\
      - Various *.jpg icon assets
    - main_window.py
  - MainMaindow.py  *Main Program Entry*
  - ElementData.dat  *Data File (Must be loaded together with NodeData.dat)*
  - NodeData.dat
  - README
# Project Overview
This project implements shell extraction and other auxiliary computations for finite element models.
It also supports yarn model operations including merging, splicing, array generation, and more.

# Environment Setup
Refer to the third-party libraries exported via the command:
pip freeze > requirements.txt
