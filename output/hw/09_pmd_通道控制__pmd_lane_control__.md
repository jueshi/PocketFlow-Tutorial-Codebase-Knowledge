# Chapter 9: PMD 通道控制 (PMD Lane Control)


欢迎来到 `hw` 项目教程的最后一章！在上一章 [连续校准与自适应 (CCA)](08_连续校准与自适应__cca__.md) 中，我们学习了系统如何在正常工作模式下，通过持续的后台校准和自适应来应对环境变化和器件老化，从而保持链路的长期稳定运行。CCA 确保了我们的通信链路能够“持久健康”。

现在，我们将目光转向通信链路的最底层——物理媒介相关子层 (Physical Medium Dependent, PMD)。一个高速接口通常由多条并行的物理通道 (Lane) 组成，每条通道都有自己独立的发送 (TX) 和接收 (RX) 路径。那么，系统是如何管理和控制这些独立的物理通道，特别是它们的电源状态、复位以及基本操作的呢？这就是本章“PMD 通道控制”要探讨的内容。

## 什么是 PMD 通道控制？

想象一条多车道的高速公路。每条车道都有其独立的交通信号灯、限速牌以及路况监控。为了确保整条高速公路顺畅运行，需要有一个控制中心来管理每条车道的开启、关闭、通行状态以及应对突发状况。

**PMD (物理媒介相关子层)** 是 OSI 模型中的最底层，它直接与物理传输介质（如铜缆、光纤）打交道。**PMD 通道控制 (PMD Lane Control)** 模块就扮演着类似高速公路上每条车道“交通控制塔”的角色。它负责：

1.  **管理单个通道 (Lane) 的物理层硬件状态**：特别是针对每个独立的发送 (TX) 路径和接收 (RX) 路径。
2.  **处理来自上层固件的命令**：例如，改变通道的电源状态 (PState)、处理特定的请求、响应复位信号等。
3.  **提供与硬件交互的底层接口**：通过读写特定的硬件寄存器来控制通道的行为。

简单来说，PMD 通道控制就像是每个数据“车道”的信号灯和控制器，管理着数据“车辆”的启动、停止和通行状态，确保每条物理通道都能按照系统的指令正确工作。

## PMD 通道控制的核心职责

PMD 通道控制模块虽然听起来很底层，但它的职责至关重要，主要包括：

*   **电源状态管理 (PState Management)**：
    *   高速接口的每个通道都有多种电源状态（PState），例如 P0 (全速工作状态)、P1 (部分功能关闭的低功耗状态)、P2 (深度睡眠状态) 和 RST (复位状态)。
    *   PMD 通道控制模块负责接收来自更高层逻辑（比如整个物理层接口的 PState 状态机）的命令，并执行将通道切换到指定电源状态所需的一系列底层硬件操作。
    *   这些操作通常定义在电源启动/关闭序列查找表（例如 `gRxPowerUpSequenceTableLut`, `gTxPowerUpSequenceTableLut`）中，我们稍后会看到它们如何与此模块交互。

*   **请求处理 (Request Handling)**：
    *   除了电源状态转换，PMD 通道控制还处理其他类型的请求，比如：
        *   **数据使能 (Data Enable)**：允许或禁止数据通过该通道。
        *   **复位 (Reset)**：对通道进行硬件复位。
        *   **中断/中止 (Abort)**：中止当前正在进行的操作。
    *   这些请求可能来自系统其他部分的固件，或者是通过软件开发工具包 (SDK) 发出的。

*   **硬件接口与状态监控**：
    *   PMD 通道控制模块直接与每个通道的 PMD 层控制与状态寄存器 (CSR) 进行交互。
    *   它通过读取这些寄存器来获取通道的当前状态（如速率、宽度、是否复位等），并通过写入这些寄存器来改变通道的行为。

## PMD 通道控制如何与系统交互？

PMD 通道控制模块通常不是由最终用户直接操作的，而是作为固件中一个关键的服务层，被更高层的逻辑所调用。

### 1. 控制与状态寄存器 (CSR) 的角色

PMD 通道控制模块与其“上级”以及物理硬件之间的沟通，很大程度上依赖于每个通道专属的控制与状态寄存器 (CSR)。这些寄存器就像是模块之间的“信箱”和“公告板”。

