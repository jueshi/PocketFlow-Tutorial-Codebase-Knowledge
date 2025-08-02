# Chapter 7: 非破坏性眼图扫描 (NDES)


欢迎来到 `c_env` 教程的最后一章！在上一章 [第 6 章：自适应协商 (Auto-Negotiation)](06_自适应协商__auto_negotiation__.md) 中，我们学习了链路两端的 PHY 设备如何自动“握手”并协商出最佳的通信参数，从而成功建立起通信链路。现在，链路已经通了，数据也开始流动了。但我们如何知道这条高速公路上的“车流”（也就是数据信号）是否顺畅、清晰呢？信号质量的好坏直接影响通信的稳定性和性能。如果信号质量差，充满了噪声和失真，那么即使链路协商成功了，也可能出现大量的传输错误。

这时，我们就需要一种方法来“观察”信号的质量。传统上，这可能需要昂贵的外部测试设备（如高速示波器），并且可能需要中断数据传输。幸运的是，现代 PHY 芯片通常内置了强大的诊断功能，其中之一就是我们本章要学习的“非破坏性眼图扫描”(Non-Destructive Eye Scan - NDES)。

## 什么是“非破坏性眼图扫描”？—— 给信号拍一张“健康快照”

想象一下，你是一位交通工程师，想知道高速公路上飞驰的汽车行驶得是否平稳。你不可能拦下每一辆车来检查。一个更好的方法是，在路边设置一个高速相机，对准一个固定的观察点，连续拍摄大量汽车通过该点的照片。然后，你把这些照片叠在一起。如果所有汽车都严格按照车道线行驶，轨迹清晰，那么叠加后的图像会显示出两条清晰的“车辙印”，中间是空旷的“安全区域”。如果汽车行驶摇摆不定，轨迹混乱，那么叠加后的图像就会模糊不清，“安全区域”也会变小甚至消失。

**非破坏性眼图扫描 (NDES)** 就是 PHY 芯片内部的一种高级诊断功能，它允许我们在**不中断正常数据传输**的情况下，评估接收到的高速串行信号的质量。它的工作原理与上面的比喻非常相似：

1.  PHY 芯片的接收器内部有一个或多个采样器，它们在特定的时间点和电压阈值去判断接收到的信号是 ‘1’ 还是 ‘0’。
2.  NDES 功能通过微调这些采样器的时间偏移（水平方向）和电压阈值（垂直方向），在信号的“单位间隔 (UI)”内进行扫描。
3.  在每个扫描点（特定的时间和电压组合），PHY 会收集大量数据样本，并统计有多少样本“击中”了这个点，或者说，在这一点上发生了多少次“误判”（例如，信号本应是高电平，但在该采样点被判断为低电平）。
4.  将所有扫描点的统计结果（通常是“击中数”或“误码数”）绘制出来，就形成了一张二维的图形，这就是**眼图 (Eye Diagram)**。

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Eye_Pattern.svg/600px-Eye_Pattern.svg.png" width="400" alt="眼图示例"/>
（图片来源：维基百科）

上图就是一个典型的眼图。中间那个像眼睛一样的空白区域被称为“眼张开 (Eye Opening)”。
*   **“眼睛”睁得越大、越清晰**：表示信号质量越好，噪声和失真小，接收器有足够的余量来正确判决数据。
*   **“眼睛”越小、越模糊，甚至闭合**：表示信号质量差，噪声大，失真严重，链路很容易出错。

NDES 的“非破坏性”体现在它是在正常数据流仍在传输时进行的。PHY 会巧妙地利用一小部分内部资源来进行这些额外的采样和统计，而不会影响主要的数据恢复路径。这使得工程师可以在系统运行时实时监控信号完整性，诊断问题，并优化接收器性能。

我们的 PHY SDK 为 NDES 功能提供了 API，支持两种主要的扫描模式：
*   **1D NDES (一维扫描)**：通常是垂直扫描。它在时间轴上的一个固定点（通常是眼睛的中心）改变电压阈值进行扫描，得到一个垂直切面上的数据分布直方图。这可以快速评估信号的垂直眼张开（即噪声容限）。
*   **2D NDES (二维扫描)**：在时间和电压两个维度上都进行扫描，从而构建出完整的二维眼图。这能提供更全面的信号质量信息，包括时间抖动和垂直噪声。

## 核心概念解析

在深入代码之前，我们先来明确几个与 NDES 相关的核心概念：

1.  **眼图 (Eye Diagram)**:
    *   **是什么？** 通过在示波器上叠加许多数字信号的波形段而形成的图形。对于串行数据，通常取一个或几个单位间隔 (UI) 的长度来观察。它直观地显示了信号的时间和幅度特性，以及噪声和抖动的影响。
    *   **好比什么？** 前面提到的，高速公路上无数辆车驶过同一观察点留下的轨迹叠加图。

2.  **非破坏性 (Non-Destructive)**:
    *   **是什么？** 指在执行眼图扫描时，不会中断或显著影响正在进行的正常数据传输。
    *   **好比什么？** 交警在不影响交通的情况下，使用雷达枪测量车速，或者使用路边摄像头拍照。

3.  **扫描点 (Scan Point / Sampling Point)**:
    *   **是什么？** 在眼图的二维平面（时间 vs 电压）中，PHY 内部采样器进行采样的具体位置。NDES 通过移动这个扫描点来遍历整个眼图区域。
    *   **好比什么？** 拍摄高速公路照片时，相机对焦点在二维平面上的某个特定小方格。

4.  **命中数/误码数 (Hit Count / Error Count)**:
    *   **是什么？** 在一个特定的扫描点，PHY 统计到有多少个数据样本落入了这个点定义的“错误”区域（或者简单地说是被采样到的次数，取决于具体实现）。这个数值越大，通常表示在该点信号质量越差（或者该点是信号的密集过渡区）。
    *   **好比什么？** 在高速公路照片的某个小方格内，统计有多少辆车的轨迹压到了这个方格。

