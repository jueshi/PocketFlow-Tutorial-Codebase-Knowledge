# Chapter 5: PHY SDK API


在上一章 [第 4 章：硬件初始化与 Preamble 加载](04_硬件初始化与_preamble_加载_.md) 中，我们学习了如何通过加载固件和执行 Preamble 脚本来“唤醒”PHY 芯片，使其进入一个基本的就绪状态。现在，我们的 PHY 已经准备好接受更具体的指令了。但是，直接操作 PHY 内部成百上千的寄存器来配置复杂的功能，比如调整信号质量（均衡）、进行诊断测试，或者管理电源状态，是一项非常繁琐且容易出错的任务。这就像试图通过直接操作发动机的每一个阀门和活塞来驾驶汽车一样，不仅困难，而且需要极深的专业知识。

为了解决这个问题，我们引入了 **PHY SDK API**。

## 什么是 PHY SDK API？—— PHY 的“高级驾驶辅助系统”

PHY SDK API（软件开发工具包应用程序接口）是一套专门为我们项目中使用的特定 PHY 芯片（在代码中通常称为 `ipname`，代表具体的 IP 型号）设计的 C 语言函数库。你可以把它想象成专为高级跑车设计的仪表盘和智能控制系统。

**核心目的：简化复杂操作，提供稳定接口**

这个 SDK 的主要目标是：

1.  **抽象化 (Abstraction)**：将底层复杂的寄存器读写操作封装成一个个功能明确、易于理解的函数。例如，你可能只需要调用一个函数 `ipname_sdk_set_tx_equalization(...)` 来设置发送端的均衡参数，而不需要知道具体要操作哪些寄存器以及如何计算这些寄存器的值。
2.  **易用性 (Ease of Use)**：提供清晰、一致的函数接口，让开发者可以像调用普通函数一样来控制 PHY 的高级功能。
3.  **稳定性 (Stability)**：即使 PHY 硬件的内部寄存器细节在不同版本之间有所变化，SDK API 也会尽量保持稳定，减少上层应用程序的修改工作。
4.  **功能覆盖 (Function Coverage)**：提供对 PHY 关键功能的控制，例如：
    *   **电源管理**：控制 PHY 不同部分的功耗状态。
    *   **时钟转发 (Clock Forwarding)**：在 retimer 模式下配置时钟的来源和路由。
    *   **频率测量 (Frequency Measurement)**：测量内部时钟频率。
    *   **发送均衡 (TX Equalization)**：调整发送信号的波形，以补偿信道损耗。
    *   **接收器配置 (Receiver Configuration)**：设置接收端的参数。
    *   **误码率测试 (BER Testing)**：进行数据传输质量的测试。
    *   **校准码读取 (Calibration Code Read)**：读取 PHY 内部自校准后的结果。
    *   **自适应状态读取 (Adaptation Code Read)**：读取接收端自适应均衡后的状态。

**打个比方：**

*   **直接操作寄存器**：就像手动调整汽车引擎的点火时序、燃油喷射量、气门间隙。你需要非常了解引擎的内部构造。
*   **使用 PHY SDK API**：就像踩油门、转动方向盘、按下“运动模式”按钮。你只需要知道你想让车做什么（加速、转向、改变驾驶模式），而不需要关心引擎内部是如何响应的。SDK API 就是你和 PHY 之间的高级交互界面。

## 如何使用 PHY SDK API？—— 以配置发送均衡 (TX Equalization) 为例

让我们来看一个具体的例子：如何使用 SDK API 来配置 PHY 发送端（TX）的均衡参数。发送均衡对于高速串行通信非常重要，它通过调整发送信号的形状（预加重、去加重）来克服信号在传输路径（如 PCB 走线、连接器）上的衰减和失真，确保接收端能正确恢复数据。

配置 TX 均衡通常涉及到设置多个“抽头”(Tap) 的系数，包括主抽头 (Main Cursor)、前向抽头 (Pre-cursors) 和后向抽头 (Post-cursors)。直接操作寄存器需要精确计算并写入多个寄存器位域。而使用 SDK API，这个过程会简单得多。