*   **命令接收**：上层固件（比如主 PState 状态机）想让某个通道执行特定操作时（如改变电源状态），它会将命令代码和相关参数写入到该通道的特定 CSR 中（例如，`RX_FW_PWRCMD` 和 `RX_FW_PWRCMD_ARG` 字段位于 `PMD_LANE_RX__RX_FW_CSR0` 寄存器中）。
*   **状态反馈**：PMD 通道控制模块执行完操作后，会更新 CSR 中的状态位（例如，`RX_FW_ACK` 字段位于 `PMD_LANE_RX__RX_FW_CSR10` 寄存器中），向上层报告操作已完成或失败。上层固件通过轮询这些状态位来了解操作的进展。
*   **硬件状态读取**：PMD 通道控制模块也会读取 CSR 来获取由硬件直接更新的状态信息，例如当前通道的速率和位宽（通过 `RX_RATE_CURR` 和 `RX_WIDTH_CURR` 字段）。

### 2. 在电源状态转换中的作用

在 [配置管理 (Configuration Management)](02_配置管理__configuration_management__.md) 章节中，我们提到系统会加载默认配置。当通道需要进行电源状态转换（例如，从 P2 低功耗状态唤醒到 P0 工作状态）时，一个复杂的序列会被执行。这个序列通常定义在 `rx_pwr_cmd_seq.c` 和 `tx_pwr_cmd_seq.c` 这样的文件中。

这些序列包含了硬件命令 (由硬件序列器自动执行) 和固件命令 (由固件，特别是 `rx_pwr_cmd_handler.c` 和 `tx_pwr_cmd_handler.c` 中的逻辑来执行)。当执行到固件命令时，`processHwSpecificRxPstateCmds()` (或 TX 的对应函数) 会被调用。这个函数内部会调用许多更底层的函数来完成特定任务，其中就包括了调用 `pmd_lane_rx_control.c` (或 TX) 中的函数来直接操作 PMD 寄存器，以完成如使能时钟、配置信号类型、加载校准码等步骤。

PMD 通道控制模块提供的函数，正是这些 PState 转换序列中固件步骤得以与硬件交互的桥梁。

下面是一个简化的时序图，展示了上层逻辑如何通过 PMD 通道控制模块与硬件交互以执行一个操作（例如，一个PState转换中的某个固件步骤）：

```mermaid
sequenceDiagram
    participant 高层逻辑 as "上层固件逻辑 (如 PState FSM 或 电源命令处理器)"
    participant PMD通道控制模块 as "PMD通道控制模块 (本章内容)"
    participant PMD通道CSR as "PMD通道控制/状态寄存器"
    participant PMD通道硬件 as "PMD通道物理硬件"

    高层逻辑->>PMD通道控制模块: 调用函数请求操作 (例如 pmdLaneRxControl_TriggerRxDataEn())
    PMD通道控制模块->>PMD通道CSR: 写入控制位 (例如 RXX_DATA_EN_I = 1)
    PMD通道硬件->>PMD通道硬件: 根据寄存器设置改变物理状态 (例如 使能数据路径)
    Note over PMD通道控制模块, 高层逻辑: 操作可能立即完成，或通过后续状态检查确认
    高层逻辑->>PMD通道控制模块: (若需确认) 调用函数读取状态 (例如 pmdLaneRxControl_GetRxAdaptInProg())
    PMD通道控制模块->>PMD通道CSR: 读取状态位 (例如 RXX_ADAPT_IN_PROG_I)
    PMD通道CSR-->>PMD通道控制模块: 返回状态值
    PMD通道控制模块-->>高层逻辑: 返回状态给调用者
end
```

## PMD 通道控制的关键操作与代码示例

让我们通过一些具体的函数示例，看看 PMD 通道控制模块是如何工作的。我们将关注 `pmd_lane_rx_control.c` (接收路径) 和 `pmd_lane_tx_control.c` (发送路径) 及其 `_derived.c` 对应文件中的一些核心功能。

### 1. 获取上层命令 (电源状态转换)