5.  **1D 扫描 (垂直扫描 - Vertical Scan)**:
    *   **是什么？** 在时间轴上固定一个点（通常是眼图的中心位置，即最佳采样时刻），然后在电压轴上从下往上（或从上往下）移动采样阈值进行扫描。
    *   **结果**：得到一个垂直方向上的“直方图”，显示了在最佳采样时刻信号电压的分布情况。
    *   **用途**：快速评估信号的垂直眼高（Voltage Margin）。

6.  **2D 扫描 (二维扫描 - Full Scan)**:
    *   **是什么？** 同时在时间轴（水平）和电压轴（垂直）上移动采样点进行扫描，覆盖整个眼图区域。
    *   **结果**：得到一个二维数组，其中每个元素代表对应扫描点的命中数/误码数，可以用来绘制出完整的眼图。
    *   **用途**：全面评估信号质量，包括眼高、眼宽（Timing Margin）、抖动等。

7.  **数据模式 (Data Mode - `data_mode`)**:
    *   **是什么？** 指定 NDES 从接收器数据路径的哪个阶段获取信号样本进行分析。常见的选项有：
        *   `NDES_DATA_MODE_ADC`: 从 ADC (模数转换器) 之后直接获取原始采样数据。
        *   `NDES_DATA_MODE_FFE`: 从 FFE (前馈均衡器) 之后获取数据，此时信号已经过初步的均衡处理。
        *   `NDES_DATA_MODE_EDFE`: 从更高级的均衡器 (如 eDFE - 增强型判决反馈均衡器) 之后获取数据，此时信号已得到更充分的补偿。
    *   **选择哪个？** 取决于你想观察哪个阶段的信号质量。ADC 模式看原始信号，FFE/eDFE 模式看均衡后的信号。

8.  **眼模式 (Eye Mode - `eye_mode`)**:
    *   **是什么？** 结合 `data_mode`，进一步定义了 NDES 的扫描范围和方式。例如：
        *   `NDES_EYE_MODE_FULL_EYE`: 扫描整个理论上的眼图区域。
        *   `NDES_EYE_MODE_INTERLEAVER_EYE` 或 `NDES_EYE_MODE_SAR_EYE`: 某些 PHY 内部可能有多个并行的采样器或子路径（如 Interleaver 或 SAR ADC 的不同比较器），这个模式允许选择性地扫描由特定子路径形成的“子眼图”。
    *   **用途**：用于更精细的诊断，例如判断是否是某个特定的内部采样路径存在问题。

9.  **步长 (Step - `v_step`, `h_step`)**:
    *   **是什么？** NDES 在电压轴（`v_step`，垂直步长）或时间轴（`h_step`，水平步长，仅用于2D）上移动扫描点的幅度。步长越小，扫描越精细，但耗时也越长。
    *   **好比什么？** 你拍照时，网格线的密度。密度越高，图像分辨率越高。

10. **分数阶延迟滤波器 (Fractional Delay Filter - FDF)**:
    *   **是什么？** 在2D NDES中，为了在时间轴上以非常精细的步长移动采样点，PHY 内部使用了一种数字滤波器（FDF）。通过改变 FDF 的系数，可以等效地微调采样时钟的相位，从而实现亚单位间隔 (sub-UI) 的时间扫描。
    *   **关键点**：`gfdf_filter` 数组（在 `ipname_sdk_ndes_2d.c` 中定义）存储了用于不同时间偏移的 FDF 系数组。

## 如何使用 NDES？—— SDK API 概览

`c_env` 项目的 PHY SDK 提供了一系列函数来执行 NDES。这些函数通常封装在 `ipname_sdk_ndes_1d.c` 和 `ipname_sdk_ndes_2d.c` 文件中，并依赖于 `ipname_sdk_ndes_derived.c` 中的一些底层实现（`ipname` 是具体 PHY 型号的占位符）。

核心的 API 函数是：
*   `int32_t ipname_sdk_ndes_1d(ipname_ndes_1d_in_t *cfg, ipname_ndes_1d_out_t *status)`: 执行一维（垂直）眼图扫描。
*   `int32_t ipname_sdk_ndes_2d(ipname_ndes_2d_in_t *cfg, ipname_ndes_2d_out_t *status)`: 执行二维（全）眼图扫描。

### 1. 输入参数结构体

调用这些函数时，你需要填充相应的输入结构体：`ipname_ndes_1d_in_t` 或 `ipname_ndes_2d_in_t`。

**对于 1D NDES (`ipname_ndes_1d_in_t`)**:
```c
typedef struct {
    uint32_t phy_base_addr; // PHY 的基地址
    uint8_t  lane_no;       // 要扫描的通道号 (0, 1, ...)
    uint8_t  sar_sel;       // SAR 选择 (具体含义取决于 PHY 架构, 通常是一个范围内的值)
    uint8_t  intl_sel;      // Interleaver 选择 (0 到 3)
    uint8_t  v_step;        // 垂直扫描步长 (0 到 5, 值越小步长越大)
    uint8_t  data_mode;     // 数据模式: NDES_DATA_MODE_ADC (0), NDES_DATA_MODE_FFE (1), NDES_DATA_MODE_EDFE (2)
    uint8_t  eye_mode;      // 眼模式: NDES_EYE_MODE_FULL_EYE (0), NDES_EYE_MODE_INTL_EYE (1), NDES_EYE_MODE_SAR_EYE (2)
} ipname_ndes_1d_in_t;
```

