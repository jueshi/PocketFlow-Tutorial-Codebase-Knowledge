# Chapter 8: 连续校准与自适应 (CCA)


欢迎来到 `hw` 项目教程的第八章！在上一章 [ADC 校准 (ADC Calibration)](07_adc_校准__adc_calibration__.md) 中，我们学习了如何对 ADC（模数转换器）进行失调、增益和时间交织 Skew 校准，确保在信号链路的初始阶段，模拟信号能够被准确地转换为数字信号。这就像我们精心校准了测量工具，确保了测量的初始精度。

然而，一个通信设备在实际工作中，并非处于一成不变的理想环境。温度的波动、供电电压的轻微漂移，甚至元器件随着时间的推移而老化，都可能悄悄地影响着硬件的性能。这就好比一把刚校准好的尺子，如果热胀冷缩了，它的精度可能就不再可靠了。那么，系统是如何在正常工作模式下，持续应对这些缓慢变化，保持链路长期稳定运行的呢？这就是我们本章要探讨的“连续校准与自适应 (CCA)”机制。

## 什么是连续校准与自适应 (CCA)？

**连续校准与自适应 (Continuous Calibration and Adaptation, CCA)** 是指在设备正常工作模式（通常称为“任务模式”，Mission Mode）下，后台持续运行的一系列校准和自适应过程。它的核心目标是**补偿由于环境因素（如温度变化、电压漂移）或器件老化等引起的硬件性能逐渐下降，从而确保通信链路能够长期稳定、可靠地运行。**

想象一下你驾驶着一辆配备了高级自动巡航系统的汽车。这个系统不仅仅是简单地保持设定的速度，它还会根据路况（比如上坡、下坡、弯道）和车辆状态（比如胎压变化、发动机负荷）来微调油门、刹车甚至方向盘，始终让你保持平稳舒适的驾驶体验。

CCA 就扮演着类似的角色。它不像初始校准那样是一次性的“大修”，而更像是一种**周期性的、非破坏性的“微调”**。它会在不中断正常数据传输的前提下，定期检查并细微调整硬件的关键参数，例如：

*   内部振荡器（如 ILO、环形振荡器）的频率和相位
*   ADC 的失调、增益和时钟偏移（Skew）
*   CDR（时钟数据恢复）的平衡状态
*   DAC（数模转换器）的直流偏置和时钟偏移
*   其他接收器自适应参数

通过这些持续的“小动作”，CCA 确保了即使面对各种缓慢变化的干扰因素，我们的高速通信链路也能始终保持在最佳的工作状态。

## CCA 是如何工作的？

CCA 并非一个单一的算法，而是一个**框架或调度机制**，它周期性地执行一系列预定义的、针对特定硬件模块的校准或自适应子任务。其工作流程大致如下：

1.  **启用与配置**：
    *   CCA 通常在系统完成初始的链路建立和主要校准（如 [链路训练 (Link Training)](03_链路训练__link_training__.md)、初始的 ADC 校准等）之后被启用。
    *   固件可以配置哪些 CCA 子任务需要执行，以及它们执行的频率或条件。

2.  **周期性执行**：
    *   系统内部有一个定时器或调度机制，会定期触发 CCA 控制器。
    *   CCA 控制器按照预设的顺序，逐个执行在当前配置中被启用的 CCA 子任务。

3.  **执行子任务**：
    *   每个 CCA 子任务都是一个相对独立的校准或自适应例程。这些例程通常是我们在前面章节中学习过的校准算法的“轻量级”或“精细调整”版本，例如慢速 ADC 失调校准、ILO 相位微调等。
    *   这些子任务被设计为**非破坏性**的，意味着它们可以在不显著影响正常数据流的情况下完成。

4.  **迭代与循环**：
    *   CCA 控制器会依次执行完所有使能的子任务，完成一轮 CCA 迭代。
    *   然后等待下一个周期到来，再次从头开始新一轮的迭代。

这个过程就像一个勤劳的机器人管家，定期巡视家中的各个设备，确保它们都工作正常，并进行必要的微调。

下面是一个简化的 CCA 工作流程示意图：