上层固件（如 `pmd_rx.c` 或 `pmd_tx.c` 中的 PState 状态机）会通过特定的 CSR 寄存器向 PMD 通道硬件序列器或固件下发电源状态转换命令。PMD 通道控制模块提供了读取这些命令参数的函数。

```c
// 文件: pmd_lane_rx_control.c (简化片段)

/**
 * @brief 检索 PMD_LANE_RX__RX_FW_CSR0 寄存器的参数
 *        并将它们存储在 @a apPstateCmdFsm 中。
 * @param[in]   apPstateCmdFsm      tRxPstateCmdFsm_t 类型的结构体指针
 */
void pmdLaneRxControl_GetRxFwPwrCmdParams(tRxPstateCmdFsm_t* apPstateCmdFsm)
{
    PMD_LANE_RX__RX_FW_CSR0_T vPmdLaneRxFwCsr0;

    // 读取包含电源命令和参数的寄存器
    vPmdLaneRxFwCsr0 = READ_REG(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__RX_FW_CSR0);
    // 获取命令类型
    apPstateCmdFsm->mCurrentCmd = vPmdLaneRxFwCsr0.mFields.RX_FW_PWRCMD;
    // 获取命令参数
    apPstateCmdFsm->mCurrentArg = vPmdLaneRxFwCsr0.mFields.RX_FW_PWRCMD_ARG;
}
```
*   `pmdLaneRxControl_GetRxFwPwrCmdParams()` 函数从 `PMD_LANE_RX__RX_FW_CSR0` 寄存器中读取 `RX_FW_PWRCMD` (电源命令) 和 `RX_FW_PWRCMD_ARG` (命令参数) 字段。
*   这些信息会被更高层的 PState 状态机用来决定接下来要执行哪个电源状态转换序列。
*   `pmd_lane_tx_control.c` 中有类似的 `pmdLaneTxControl_GetTxFwPwrCmdParams()` 函数。

### 2. 确认固件请求 (Ack)

当固件处理完一个来自硬件或其他模块的请求后，需要通过设置一个确认位 (Ack) 来通知请求方。

```c
// 文件: pmd_lane_rx_control.c (简化片段)

/**
 * @brief 设置 PMD_LANE_RX__RX_FW_CSR10 寄存器的 RX_FW_ACK 字段。
 * @param[in]   aSet        布尔变量，指定要设置的值。
 */
void pmdLaneRxControl_SetRxFwAck(bool aSet)
{
    // 将 RX_FW_ACK 字段设置为指定的值 (通常是 1 表示确认)
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__RX_FW_CSR10, RX_FW_ACK, aSet);
}
```
*   `pmdLaneRxControl_SetRxFwAck()` 函数用于设置 `PMD_LANE_RX__RX_FW_CSR10` 寄存器中的 `RX_FW_ACK` 位。这个位通常由固件在完成由硬件（例如PMD硬件序列器）或SDK发起的请求（通过 `RX_FW_REQ` 位）后设置。
*   `pmd_lane_tx_control.c` 中有类似的 `pmdLaneTxControl_SetTxFwAck()` 函数。

### 3. 使能数据路径

在通道完成初始化和自适应过程后，需要显式使能其数据路径，允许数据开始流动。

```c
// 文件: pmd_lane_rx_control.c (简化片段)

/**
 * @brief 将 rx_data_en 设置为高电平的函数。
 *
 * 该函数将 rx_data_en 设置为高电平，以在以太网模式下触发 Rx 适配启动过程。
 */
void pmdLaneRxControl_TriggerRxDataEn()
{
    // 设置 RXX_DATA_EN_I 字段为 1，通常表示使能接收数据路径
    // 这个信号可能会连接到接收器自适应引擎的启动逻辑
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__PMD_RX_OVRDVAL2, RXX_DATA_EN_I, 1);
}
```
*   `pmdLaneRxControl_TriggerRxDataEn()` 将 `PMD_LANE_RX__PMD_RX_OVRDVAL2` 寄存器中的 `RXX_DATA_EN_I` 位置 1。这个信号通常用于通知 PMD 硬件（特别是接收器自适应逻辑）数据路径已准备好，可以开始处理进入的数据。
*   这通常是链路建立过程中的一个重要步骤，在[接收器自适应引擎](01_接收器自适应引擎_.md)章节中我们看到自适应过程可能由此触发。
*   `pmd_lane_tx_control.c` 中有类似的 `pmdLaneTxControl_TriggerTxDataEn()` 函数。