**对于 2D NDES (`ipname_ndes_2d_in_t`)**:
```c
typedef struct {
    uint32_t phy_base_addr; // PHY 的基地址
    uint8_t  lane_no;       // 要扫描的通道号
    uint8_t  sar_sel;       // SAR 选择 (通常用于选择采样数据的来源, 如 10-15)
    uint8_t  v_step;        // 垂直扫描步长 (0 到 5)
    uint8_t  h_step;        // 水平扫描步长 (1 到 4, 值越小步长越大)
} ipname_ndes_2d_in_t; 
// 注意：2D 扫描的 data_mode 和 eye_mode 通常是固定的 (例如，使用 eDFE 数据进行全眼扫描)
// 或者在 _ndes_2d_setup 内部硬编码。
```

### 2. 输出参数结构体

扫描结果会存放在输出结构体中：`ipname_ndes_1d_out_t` 或 `ipname_ndes_2d_out_t`。

**对于 1D NDES (`ipname_ndes_1d_out_t`)**:
```c
#define NDES_Y_LEVEL (64) // 定义了垂直方向上扫描的级别数 (例如，+/- 63 个级别)

typedef struct {
    uint32_t ndes_1d_array[NDES_Y_LEVEL * 2]; // 存储扫描结果的一维数组
                                              // 数组索引对应电压级别，值是该级别的命中数
                                              // 通常，中间的索引对应0电压，向两边扩展
    ipname_error_code error_code;             // 错误码
} ipname_ndes_1d_out_t;
```
*   `ndes_1d_array`: 这是一个大小为 `128` (即 `64*2`) 的数组。你可以把它想象成以 `NDES_Y_LEVEL - 1` (例如索引63) 为中心（代表0电压），向上和向下各扩展 `NDES_Y_LEVEL` 个级别。例如：
    *   `ndes_1d_array[63]` 是中心点（0电压）的命中数。
    *   `ndes_1d_array[62]` 是 +1 电压级别的命中数，`ndes_1d_array[0]` 是最高正电压级别的命中数。
    *   `ndes_1d_array[64]` 是 -1 电压级别的命中数，`ndes_1d_array[127]` 是最低负电压级别的命中数。
    （具体的索引到电压级别的映射关系请参考 SDK 文档或 `_read_ndes_1d_samples` 内部的存储逻辑。）

**对于 2D NDES (`ipname_ndes_2d_out_t`)**:
```c
#define NDES_X_COUNT (64) // 定义了水平方向上扫描的迭代次数 (时间点数)

typedef struct {
    uint32_t ndes_2d_array[NDES_X_COUNT][NDES_Y_LEVEL * 2]; // 存储扫描结果的二维数组
                                                           // 第一维是时间 (xiter), 第二维是电压 (level)
    double   baud_rate;    // 探测到的波特率 (用于校准时间轴)
    double   step;         // 水平扫描的等效时间步长 (单位：飞秒 fs)
    ipname_error_code error_code; // 错误码
} ipname_ndes_2d_out_t;
```
*   `ndes_2d_array`: 这是一个 `64x128` 的二维数组（如果 `NDES_X_COUNT` 和 `NDES_Y_LEVEL` 如上定义）。`ndes_2d_array[x][y]` 就代表了在时间点 `x` 和电压级别 `y` 的命中数。这个数组可以直接用来绘制眼图。

### 3. 示例：执行 1D NDES

```c
#include "ipname_sdk_ndes.h"  // 包含 NDES API
#include <stdio.h>            // 用于 printf
#include <string.h>           // 用于 memset

// 假设 phy_base_addr, target_lane_no 已定义
// extern uint32_t phy_base_addr;
// extern uint8_t  target_lane_no;

void run_1d_ndes_example() {
    ipname_ndes_1d_in_t ndes_1d_cfg;
    ipname_ndes_1d_out_t ndes_1d_status;
    int32_t result;

    // 1. 填充输入参数
    ndes_1d_cfg.phy_base_addr = phy_base_addr;
    ndes_1d_cfg.lane_no       = target_lane_no;
    ndes_1d_cfg.sar_sel       = 0;  // 示例值, 具体根据 PHY 文档选择
    ndes_1d_cfg.intl_sel      = 0;  // 示例值 (0-3)
    ndes_1d_cfg.v_step        = 2;  // 示例垂直步长 (0-5)
    ndes_1d_cfg.data_mode     = NDES_DATA_MODE_FFE; // 从 FFE 后获取数据
    ndes_1d_cfg.eye_mode      = NDES_EYE_MODE_FULL_EYE; // 扫描全眼

    printf("开始执行 1D NDES (通道 %u)...\n", ndes_1d_cfg.lane_no);

    // 2. 调用 1D NDES API
    result = ipname_sdk_ndes_1d(&ndes_1d_cfg, &ndes_1d_status);

    // 3. 检查结果
    if (result == 0 && ndes_1d_status.error_code == IPNAME_NO_ERROR) {
        printf("1D NDES 完成。\n");
        printf("垂直扫描结果 (部分示例 - 中心附近):\n");
        // NDES_Y_LEVEL 通常是 64
        // 中心点 (0电压) 附近的数据
        for (int level_offset = -3; level_offset <= 3; ++level_offset) {
            int array_index;
            if (level_offset >= 0) { // 正电压
                array_index = (NDES_Y_LEVEL - 1) - level_offset;
            } else { // 负电压
                array_index = (NDES_Y_LEVEL - 1) + (-level_offset);
            }
            // 确保索引在有效范围内
            if (array_index >= 0 && array_index < (NDES_Y_LEVEL * 2)) {
                 printf("  电压级别 (偏移) %d: 命中数 = %u\n", 
                        level_offset, 
                        ndes_1d_status.ndes_1d_array[array_index]);
            }
        }
        // 实际应用中，可以将 ndes_1d_status.ndes_1d_array 的数据导出或绘制成直方图
    } else {
        printf("1D NDES 失败。SDK 返回: %d, 内部错误码: %d\n", result, ndes_1d_status.error_code);
    }
}
```
**代码解释**：
1.  我们创建了 `ipname_ndes_1d_in_t` 和 `ipname_ndes_1d_out_t` 类型的变量。
2.  填充了 `ndes_1d_cfg` 的各个字段，包括 PHY 地址、通道号、扫描模式和参数。
3.  调用 `ipname_sdk_ndes_1d()` 函数。这个函数会阻塞执行，直到扫描完成。
4.  检查返回值和 `ndes_1d_status.error_code` 来判断是否成功。
5.  如果成功，`ndes_1d_status.ndes_1d_array` 中就包含了扫描结果。代码中简单打印了中心点附近几个电压级别的命中数。一个“健康”的1D扫描结果通常是在中心（0电压）附近有较低的命中数（代表眼张开），而在远离中心的高、低电压区域有较高的命中数（代表信号的稳定电平）。