### 1. 包含必要的头文件

首先，你需要包含 SDK 的主头文件和与 TX 均衡相关的特定头文件。

```c
#include "ipname_sdk_apis.h"         // SDK 主头文件 (可能已包含其他必要文件)
#include "ipname_sdk_tx_equalization.h" // TX 均衡相关的 API 定义
#include "ipname_sdk_platform.h"     // 平台相关的定义 (例如寄存器读写函数)
#include "ipname_sdk_poll_states.h" // 轮询状态定义
#include <stdio.h>                // 用于 printf 打印信息
```

### 2. 准备配置参数

大多数 SDK 函数需要一个配置结构体作为输入参数。对于 TX 均衡，我们需要填充 `ipname_tx_eq_cfg_t` 结构体。

```c
// 定义配置结构体变量
ipname_tx_eq_cfg_t tx_eq_config;
ipname_poll_states_t poll_state; // 用于异步操作的状态变量

// 假设 phy_base_addr 变量已经包含了目标 PHY 的基地址
// 假设 target_lane_no 是我们要配置的通道号 (例如 0)
tx_eq_config.phy_base_addr = phy_base_addr;
tx_eq_config.lane_no = target_lane_no;

// 设置均衡系数 (这些值只是示例，实际值需要根据链路特性确定)
tx_eq_config.eq_main = 30;  // 主抽头系数 (幅度)
tx_eq_config.eq_pre1 = -2;  // 第一个前向抽头系数
tx_eq_config.eq_pre2 = 1;   // 第二个前向抽头系数
tx_eq_config.eq_post1 = -5; // 第一个后向抽头系数
tx_eq_config.eq_post2 = 2;  // 第二个后向抽头系数
// 根据 PHY 型号 (如 x812 或 x814)，可能还有更多抽头 (pre3, pre4 等)
// tx_eq_config.eq_pre3 = ...;
// tx_eq_config.eq_pre4 = ...;

printf("准备配置通道 %d 的 TX 均衡...\n", tx_eq_config.lane_no);
```
**代码解释**：
*   我们创建了 `ipname_tx_eq_cfg_t` 类型的变量 `tx_eq_config` 和 `ipname_poll_states_t` 类型的变量 `poll_state`。
*   `phy_base_addr`: 这是 PHY 寄存器空间的基地址，SDK 函数需要知道去哪里访问寄存器。这个地址通常在系统初始化时确定。
*   `lane_no`: 指定要配置哪一个物理通道（Lane）。
*   `eq_main`, `eq_pre1`, `eq_pre2`, `eq_post1`, `eq_post2`, ...: 这些字段用于设置 FFE (Feed-Forward Equalizer) 滤波器的各个抽头系数。正值通常表示增强，负值表示减弱（相对于主抽头）。

### 3. 调用 SDK API 函数启动配置

配置 TX 均衡通常不是瞬间完成的，硬件内部可能需要一些时间来应用这些设置。因此，SDK 提供了“启动 (start)”和“轮询 (poll)”两种函数。

```c
// 调用启动函数，开始配置 TX 均衡
ipname_error_code result = ipname_sdk_tx_equalization_start(&tx_eq_config, &poll_state);

if (result != IPNAME_NO_ERROR) {
    printf("启动 TX 均衡配置失败，错误码: %d\n", result);
    // 处理错误...
} else {
    printf("TX 均衡配置已启动，等待完成...\n");
}
```
**代码解释**：
*   `ipname_sdk_tx_equalization_start(&tx_eq_config, &poll_state)`：这个函数会接收我们准备好的配置参数，并开始执行配置序列（即向 PHY 写入相应的寄存器值）。它通常会立即返回，表示配置过程已经启动。
*   `poll_state`: 这个变量用于存储异步操作的内部状态，在后续的轮询调用中会用到。
*   返回值 `result`: 用于检查启动操作是否成功。`IPNAME_NO_ERROR` (通常为 0) 表示成功。

