# Chapter 4: CDR 自适应 (CDR Adaptation)


欢迎来到 `hw` 项目教程的第四章！在上一章 [链路训练 (Link Training)](03_链路训练__link_training__.md) 中，我们学习了通信双方设备如何通过“握手”和“协商”来优化远端发送器的参数，从而建立一条初步可用的通信链路。这就像我们找到了正确的电台频道。但是，仅仅找到频道还不够，我们还需要微调旋钮，让声音最清晰，消除噪音和干扰。在数字通信中，这个“微调”的过程就和我们本章要学习的 **CDR 自适应 (CDR Adaptation)** 密切相关。

## 什么是 CDR 自适应？

想象一下，你正在努力辨认一段语速很快、且夹杂着些许杂音的录音。你需要非常专注，准确地捕捉每个字词的开始和结束，才能理解内容。如果你的“耳朵”能自动调整，过滤掉一些噪音，并精确地跟上说话人的节奏，那就太棒了！

在高速数据传输中，接收器也面临类似的挑战。数据信号在传输过程中，会因为各种原因（如线缆质量、外部干扰）而产生**抖动 (Jitter)**（时钟信号在时间轴上的不规则晃动）和**噪声 (Noise)**。这些都会导致信号的边缘变得模糊，使得接收器很难在正确的时间点对数据进行采样。如果采样时间不对，就可能把“0”误判为“1”，或者把“1”误判为“0”，这就是所谓的**误码 (Bit Error)**。

**CDR (Clock and Data Recovery, 时钟和数据恢复)** 模块是接收器的核心组成部分之一。它的主要任务是：

1.  **时钟恢复 (Clock Recovery)**：从接收到的、可能带有抖动的串行数据信号中提取出一个干净、稳定的时钟信号。这个时钟信号将指导接收器何时对数据进行采样。
2.  **数据恢复 (Data Recovery)**：使用恢复出来的时钟，在数据的最佳位置进行采样，从而准确地还原原始的数字比特流。

**CDR 自适应 (CDR Adaptation)** 则是一个动态的优化过程。你可以把它想象成一个非常精密的“调谐器”或者“校准师”。它会持续监控接收信号的状况，并不断调整 CDR 模块内部的参数，以及一个位于 CDR 路径内部的特殊 **FFE (Feed-Forward Equalizer, 前馈均衡器)** 的系数。

这个内部 FFE 与我们在 [FFE 自适应 (FFE Adaptation)](05_ffe_自适应__ffe_adaptation__.md) 章节将要学习的主 FFE 不同，它是 CDR 为了更好地完成自身任务而使用的一个“辅助工具”。CDR 自适应调整这些参数的目的，就是为了让恢复出来的时钟能够**精确地对准数据信号的最佳采样点**，即使在信号存在抖动和噪声的情况下，也能**最大限度地减少误码**。

CDR 自适应模块会调整的关键参数包括：

*   **CDR 环路参数**：例如环路增益 (Gain)、滤波器特性 (Filter Characteristics)。这些参数影响 CDR 跟踪输入信号抖动的速度和精度。
*   **CDR 内部 FFE 系数**：调整这些系数可以对进入 CDR 判决电路前的信号进行细微的整形，以补偿一部分残留的码间干扰 (ISI)，帮助 CDR 更清晰地看到数据转换的边缘。

其中一个重要的自适应算法是 `cdrFfeCm1PowerBalance`，它专门用于平衡 CDR 内部 FFE 特定抽头的“功率”贡献，我们稍后会详细了解。

## CDR 自适应是如何工作的？

CDR 自适应通常由[接收器自适应引擎](01_接收器自适应引擎_.md)在特定的自适应阶段（例如，在执行 `runAdaptModes` 时）触发和管理。它的工作可以概括为以下几个步骤：

1.  **评估**：CDR 模块或者相关的监测电路会间接或直接地评估当前时钟恢复和数据采样的质量。这可能通过内部的眼图监控、错误计数或其他性能指标来完成。
2.  **调整**：根据评估结果，自适应算法会决定如何调整 CDR 环路参数或其内部 FFE 的系数。例如，如果检测到时钟相位滞后，可能会调整相位插值器的控制信号；如果发现 FFE 的预设抽头和后设抽头的贡献不平衡，可能会调整某个抽头的系数。
3.  **迭代**：这个“评估-调整”的过程会不断重复，直到达到一个稳定的、误码率最低的状态，或者完成了预设的调整次数。