**预期输出 (概念性)**:
```
开始执行 1D NDES (通道 0)...
1D NDES 完成。
垂直扫描结果 (部分示例 - 中心附近):
  电压级别 (偏移) -3: 命中数 = 1500 
  电压级别 (偏移) -2: 命中数 = 800
  电压级别 (偏移) -1: 命中数 = 100
  电压级别 (偏移) 0: 命中数 = 20   // 眼的中心，命中数应该很低
  电压级别 (偏移) 1: 命中数 = 110
  电压级别 (偏移) 2: 命中数 = 850
  电压级别 (偏移) 3: 命中数 = 1600 
```
(注意：上述命中数只是示意，实际值和分布会因信号质量而异。“命中数”的含义也可能随PHY和扫描模式不同，有时低命中数代表好的区域，有时高命中数代表稳定电平。)

### 4. 示例：执行 2D NDES

```c
#include "ipname_sdk_ndes.h"
#include <stdio.h>
#include <string.h>

// extern uint32_t phy_base_addr;
// extern uint8_t  target_lane_no;

void run_2d_ndes_example() {
    ipname_ndes_2d_in_t ndes_2d_cfg;
    ipname_ndes_2d_out_t ndes_2d_status;
    int32_t result;

    // 1. 填充输入参数
    ndes_2d_cfg.phy_base_addr = phy_base_addr;
    ndes_2d_cfg.lane_no       = target_lane_no;
    ndes_2d_cfg.sar_sel       = 10; // 示例值, 2D扫描通常用一个固定范围的SAR选择
    ndes_2d_cfg.v_step        = 2;  // 示例垂直步长
    ndes_2d_cfg.h_step        = 1;  // 示例水平步长 (1表示最精细)

    printf("开始执行 2D NDES (通道 %u)...\n", ndes_2d_cfg.lane_no);

    // 2. 调用 2D NDES API
    result = ipname_sdk_ndes_2d(&ndes_2d_cfg, &ndes_2d_status);

    // 3. 检查结果
    if (result == 0 && ndes_2d_status.error_code == IPNAME_NO_ERROR) {
        printf("2D NDES 完成。\n");
        printf("  波特率: %.4f ps/UI\n", ndes_2d_status.baud_rate);
        printf("  水平步长: %.4f fs\n", ndes_2d_status.step);
        
        // 打印眼图中心点 (时间中心 x=31, 电压中心 y=63) 的命中数
        // NDES_X_COUNT 通常是 64, NDES_Y_LEVEL 通常是 64
        int time_center_idx = NDES_X_COUNT / 2 -1; // 对应 xiter=31 (0-63)
        int voltage_center_idx = NDES_Y_LEVEL -1;  // 对应0电压
        
        printf("  眼图中心点 (时间索引 %d, 电压索引 %d) 命中数: %u\n",
               time_center_idx, voltage_center_idx,
               ndes_2d_status.ndes_2d_array[time_center_idx][voltage_center_idx]);
        
        // 实际应用中，可以将 ndes_2d_status.ndes_2d_array 绘制成热力图或等高线图来可视化眼图
        #ifdef IPNAME_SDK_DEBUG_LOG // 如果开启了调试日志
            printf("  数据已保存到 sdk_2d_eye_scan_histogram_lane_no_%d.csv\n", ndes_2d_cfg.lane_no);
        #endif

    } else {
        printf("2D NDES 失败。SDK 返回: %d, 内部错误码: %d\n", result, ndes_2d_status.error_code);
    }
}
```
**代码解释**：
1.  与 1D 扫描类似，填充 `ipname_ndes_2d_in_t` 结构体，但这里需要额外指定 `h_step` (水平步长)。
2.  调用 `ipname_sdk_ndes_2d()`。这个函数同样会阻塞直到扫描完成。
3.  检查结果。如果成功，`ndes_2d_status.ndes_2d_array` 中包含了完整的二维眼图数据。`ndes_2d_status.baud_rate` 和 `ndes_2d_status.step` 提供了用于校准时间轴的信息。
4.  代码中简单打印了眼图中心点的命中数。一个“张开”的眼睛，其中心区域的命中数应该非常低。
5.  SDK 内部（如果启用了 `IPNAME_SDK_DEBUG_LOG`）通常会将扫描数据保存到 CSV 文件中，方便后续使用 Python、MATLAB 等工具进行绘图和分析。

## 深入幕后：NDES 是如何工作的？

当我们调用 `ipname_sdk_ndes_1d()` 或 `ipname_sdk_ndes_2d()` 时，SDK 内部会精确地配置 PHY 硬件的多个寄存器，并协调整个扫描和数据读取过程。

### 流程概览 (以 1D NDES 为例)