### 4. 处理复位信号

PMD 通道控制也负责处理和响应通道的复位请求。

```c
// 文件: pmd_lane_rx_control.c (简化片段)

/**
 * @brief 字段获取函数。
 * @returns PMD_LANE_RX__RX_FW_CSR0 寄存器的 RX_RESET_STICKY 字段的布尔转换值。
 */
bool pmdLaneRxControl_GetRxResetSticky()
{
    // 读取 RX_RESET_STICKY 粘性位，如果为1，表示曾经发生过复位
    return ( (bool) (READ_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__RX_FW_CSR0, RX_RESET_STICKY)) );
}

/**
 * @brief 设置 PMD_LANE_RX__RX_FW_CSR0 寄存器的 RX_RESET_STICKY_CLR 字段。
 * @param[in]   aSet        布尔变量，指定要设置的值。
 */
void pmdLaneRxControl_SetRxResetStickyClr(bool aSet)
{
    // 设置 RX_RESET_STICKY_CLR 位 (通常为1) 来清除 RX_RESET_STICKY 粘性位
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__RX_FW_CSR0, RX_RESET_STICKY_CLR, aSet);
}
```
*   `RX_RESET_STICKY` 是一个“粘性”状态位。如果通道发生过复位（例如，由硬件或软件触发），这个位会被置位并保持，直到被显式清除。
*   固件可以通过 `pmdLaneRxControl_GetRxResetSticky()` 来检测是否发生过复位事件。
*   通过调用 `pmdLaneRxControl_SetRxResetStickyClr(true)` 可以清除这个粘性位。
*   实际的复位操作（例如，在 `rx_pwr_cmd_handler.c` 中的 `eRxFwCmd_RxReset` 命令处理中）会直接写寄存器来拉低复位信号，如：
    ```c
    // rx_pwr_cmd_handler.c 中的 eRxFwCmd_RxReset 命令处理片段
    // WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__PIN_OVRDEN0, OVRD_EN_RX0_RSTN_I, 1); // 使能覆盖
    // WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__PIN_OVRDVAL0, INT_RX0_RSTN_I, 0);    // 拉低复位 (RSTN低有效)
    // WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__PIN_OVRDEN0, OVRD_EN_RX0_RSTN_I, 0); // 释放覆盖
    ```

### 5. 配置特定于通道的参数

在通道的电源状态转换过程中，需要根据当前的速率和工作模式配置一些特定于该通道的 PMD 参数。

```c
// 文件: pmd_lane_rx_control_derived.c (简化片段)

/**
 * @brief 为 PMD_LANE_RX 配置 RX_SIGNAL TYPE 字段。PAM4 默认为0，NRZ 为1。
 * @param[in]   aRateIndex      指定 phy 速率。
 */
void pmdLaneRxControl_ConfigureRxSignalType(const uint32_t aRateIndex)
{
    // 从 gRxConfigMasterDefaults (在 rx_config_master_defaults.c 中定义) 获取信号类型
    // 并将其写入 PMD_LANE_RX__RX_LANE_CFG1 寄存器的 RX_SIGNAL_TYPE 字段
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__RX_LANE_CFG1, RX_SIGNAL_TYPE, gRxConfigMasterDefaults[aRateIndex].mRx0SignalTypeIReg);
}
```
*   `pmdLaneRxControl_ConfigureRxSignalType()` 函数根据当前速率索引 `aRateIndex`，从 [配置管理 (Configuration Management)](02_配置管理__configuration_management__.md) 章节中提到的 `gRxConfigMasterDefaults` 查找表中获取预设的信号类型（例如 PAM4 或 NRZ），并将其写入到该通道的 `RX_SIGNAL_TYPE` 寄存器字段。
*   这个函数通常在处理 `eRxFwCmd_RateConfig` 固件命令时被 `configureRxRateDependentSettings` (位于 `rx_pwr_cmd_handler.c`) 调用。
*   类似的，`pmdLaneRxControl_configureRxPwrUpStepMapping()` 和 `pmdLaneRxControl_configureRxPwrDownStepMapping()` 函数负责将电源状态转换序列中的步骤映射关系（定义在 `rx_pwr_cmd_seq.c` 中的 `gRxPowerUpPStateStepMapping` 等）写入到 PMD 硬件序列器的配置寄存器中。