```mermaid
sequenceDiagram
    participant 系统定时器/调度器 as 系统定时器/调度器
    participant CCA控制器 as "CCA控制器 (adapt_ctrl_derived.c)"
    participant CCA命令列表 as "CCA命令列表 (gRxCcaCmdLut/gTxCcaCmdLut)"
    participant 具体校准/自适应模块 as 各校准/自适应模块 (ADC, CDR, ILO, RO等)
    participant 硬件参数 as "硬件参数"

    系统定时器/调度器->>CCA控制器: 触发CCA执行周期
    CCA控制器->>CCA控制器: 初始化/选择下一个CCA任务 (如 processRxCcaRequests)
    CCA控制器->>CCA命令列表: 根据配置读取下一个使能的命令
    CCA命令列表-->>CCA控制器: 返回命令 (例如：ADC失调慢速校准)
    CCA控制器->>具体校准/自适应模块: 执行选定的CCA命令 (通过 runCommandGated)
    Note over 具体校准/自适应模块: (例如，执行ADC失调慢速校准)
    具体校准/自适应模块->>硬件参数: 微调相关硬件参数
    具体校准/自适应模块-->>CCA控制器: 当前CCA命令执行完成
    CCA控制器->>CCA控制器: 记录任务进度，准备执行下一个任务或结束当前轮次
end
```

## 深入探索：代码中的 CCA

CCA 的核心控制逻辑主要位于 `adapt_ctrl_derived.c` 文件中。让我们看看它是如何实现的。

### 1. 启用 CCA

CCA 通常在系统完成主要的启动自适应序列后，通过一个特定的适配命令（如 `eAdaptCmd_PostAdaptCcaEnable`）或在进入“任务模式”时由硬件配置来启用。

在 `adapt_ctrl_derived.c` 的 `initStrupAdaptEth()` 函数中，我们可以看到与任务模式（即 CCA 运行的环境）相关的设置：

```c
// 文件: x812_rel2p1\adapt_ctrl_derived.c (initStrupAdaptEth 片段)
void initStrupAdaptEth(void)
{
    // ... 其他初始化 ...

    // 使能 CCA 定时器和任务模式
    // 将 CCA 的起始状态设为0 (由 stn_fw_cmd_en 的位0控制)
    PMD_LANE_RX__ETH_ADAPT_CTRL60_T vPmdRxEthAdaptCtrl = READ_REG(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__ETH_ADAPT_CTRL60);
    vPmdRxEthAdaptCtrl.mFields.MISSION_MODE_START_ST = 0; // 任务模式起始状态
    vPmdRxEthAdaptCtrl.mFields.EN_MISSION_MODE = 1;       // 使能任务模式 (CCA在此模式下运行)
    WRITE_REG(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__ETH_ADAPT_CTRL60, vPmdRxEthAdaptCtrl);

    // ... 其他初始化 ...
}
```
*   `EN_MISSION_MODE` 置为 1 表示系统进入了正常的运行模式，CCA 机制也将在这个模式下被激活。

此外，在主自适应序列（定义在 `eth_adapt_seq.c`）的末尾，通常会有一个命令来显式使能 CCA 的各个子任务：
```c
// 文件: x812_rel2p1\eth_adapt_seq.c (相关命令)
// ...
        { eAdaptCmd_PostAdaptCcaEnable  , 0   , 0         },   /* 28, 在主自适应后使能CCA */
// ...
```
当执行到 `eAdaptCmd_PostAdaptCcaEnable` 命令时，`runCommand()` 函数会设置 `gSwAdaptArg2.mCcaEnable` 中的相应位掩码，从而允许特定的 CCA 子任务在后续的 CCA 周期中运行。

### 2. CCA 命令序列

CCA 控制器需要知道在每个周期应该执行哪些校准或自适应任务。这些任务被定义在专门的查找表 (LUT) 中，分为发送端 (TX) 和接收端 (RX) 两部分。