### 4. 轮询等待配置完成

由于硬件应用配置需要时间，我们需要调用轮询函数来检查配置是否完成。

```c
// 轮询等待完成 (简化示例，实际应用中可能有超时机制)
while (result == IPNAME_NO_ERROR) {
    result = ipname_sdk_tx_equalization_poll(&tx_eq_config, &poll_state);
    if (result == IPNAME_ERROR_NOT_READY) {
        // 操作尚未完成，继续轮询 (可以加延时避免过于频繁的查询)
        // ipname_sdk_plat_usleep(100); // 示例：等待 100 微秒
        result = IPNAME_NO_ERROR; // 重置 result 以便继续循环
        continue;
    } else if (result != IPNAME_NO_ERROR) {
        // 轮询过程中发生错误
        printf("TX 均衡配置过程中发生错误，错误码: %d\n", result);
        break;
    } else {
        // result == IPNAME_NO_ERROR 且不是 IPNAME_ERROR_NOT_READY，表示成功完成
        printf("TX 均衡配置成功完成！\n");
        break;
    }
}
```
**代码解释**：
*   `ipname_sdk_tx_equalization_poll(&tx_eq_config, &poll_state)`：这个函数用于检查由 `_start` 函数启动的操作是否已经完成。
*   **返回值 `result` 的含义**:
    *   `IPNAME_ERROR_NOT_READY`: 表示硬件仍在处理中，需要继续调用 `_poll` 函数。
    *   `IPNAME_NO_ERROR`: 表示配置成功完成。
    *   其他非零值: 表示在配置过程中发生了错误。
*   **轮询循环**: 代码使用一个 `while` 循环来不断调用 `_poll` 函数，直到它返回 `IPNAME_NO_ERROR` (成功) 或其他错误码。

**预期行为**:
执行完这一系列调用后，目标 PHY 通道的发送器会根据我们设置的 `eq_main`, `eq_pre1` 等系数来调整其输出信号的波形。

**注意**: 某些简单的 SDK 函数可能是同步的，调用后会直接阻塞直到操作完成并返回最终结果，这种情况下就不需要 `_start` 和 `_poll` 两个函数。但对于可能耗时较长的操作（如硬件校准、均衡调整、BER 测试），采用异步的 `start/poll` 模式更常见，可以避免阻塞主程序流程。另外，通常还有一个 `_abort` 函数用于中途中止操作。

## 深入幕后：SDK API 是如何工作的？

当我们调用一个 SDK 函数，例如 `ipname_sdk_tx_equalization_start()` 时，它内部执行了一系列步骤，将我们的高级请求转换为底层的硬件操作。

### 流程概览 (非代码)

1.  **参数校验 (Validation)**：SDK 函数首先会检查传入的参数（例如 `cfg` 结构体中的值）是否在有效范围内。比如，通道号 `lane_no` 是否超出了 PHY 支持的最大通道数？均衡系数 `eq_main` 是否在硬件允许的范围内？如果参数无效，函数会立即返回错误码。
2.  **转换与计算 (Translation & Calculation)**：函数会将用户提供的高级参数（如 `eq_main = 30`）转换为硬件寄存器所需的具体数值和位域格式。这可能涉及到查表、计算或简单的格式转换。例如，将带符号的系数转换为寄存器使用的二进制补码或特定编码。
3.  **寄存器访问 (Register Access)**：函数会调用底层的寄存器读写函数（例如 `ipname_sdk_reg_write()` 或 `ipname_sdk_reg_read()`）来访问 PHY 内部的寄存器。这些底层函数最终会依赖我们在 [第 2 章：寄存器访问抽象层](02_寄存器访问抽象层_.md) 中学习的 `asr()` 和 `agr()` 函数来与硬件通信。
4.  **序列化操作 (Sequencing)**：配置一个功能可能需要按特定顺序写入多个寄存器。SDK 函数会负责管理这个顺序。例如，在写入均衡系数之前，可能需要先通过设置某个寄存器位来使能系数的 JTAG 覆写 (override)。
5.  **触发硬件操作 (Triggering)**：写入配置值后，可能需要写入一个特定的“命令”或“触发”寄存器位来告诉硬件应用这些新的设置。例如，在 `ipname_sdk_tx_equalization_start()` 的末尾，会设置 `INT_TX0_FFE_COEFF_UPDATE_I` 位来触发 FFE 系数的更新。
6.  **状态管理 (State Management for Async Ops)**：对于异步操作，`_start` 函数会设置好初始状态，并将必要的信息存储在 `poll_state` 结构中。`_poll` 函数则会读取 PHY 的状态寄存器（例如 `INT_TX0_FFE_COEFF_UPDATE_ACK_O` 位），检查硬件操作是否完成，并根据结果更新 `poll_state` 和返回值。