下面我们通过一个简化的时序图来看看 CDR 自适应（特别是 FFE 功率平衡）大致是如何与接收器自适应引擎协同工作的：

```mermaid
sequenceDiagram
    participant 接收器自适应引擎 as "接收器自适应引擎"
    participant CDR自适应模块 as "CDR自适应模块"
    participant CDR硬件及内部FFE as "CDR硬件及内部FFE"

    接收器自适应引擎->>CDR自适应模块: 请求执行CDR自适应 (例如调用 cdrFfeCm1PowerBalance)
    CDR自适应模块->>CDR自适应模块: (1) 初始化算法参数
    loop 多次迭代调整
        CDR自适应模块->>CDR硬件及内部FFE: (2) 读取当前CDR FFE抽头值/状态
        CDR自适应模块->>CDR自适应模块: (3) 计算如何调整参数 (如FFE抽头功率)
        CDR自适应模块->>CDR硬件及内部FFE: (4) 更新CDR环路参数或FFE系数
        CDR自适应模块->>接收器自适应引擎: (可选) 请求运行一轮本地硬件自适应 (runAdaptModes)
        接收器自适应引擎-->>CDR自适应模块: 本地硬件自适应完成
        CDR自适应模块->>CDR自适应模块: (5) 评估调整效果
    end
    CDR自适应模块-->>接收器自适应引擎: CDR自适应完成
end
```
这个图展示了 CDR 自适应模块如何通过一系列的读、算、写操作，并可能借助[接收器自适应引擎](01_接收器自适应引擎_.md)来运行更广泛的硬件自适应，从而达到优化 CDR 性能的目的。

## 深入探索：代码中的 CDR 自适应

现在，让我们深入 `adapt_cdr.c` 文件，看看 CDR 自适应是如何在代码层面实现的。

### 1. 初始化 CDR 自适应参数：`initCdrAdapt()`

在 CDR 自适应算法开始运行之前，需要为 CDR 模块加载一些初始配置参数。这些参数很多来自于我们在 [配置管理 (Configuration Management)](02_配置管理__configuration_management__.md) 章节中学习到的 `gFwAdaptConfig` 结构体。`initCdrAdapt()` 函数就负责这个任务。

```c
// 文件: adapt_cdr.c (简化片段)

#include "adapt_cdr.h"
#include "fw_adapt_config.h" // 包含 gFwAdaptConfig
#include "rx_reg_structs.h"  // 包含寄存器结构体定义

/*!
 * @brief 加载 CDR 设置到寄存器
 */
void initCdrAdapt()
{
    // 从 gFwAdaptConfig 中读取 CDR 环路滤波器的慢速和快速增益控制参数
    RX__CDR_CONFIG0_T vConfig0 = READ_REG(RX_REG_BASE, RX__CDR_CONFIG0);
    vConfig0.mFields.PI_SLOW_GAIN_CTRL = gFwAdaptConfig.mCdrPhugSlow; // PI环慢速增益
    vConfig0.mFields.PI_FAST_GAIN_CTRL = gFwAdaptConfig.mCdrPhugFast; // PI环快速增益
    WRITE_REG(RX_REG_BASE, RX__CDR_CONFIG0, vConfig0);

    // 设置 MM CDR 积分器慢速增益
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__CDR_CONFIG1, MM_CDR_INTEG_SLOW_GAIN_CTRL, gFwAdaptConfig.mCdrFrugSlow);
    // 设置 MM CDR 积分器快速增益
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__CDR_CONFIG4, MM_CDR_INTEG_FAST_GAIN_CTRL, gFwAdaptConfig.mCdrFrugFast);

    // 设置其他 CDR 相关参数，如饱和值、回滚值、KV 控制等
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__RXS_CFG2, MM_CDR_INTEG_ACC_SAT_VALUE, gFwAdaptConfig.mCdrIntegAccSatValue);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__RXS_CFG0, MM_KV_CTRL, gFwAdaptConfig.mCdrKvCtrl);
}
```

*   这个函数从 `gFwAdaptConfig` (在 `fw_adapt_config.c` 中定义) 读取预设的 CDR 参数值，如 `mCdrPhugSlow` (CDR PI 环慢速增益)、`mCdrFrugFast` (CDR 积分器快速增益) 等。
*   然后，它通过 `WRITE_REG` 或 `WRITE_REG_FIELD_NEW` 将这些值写入到接收器 (RX) 模块内相应的 CDR 配置寄存器中（如 `RX__CDR_CONFIG0`, `RX__CDR_CONFIG1` 等）。
*   这为 CDR 模块提供了一个良好的初始工作点。

