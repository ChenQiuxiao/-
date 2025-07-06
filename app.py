import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd
from io import BytesIO
import base64

# 设置全局样式
st.set_page_config(
    page_title="凸轮设计及仿真系统",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置Matplotlib中文字体
rcParams['font.family'] = 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False

# 自定义CSS样式
st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stButton>button {
        background-color: #4a8cff;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #3a7be0;
    }
    .stNumberInput>div>div>input {
        background-color: #ffffff;
    }
    .stSelectbox>div>div>select {
        background-color: #ffffff;
    }
    .css-1v0mbdj {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .css-1fv8s86 {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header {
        color: #1f77b4;
        text-align: center;
        padding-bottom: 20px;
    }
    .highlight {
        background-color: #e6f2ff;
        border-left: 4px solid #4a8cff;
        padding: 10px;
        border-radius: 0 5px 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 标题区域
st.title("⚙️ 凸轮设计及仿真系统")
st.markdown("""
    <div class="highlight">
    本应用用于设计凸轮轮廓并进行运动仿真。输入设计参数后，系统将自动计算凸轮轮廓曲线、
    推杆位移、速度和加速度曲线，并提供数据下载功能。
    </div>
    """, unsafe_allow_html=True)

# 侧边栏 - 输入参数
with st.sidebar:
    st.header("设计参数")
    with st.expander("基本参数", expanded=True):
        r0 = st.number_input("基圆半径 (mm)", min_value=10.0, max_value=200.0, value=50.0, step=1.0)
        h = st.number_input("推杆最大位移 (mm)", min_value=5.0, max_value=100.0, value=20.0, step=1.0)
        n = st.number_input("凸轮转速 (rpm)", min_value=10.0, max_value=1000.0, value=100.0, step=10.0)
        e = st.number_input("偏距 (mm)", min_value=0.0, max_value=50.0, value=0.0, step=1.0)
        k = st.selectbox("旋转方向", ["逆时针 (1)", "顺时针 (-1)"], index=0)
        k = 1 if k == "逆时针 (1)" else -1

    with st.expander("运动角度参数", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            θri = st.number_input("推程运动角 (°)", min_value=10.0, max_value=180.0, value=90.0, step=5.0)
            θfa = st.number_input("远休止角 (°)", min_value=0.0, max_value=180.0, value=60.0, step=5.0)
        with col2:
            θre = st.number_input("回程运动角 (°)", min_value=10.0, max_value=180.0, value=90.0, step=5.0)
            θn = 360 - (θri + θfa + θre)
            st.metric("近休止角 (°)", f"{θn:.2f}")

    if θn < 0:
        st.error("错误：总角度超过360°，请重新输入运动角参数！")
        st.stop()

    # 添加分隔线
    st.markdown("---")

    # 添加一个计算按钮
    calculate_btn = st.button("计算凸轮轮廓")
    st.markdown("---")

    # 添加应用信息
    st.caption("**凸轮设计及仿真系统**")
    st.caption("版本: 1.0 | 设计: 陈小秋是皮卡秋")
    st.caption("© 2025 机械原理课程设计")

# 主内容区域
if calculate_btn:
    # 计算角速度 (rad/s)
    ω = 2 * np.pi * n / 60

    # 角度数组 (度)
    θ_total = np.linspace(0, 360, 1000)

    # 转换为弧度
    θ_rad = np.deg2rad(θ_total)

    # 初始化位移、速度、加速度数组
    s = np.zeros_like(θ_total)
    v = np.zeros_like(θ_total)
    a = np.zeros_like(θ_total)

    # 计算推程阶段 (正弦加速度)
    θ_rise = θ_total[θ_total < θri]
    β_rise = θ_ri_rad = np.deg2rad(θri)
    θ_rise_rad = np.deg2rad(θ_rise)
    s_rise = h * (θ_rise_rad / β_rise - np.sin(2 * np.pi * θ_rise_rad / β_rise) / (2 * np.pi))
    v_rise = (h * ω / β_rise) * (1 - np.cos(2 * np.pi * θ_rise_rad / β_rise))
    a_rise = (2 * np.pi * h * ω ** 2 / β_rise ** 2) * np.sin(2 * np.pi * θ_rise_rad / β_rise)

    # 远休止阶段
    θ_dwell1 = θ_total[(θ_total >= θri) & (θ_total < (θri + θfa))]
    s_dwell1 = np.full_like(θ_dwell1, h)
    v_dwell1 = np.zeros_like(θ_dwell1)
    a_dwell1 = np.zeros_like(θ_dwell1)

    # 回程阶段 (正弦加速度)
    θ_return = θ_total[(θ_total >= (θri + θfa)) & (θ_total < (θri + θfa + θre))]
    θ_return_start = θri + θfa
    β_return = θ_re_rad = np.deg2rad(θre)
    θ_return_rad = np.deg2rad(θ_return - θ_return_start)
    s_return = h * (1 - θ_return_rad / β_return + np.sin(2 * np.pi * θ_return_rad / β_return) / (2 * np.pi))
    v_return = (h * ω / β_return) * (-1 + np.cos(2 * np.pi * θ_return_rad / β_return))
    a_return = (-2 * np.pi * h * ω ** 2 / β_return ** 2) * np.sin(2 * np.pi * θ_return_rad / β_return)

    # 近休止阶段
    θ_dwell2 = θ_total[(θ_total >= (θri + θfa + θre)) & (θ_total <= 360)]
    s_dwell2 = np.zeros_like(θ_dwell2)
    v_dwell2 = np.zeros_like(θ_dwell2)
    a_dwell2 = np.zeros_like(θ_dwell2)

    # 合并所有阶段
    s = np.concatenate((s_rise, s_dwell1, s_return, s_dwell2))
    v = np.concatenate((v_rise, v_dwell1, v_return, v_dwell2))
    a = np.concatenate((a_rise, a_dwell1, a_return, a_dwell2))

    # 计算凸轮轮廓
    if k == -1:  # 顺时针
        x = (r0 + s) * np.sin(θ_rad) + e * np.cos(θ_rad)
        y = (r0 + s) * np.cos(θ_rad) - e * np.sin(θ_rad)
    else:  # 逆时针
        x = (r0 + s) * np.sin(θ_rad) - e * np.cos(θ_rad)
        y = (r0 + s) * np.cos(θ_rad) + e * np.sin(θ_rad)

    # 创建数据框用于下载
    df = pd.DataFrame({
        '角度(度)': θ_total,
        '位移(mm)': s,
        '速度(mm/s)': v,
        '加速度(mm/s²)': a,
        '轮廓X(mm)': x,
        '轮廓Y(mm)': y
    })

    # 计算关键参数
    max_velocity = np.max(v)
    min_velocity = np.min(v)
    max_acceleration = np.max(a)
    min_acceleration = np.min(a)
    rotation_direction = "逆时针" if k == 1 else "顺时针"

    # 参数汇总表格
    st.subheader("设计参数汇总")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | 参数 | 值 |
        |---|---|
        | **基圆半径 (mm)** | {r0:.2f} |
        | **推杆最大位移 (mm)** | {h:.2f} |
        | **凸轮转速 (rpm)** | {n:.2f} |
        | **旋转方向** | {rotation_direction} |
        | **推程运动角 (°)** | {θri:.2f} |
        | **远休止角 (°)** | {θfa:.2f} |
        """)

    with col2:
        st.markdown(f"""
        | 参数 | 值 |
        |---|---|
        | **回程运动角 (°)** | {θre:.2f} |
        | **近休止角 (°)** | {θn:.2f} |
        | **偏距 (mm)** | {e:.2f} |
        | **角速度 (rad/s)** | {ω:.2f} |
        | **最大速度 (mm/s)** | {max_velocity:.2f} |
        | **最小速度 (mm/s)** | {min_velocity:.2f} |
        | **最大加速度 (mm/s²)** | {max_acceleration:.2f} |
        | **最小加速度 (mm/s²)** | {min_acceleration:.2f} |
        """)

    # 创建图表
    st.subheader("运动曲线分析")

    # 位移曲线
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(θ_total, s, 'b-', linewidth=2.5, label='位移')
    ax1.fill_between(θ_total, 0, s, color='#1f77b4', alpha=0.2)
    ax1.set_title('推杆位移曲线', fontsize=14, fontweight='bold')
    ax1.set_xlabel('凸轮转角 (°)', fontsize=12)
    ax1.set_ylabel('位移 (mm)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper right', fontsize=12)
    ax1.set_xlim(0, 360)
    ax1.set_ylim(0, h * 1.2)
    ax1.axvline(x=θri, color='r', linestyle='--', alpha=0.5)
    ax1.axvline(x=θri + θfa, color='r', linestyle='--', alpha=0.5)
    ax1.axvline(x=θri + θfa + θre, color='r', linestyle='--', alpha=0.5)
    ax1.text(θri / 2, h * 1.1, '推程', ha='center', fontsize=11, color='darkblue')
    ax1.text(θri + θfa / 2, h * 1.1, '远休止', ha='center', fontsize=11, color='darkblue')
    ax1.text(θri + θfa + θre / 2, h * 1.1, '回程', ha='center', fontsize=11, color='darkblue')
    ax1.text(θri + θfa + θre + θn / 2, h * 1.1, '近休止', ha='center', fontsize=11, color='darkblue')
    st.pyplot(fig1)

    # 速度和加速度曲线
    col1, col2 = st.columns(2)
    with col1:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(θ_total, v, 'g-', linewidth=2.5, label='速度')
        ax2.fill_between(θ_total, 0, v, where=v >= 0, color='green', alpha=0.2)
        ax2.fill_between(θ_total, 0, v, where=v < 0, color='red', alpha=0.2)
        ax2.set_title('推杆速度曲线', fontsize=14, fontweight='bold')
        ax2.set_xlabel('凸轮转角 (°)', fontsize=12)
        ax2.set_ylabel('速度 (mm/s)', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        ax2.legend(loc='upper right', fontsize=12)
        ax2.set_xlim(0, 360)
        v_max = np.max(np.abs(v)) * 1.2
        ax2.set_ylim(-v_max, v_max)
        ax2.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        st.pyplot(fig2)

    with col2:
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.plot(θ_total, a, 'r-', linewidth=2.5, label='加速度')
        ax3.fill_between(θ_total, 0, a, where=a >= 0, color='red', alpha=0.2)
        ax3.fill_between(θ_total, 0, a, where=a < 0, color='green', alpha=0.2)
        ax3.set_title('推杆加速度曲线', fontsize=14, fontweight='bold')
        ax3.set_xlabel('凸轮转角 (°)', fontsize=12)
        ax3.set_ylabel('加速度 (mm/s²)', fontsize=12)
        ax3.grid(True, linestyle='--', alpha=0.7)
        ax3.legend(loc='upper right', fontsize=12)
        ax3.set_xlim(0, 360)
        a_max = np.max(np.abs(a)) * 1.2
        ax3.set_ylim(-a_max, a_max)
        ax3.axhline(y=0, color='k', linestyle='-', alpha=0.5)
        st.pyplot(fig3)

    # 凸轮轮廓
    st.subheader("凸轮轮廓设计")
    fig4, ax4 = plt.subplots(figsize=(8, 8))

    # 绘制基圆
    base_circle = plt.Circle((0, 0), r0, fill=False, color='blue', linestyle='--', alpha=0.7)
    ax4.add_patch(base_circle)

    # 绘制偏距圆
    if e > 0:
        offset_circle = plt.Circle((0, 0), e, fill=False, color='green', linestyle=':', alpha=0.7)
        ax4.add_patch(offset_circle)

    # 绘制凸轮轮廓
    ax4.plot(x, y, 'r-', linewidth=2.5, label='凸轮轮廓')
    ax4.plot([x[0], x[-1]], [y[0], y[-1]], 'r-', linewidth=2.5)

    # 设置图形属性
    ax4.set_aspect('equal', 'box')
    ax4.set_title('凸轮轮廓曲线', fontsize=16, fontweight='bold')
    ax4.set_xlabel('X (mm)', fontsize=12)
    ax4.set_ylabel('Y (mm)', fontsize=12)
    ax4.grid(True, linestyle='--', alpha=0.7)
    ax4.legend(loc='upper right', fontsize=12)
    ax4.set_xlim(-(r0 + h + e + 5), (r0 + h + e + 5))
    ax4.set_ylim(-(r0 + h + e + 5), (r0 + h + e + 5))

    # 添加坐标原点
    ax4.plot(0, 0, 'ko', markersize=8)
    ax4.text(0, -3, 'O', fontsize=12, ha='center')

    st.pyplot(fig4)

    # 数据下载功能
    st.subheader("数据导出")
    st.markdown("### 计算结果数据")

    # 显示数据预览
    st.dataframe(df.head(10))


    # 创建下载链接
    def get_table_download_link(df, filename):
        """生成下载链接"""
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">下载CSV文件</a>'
        return href


    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(get_table_download_link(df, "凸轮设计数据.csv"), unsafe_allow_html=True)

    # 图表下载
    with col2:
        # 位移图下载
        buf = BytesIO()
        fig1.savefig(buf, format="png", dpi=120)
        buf.seek(0)
        st.download_button(
            label="下载位移图",
            data=buf,
            file_name="位移曲线.png",
            mime="image/png"
        )

    with col3:
        # 轮廓图下载
        buf = BytesIO()
        fig4.savefig(buf, format="png", dpi=120)
        buf.seek(0)
        st.download_button(
            label="下载轮廓图",
            data=buf,
            file_name="凸轮轮廓.png",
            mime="image/png"
        )

    # 添加设计信息
    st.markdown("---")
    st.caption(f"凸轮轮廓设计及运动仿真 | 设计时间: 2025年 | 采用正弦加速度运动规律")

else:
    # 初始状态显示帮助信息
    st.subheader("使用说明")
    st.markdown("""
    1. 在左侧边栏输入凸轮设计参数
    2. 点击"计算凸轮轮廓"按钮开始计算
    3. 系统将自动计算并显示：
        - 推杆位移、速度和加速度曲线
        - 凸轮轮廓曲线
        - 设计参数汇总表
    4. 使用数据导出功能下载计算结果

    ### 参数说明：
    - **基圆半径**：凸轮的最小半径
    - **推杆最大位移**：推杆从基圆位置上升的最大高度
    - **凸轮转速**：凸轮旋转速度（转/分钟）
    - **偏距**：推杆中心线与凸轮旋转中心的距离
    - **旋转方向**：凸轮的旋转方向（顺时针或逆时针）
    - **推程运动角**：推杆上升过程对应的凸轮转角
    - **远休止角**：推杆在最高位置停留对应的凸轮转角
    - **回程运动角**：推杆下降过程对应的凸轮转角
    - **近休止角**：推杆在最低位置停留对应的凸轮转角（自动计算）
    """)


    # 添加设计理论
    with st.expander("设计理论说明"):
        st.markdown("""
        ### 正弦加速度运动规律

        在凸轮设计中，正弦加速度运动规律（也称为摆线运动规律）是一种常用的运动规律，
        它可以提供平滑的运动特性，减少冲击和振动。

        #### 推程阶段公式：

        - 位移：$s = h \\left( \\frac{\\theta}{\\beta} - \\frac{1}{2\\pi} \\sin\\left(\\frac{2\\pi\\theta}{\\beta}\\right) \\right)$
        - 速度：$v = \\frac{h\\omega}{\\beta} \\left( 1 - \\cos\\left(\\frac{2\\pi\\theta}{\\beta}\\right) \\right)$
        - 加速度：$a = \\frac{2\\pi h \\omega^2}{\\beta^2} \\sin\\left(\\frac{2\\pi\\theta}{\\beta}\\right)$

        其中：
        - $h$ 为推杆最大位移
        - $\\theta$ 为凸轮转角
        - $\\beta$ 为推程运动角
        - $\\omega$ 为凸轮角速度

        #### 回程阶段公式：

        - 位移：$s = h \\left( 1 - \\frac{\\theta}{\\beta} + \\frac{1}{2\\pi} \\sin\\left(\\frac{2\\pi\\theta}{\\beta}\\right) \\right)$
        - 速度：$v = \\frac{h\\omega}{\\beta} \\left( -1 + \\cos\\left(\\frac{2\\pi\\theta}{\\beta}\\right) \\right)$
        - 加速度：$a = -\\frac{2\\pi h \\omega^2}{\\beta^2} \\sin\\left(\\frac{2\\pi\\theta}{\\beta}\\right)$

        ### 凸轮轮廓计算

        对于偏置直动推杆凸轮机构，凸轮轮廓坐标计算公式为：

        - 逆时针旋转：
          $x = (r_0 + s)\\sin\\theta - e\\cos\\theta$
          $y = (r_0 + s)\\cos\\theta + e\\sin\\theta$

        - 顺时针旋转：
          $x = (r_0 + s)\\sin\\theta + e\\cos\\theta$
          $y = (r_0 + s)\\cos\\theta - e\\sin\\theta$

        其中：
        - $r_0$ 为基圆半径
        - $e$ 为偏距
        - $s$ 为推杆位移
        - $\\theta$ 为凸轮转角
        """)