### 简化版序列图 (以 TX EQ 为例)

```mermaid
sequenceDiagram
    participant 用户代码
    participant TX EQ SDK API as SdkTxEq
    participant 寄存器访问层 as "SdkRegAccess"
    participant PHY硬件

    用户代码->>SdkTxEq: ipname_sdk_tx_equalization_start(cfg, poll_state)
    SdkTxEq->>SdkTxEq: 1. 校验 cfg 参数
    Note over SdkTxEq: 检查 lane_no, eq_main 等是否有效
    SdkTxEq->>SdkRegAccess: 2. ipname_sdk_reg_write(TX_PIN_OVRDVAL21_ADDR, value_for_eq_coeffs)
    SdkRegAccess->>PHY硬件: (写入均衡系数寄存器)
    PHY硬件-->>SdkRegAccess: (状态)
    SdkRegAccess-->>SdkTxEq: (写入状态)
    SdkTxEq->>SdkRegAccess: 3. ipname_sdk_reg_write(TX_PIN_OVRDEN0_ADDR, value_to_enable_override)
    SdkRegAccess->>PHY硬件: (写入Override使能寄存器)
    PHY硬件-->>SdkRegAccess: (状态)
    SdkRegAccess-->>SdkTxEq: (写入状态)
    SdkTxEq->>SdkRegAccess: 4. ipname_sdk_reg_write(TX_PIN_OVRDVAL0_ADDR, value_to_trigger_update)
    SdkRegAccess->>PHY硬件: (写入触发更新寄存器位)
    PHY硬件-->>SdkRegAccess: (状态)
    SdkRegAccess-->>SdkTxEq: (写入状态)
    SdkTxEq->>用户代码: 返回 IPNAME_NO_ERROR (启动成功)

    用户代码->>SdkTxEq: ipname_sdk_tx_equalization_poll(cfg, poll_state)
    SdkTxEq->>SdkRegAccess: ipname_sdk_reg_read(TX_PIN_OVRDVAL0_ADDR)
    SdkRegAccess->>PHY硬件: (读取状态寄存器)
    PHY硬件-->>SdkRegAccess: (返回寄存器值)
    SdkRegAccess-->>SdkTxEq: (寄存器值)
    SdkTxEq->>SdkTxEq: 检查 INT_TX0_FFE_COEFF_UPDATE_ACK_O 位
    alt 操作未完成
        SdkTxEq->>用户代码: 返回 IPNAME_ERROR_NOT_READY
    else 操作完成
        SdkTxEq->>SdkRegAccess: (清理操作，例如清除触发位/Override使能)
        SdkRegAccess->>PHY硬件: (...)
        PHY硬件-->>SdkRegAccess: (状态)
        SdkRegAccess-->>SdkTxEq: (状态)
        SdkTxEq->>用户代码: 返回 IPNAME_NO_ERROR (轮询成功)
    end
end
```
**图解**:
*   用户调用 `_start` 函数。
*   SDK 内部进行参数校验。
*   SDK 通过 `ipname_sdk_reg_write` (最终调用 `asr`) 向 PHY 硬件写入多个寄存器：配置均衡系数、使能 JTAG 覆写、触发硬件更新。
*   `_start` 函数返回，表示启动成功。
*   用户随后调用 `_poll` 函数。
*   SDK 通过 `ipname_sdk_reg_read` (最终调用 `agr`) 读取 PHY 的状态寄存器。
*   SDK 检查状态位。如果未完成，返回 `IPNAME_ERROR_NOT_READY`。如果完成，执行清理操作（写寄存器）并返回 `IPNAME_NO_ERROR`。