### 2. CDR FFE 抽头功率平衡：`cdrFfeCm1PowerBalance()`

`cdrFfeCm1PowerBalance` 函数是 CDR 自适应中一个非常关键的算法。CDR 内部有一个小型的 FFE，用于在信号进入最终判决前进行精细调整。这个 FFE 也有多个抽头（Taps），比如前置抽头 (Pre-cursor taps)、主抽头 (Cursor tap) 和后置抽头 (Post-cursor taps)。这些抽头的系数值决定了它们对信号的“贡献”或“功率”。

如果前置抽头和后置抽头的总体“功率”不平衡，可能会导致恢复出的时钟偏离最佳采样点。`cdrFfeCm1PowerBalance` 的目标就是通过调整其中一个关键的前置抽头，通常是 **Cm1 (即 Pre1，CDR FFE 的第一个前置抽头，对应代码中的 `DIG_CDR_FFE_COEFF_C11`)**，来使得前置抽头总功率和后置抽头总功率达到一个预设的平衡关系（或者说一个目标偏移量 `aPowerOffset`）。

这个函数通常以状态机的方式实现：

```c
// 文件: adapt_cdr.c (简化片段)

// 枚举定义了 cdrFfeCm1PowerBalance 状态机的状态
enum eCm1PwrBalanceState_t
{
    ePwrBalance_Setup,      // 设置阶段
    ePwrBalance_Balance,    // 平衡调整阶段
    ePwrBalance_RunAdapt,   // 运行本地自适应阶段
    ePwrBalance_End         // 结束阶段
};

// 存储 Cm1 功率平衡状态的结构体 (简化)
struct tCm1PwrBalance_t {
    enum eCm1PwrBalanceState_t mCm1PwrBalanceState; // 当前状态
    uint32_t mCm1PwrBalanceCnt; // 当前迭代次数
    int32_t mCm1;               // 当前软件中 Cm1 (Pre1) 的目标值 (定点数)
    int32_t mDir;               // 上一次调整 Cm1 的方向 (+1 或 -1)
    // ... 其他成员 ...
};

// 全局变量，存储每个通道的 Cm1 功率平衡状态 (gRx 和 gActiveLane 在其他地方定义)
// struct tRxLaneAdaptState_t gRx[NUM_LANES];
// gRx[gActiveLane].mAdapt.mCm1PwrBalance

/*!
 * @brief 运行 CDR FFE Cm1 功率平衡算法
 *
 * @param[in] aIterations  要运行的平衡-自适应迭代次数
 * @param[in] aPowerOffset 前置/后置抽头之间的目标功率偏移 (Q23.8格式)
 * @param[in] aMu          调整 Cm1 抽头时的步长 (Q23.8格式)
 * @param[in] aStartMode   运行本地自适应的起始模式
 * @param[in] aEndMode     运行本地自适应的结束模式
 * @return 如果为 true，则完成；否则，进行中，稍后再次调用此函数
 */
bool cdrFfeCm1PowerBalance(uint32_t aIterations, int32_t aPowerOffset, int32_t aMu, uint32_t aStartMode, uint32_t aEndMode)
{
    bool vDone = false;
    // 获取当前活动通道的功率平衡状态机指针
    struct tCm1PwrBalance_t* vpPwrBalance = &gRx[gActiveLane].mAdapt.mCm1PwrBalance;

    switch (vpPwrBalance->mCm1PwrBalanceState)
    {
        case ePwrBalance_Setup: // 初始化阶段
        {
            vpPwrBalance->mCm1PwrBalanceCnt = 0; // 重置迭代计数器
            // 读取当前硬件中的 Cm1 (DIG_CDR_FFE_COEFF_C11) 值作为初始 mCm1
            vpPwrBalance->mCm1 = signExtend32(READ_REG_FIELD_NEW(RX_REG_BASE, RX__DIG_CDR_OVRDVAL30, DIG_CDR_FFE_COEFF_C11), eAdaptCdr_CdrFfeC11Bits);
            // ... 其他初始化 ...

            // 设置 CDR FFE 抽头训练的初始"提示" (hint) 值
            // setPwrBalanceHint() 会读取当前 DIG_CDR_OVRDVALxx 中的所有 CDR FFE 系数值
            // 并将它们写入到 RX__CDR_FFE_TRAININGx 寄存器的 HINT 字段
            setPwrBalanceHint();

            vpPwrBalance->mCm1PwrBalanceState = ePwrBalance_Balance; // 进入平衡调整阶段
            break;
        }

        case ePwrBalance_Balance: // 平衡调整阶段
        {
            // 计算 CDR FFE 前置抽头总功率 (简化：假设 getCdrPowerPre() 完成)
            int32_t vPowerPre = getCdrPowerPre();
            // 计算 CDR FFE 后置抽头总功率 (简化：假设 getCdrPowerPost() 完成)
            int32_t vPowerPost = getCdrPowerPost();

            // 根据功率差异，决定如何调整软件中的 Cm1 值
            if (vPowerPost > vPowerPre + aPowerOffset)
            {
                vpPwrBalance->mDir = -1; // 后置功率大，Cm1 需要减小 (更负或更小的正)
                vpPwrBalance->mCm1 -= aMu;
            }
            else
            {
                vpPwrBalance->mDir = 1;  // 前置功率大 (或后置不足)，Cm1 需要增大
                vpPwrBalance->mCm1 += aMu;
            }

            // 限制 Cm1 的调整范围
            if (vpPwrBalance->mCm1 < eAdaptCdr_CdrFfeC11Min) vpPwrBalance->mCm1 = eAdaptCdr_CdrFfeC11Min;
            else if (vpPwrBalance->mCm1 > eAdaptCdr_CdrFfeC11Max) vpPwrBalance->mCm1 = eAdaptCdr_CdrFfeC11Max;

            // 将调整后的软件 Cm1 值 (vpPwrBalance->mCm1) 更新到 CDR FFE 的 C11 "提示"寄存器
            // 注意：setPwrBalanceHint() 在Setup阶段已经设置了所有其他抽头的提示值。
            // 这里我们只特别更新 C11 的提示值。
            uint32_t vCm1Fixed = *(uint32_t*)(&vpPwrBalance->mCm1); //转换为无符号整数写入寄存器
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__CDR_FFE_TRAINING4, CDR_FFE_COEFF_HINT_C11, vCm1Fixed);

            // 加载所有提示值到硬件，让 CDR 内部 FFE 使用新的提示值进行工作
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING14, CDR_FFE_COEFF_HINT_LOAD, 0);
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING14, CDR_FFE_COEFF_HINT_LOAD, 1); // 脉冲加载
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING14, CDR_FFE_COEFF_HINT_LOAD, 0);

            vpPwrBalance->mCm1PwrBalanceState = ePwrBalance_RunAdapt; // 进入运行本地自适应阶段
            break;
        }

        case ePwrBalance_RunAdapt: // 运行本地自适应阶段
        {
            // 调用接收器自适应引擎的 runAdaptModes 函数，
            // 运行一系列预定义的硬件自适应模式 (aStartMode 到 aEndMode)。
            // 这使得接收器的其他部分（包括CDR本身）能够适应新的 Cm1 设置。
            if (runAdaptModes(aStartMode, aEndMode))
            {
                // ... (检查是否需要提前退出，例如调整方向来回摆动) ...

                vpPwrBalance->mCm1PwrBalanceCnt++; // 增加迭代计数
                if (vpPwrBalance->mCm1PwrBalanceCnt < aIterations)
                {
                    vpPwrBalance->mCm1PwrBalanceState = ePwrBalance_Balance; // 继续下一轮平衡调整
                }
                else
                {
                    vpPwrBalance->mCm1PwrBalanceState = ePwrBalance_End; // 达到迭代次数，结束
                }
            }
            // 如果 runAdaptModes() 返回 false，则表示本地自适应未完成，下次调用时会继续。
            break;
        }

        case ePwrBalance_End: // 结束阶段
        default:
        {
            vpPwrBalance->mCm1PwrBalanceState = ePwrBalance_Setup; // 重置状态机为 Setup，以便下次调用
            vDone = true; // 标记整个功率平衡过程完成
            break;
        }
    }
    return vDone;
}
```