```c
// 文件: x812_rel2p1\adapt_ctrl_derived.c (CCA 命令查找表示例)

// 发送端 (TX) CCA 命令列表
static enum tAdaptCmd_t gTxCcaCmdLut[eEthRxAdapt_MaxTxCcaCmd] =
{
    eAdaptCmd_CcaTxRingOscCal,   // 0: TX 环形振荡器校准
    eAdaptCmd_CcaTxIloPhaseCal,  // 1: TX ILO 相位校准
    eAdaptCmd_CcaTxDacDc,        // 2: TX DAC 直流校准
    eAdaptCmd_CcaTxDacDeskew,    // 3: TX DAC 时钟偏移校准
    eAdaptCmd_None,              // 4: 无操作 (保留)
    // ... 更多 TX CCA 命令或保留位 ...
};

// 接收端 (RX) CCA 命令列表
static enum tAdaptCmd_t gRxCcaCmdLut[eEthRxAdapt_MaxRxCcaCmd] =
{
    eAdaptCmd_CcaRxRingOscCal,       // 0: RX 环形振荡器校准
    eAdaptCmd_None,                  // 1: 无操作
    eAdaptCmd_CcaRxPrIlo,            // 2: RX PR (Pattern Recognizer) ILO 校准
    eAdaptCmd_CcaRxAdcIlo,           // 3: RX ADC ILO 校准
    eAdaptCmd_CcaCDRBalance,         // 4: CDR 平衡
    eAdaptCmd_CcaRxAdcClkCondDc,     // 5: RX ADC 时钟调理器直流校准
    eAdaptCmd_MMDeskewSlow,          // 6: ADC 慢速时钟偏移校准 (来自Ch7)
    eAdaptCmd_SARGainSlow,           // 7: ADC 慢速增益校准 (来自Ch7)
    eAdaptCmd_SAROfstSlow,           // 8: ADC 慢速失调校准 (来自Ch7)
    eAdaptCmd_RunAdaptNtoM,          // 9: 运行一段通用的硬件自适应模式 (N到M)
    eAdaptCmd_NwayAdapt,             // 10: NWay 自适应 (一种协商机制)
    eAdaptCmd_CcaRxAdcClkCondDeskew, // 11: RX ADC 时钟调理器时钟偏移校准
    // ... 更多 RX CCA 命令或保留位 ...
};
```
*   `gTxCcaCmdLut` 和 `gRxCcaCmdLut` 分别定义了发送端和接收端在 CCA 模式下周期性执行的命令序列。
*   每个命令（如 `eAdaptCmd_CcaTxRingOscCal`）都对应一个特定的校准或自适应功能。很多命令，如 `eAdaptCmd_MMDeskewSlow` (ADC Skew 校准慢速版)、`eAdaptCmd_SARGainSlow` (ADC 增益校准慢速版)、`eAdaptCmd_SAROfstSlow` (ADC 失调校准慢速版)，实际上是我们在 [ADC 校准 (ADC Calibration)](07_adc_校准__adc_calibration__.md) 章节中学过的校准过程的变体，通常参数会调整得更保守，以减少对正常工作的影响。
*   `eAdaptCmd_None` 表示该位置没有分配任务，CCA 控制器会跳过。

### 3. CCA 状态机与处理逻辑

CCA 的核心逻辑由 `processTxCcaRequests()` 和 `processRxCcaRequests()` 这两个函数（定义在 `adapt_ctrl_derived.c`）驱动。它们各自管理一个状态机，用于遍历对应的 CCA 命令列表并执行命令。