### 代码实现片段 (以 `ipname_sdk_tx_equalization.c` 为例)

让我们看看 SDK 函数内部的简化代码，了解它是如何操作寄存器的。

1.  **`_validate_tx_eq_config()` 函数 (参数校验)**

    ```c
    // 文件: sdk_api/design/hw/x814_rel1p0/ipname_sdk_tx_equalization.c (简化片段)
    // 这个内部函数用于检查传入的均衡配置参数是否有效
    ipname_error_code _validate_tx_eq_config(ipname_tx_eq_cfg_t *cfg)
    {
        ipname_error_code result = IPNAME_NO_ERROR;

        // 检查通道号是否超出范围
        if (cfg->lane_no > (ipname_sdk_get_lanes_count(cfg->phy_base_addr)-1)) {
            IPNAME_DEBUG_INFO("\n IPNAME_SDK:: %s Error:: provided lane_no = %d is out of range \n", __func__, cfg->lane_no);
            result = IPNAME_INCORRECT_TX_LANE_NUMBER;
        }
        // 检查主抽头系数是否超出范围 (假设 MAINCURSOR_LENGTH 定义了其位宽)
        else if (cfg->eq_main < 0 || (cfg->eq_main >= (1 << (MAINCURSOR_LENGTH)))) {
            IPNAME_DEBUG_INFO("\n IPNAME_SDK:: %s Error:: provided eq_main = %d is out of rang \n", __func__, cfg->eq_main);
            result = IPNAME_TXEQ_FFE_TAP_OVERFLOW;
        }
        // 检查第一个后向抽头系数是否超出范围 (假设 POSTCURSOR1_LENGTH 定义了位宽，注意带符号范围)
        else if ((cfg->eq_post1 < -(1 << (POSTCURSOR1_LENGTH-1))) || (cfg->eq_post1 >= (1 << (POSTCURSOR1_LENGTH-1)))) {
            IPNAME_DEBUG_INFO("\n IPNAME_SDK:: %s Error:: provided eq_post1 = %d is out of range \n", __func__, cfg->eq_post1);
            result = IPNAME_TXEQ_FFE_TAP_OVERFLOW;
        }
        // ... 对其他抽头系数 (pre1, pre2, post2, ...) 进行类似的范围检查 ...

        return result;
    }
    ```
    **代码解释**:
    *   这个函数在实际配置硬件之前，对用户传入的 `cfg` 结构体中的每个重要字段进行有效性检查。
    *   它使用了像 `ipname_sdk_get_lanes_count()` 这样的辅助函数来获取 PHY 的能力（例如最大通道数）。
    *   它还使用了预定义的宏（如 `MAINCURSOR_LENGTH`, `POSTCURSOR1_LENGTH`）来确定每个系数的有效位宽和范围。
    *   如果任何参数无效，它会返回相应的错误码。