1.  **参数校验 (`_ndes_1d_validate_input`)**: SDK 首先检查用户传入的 `cfg` 参数（如通道号、步长、模式等）是否在有效范围内。
2.  **NDES 初始化设置 (`_ndes_1d_setup`)**:
    *   **配置数据源和时钟**:
        *   设置 `RX__RXS_CFG2__DBGDATA_MUX_CG_EN = 1` 来旁路某些时钟门控，确保 NDES 模块所需的时钟是开启的。
        *   根据 `cfg->data_mode` (ADC/FFE/eDFE) 设置 `RX__DFT10__DEBUG_MODE` 寄存器，选择从数据路径的哪个点抓取信号样本。
    *   **配置 NDES 控制寄存器 (`PMD_LANE_RX__EYE_SCAN0__ADDR`)**:
        *   `NDES_CLK_EN = 1`: 使能 NDES 模块的时钟。
        *   `NDES_SAR_SEL = cfg->sar_sel`: 设置 SAR 选择。
        *   `NDES_INTL_SEL = cfg->intl_sel`: 设置 Interleaver 选择。
        *   `NDES_STEP = cfg->v_step`: 设置垂直扫描的步长。
        *   `NDES_MODE = ((cfg->eye_mode << 2) | cfg->data_mode)`: 将用户指定的 `eye_mode` 和 `data_mode` 组合成硬件寄存器所需的模式值。
        *   `NDES_FDF_EN = NDES_FDF_EN_1D` (对于1D通常为0或固定值，2D时会启用FDF)。
    *   **配置扫描定时器 (`PMD_LANE_RX__EYE_SCAN1__ADDR`)**:
        *   `NDES_REF_TIMER = NDES_REF_TIMER_1D`: 设置在每个垂直扫描点停留多长时间来收集样本。这个值越大，收集的样本越多，结果越准确，但扫描也越慢。
3.  **执行扫描并读取样本 (`_read_ndes_1d_samples`)**:
    *   **使能 NDES 引擎**: 调用 `ipname_sdk_enable_eye_scan(phy_base_addr, lane_no, true)`。这个函数会：
        *   设置 `PMD_LANE_RX__RX_LANE_CFG0__DBG_RETIME_FIFO_EN = 1` (使能用于收集样本的重定时 FIFO)。
        *   如果 NDES 已经在运行，先禁用它 (`PMD_LANE_RX__EYE_SCAN0__NDES_EN = 0`)。
        *   正式使能 NDES (`PMD_LANE_RX__EYE_SCAN0__NDES_EN = 1`)。
    *   **轮询与数据读取循环**:
        *   硬件开始在第一个电压级别进行采样和计数。
        *   SDK 进入一个循环，直到 PHY 硬件通过 `PMD_LANE_RX__EYE_SCAN3__NDES_DONE` 状态位指示整个垂直扫描完成。
        *   **在循环的每一次迭代中 (对应一个垂直电压级别的数据收集)**:
            1.  **请求数据**: 设置 `PMD_LANE_RX__EYE_SCAN0__NDES_READ_EN = 1`，通知硬件准备好了一个级别的数据，可以读取了。
            2.  **等待数据就绪**: 轮询 `PMD_LANE_RX__EYE_SCAN3__NDES_DATA_READY` 状态位，直到它变为1。这表示硬件已经将当前电压级别的扫描结果（级别值和命中数）准备好了。SDK 使用 `ipname_wait_flag_timeout` 来实现带超时的等待。
            3.  **读取结果**:
                *   从 `PMD_LANE_RX__EYE_SCAN3__NDES_LEVEL` 读取当前的电压级别值。
                *   从 `PMD_LANE_RX__EYE_SCAN2__NDES_COUNT` 读取在该电压级别的命中数。
            4.  **存储结果**: 将读取到的命中数存入 `status->ndes_1d_array` 中对应电压级别的位置。代码中会根据 `ndes_level` 的值（正负）将其映射到数组索引。
            5.  **清除请求**: 设置 `PMD_LANE_RX__EYE_SCAN0__NDES_READ_EN = 0`，准备下一次迭代。
            6.  **检查完成标志**: 再次读取 `PMD_LANE_RX__EYE_SCAN3__NDES_DONE`，如果为1则退出循环。
    *   **禁用 NDES 引擎**: 扫描完成后，调用 `ipname_sdk_enable_eye_scan(phy_base_addr, lane_no, false)` 来禁用 NDES，并恢复 `DBG_RETIME_FIFO_EN`。
4.  **返回结果**: 将填充好的 `status` 结构体返回给调用者。

**对于 2D NDES**，流程更为复杂：
*   `_ndes_2d_setup` 的配置与 1D 类似，但 `NDES_MODE` 会设为 2D 模式，并且 `NDES_FDF_EN` 会被启用。
*   `ipname_sdk_ndes_2d` 函数外层会有一个循环，遍历所有的时间偏移（水平扫描点，由 `cfg->h_step` 控制，从 `j = 0` 到 `NDES_X_COUNT-1`）。
*   在每个时间偏移点 `j`：
    *   会调用 `_program_2d_fdf_filter_coeff(cfg, j)` 来设置 FDF 滤波器的系数。`gfdf_filter[j]` 数组提供了对应时间点 `j` 的11个抽头系数，这些系数被写入到 `EYE_SCAN4`, `EYE_SCAN5`, `EYE_SCAN6` 寄存器中。这相当于在时间上精确地“移动”了采样器。
    *   然后，调用 `_read_ndes_2d_samples(cfg, status, j)`。这个函数内部的逻辑与 `_read_ndes_1d_samples` 非常相似（使能NDES，循环读取每个垂直级别的数据），只是它会将结果存入 `status->ndes_2d_array[j][电压级别索引]`。
*   所有时间点都扫描完毕后，2D NDES 完成。SDK 还会调用 `_read_ndes_2d_baud_rate` 从 PHY 寄存器（如 `PMD_RX_OVRDVAL2__RXX_RATE_I`）读取当前的线路速率，用于计算眼图的时间轴刻度。

### 简化版序列图 (1D NDES)