```c
// 文件: adapt_ctrl_derived.c (CCA处理逻辑简化片段)

// CCA 状态机的状态定义 (示例)
enum eCcaState_t {
    eCcaState_Init,     // 初始化状态
    eCcaState_RunCmd    // 运行命令状态
};

// CCA 状态机结构体
typedef struct tCca_s {
    enum eCcaState_t mState;     // 当前状态
    uint32_t mCcaEnable;         // 使能的CCA命令位掩码
    enum tAdaptCmd_t mCmd;       // 当前正在执行的命令
    uint32_t mCmdIdx;            // 当前命令在LUT中的索引
} tCca_t;

tCca_t gRxCcaFsm[NUM_LANES]; // 每个通道的RX CCA状态机
// tCca_t gTxCcaFsm[NUM_LANES]; // 每个通道的TX CCA状态机 (类似)

bool processRxCcaRequests()
{
    tCca_t* vpFsm = &gRxCcaFsm[gActiveLane]; // 获取当前活动通道的RX CCA状态机
    bool vIterationDone = false; // 当前一轮CCA是否完成的标志

    switch (vpFsm->mState)
    {
        case eCcaState_Init:
            // 当一轮CCA完成或首次启动时，进入初始化状态
            // 从配置中读取哪些RX CCA命令被使能 (gSwAdaptArg2 在 fw_adapt_config.c 中定义)
            vpFsm->mCcaEnable = gSwAdaptArg2.mCcaEnable[gActiveLane].mRx;
            vpFsm->mCmd = eAdaptCmd_None; // 初始设置为无操作
            vpFsm->mCmdIdx = 0;           // 命令索引从0开始
            vpFsm->mState = eCcaState_RunCmd; // 转换到运行命令状态
            break;

        case eCcaState_RunCmd:
            // 执行当前命令 (vpFsm->mCmd)
            // runCommandGated 会检查全局跳过标志并执行命令，返回true表示命令完成
            if (runCommandGated(vpFsm->mCmd))
            {
                // 当前命令已完成，准备处理下一个命令
                if (vpFsm->mCmdIdx >= eEthRxAdapt_MaxRxCcaCmd) // 如果命令索引超出LUT范围
                {
                    vpFsm->mState = eCcaState_Init; // 所有命令已尝试，重置状态机，准备下一轮CCA
                    vIterationDone = true;          // 标记一整轮CCA迭代完成
                }
                else
                {
                    // 检查下一个命令 (由 mCmdIdx 指示) 是否在 mCcaEnable 位掩码中被使能
                    bool vEnabled = (vpFsm->mCcaEnable & (1UL << vpFsm->mCmdIdx)) != 0;
                    // 如果使能，则从 gRxCcaCmdLut 中获取该命令；否则，设置为无操作
                    vpFsm->mCmd = vEnabled ? gRxCcaCmdLut[vpFsm->mCmdIdx] : eAdaptCmd_None;
                    ++vpFsm->mCmdIdx; // 命令索引递增，指向下一个命令
                    // 状态保持在 eCcaState_RunCmd，以便下次调用时继续执行新选定的 vpFsm->mCmd
                }
            }
            // 如果 runCommandGated(vpFsm->mCmd) 返回 false，
            // 说明当前命令 (vpFsm->mCmd) 尚未完成，下次调用 processRxCcaRequests 时会继续执行它。
            break;

        default:
            // 遇到未定义状态，重置状态机
            vpFsm->mState = eCcaState_Init;
            break;
    }
    return vIterationDone; // 返回当前CCA迭代是否完成
}
```
*   **状态机 (`tCca_t`)**：每个通道的CCA（无论是TX还是RX）都有一个状态机 (`gRxCcaFsm[gActiveLane]`)。它包含当前状态 (`mState`)、一个位掩码 (`mCcaEnable`) 用于指示哪些CCA子任务被允许运行、当前正在执行的命令 (`mCmd`) 以及当前命令在LUT中的索引 (`mCmdIdx`)。
*   **初始化 (`eCcaState_Init`)**：在此状态下，状态机会从全局配置 (`gSwAdaptArg2.mCcaEnable`) 中加载当前通道允许运行的CCA任务列表（位掩码形式）。然后重置命令索引和当前命令，并转换到 `eCcaState_RunCmd` 状态。
*   **运行命令 (`eCcaState_RunCmd`)**：
    *   它调用 `runCommandGated(vpFsm->mCmd)` 来执行当前选定的CCA命令。`runCommandGated` 最终会调用我们在 [接收器自适应引擎](01_接收器自适应引擎_.md) 章节中见过的 `runCommand` 函数。这个函数会根据命令类型分派到具体的校准或自适应例程。
    *   如果 `runCommandGated` 返回 `true`（表示当前CCA命令执行完毕），状态机会检查是否已经遍历完整个CCA命令列表 (`gRxCcaCmdLut`)。
        *   如果是，则表示一轮CCA迭代完成，状态机将重置回 `eCcaState_Init`，并返回 `true`。
        *   如果否，它会根据 `mCcaEnable` 位掩码和 `mCmdIdx` 查找下一个被使能的CCA命令。如果找到，就将其设置为 `vpFsm->mCmd`，并增加 `mCmdIdx`。下次 `processRxCcaRequests` 被调用时，就会执行这个新的命令。如果下一个命令未被使能，`vpFsm->mCmd` 会被设为 `eAdaptCmd_None`（无操作），状态机同样会跳到下下个命令。
    *   如果 `runCommandGated` 返回 `false`（表示当前CCA命令尚未完成），则状态机保持不变，下次调用时会继续执行同一个命令。