2.  **`ipname_sdk_tx_equalization_start()` 函数 (启动配置)**

    ```c
    // 文件: sdk_api/design/hw/x814_rel1p0/ipname_sdk_tx_equalization.c (简化片段)
    ipname_error_code ipname_sdk_tx_equalization_start(ipname_tx_eq_cfg_t *cfg, ipname_poll_states_t *poll_state)
    {
        uint32_t reg_val = 0;
        ipname_error_code result = _validate_tx_eq_config(cfg); // 首先校验参数

        if(result == IPNAME_NO_ERROR)
        {
            IPNAME_DEBUG_INFO("\n IPNAME_SDK:: Start TX Equalitzaion Initiation \n");

            // --- 步骤 1: 准备并写入均衡系数值 ---
            // 读取包含多个系数的寄存器 (例如 TX__PIN_OVRDVAL21__ADDR)
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL21__ADDR);
            // 使用宏 IPNAME_SET_FIELD 设置寄存器中的特定位域
            // 注意 ipname_signed_to_unsigned 用于将带符号的系数转换为寄存器所需的无符号格式
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDVAL21__INT_TX0_FFE_CURSOR_COEFF_I , cfg->eq_main);
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDVAL21__INT_TX0_FFE_POSTCURSOR1_COEFF_I , ipname_signed_to_unsigned(cfg->eq_post1, POSTCURSOR1_LENGTH));
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDVAL21__INT_TX0_FFE_PRECURSOR1_COEFF_I , ipname_signed_to_unsigned(cfg->eq_pre1, PRECURSOR1_LENGTH));
            // ... 设置同一寄存器中的其他系数 (pre2, pre3) ...
            // 将修改后的值写回寄存器
            ipname_sdk_reg_write(cfg->phy_base_addr + IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL21__ADDR, reg_val);

            // 对包含其他系数的寄存器执行类似操作 (例如 TX__PIN_OVRDVAL22__ADDR for post2, pre4)
            // reg_val = ipname_sdk_reg_read(... TX__PIN_OVRDVAL22__ADDR);
            // IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDVAL22__INT_TX0_FFE_POSTCURSOR2_COEFF_I, ...);
            // ipname_sdk_reg_write(... TX__PIN_OVRDVAL22__ADDR, reg_val);

            // --- 步骤 2: 使能 JTAG Override ---
            // 读取 Override 使能寄存器 (TX__PIN_OVRDEN0__ADDR)
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDEN0__ADDR);
            // 为所有要配置的系数对应的 Override 使能位置 1
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDEN0__OVRD_EN_TX0_FFE_CURSOR_COEFF_I, 1);
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDEN0__OVRD_EN_TX0_FFE_POSTCURSOR1_COEFF_I, 1);
            // ... 为其他系数设置相应的 OVRD_EN 位 ...
            // 写回 Override 使能寄存器
            ipname_sdk_reg_write(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDEN0__ADDR, reg_val);

            // --- 步骤 3: 触发硬件更新 ---
            // 使能 FFE 系数更新信号的 Override
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDEN0__ADDR);
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDEN0__OVRD_EN_TX0_FFE_COEFF_UPDATE_I, 1);
            ipname_sdk_reg_write(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDEN0__ADDR, reg_val);

            // 通过 Override 值寄存器 (TX__PIN_OVRDVAL0__ADDR) 发送更新脉冲 (置 1)
            reg_val = ipname_sdk_reg_read(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL0__ADDR);
            IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDVAL0__INT_TX0_FFE_COEFF_UPDATE_I, 1);
            ipname_sdk_reg_write(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL0__ADDR, reg_val);

            IPNAME_DEBUG_INFO("\n IPNAME_SDK:: Finish TX Equalitzaion Initiation \n");

            // --- 步骤 4: 设置轮询状态 ---
            poll_state->tx_eq_state.state = IPNAME_TX_EQ_CHK_FFE_UPDATE_ACK; // 设置 FSM 状态为等待 ACK
        }
        return result;
    }

    ```
    **代码解释**:
    *   **宏的作用**:
        *   `IPNAME_TX_BASE_ADDR(lane_no)`: 计算指定通道的 TX 模块基地址。
        *   `TX__PIN_OVRDVAL21__ADDR`: 这是一个宏，代表某个具体寄存器的地址偏移量。
        *   `IPNAME_SET_FIELD(reg_val, FIELD_MACRO, value)`: 这个宏非常关键。它负责将 `value` 设置到 `reg_val` 变量中由 `FIELD_MACRO` 定义的位域。例如，`TX__PIN_OVRDVAL21__INT_TX0_FFE_CURSOR_COEFF_I` 定义了主抽头系数在 `TX__PIN_OVRDVAL21__ADDR` 寄存器中的具体位位置和宽度。这个宏隐藏了位操作（如移位和掩码）的细节。
        *   `ipname_signed_to_unsigned()`: 一个辅助函数，用于将可能为负数的系数（如 `eq_post1`）转换为寄存器所需的无符号二进制表示（通常是二进制补码）。
    *   **底层函数**: `ipname_sdk_reg_read()` 和 `ipname_sdk_reg_write()` 是 SDK 内部用于读写寄存器的函数。它们很可能封装了 [第 2 章：寄存器访问抽象层](02_寄存器访问抽象层_.md) 提供的 `agr()` 和 `asr()` 函数。
    *   **执行流程**: 函数严格按照硬件要求的顺序执行操作：先写入所有系数值，然后使能 Override，最后发送更新触发信号。
    *   **状态机**: 最后，它设置了 `poll_state` 中的状态，为 `_poll` 函数的第一次调用做准备。