*   **状态机**：`cdrFfeCm1PowerBalance` 通过 `mCm1PwrBalanceState` 在几个状态之间切换：
    *   `ePwrBalance_Setup`：进行初始化，包括读取当前的 Cm1 值，并使用 `setPwrBalanceHint()` 设置 CDR FFE 所有抽头的初始“提示”值。
    *   `ePwrBalance_Balance`：核心调整逻辑。它调用 `getCdrPowerPre()` 和 `getCdrPowerPost()`（我们稍后会看这两个函数）来获取 CDR FFE 前置和后置抽头的当前总功率。然后根据它们与目标偏移 `aPowerOffset` 的比较结果，使用步长 `aMu` 来增加或减少软件中 `mCm1` 的值。调整后的 `mCm1` 会被写入到 `RX__CDR_FFE_TRAINING4` 寄存器的 `CDR_FFE_COEFF_HINT_C11` 字段，然后通过 `CDR_FFE_COEFF_HINT_LOAD` 脉冲加载到硬件中。
    *   `ePwrBalance_RunAdapt`：调用 `runAdaptModes(aStartMode, aEndMode)`。这个函数我们已经在 [接收器自适应引擎](01_接收器自适应引擎_.md) 章节见过，它会启动硬件执行一系列预定义的自适应模式。这允许 CDR 环路以及接收器的其他部分（如 CTLE、VGA）对 Cm1 的变化做出反应并进行相应的调整。
    *   `ePwrBalance_End`：表示当前轮次的功率平衡已完成。