*   `processTxCcaRequests()` 的逻辑与 `processRxCcaRequests()` 非常相似，只是它使用 `gTxCcaFsm` 和 `gTxCcaCmdLut`。

### 4. CCA 子任务示例

CCA 通过 `runCommand` 执行的子任务多种多样，很多是前面章节内容的“CCA版本”。

*   **ILO 校准 (`ilo_cal.c`, `ilo_cal_derived.c`)**：
    *   命令如 `eAdaptCmd_CcaTxIloPhaseCal`、`eAdaptCmd_CcaRxPrIlo`、`eAdaptCmd_CcaRxAdcIlo`。
    *   这些命令会调用 `iloPhaseCal()` 或 `iloFreqCal()` 函数。ILO（注入锁定振荡器）是芯片内部一种重要的时钟源，其频率和相位的稳定性对系统性能至关重要。CCA会定期微调它们。
    *   `iloPhaseCal()` 函数接受一个 `aCalMode` 参数。当以 `eCalMode_Cca` 模式调用时（如 `iloPhaseCal(eIloCalConst_TxIlo, eCalMode_Cca)`），校准的迭代次数会受到限制（`eIloPhaseCalConst_MaxTuneIter`），确保CCA任务不会运行太久。

    ```c
    // 文件: ilo_cal.c (iloPhaseCal 片段，展示CCA模式下的迭代限制)
    bool iloPhaseCal(enum tIloCalConst_t aIloPhaseType, enum tCalMode_t aCalMode)
    {
        // ...
        switch (vpIloPhaseCalState->mIloPhaseCalState)
        {
            // ...
            case eIloPhaseCalState_Meas:
            {
                // 如果是CCA模式，并且迭代次数达到上限，则结束
                if (vpIloPhaseCalState->mIter >= eIloPhaseCalConst_MaxTuneIter && aCalMode == eCalMode_Cca)
                {
                    vpIloPhaseCalState->mIloPhaseCalState = eIloPhaseCalState_Done;
                    break;
                }
                // ... 执行测量 ...
            }
            // ...
        }
        return vDone;
    }
    ```

*   **环形振荡器校准 (`ro_cal_derived.c`)**：
    *   命令如 `eAdaptCmd_CcaTxRingOscCal`、`eAdaptCmd_CcaRxRingOscCal`。
    *   这些命令会调用 `ringOscCalControl()`。环形振荡器（RO）是另一种片上时钟源。
    *   同样，`ringOscCalControl()` 函数也接受 `aCalMode` 参数，当以 `eCalMode_Cca` 调用时，其内部迭代次数 (`vpFsm->mIter`) 也会受到 `eRoCfgConst_MaxIter` 的限制。

*   **ADC 校准 (慢速/精细模式)**：
    *   命令如 `eAdaptCmd_MMDeskewSlow`、`eAdaptCmd_SARGainSlow`、`eAdaptCmd_SAROfstSlow`。
    *   它们分别调用 `rxAdcIntlCal(eCalMode_Fine)`（精细模式的Skew校准）、`rxSarGain(false)`（慢速增益校准）和 `rxSarOffset(false)`（慢速失调校准）。这些函数我们在 [ADC 校准 (ADC Calibration)](07_adc_校准__adc_calibration__.md) 章节已经学习过，这里的“慢速”或“精细”通常意味着使用更小的调整步长和/或更少的迭代次数，以适应CCA的非破坏性要求。