3.  **`ipname_sdk_tx_equalization_poll()` 函数 (轮询检查)**

    ```c
    // 文件: sdk_api/design/hw/x814_rel1p0/ipname_sdk_tx_equalization.c (简化片段)
    ipname_error_code ipname_sdk_tx_equalization_poll(ipname_tx_eq_cfg_t *cfg, ipname_poll_states_t *poll_state)
    {
        uint32_t reg_val = 0;
        ipname_error_code result = IPNAME_NO_ERROR;

        // 根据 poll_state 中的当前状态执行操作
        switch(poll_state->tx_eq_state.state)
        {
            case IPNAME_TX_EQ_CHK_FFE_UPDATE_ACK: // 状态：检查硬件确认信号
                // 读取包含确认信号的状态寄存器 (TX__PIN_OVRDVAL0__ADDR)
                reg_val = ipname_sdk_reg_read(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL0__ADDR);
                // 使用 IPNAME_GET_FIELD 宏提取确认位 (ACK) 的状态
                reg_val = IPNAME_GET_FIELD(reg_val, TX__PIN_OVRDVAL0__INT_TX0_FFE_COEFF_UPDATE_ACK_O);

                if(reg_val != 1) { // 如果 ACK 位不是 1
                    IPNAME_DEBUG_INFO("\n IPNAME_SDK:: FFE_COEFF_UPDATE ACK Not Received \n");
                    result = IPNAME_ERROR_NOT_READY; // 返回“未就绪”
                    break; // 保持当前状态，等待下次轮询
                }

                // ACK 位是 1，表示硬件已应用配置
                IPNAME_DEBUG_INFO("\n IPNAME_SDK:: FFE_COEFF_UPDATE ACK Received \n");
                poll_state->tx_eq_state.state = IPNAME_TX_EQ_FFE_CLEAN_UP; // 进入下一个状态：清理

            // fall-through (如果 ACK 已收到，直接执行清理步骤)
            case IPNAME_TX_EQ_FFE_CLEAN_UP: // 状态：执行清理操作
                IPNAME_DEBUG_INFO("\n IPNAME_SDK:: TX Equalization Starts Cleaning\n");

                // 清除触发信号 (将 INT_TX0_FFE_COEFF_UPDATE_I 置 0)
                reg_val = ipname_sdk_reg_read(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL0__ADDR);
                IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDVAL0__INT_TX0_FFE_COEFF_UPDATE_I, 0);
                ipname_sdk_reg_write(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDVAL0__ADDR, reg_val);

                // 清除 Override 使能 (将 OVRD_EN_TX0_FFE_COEFF_UPDATE_I 和其他 OVRD_EN 位 置 0)
                reg_val = ipname_sdk_reg_read(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDEN0__ADDR);
                IPNAME_SET_FIELD(reg_val, TX__PIN_OVRDEN0__OVRD_EN_TX0_FFE_COEFF_UPDATE_I , 0);
                // ... 清除其他 OVRD_EN 位 ...
                ipname_sdk_reg_write(cfg->phy_base_addr+ IPNAME_TX_BASE_ADDR(cfg->lane_no) + TX__PIN_OVRDEN0__ADDR, reg_val);

                poll_state->tx_eq_state.state = IPNAME_TX_EQ_UNKNOWN; // 将状态重置为未知/完成
                result = IPNAME_NO_ERROR; // 返回成功
                break;

            default: // 无效状态
                result = IPNAME_POLLING_FSM_INVALID;
                break;
        }
        return result;
    }

    ```
    **代码解释**:
    *   **状态机**: 这个函数使用 `poll_state->tx_eq_state.state` 来驱动一个简单的状态机。
    *   **检查 ACK**: 在 `IPNAME_TX_EQ_CHK_FFE_UPDATE_ACK` 状态下，它读取状态寄存器，并使用 `IPNAME_GET_FIELD` 宏来检查硬件是否已经完成了系数更新（通过检查 `ACK` 位）。
    *   **返回 `NOT_READY`**: 如果 `ACK` 位还没置位，表示硬件仍在忙，函数返回 `IPNAME_ERROR_NOT_READY`，提示调用者需要继续轮询。
    *   **清理**: 一旦检测到 `ACK` 位，函数就进入 `IPNAME_TX_EQ_FFE_CLEAN_UP` 状态。在这个状态下，它会清除之前设置的触发信号和 Override 使能位，将硬件恢复到正常状态。
    *   **返回成功**: 清理完成后，函数将状态设置为 `IPNAME_TX_EQ_UNKNOWN` (表示完成或空闲)，并返回 `IPNAME_NO_ERROR` 表示整个操作成功结束。