*   **迭代**：整个过程会重复 `aIterations` 次，或者直到满足某些提前退出的条件。
*   **提示 (Hint)**：`setPwrBalanceHint()` 函数和对 `CDR_FFE_COEFF_HINT_C11` 的直接写入，是将软件计算出的 FFE 系数值“提示”给 CDR 内部的 FFE 硬件自适应逻辑的一种方式。硬件可以利用这些提示值作为其自身优化算法的起点。

#### 辅助函数：`setPwrBalanceHint()`

这个函数负责将当前 CDR FFE 的所有抽头系数（通常从 `DIG_CDR_OVRDVALxx` 寄存器读取，这些寄存器反映了固件或硬件最后确定的 CDR FFE 系数值）加载到 `RX__CDR_FFE_TRAININGx` 寄存器中的相应 `_HINT_` 字段。

```c
// 文件: adapt_cdr.c (简化片段)

/*!
 * @brief 设置 CDR FFE 提示值用于功率平衡
 *
 * 将当前 CDR FFE 系数设置为训练提示值
 */
static void setPwrBalanceHint(void)
{
    // 首先确保加载位为0
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING14, CDR_FFE_COEFF_HINT_LOAD, 0);

    // 读取 DIG_CDR_OVRDVAL58 寄存器中存储的 CDR FFE Post 10 到 Post 7 系数值
    RX__DIG_CDR_OVRDVAL58_T vOvrdVal58 = READ_REG(RX_REG_BASE, RX__DIG_CDR_OVRDVAL58);
    // 读取 CDR_FFE_TRAINING0 寄存器，准备写入提示值
    RX__CDR_FFE_TRAINING0_T vTraining0 = READ_REG(RX_REG_BASE, RX__CDR_FFE_TRAINING0);
    // 将读取到的值写入到提示字段
    vTraining0.mFields.CDR_FFE_COEFF_HINT_C0 = vOvrdVal58.mFields.DIG_CDR_FFE_COEFF_C0; // Post 10
    vTraining0.mFields.CDR_FFE_COEFF_HINT_C1 = vOvrdVal58.mFields.DIG_CDR_FFE_COEFF_C1; // Post 9
    // ... (设置 C2, C3) ...
    WRITE_REG(RX_REG_BASE, RX__CDR_FFE_TRAINING0, vTraining0);

    // 类似地为其他抽头 (C4-C8, C9-C11, C12-C14) 设置提示值
    // ... (省略了对 RX__CDR_FFE_TRAINING1, RX__CDR_FFE_TRAINING2,
    //             RX__CDR_FFE_TRAINING4, RX__CDR_FFE_TRAINING3 的操作) ...
    // 例如，设置 Cm1 (Pre1, 即 C11) 的提示值
    RX__DIG_CDR_OVRDVAL30_T vOvrdVal30 = READ_REG(RX_REG_BASE, RX__DIG_CDR_OVRDVAL30);
    RX__CDR_FFE_TRAINING4_T vTraining4 = READ_REG(RX_REG_BASE, RX__CDR_FFE_TRAINING4);
    vTraining4.mFields.CDR_FFE_COEFF_HINT_C11 = vOvrdVal30.mFields.DIG_CDR_FFE_COEFF_C11; // Pre 1
    WRITE_REG(RX_REG_BASE, RX__CDR_FFE_TRAINING4, vTraining4);
}
```
这个函数从多个 `DIG_CDR_OVRDVALxx` 寄存器（这些寄存器保存了 CDR FFE 各个抽头的当前值，可能是硬件自适应的结果，也可能是固件直接写入的覆盖值）中读取值，然后将它们写入到 `RX__CDR_FFE_TRAININGx` 寄存器对应的 `CDR_FFE_COEFF_HINT_Cx` 字段。这些 `_HINT_` 值随后可以被 CDR 内部的 FFE 硬件训练逻辑用作初始值或指导。