```mermaid
sequenceDiagram
    participant 用户代码
    participant NDES_1D_SDK as "SdkNdes1D"
    participant 内部NDES设置 as "SdkNdesSetup"
    participant 内部NDES读取 as "SdkNdesReadLoop"
    participant PHY硬件 (寄存器)

    用户代码->>SdkNdes1D: ipname_sdk_ndes_1d(cfg, status)
    SdkNdes1D->>SdkNdesSetup: _ndes_1d_setup(cfg)
    Note over SdkNdesSetup, PHY硬件 (寄存器): SDK通过asr()写入EYE_SCAN0, EYE_SCAN1等配置寄存器
    SdkNdes1D->>SdkNdesReadLoop: _read_ndes_1d_samples(cfg, status)
    SdkNdesReadLoop->>PHY硬件 (寄存器): 通过asr()设置NDES_EN=1 (使能扫描)
    loop 直到 NDES_DONE 状态位为1
        SdkNdesReadLoop->>PHY硬件 (寄存器): 通过asr()设置NDES_READ_EN=1 (请求数据)
        SdkNdesReadLoop->>PHY硬件 (寄存器): 通过agr()轮询NDES_DATA_READY状态位
        Note over SdkNdesReadLoop, PHY硬件 (寄存器): SDK通过agr()读取EYE_SCAN3 (NDES_LEVEL), EYE_SCAN2 (NDES_COUNT)
        SdkNdesReadLoop-->>SdkNdesReadLoop: 将NDES_COUNT存入status->ndes_1d_array
        SdkNdesReadLoop->>PHY硬件 (寄存器): 通过asr()设置NDES_READ_EN=0
        SdkNdesReadLoop->>PHY硬件 (寄存器): 通过agr()读取NDES_DONE状态位
    end
    SdkNdesReadLoop->>PHY硬件 (寄存器): 通过asr()设置NDES_EN=0 (禁用扫描)
    SdkNdes1D-->>用户代码: 返回status (包含扫描结果)
end
```

### 代码实现片段解析

我们来看一下 SDK 源码中几个关键函数的简化片段，以更好地理解它们是如何操作硬件的。

1.  **`ipname_sdk_enable_eye_scan()` (使能/禁用 NDES 引擎)**
    (位于 `ipname_sdk_ndes_derived.c`，对 x812 和 x814 PHY 通用)

    ```c
    // (假设用于 x812 PHY)
    // 文件: sdk_api/design/hw/x812_rel2p1/ipname_sdk_ndes_derived.c
    void ipname_sdk_enable_eye_scan(uint32_t phy_base_addr, uint8_t lane_no, bool enable)
    {    
        uint32_t reg_val;
        uint32_t setting =  enable ? 0x1 :0x0; 
    
        // 使能/禁用重定时FIFO (用于收集样本)
        reg_val = ipname_sdk_reg_read(phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__RX_LANE_CFG0__ADDR);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__RX_LANE_CFG0__DBG_RETIME_FIFO_EN,setting);
        ipname_sdk_reg_write((phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__RX_LANE_CFG0__ADDR), reg_val);

        // 读取 NDES 控制寄存器
        reg_val = ipname_sdk_reg_read(phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR);
        if(enable)
        {
            // 如果要使能，并且 NDES 可能已经在运行，则先禁用它一下
            IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_EN,0);
            ipname_sdk_reg_write((phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR), reg_val);
        }
        // 设置 NDES_EN 位 (0 或 1)
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_EN,setting);
        ipname_sdk_reg_write((phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR), reg_val);
        // IPNAME_DEBUG_INFO("\n [%s]:: Setting NDES_EN = %d \n",__func__, setting);
    }
    ```
    **代码解释**:
    *   此函数通过读写 `PMD_LANE_RX__RX_LANE_CFG0__ADDR` 和 `PMD_LANE_RX__EYE_SCAN0__ADDR` 寄存器来控制 NDES 的总开关。
    *   `DBG_RETIME_FIFO_EN` 位用于使能一个内部 FIFO，该 FIFO 用于暂存 NDES 过程中收集到的信号样本。
    *   `NDES_EN` 位是 NDES 引擎的主使能位。在使能前，代码会先尝试禁用一次，以确保从一个干净的状态开始。
    *   这里的 `ipname_sdk_reg_read` 和 `ipname_sdk_reg_write` 是 SDK 提供的寄存器访问函数，它们内部会调用我们在 [第 2 章：寄存器访问抽象层](02_寄存器访问抽象层_.md) 中学习的 `agr()` 和 `asr()` 函数。

2.  **`_ndes_1d_setup()` (1D NDES 初始化配置)**
    (位于 `ipname_sdk_ndes_1d.c` 或 `ipname_sdk_ndes_derived.c`，具体PHY型号文件)

    ```c
    // (假设用于 x812 PHY)
    // 文件: sdk_api/design/hw/x812_rel2p1/ipname_sdk_ndes_derived.c
    // 注意：在 x814 SDK 中，这个函数可能在 ipname_sdk_ndes_1d.c 中
    void _ndes_1d_setup(ipname_ndes_1d_in_t *cfg)
    {
        uint32_t reg_val;
        // 将 eye_mode 和 data_mode 组合成硬件寄存器使用的 ndes_mode 值
        uint8_t  ndes_mode      = ((cfg->eye_mode << 2) | cfg->data_mode);

        // ... (配置 RXS_CFG2 和 DFT10 寄存器以选择数据源和旁路时钟门控 - 如流程概览中所述) ...

        // 读取 NDES 控制寄存器 EYE_SCAN0
        reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_CLK_EN, 0x1); // 使能 NDES 时钟
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_SAR_SEL, cfg->sar_sel);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_INTL_SEL, cfg->intl_sel);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_STEP, cfg->v_step); // 垂直步长
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_MODE, ndes_mode);   // 扫描模式
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_FDF_EN, NDES_FDF_EN_1D); // 1D扫描通常不使用FDF
        ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR), reg_val);

        // 配置 NDES 定时器寄存器 EYE_SCAN1
        reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN1__ADDR);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN1__NDES_REF_TIMER, NDES_REF_TIMER_1D); // 每个点采样时长
        ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN1__ADDR), reg_val);
    }
    ```
    **代码解释**:
    *   这个函数负责在 NDES 扫描开始前，对 PHY 的 NDES 相关控制寄存器（主要是 `EYE_SCAN0` 和 `EYE_SCAN1`）进行全面的配置。
    *   它将用户通过 `cfg` 结构传入的参数（如步长、模式选择）写入到寄存器的相应位域。
    *   `NDES_FDF_EN_1D` 和 `NDES_REF_TIMER_1D` 是预定义的宏，代表 1D 扫描时 FDF 使能状态和参考定时器的默认值。