### SDK API 的优势

使用 PHY SDK API 而不是直接操作寄存器，带来了明显的好处：
1.  **大大简化开发**：将复杂的硬件操作封装成简单的函数调用。
2.  **提高代码可读性**：函数名（如 `ipname_sdk_tx_equalization_start`）比直接读写寄存器地址和位域更能表达意图。
3.  **减少错误**：SDK 内部处理了正确的操作顺序、参数转换和状态检查，降低了因手动操作寄存器而出错的风险。
4.  **提升代码可维护性**：如果底层硬件寄存器在未来版本中发生变化，理想情况下只需要更新 SDK 库，而调用 SDK 的上层代码可以保持不变。

## 总结与展望

在本章中，我们揭开了 PHY SDK API 的面纱。我们了解到：
*   PHY SDK API 是一套用于控制特定 PHY (`ipname`) 的高级函数库，它简化了复杂的操作，提供了比直接寄存器访问更抽象、更易用、更稳定的接口。
*   它涵盖了 PHY 的多种功能，如电源管理、时钟转发、频率测量、发送均衡、接收器配置、BER 测试等。
*   通过一个配置 TX 均衡的例子，我们学习了如何使用 SDK API：包含头文件、填充配置结构体、调用 `_start` 函数启动操作，以及使用 `_poll` 函数等待操作完成。
*   我们也探讨了 SDK API 函数内部的大致工作流程：参数校验、转换为寄存器操作、调用底层寄存器访问函数、管理操作序列和状态。

PHY SDK API 是我们与 PHY 芯片进行高级交互的主要工具。掌握了它，我们就能更有效地利用 PHY 的强大功能来实现复杂的通信任务或进行深入的诊断。

有了对 PHY 的基本初始化和通过 SDK API 进行配置的能力，下一步自然是探索 PHY 中一些关键的自动化过程。在下一章 [第 6 章：自适应协商 (Auto-Negotiation)](06_自适应协商__auto_negotiation__.md) 中，我们将学习 PHY 如何自动与其连接的对端设备协商通信速率、模式等参数，这是现代高速链路建立过程中的核心环节。敬请期待！

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)