#### 辅助函数：`getCdrPowerPre()` 和 `getCdrPowerPost()`

这两个函数用于计算 CDR 内部 FFE 的前置抽头和后置抽头的总“功率”或影响。它们读取相应抽头的系数值（同样来自 `DIG_CDR_OVRDVALxx` 寄存器），进行符号扩展（因为系数值可能是有符号数），然后累加起来。注意，某些抽头的贡献可能是负的，这取决于 FFE 的具体实现。

```c
// 文件: adapt_cdr.c (简化片段)

/*!
 * @brief 计算 CDR FFE 前置抽头功率偏移, Q23.8 格式
 */
int32_t getCdrPowerPre()
{
    int32_t vPowerPre = 0;
    // Pre 1 (Cm1, 即 C11)
    vPowerPre += -1 * signExtend32(READ_REG_FIELD_NEW(RX_REG_BASE, RX__DIG_CDR_OVRDVAL30, DIG_CDR_FFE_COEFF_C11), eAdaptCdr_CdrFfeC11Bits);
    // Pre 2 (C12)
    vPowerPre +=      signExtend32(READ_REG_FIELD_NEW(RX_REG_BASE, RX__DIG_CDR_OVRDVAL29, DIG_CDR_FFE_COEFF_C12), eAdaptCdr_CdrFfeC12Bits);
    // ... (累加其他前置抽头 C13, C14 的贡献) ...
    return vPowerPre;
}

/*!
 * @brief 计算 CDR FFE 后置抽头功率偏移, Q23.8 格式
 */
int32_t getCdrPowerPost()
{
    int32_t vPowerPost = 0;
    // Post 10 (C0)
    vPowerPost +=      signExtend32(READ_REG_FIELD_NEW(RX_REG_BASE, RX__DIG_CDR_OVRDVAL58, DIG_CDR_FFE_COEFF_C0), eAdaptCdr_CdrFfeC0Bits);
    // Post 9 (C1)
    vPowerPost += -1 * signExtend32(READ_REG_FIELD_NEW(RX_REG_BASE, RX__DIG_CDR_OVRDVAL58, DIG_CDR_FFE_COEFF_C1), eAdaptCdr_CdrFfeC1Bits);
    // ... (累加其他后置抽头 C2 到 C9 的贡献) ...
    return vPowerPost;
}
```
*   `signExtend32(value, bits)` 是一个实用函数，用于将一个特定位数 `bits` 的有符号数 `value` 扩展到32位有符号整数。
*   `eAdaptCdr_CdrFfeCxBits` 是一个枚举或宏，定义了对应抽头系数的位数。
*   这些函数读取 CDR FFE 各个抽头的系数值，并根据其对信号的贡献方式（正或负）进行加权求和，得到前置和后置抽头的总功率值。

### 3. CDR 功率偏移扫描：`cdrPwrOfstSweep()`

在某些情况下，简单地将前置和后置功率平衡（即目标偏移为0）可能不是最优的。`cdrPwrOfstSweep()` 函数通过尝试一系列不同的目标功率偏移值（`aPowerOffset`）来进行优化。对于每个尝试的偏移值，它会调用 `cdrFfeCm1PowerBalance()` 来进行功率平衡，然后使用 `fomMeas()`（一个用于测量信号质量，即 Figure of Merit 的函数）来评估结果。最后，它会选择产生最佳 FOM 的那个功率偏移值作为最终设置。