*   **其他校准**：
    *   `eAdaptCmd_CcaCDRBalance`：调用 `cdrFfeCm1PowerBalance()`（来自 [CDR 自适应 (CDR Adaptation)](04_cdr_自适应__cdr_adaptation__.md)），使用专门为CCA配置的参数（如迭代次数、目标偏移、硬件自适应模式范围）。
    *   `eAdaptCmd_CcaTxDacDc`, `eAdaptCmd_CcaTxDacDeskew`：调用 `txDacCal()` (在 `tx_dac_output_cal.c`)，使用 `eCalMode_Fine`。
    *   `eAdaptCmd_CcaRxAdcClkCondDc`, `eAdaptCmd_CcaRxAdcClkCondDeskew`：调用 `processAdcCndInitDcSkewCal()` 或 `processRxPrClkDeskew()` (在 `clk_cond_cal.c` 或 `rx_pr_input_cal_derived.c`)，使用 `eCalMode_Fine`。

### 5. CCA 配置

哪些CCA任务被执行，以及它们的一些参数，可以通过固件配置来设定。`gSwAdaptArg2` 结构体 (在 `fw_adapt_config.c` 中定义) 扮演了重要角色。

```c
// 文件: fw_adapt_config.c (gSwAdaptArg2.mCcaEnable 示意)
// 该文件已在教程前文的上下文中提供，这里仅作概念性回顾

// struct tSwAdaptArg2_t gSwAdaptArg2 = {
//    ...
//    // mCcaEnable 数组为每个通道存储一个结构体，
//    // 该结构体包含 .mTx 和 .mRx 两个位掩码字段。
//    // 每个位掩码中的每一位对应 gTxCcaCmdLut 或 gRxCcaCmdLut 中的一个命令。
//    // 如果某位为1，则对应的CCA命令被使能；为0则禁用。
//    .mCcaEnable = {
//        [0] = {.mTx = 0xF, .mRx = 0xFFF }, // 通道0: TX CCA使能掩码, RX CCA使能掩码
//        [1] = {.mTx = 0xF, .mRx = 0xFFF }, // 通道1
//        // ... 其他通道 ...
//    },
//    // ... 其他如CDR平衡迭代次数 (mL0Iter)、目标偏移 (mL0CdrOffset) 等参数 ...
// };
```
通过修改 `mCcaEnable` 中的位掩码，开发者可以灵活地控制在特定产品或应用场景下，哪些CCA子任务应该被激活。例如，`0xF` (二进制 `00001111`) 作为 TX 的掩码，意味着 `gTxCcaCmdLut` 中的前四个命令会被执行。

## 总结

在本章中，我们探索了“连续校准与自适应 (CCA)”机制。我们了解到：

*   CCA 是设备在正常工作模式下，后台持续运行的校准和自适应过程，旨在补偿因环境变化和器件老化带来的性能漂移，确保链路长期稳定。
*   CCA 像一个自动巡航系统，周期性地、非破坏性地微调硬件参数。
*   CCA 的核心是一个调度控制器（如 `processRxCcaRequests`），它按顺序执行预定义的、在配置中被使能的 CCA 子任务。
*   这些子任务（定义在 `gTxCcaCmdLut` 和 `gRxCcaCmdLut` 中）通常是标准校准过程的“轻量级”版本，例如慢速ADC校准、ILO/RO振荡器微调、CDR平衡等。
*   CCA 的行为（如哪些任务执行，以及任务的一些参数）可以通过固件配置（如 `gSwAdaptArg2.mCcaEnable`）进行定制。
*   CCA 的各个子任务在设计时都考虑了其执行模式（如 `eCalMode_Cca` 或 `eCalMode_Fine`），以确保它们对正常数据传输的影响最小。

CCA 机制是确保高速串行链路在复杂多变的真实环境中能够长期保持高性能和高可靠性的关键保障。它体现了现代通信芯片设计的智能化和自适应能力。

到目前为止，我们已经学习了接收器自适应的许多方面，从初始的链路建立、各种均衡器的优化，到ADC的精确校准，再到CCA提供的持续维护。这些功能大多集中在单个通道（Lane）内部的优化。但是，一个完整的高速接口通常由多个并行的通道组成。

在下一章，我们将学习 [PMD 通道控制 (PMD Lane Control)](09_pmd_通道控制__pmd_lane_control__.md)，了解系统是如何管理和控制这些并行通道，以及它们之间是如何协同工作的。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)