3.  **`_read_ndes_1d_samples()` (1D NDES 核心扫描循环)**
    (位于 `ipname_sdk_ndes_derived.c`)

    ```c
    // (假设用于 x812 PHY)
    // 文件: sdk_api/design/hw/x812_rel2p1/ipname_sdk_ndes_derived.c
    ipname_error_code _read_ndes_1d_samples(ipname_ndes_1d_in_t *cfg, ipname_ndes_1d_out_t *status)
    {
        uint32_t reg_val;
        uint8_t  ndes_done  = 0;
        int16_t  ndes_level = 0; // 从硬件读出的当前电压级别
        // uint64_t ndes_time_marker; // 用于超时检测
        ipname_error_code result = IPNAME_NO_ERROR;
        
        ipname_sdk_enable_eye_scan(cfg->phy_base_addr , cfg->lane_no, true); // 使能NDES引擎
          
        // 读取 EYE_SCAN3 寄存器，获取 NDES_DONE 初始状态
        reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN3__ADDR);
        ndes_done = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN3__NDES_DONE);
        // ndes_time_marker = ipname_mark_timeout_start(); // 启动超时计时器

        while(ndes_done == 0 && (IPNAME_NO_ERROR == result))
        {
            // if( ipname_period_elapsed(ndes_time_marker, NDES_TIMEOUT_DURATION) ) { /* 超时处理 */ }

            // 1. 请求硬件读取下一个数据点 (NDES_READ_EN = 1)
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR);
            IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_READ_EN, 0x1);
            ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR), reg_val);

            // 2. 等待硬件准备好数据 (NDES_DATA_READY = 1)
            //    ipname_wait_flag_timeout 会轮询 EYE_SCAN3 寄存器的 NDES_DATA_READY 位
            if( 0 != ipname_wait_flag_timeout( (cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN3__ADDR),
                                             PMD_LANE_RX__EYE_SCAN3__NDES_DATA_READY__MASK, // 要检查的位掩码
                                             PMD_LANE_RX__EYE_SCAN3__NDES_DATA_READY__MASK, // 期望值 (位为1)
                                             START_NDES_TIMEOUT_SEC * MS_IN_SECONDS ) ) // 超时时长
            {
                result = IPNAME_SDK_LOOP_TIME_OUT; /* 超时错误 */ break;
            }
            
            // 3. 读取数据 (NDES_LEVEL 和 NDES_COUNT)
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN3__ADDR);
            ndes_level = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN3__NDES_LEVEL);
            
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN2__ADDR);
            uint32_t ndes_count_value = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN2__NDES_COUNT);

            // 4. 将 NDES_COUNT 存入结果数组 (根据 ndes_level 映射到索引)
            if(ndes_count_value != 0) {
                if(ndes_level >= (NDES_Y_LEVEL)) { // 负电压级别
                    int mapped_level = (NDES_Y_LEVEL*2) - ndes_level; // 硬件level值可能从0到127，其中高值代表负电压
                    status->ndes_1d_array[NDES_Y_LEVEL-1+mapped_level] = ndes_count_value;
                } else { // 正电压级别 (包括0)
                    status->ndes_1d_array[NDES_Y_LEVEL-ndes_level-1] = ndes_count_value;
                }
            }
            
            // 5. 再次读取 NDES_DONE 标志，看整个扫描是否已完成
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN3__ADDR);
            ndes_done = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN3__NDES_DONE);

            // 6. 清除读取请求 (NDES_READ_EN = 0)
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR);
            IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN0__NDES_READ_EN, 0x0);
            ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN0__ADDR), reg_val);
        } // 结束 while 循环

        ipname_sdk_enable_eye_scan(cfg->phy_base_addr , cfg->lane_no, false); // 禁用NDES引擎
        return result;
    }
    ```
    **代码解释**:
    *   这个函数是 NDES 的核心。它首先使能 NDES 引擎。
    *   然后进入一个 `while` 循环，该循环会一直执行，直到硬件通过 `NDES_DONE` 标志位通知整个垂直扫描完成。
    *   在每次循环中，它通过 `NDES_READ_EN` 位与硬件进行“握手”：先置1请求数据，然后等待 `NDES_DATA_READY` 位变为1，表示硬件已准备好一个数据点（一个电压级别 `NDES_LEVEL` 及其对应的命中数 `NDES_COUNT`）。
    *   读取到数据后，它会根据 `ndes_level`（硬件报告的级别值）将其转换为数组索引，并将 `NDES_COUNT` 存入 `status->ndes_1d_array`。硬件通常会从一个极端电压开始，逐步扫向另一个极端电压，每次硬件内部完成一个电压级别的采样和计数后，就会通过 `NDES_DATA_READY` 通知软件来取走数据。
    *   最后，清除 `NDES_READ_EN` 并检查 `NDES_DONE`。
    *   整个扫描完成后，禁用 NDES 引擎。