```c
// 文件: adapt_cdr.c (简化片段)

// 枚举定义了 cdrPwrOfstSweep 状态机的状态 (简化)
enum ePwrOfstState_t
{
    ePwrOfst_Init,                  // 初始化
    ePwrOfst_RunCm1PowerBalance1,   // 运行第一轮功率平衡
    ePwrOfst_GetFomMeas,            // 获取 FOM 测量结果
    ePwrOfst_RunAdapt,              // （可选）在选择最佳偏移后运行自适应
    ePwrOfst_RunCm1PowerBalance2,   // 使用最佳偏移运行最终功率平衡
    // ... 其他状态，如重试 ...
};

/*!
 * @brief CDR 功率偏移扫描自适应的状态机
 *
 * @param[in] aOffsetStart CDR 功率偏移扫描的起始值 (Q23.8)
 * @param[in] aOffsetEnd   CDR 功率偏移扫描的结束值 (Q23.8)
 * @param[in] aOffsetStep  CDR 功率偏移扫描的步长 (Q23.8)
 * @return 如果为 true，则完成；否则，进行中
 */
bool cdrPwrOfstSweep(int32_t aOffsetStart, int32_t aOffsetEnd, int32_t aOffsetStep)
{
    bool vDone = false;
    // 获取当前活动通道的功率偏移扫描状态机指针
    tPwrOfstSweep_t* vpFsm = &gRx[gActiveLane].mAdapt.mPwrOfstSweep;

    switch (vpFsm->mState)
    {
        case ePwrOfst_Init:
            vpFsm->mOffset = aOffsetStart; // 当前尝试的偏移值
            vpFsm->mBestOffset = aOffsetStart; // 记录的最佳偏移值
            vpFsm->mCtleBestFomMeas = eAdaptCdr_FomMaxVal; // 记录的最佳 FOM (初始为最差)
            // ... 其他初始化 ...
            setPwrOffsetHint(); // 设置用于偏移扫描的初始 FFE 提示值
            vpFsm->mState = ePwrOfst_RunCm1PowerBalance1;
            break;

        case ePwrOfst_RunCm1PowerBalance1:
            // 使用当前 vpFsm->mOffset 作为目标偏移，调用 cdrFfeCm1PowerBalance
            if (cdrFfeCm1PowerBalance(eAdaptCdr_PowerBalanceIters, vpFsm->mOffset, ...))
            {
                // ... (检查是否需要重试功率平衡) ...
                vpFsm->mState = ePwrOfst_GetFomMeas; // 功率平衡完成，去测量 FOM
            }
            break;

        case ePwrOfst_GetFomMeas:
            uint32_t vFom;
            if (fomMeas(&vFom)) // 如果 FOM 测量完成
            {
                if (vFom < vpFsm->mCtleBestFomMeas) // 如果当前 FOM 更好
                {
                    vpFsm->mCtleBestFomMeas = vFom; // 更新最佳 FOM
                    vpFsm->mBestOffset = vpFsm->mOffset; // 更新最佳偏移值
                }

                vpFsm->mOffset += aOffsetStep; // 移动到下一个要尝试的偏移值
                if (/* 是否已尝试完所有偏移值 */ ((aOffsetStep > 0 && vpFsm->mOffset > aOffsetEnd) || (aOffsetStep < 0 && vpFsm->mOffset < aOffsetEnd) || aOffsetStep == 0) )
                {
                    // ... (保存最佳偏移值到 gSwAdaptArg2) ...
                    // 如果只扫描了一个点，或者扫描范围结束，则准备应用最佳偏移或结束
                    if (/* 只有一个扫描点或扫描结束 */ true) { // 简化条件
                         // 如果不是只扫描一个点，则需要用找到的最佳offset再跑一次balance
                         // setPwrOffsetHint(); // 重新设置 FFE 提示 (可能基于最佳配置)
                         // vpFsm->mState = ePwrOfst_RunAdapt; // 或直接 ePwrOfst_RunCm1PowerBalance2
                         // 为了简化，我们假设扫描完就结束
                        vpFsm->mState = ePwrOfst_Init; // 重置状态机
                        vDone = true;
                    } else {
                        // setPwrOffsetHint(); // 为下一次迭代设置 FFE 提示
                        // vpFsm->mState = ePwrOfst_RunCm1PowerBalance1; // 继续扫描
                    }
                }
                else // 继续扫描下一个偏移值
                {
                    // setPwrOffsetHint();
                    vpFsm->mState = ePwrOfst_RunCm1PowerBalance1;
                }
            }
            break;

        // case ePwrOfst_RunAdapt: ...
        // case ePwrOfst_RunCm1PowerBalance2: ... （使用 vpFsm->mBestOffset 运行最终的功率平衡）

        default:
            vpFsm->mState = ePwrOfst_Init;
            vDone = true;
            break;
    }
    return vDone;
}
```
这个函数的核心思想是：
1.  从 `aOffsetStart` 开始，以 `aOffsetStep` 为步长，遍历到 `aOffsetEnd`。
2.  在每个 `mOffset` 点，调用 `cdrFfeCm1PowerBalance` 进行功率平衡。
3.  平衡后，调用 `fomMeas` 测量信号质量。
4.  记录下产生最小 (最好) `vFom` 的那个 `mOffset` 作为 `mBestOffset`。
5.  （在完整实现中）扫描结束后，会使用找到的 `mBestOffset` 再次运行 `cdrFfeCm1PowerBalance` 来最终应用最佳设置。