### 6. 清除请求信号

在某些交互中，上层逻辑或SDK可能通过设置一个请求信号（如 `RXX_REQ_I`）来请求固件执行某些操作。操作完成后，这个请求信号需要被清除。

```c
// 文件: pmd_lane_rx_control.c (简化片段)
/**
 * @brief   清除 rxX_req_i，这是上下文更改所必需的
 * @note    主要由 SDK 驱动
 */
void pmdLaneRxControl_ClearRxReq()
{
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__PMD_RX_OVRDVAL2, RXX_REQ_I, 0);
}
```
* `pmdLaneRxControl_ClearRxReq()` 用于清除接收器请求信号 `RXX_REQ_I`。

这些函数共同构成了 PMD 通道控制模块的核心功能，使得固件能够精细地管理和控制每个物理通道的硬件状态。

## 总结

在本章中，我们一起了解了“PMD 通道控制”模块：

*   它像每个数据“车道”的交通控制塔，负责管理单个物理通道 (Lane) 的发送 (TX) 和接收 (RX) 路径的底层硬件状态。
*   其核心职责包括响应来自上层固件的电源状态 (PState) 转换命令、处理数据使能和复位等请求，并提供与硬件寄存器交互的接口。
*   PMD 通道控制通过读写每个通道专属的控制与状态寄存器 (CSR) 来与上层逻辑和硬件进行通信。
*   我们通过代码示例了解了一些关键操作，如获取电源命令参数 (`pmdLaneRxControl_GetRxFwPwrCmdParams`)、设置确认位 (`pmdLaneRxControl_SetRxFwAck`)、使能数据路径 (`pmdLaneRxControl_TriggerRxDataEn`)、处理复位 (`pmdLaneRxControl_GetRxResetSticky`) 以及配置通道特定参数 (`pmdLaneRxControl_ConfigureRxSignalType`)。
*   PMD 通道控制模块是实现复杂电源状态转换序列（定义在 `*_pwr_cmd_seq.c` 和 `*_pwr_cmd_handler.c` 中）和响应外部请求的关键底层组件。

PMD 通道控制确保了在多通道高速接口中，每一条物理通道都能被精确、独立地控制，从而为整个系统的稳定可靠运行奠定了坚实的物理基础。

---

### `hw` 项目教程结语

恭喜你完成了 `hw` 项目的入门教程！

从第一章的[接收器自适应引擎](01_接收器自适应引擎_.md)开始，我们一起踏上了一段探索高速串行通信核心技术的旅程。我们了解了系统如何：

*   通过**接收器自适应引擎**来协调各种复杂的调整过程。
*   利用**配置管理**为硬件打下坚实的初始设置基础。
*   通过**链路训练**与远端设备“握手”并优化通信参数。
*   依赖**CDR 自适应**精确恢复时钟并对齐数据。
*   使用**FFE 自适应**和**CTLE 自适应**这两种不同的均衡技术来对抗信号失真。
*   通过**ADC 校准**确保模数转换的准确性。
*   利用**连续校准与自适应 (CCA)** 机制来维持链路的长期稳定。
*   最后，通过**PMD 通道控制**来管理每一条物理数据通道的底层状态。

虽然本教程侧重于非常入门级的概念介绍，并大量简化了实际代码的复杂性，但希望它能为你揭开 `hw` 项目固件设计的一些神秘面纱，让你对这些核心模块的作用和它们之间如何协同工作有一个初步的认识。

高速通信技术是一个涉及模拟、数字、信号处理和固件编程等多个领域的复杂学科。`hw` 项目的固件正是这些知识的结晶。如果你对某个特定主题产生了浓厚的兴趣，我们鼓励你以本教程为起点，深入阅读相关的代码、设计文档以及行业标准，继续你的探索之旅。

感谢你的学习！希望这段旅程对你有所启发。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)