4.  **2D NDES 中的 FDF 系数配置 (`_program_2d_fdf_filter_coeff`)**
    (位于 `ipname_sdk_ndes_derived.c` 或 `ipname_sdk_ndes_2d.c`)

    ```c
    // (假设用于 x812 PHY)
    // 文件: sdk_api/design/hw/x812_rel2p1/ipname_sdk_ndes_derived.c
    // 注意：在 x814 SDK 中，这个函数可能在 ipname_sdk_ndes_2d.c 中
    void _program_2d_fdf_filter_coeff(ipname_ndes_2d_in_t *cfg, int16_t xiter)
    {
        uint8_t idx;
        uint32_t reg_val;
        // gfdf_filter 是一个二维数组，存储了不同时间偏移 (xiter) 下的11个FDF抽头系数
        // extern int8_t  gfdf_filter[NDES_X_COUNT][FDF_TAB_COUNT]; 
        
        // IPNAME_DEBUG_INFO("\n IPNAME_SDK::[%s] Setting NDES_FDF_COEFF (x=%0d):\n", __func__, xiter);
        // for(idx=0; idx< (FDF_TAB_COUNT-1); idx++) { /* 打印系数 */ }

        // 将 gfdf_filter[xiter] 中的11个系数写入到 EYE_SCAN4, EYE_SCAN5, EYE_SCAN6 寄存器
        idx=0;
        reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN4__ADDR);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN4__NDES_FDF_COEFF_0, gfdf_filter[xiter][idx++]);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN4__NDES_FDF_COEFF_1, gfdf_filter[xiter][idx++]);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN4__NDES_FDF_COEFF_2, gfdf_filter[xiter][idx++]);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN4__NDES_FDF_COEFF_3, gfdf_filter[xiter][idx++]);
        ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN4__ADDR), reg_val);

        // 写入 EYE_SCAN5 寄存器 (系数 4 到 7)
        reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN5__ADDR);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN5__NDES_FDF_COEFF_4, gfdf_filter[xiter][idx++]);
        // ... 设置系数 5, 6, 7 ...
        ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN5__ADDR), reg_val);

        // 写入 EYE_SCAN6 寄存器 (系数 8 到 10)
        reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN6__ADDR);
        IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__EYE_SCAN6__NDES_FDF_COEFF_8, gfdf_filter[xiter][idx++]);
        // ... 设置系数 9, 10 ...
        ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__EYE_SCAN6__ADDR), reg_val);   
    }
    ```
    **代码解释**:
    *   在2D NDES中，每次要扫描一个新的时间点（由 `xiter` 参数指定，它代表从 `gfdf_filter` 数组中选择哪一组FDF系数），SDK都会调用这个函数。
    *   `gfdf_filter` 是一个预先定义好的二维数组，存储了 `NDES_X_COUNT` (例如64) 组FDF系数，每组包含 `FDF_TAB_COUNT` (例如11) 个抽头系数。每一组系数对应一个微小的时间偏移。
    *   函数将 `gfdf_filter[xiter]` 这一行（11个系数）的值，依次写入到 PHY 的 `EYE_SCAN4`、`EYE_SCAN5` 和 `EYE_SCAN6` 寄存器中专门用于 FDF 系数的位域。
    *   通过改变这些FDF系数，PHY内部的采样时钟相位会发生微小的变化，从而等效地在时间轴上移动了采样点，实现了水平方向的扫描。这就是为什么2D NDES能够捕捉到眼图的时间维度信息。

## 总结与展望

在本章中，我们一起探索了“非破坏性眼图扫描 (NDES)”这一强大的 PHY 诊断功能。我们学习到：
*   NDES 允许我们在不中断数据传输的情况下，评估接收信号的质量，就像给高速信号拍一张“健康快照”。
*   核心概念包括眼图本身、1D（垂直）扫描和 2D（全）扫描的区别、扫描点、命中数，以及与扫描配置相关的参数如数据模式、眼模式和步长。2D扫描中还用到了分数阶延迟滤波器 (FDF) 来实现精细的时间轴扫描。
*   如何使用 `c_env` 的 PHY SDK API（主要是 `ipname_sdk_ndes_1d` 和 `ipname_sdk_ndes_2d` 函数）来启动扫描并获取结果。我们了解了输入和输出数据结构，并通过示例代码演示了基本用法。
*   NDES 的内部工作流程：SDK 如何通过配置 PHY 的控制寄存器（如 `EYE_SCAN0` 到 `EYE_SCAN6`）来初始化扫描参数、使能 NDES 引擎、并通过“握手”方式（`NDES_READ_EN` 和 `NDES_DATA_READY`）从硬件读取每个扫描点的电压级别和命中数，最终构建出1D直方图或2D眼图数据。

NDES 是诊断高速串行链路信号完整性问题、优化接收器性能的重要工具。通过分析 NDES 的结果，工程师可以判断链路是否存在过多的噪声、抖动或码间干扰，并据此调整均衡设置或排查硬件问题。

到这里，我们 `c_env` 项目的入门教程系列就全部结束了！回顾一下，我们从最基础的 [项目/设备定义与管理](01_项目_设备定义与管理_.md) 开始，学习了如何通过 [寄存器访问抽象层](02_寄存器访问抽象层_.md) 与硬件对话，如何进行 [时钟源配置](03_时钟源配置_.md) 和 [硬件初始化与 Preamble 加载](04_硬件初始化与_preamble_加载_.md) 来为 PHY 的运行做好准备。接着，我们探索了功能强大的 [PHY SDK API](05_phy_sdk_api_.md)，学会了如何通过它来控制 PHY 的高级功能，并了解了关键的自动化过程如 [自适应协商 (Auto-Negotiation)](06_自适应协商__auto_negotiation__.md)。最后，我们还学习了如何使用 NDES 来诊断信号质量。

希望这个系列教程能帮助你对 `c_env` 项目的结构和核心功能有一个初步的理解。虽然我们只触及了冰山一角，但这些基础知识为你进一步深入探索和使用 `c_env` 项目进行更复杂的硬件开发与测试工作打下了坚实的基础。

感谢你的学习！祝你在 `c_env` 项目的探索之路上一切顺利！

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)