`setPwrOffsetHint()` 与 `setPwrBalanceHint()` 类似，但它通常会将 CDR FFE 的大部分抽头提示值设为0，只保留主抽头 (Cursor, C10) 和第一个前置抽头 (Pre1, C11) 为一些预设的默认值（如 `eAdaptCdr_CdrFfeC10`, `eAdaptCdr_CdrFfeC11`）。这为功率偏移扫描提供了一个干净的、可重复的起点。

### CDR 自适应的配置参数

CDR 自适应算法的行为受到 `fw_adapt_config.c` 文件中定义的 `gFwAdaptConfig` 结构体的影响。

```c
// 文件: x812_rel2p1\fw_adapt_config.c (部分摘录)

__attribute__((used)) const volatile struct tFwAdaptConfig_t gFwAdaptConfig =
{
    // CDR 环路滤波器参数
    21,         // mCdrPhugSlow (CDR PI环慢速增益)
    84,         // mCdrPhugFast (CDR PI环快速增益)
    1,          // mCdrFrugSlow (CDR 积分器慢速增益)
    4,          // mCdrFrugFast (CDR 积分器快速增益)

    // ...
    2,          // mCdrKvCtrl (CDR KV 控制，影响环路带宽)
    12500,      // mCdrIntegAccSatValue (CDR 积分器累加饱和值)
    10000,      // mCdrIntegAccRollBackValue (CDR 积分器累加回滚值)
    // ... 其他模块的参数 ...
};

// 另外，在 gSwAdaptArg2 (也在 fw_adapt_config.c 中定义) 中，
// 可能也包含了一些与CDR自适应（特别是功率偏移扫描）相关的参数，
// 例如：
// gSwAdaptArg2.mPwrOfstMaxErr; // 功率偏移扫描中允许的最大误差
// gSwAdaptArg2.mL0CdrOffset; // 通道0找到的最佳CDR功率偏移值 (存储结果)
// gSwAdaptArg2.mL0Iter;      // 通道0 CDR功率平衡迭代次数
```
这些参数（如 `mCdrPhugSlow`、`mCdrFrugSlow` 等）在 `initCdrAdapt()` 函数中被读取并写入硬件寄存器，为 CDR 模块设定了基础的工作特性。而像 `cdrFfeCm1PowerBalance` 和 `cdrPwrOfstSweep` 函数中使用的迭代次数、步长等常量（如 `eAdaptCdr_PowerBalanceIters`, `eAdaptCdr_PowerBalanceMu`）虽然在代码片段中没有直接展示其来源，但它们通常也是在类似 `fw_adapt_config.c` 的配置文件中定义，或者作为参数传递进来，最终源于系统级别的配置。

## 总结

在本章中，我们深入了解了“CDR 自适应”的机制。我们学到：

*   CDR (时钟和数据恢复) 是从带有噪声和抖动的信号中提取时钟并恢复数据的关键过程。
*   CDR 自适应是一个动态优化过程，通过调整 CDR 环路参数和其内部 FFE 的系数，来确保时钟精确对准数据的最佳采样点，从而最小化误码。
*   `initCdrAdapt()` 函数负责从配置中加载 CDR 模块的初始参数。
*   `cdrFfeCm1PowerBalance()` 是一个重要的算法，它通过调整 CDR FFE 的 Cm1 (Pre1) 抽头，来平衡前置抽头和后置抽头的功率贡献。这个过程包括读取当前功率、计算调整量、更新 FFE 提示值并加载到硬件，以及运行本地自适应模式。
*   `getCdrPowerPre()` 和 `getCdrPowerPost()` 用于计算 CDR FFE 前/后置抽头的总功率。
*   `cdrPwrOfstSweep()` 通过扫描不同的目标功率偏移值，并结合 `cdrFfeCm1PowerBalance` 和 FOM 测量，来找到最优的功率偏移设置。
*   CDR 自适应的参数来源于 `gFwAdaptConfig` 等配置结构。

CDR 自适应就像一个不知疲倦的调音师，时刻确保接收器能够以最高的保真度“聆听”并还原远端发送过来的数据。这是实现稳定可靠高速通信的又一个重要环节。

在下一章，我们将把目光投向接收路径上另一个重要的均衡器：[FFE 自适应 (FFE Adaptation)](05_ffe_自适应__ffe_adaptation__.md)，看看主 FFE 是如何补偿信道引入的更广泛的失真的。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)