# Chapter 5: FFE 自适应 (FFE Adaptation)


欢迎来到 `hw` 项目教程的第五章！在上一章 [CDR 自适应 (CDR Adaptation)](04_cdr_自适应__cdr_adaptation__.md) 中，我们学习了 CDR 模块如何从接收到的信号中精确恢复时钟并对齐数据，确保我们在正确的时间点对信号进行采样。这就像我们已经校准了“耳朵”的节奏感，能够准确地跟上快速的语速。但是，即使节奏对了，如果每个字本身发音模糊不清，我们仍然难以理解内容。高速信号在传输过程中，也会因为信道（比如网线、电路板走线）的“不完美”而变得“模糊不清”，这就是所谓的**码间干扰 (Inter-Symbol Interference, ISI)**。

本章，我们将探索 **FFE 自适应 (FFE Adaptation)**，看看它是如何像一副“智能矫正眼镜”一样，帮助我们看清这些模糊的信号。

## 什么是 FFE 自适应？信号的“矫正眼镜”

想象一下，你正在看远处的文字，但因为近视，文字看起来很模糊，旁边的字好像都叠在了一起。这时，你需要一副合适的眼镜来矫正视力，让每个字都清晰可见。

在高速数字通信中，信号在通过长距离线缆或复杂的电路板时，高频部分会衰减得更厉害，信号波形会发生展宽和变形。这导致当前传输的“1”或“0”（我们称之为符号，Symbol）会干扰到它前面和后面的符号，就像模糊的字迹一样，难以辨认。这就是**码间干扰 (ISI)**。

**FFE (Feed-Forward Equalizer, 前馈均衡器)** 是一种数字滤波器，它的作用就像一副“矫正眼镜”。它通过一系列可调节的“旋钮”（称为**抽头系数 (Tap Coefficients)**），对接收到的信号进行处理，以补偿信道造成的失真，特别是高频衰减和码间干扰。

**FFE 自适应 (FFE Adaptation)** 则是这个“矫正眼镜”的“自动验光和调节”过程。它是一个动态的模块，负责：

1.  **评估信号质量**：判断当前信号的“模糊”程度。
2.  **调整 FFE 抽头系数**：自动调节那些“旋钮”，使得“矫正”效果最佳。
3.  **处理固定抽头和浮动抽头**：FFE 的抽头有些是位置固定的，有些则可以“浮动”到信号失真最严重的地方进行补偿，FFE 自适应模块需要管理和训练这些不同类型的抽头。

最终目标是增强信号中的高频成分，抑制码间干扰，使信号的波形恢复清晰，接收器能够更容易、更准确地判决出原始的“1”和“0”。

## FFE 和抽头：眼镜的镜片是如何工作的？

FFE 的核心思想是利用当前符号周围的符号信息来消除当前符号受到的干扰。它通过一系列**抽头 (Taps)** 来实现这一点。每个抽头都会对信号的一个延迟版本进行加权求和。

我们可以把 FFE 想象成一个有很多小镜片的组合：

*   **主抽头 (Cursor Tap)**：对应当前正在判决的符号。它的系数通常是最大的，代表了我们最关心的信号部分。
*   **前置抽头 (Pre-cursor Taps)**：对应当前符号之前的符号。它们用来补偿由后续符号对当前符号造成的“前回声”干扰。
*   **后置抽头 (Post-cursor Taps)**：对应当前符号之后的符号。它们用来补偿由先前符号对当前符号造成的“拖尾回声”干扰。

每个抽头的“强度”（即系数）是可以调整的。FFE 自适应算法就是通过调整这些系数来“塑造”信号，使其尽可能接近原始的清晰波形。

```mermaid
graph LR
    subgraph "FFE 滤波器"
        direction LR
        Input[输入信号] --> D1[延迟] --> Add1(+)
        D1 --> T_pre[Pre-cursor抽头 C-1] --> Mul_pre(x) --> Add1
        Input --> T_main[Cursor抽头 C0] --> Mul_main(x) --> Add1
        Input --> D2[延迟] --> T_post[Post-cursor抽头 C+1] --> Mul_post(x) --> Add1
        Add1 --> Output[输出信号]
    end
    Note right of Output: 简化版3抽头FFE
```
上图展示了一个简化的3抽头FFE。实际的FFE可能有数十个抽头，以提供更精细的均衡能力。

### 固定抽头 vs. 浮动抽头

FFE 的抽头可以分为两大类：

*   **固定抽头 (Fixed Taps)**：这些抽头的位置是固定的，通常围绕在主抽头附近。它们的系数由 FFE 自适应算法进行优化。
*   **浮动抽头 (Floating Taps)**：这是 `hw` 项目中 FFE 的一个强大特性！想象一下，你的眼镜上有一些可以自由移动的小镜片，你可以把它们精确地放到视野中最模糊的地方去矫正。浮动抽头就是这样，它们不是固定在某个延迟位置，而是可以被“指派”到信号中码间干扰最强的几个点上进行补偿。这使得 FFE 能够更有效地处理那些具有复杂、非典型失真特性的信道。

FFE 自适应模块需要智能地决定这些浮动抽头应该“浮动”到哪里，并训练它们的系数值。

## FFE 自适应是如何工作的？

FFE 自适应通常是[接收器自适应引擎](01_接收器自适应引擎_.md)在执行其自适应序列时的一个重要环节。它的大致流程如下：

1.  **初始化**：加载 FFE 的初始配置参数，这些参数很多来自 [配置管理 (Configuration Management)](02_配置管理__configuration_management__.md) 中定义的 `gFwAdaptConfig`。
2.  **浮动抽头位置搜索 (如果支持并启用)**：
    *   系统会分析信号，找出码间干扰最大的几个“点”。
    *   然后将浮动抽头“移动”到这些点上。
3.  **抽头系数训练**：
    *   系统让 FFE 硬件根据一定的算法（比如 LMS - 最小均方算法）自动调整固定抽头和已定位的浮动抽头的系数。
    *   这个训练过程会持续一段时间，或者迭代一定的次数，直到信号质量达到某个标准，或者不再有明显改善。
4.  **评估与迭代**：在训练过程中或训练后，系统会评估信号质量（例如，通过内部的眼图监控或错误统计）。如果效果不佳，可能会重复某些步骤或尝试不同的策略。

下面是一个简化的 FFE 自适应（特别是浮动抽头搜索和训练）的流程图：

```mermaid
sequenceDiagram
    participant AdaptEngine as "接收器自适应引擎"
    participant FFEAdapt as "FFE自适应模块"
    participant FFEHardware as "FFE硬件 (包括抽头和MUX)"
    participant SigQuality as "信号质量评估"

    AdaptEngine->>FFEAdapt: 请求执行FFE自适应
    FFEAdapt->>FFEHardware: (1) 加载初始配置 (initFfeAdapt)
    Note over FFEAdapt: 开始浮动抽头索引搜索 (ffeFloatIndexSearch)
    loop 迭代搜索浮动抽头位置
        FFEAdapt->>FFEHardware: (2) 设置浮动抽头MUX选择特定位置
        FFEAdapt->>FFEHardware: (3) 硬件收集信号相关性数据
        FFEHardware-->>FFEAdapt: 返回相关性数据
        FFEAdapt->>FFEAdapt: (4) 存储并分析相关性 (storeFloatingTapCorrStat)
    end
    FFEAdapt->>FFEAdapt: (5) 确定最佳浮动抽头位置 (findOptimalFloatingTap, findFloatingTapGroupInd)
    FFEAdapt->>FFEHardware: (6) 将浮动抽头MUX配置到最佳位置 (setFloatingTapMuxSel)
    Note over FFEAdapt: 开始FFE抽头系数训练
    FFEAdapt->>AdaptEngine: (7) 请求运行硬件自适应模式 (runAdaptModes)
    AdaptEngine->>FFEHardware: 启动FFE硬件训练
    FFEHardware->>FFEHardware: FFE抽头系数自动调整
    FFEHardware-->>AdaptEngine: 硬件自适应完成
    AdaptEngine-->>FFEAdapt: 硬件自适应完成
    FFEAdapt->>SigQuality: (8) 评估最终信号质量
    FFEAdapt-->>AdaptEngine: FFE自适应完成
end
```

## 深入探索：代码中的 FFE 自适应

现在，让我们深入代码，看看 FFE 自适应在 `hw` 项目中是如何实现的。我们将重点关注 `adapt_ffe.c`、`adapt_ffe_derived.c` 和 `fw_adapt_config.c` 中的相关部分。

### 1. 初始化 FFE 自适应参数：`initFfeAdapt()`

与 CDR 自适应类似，FFE 自适应在开始之前，也需要从 `gFwAdaptConfig` 加载一些初始配置。

```c
// 文件: adapt_ffe.c (简化片段)
#include "adapt_ffe.h"
#include "fw_adapt_config.h" // 包含 gFwAdaptConfig
#include "rx_reg_structs.h"  // 包含 RX 寄存器结构体

void initFfeAdapt()
{
    // 设置 DFE (判决反馈均衡器, 有时与FFE协同工作) 训练增益和模式
    RX__DFE_TRAINING0_T vDfeTraining0 = READ_REG(RX_REG_BASE, RX__DFE_TRAINING0);
    vDfeTraining0.mFields.DFE_TRAIN_GAIN_POST_LOCK = gFwAdaptConfig.mDfeTrainGainPostLock;
    // ... 其他 DFE 设置 ...
    vDfeTraining0.mFields.DFE_MODE = 2; // 设置 DFE 模式
    WRITE_REG(RX_REG_BASE, RX__DFE_TRAINING0, vDfeTraining0);

    // 使能 FFE 固定抽头 (Fixed Taps)
    // gFwAdaptConfig.mFfeFixCoeffEn 是一个位掩码，每一位对应一个固定抽头的使能
    RX__FFE_CONFIG0_T vRxFfeConfig0 = READ_REG(RX_REG_BASE, RX__FFE_CONFIG0);
    vRxFfeConfig0.mFields.FFE_FLOAT_COEFF_EN = 0; // 初始可能先禁用浮动抽头
    vRxFfeConfig0.mFields.FFE_FIX_COEFF_EN = gFwAdaptConfig.mFfeFixCoeffEn & eFfeInit_FfeFixCoeffEn0Mask; // 低位部分
    WRITE_REG(RX_REG_BASE, RX__FFE_CONFIG0, vRxFfeConfig0);
    // ... (通过 RX__FFE_CONFIG1 设置 FFE_FIX_COEFF_EN 的高位部分) ...

    // 使能 FFE 固定抽头参与训练
    // gFwAdaptConfig.mFfeFixCoeffTrainEn 也是一个位掩码
    RX__FFE_TRAINING0_T vRxFfeTraining0 = READ_REG(RX_REG_BASE, RX__FFE_TRAINING0);
    vRxFfeTraining0.mFields.FFE_TRAIN_GAIN_POST_LOCK = gFwAdaptConfig.mFfeTrainGainPostLock;
    vRxFfeTraining0.mFields.FFE_FIXED_TAP_EN = gFwAdaptConfig.mFfeFixCoeffTrainEn & eFfeInit_FfeFixCoeffEn0TrainMask;
    WRITE_REG(RX_REG_BASE, RX__FFE_TRAINING0, vRxFfeTraining0);
    // ... (通过 RX__FFE_TRAINING1 设置 FFE_FIXED_TAP_EN 的高位部分和 CDR FFE 训练增益) ...

    // 设置 FFE 抽头系数的 "提示" (Hint) 值，硬件可以此为起点进行训练
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING3, FFE_COEFF_HINT_C24, gFwAdaptConfig.mFfeCoeffHintC24);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING19, FFE_FIXED_COEFF_HINT_LOAD_EN, gFwAdaptConfig.mFfeFixCoeffHintLoadEn);

    // 更新 FFE 抽头使能配置到硬件
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING0, FFE_TAP_EN_UPD, 0);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING0, FFE_TAP_EN_UPD, 1); // 脉冲更新
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING0, FFE_TAP_EN_UPD, 0);

    // 更新 FFE 系数使能配置到硬件
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG0, FFE_COEFF_EN_UPD, 0);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG0, FFE_COEFF_EN_UPD, 1); // 脉冲更新
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG0, FFE_COEFF_EN_UPD, 0);
}
```
*   `initFfeAdapt()` 从 `gFwAdaptConfig` 中读取 FFE 的各种配置，如训练增益 (`mFfeTrainGainPostLock`)、哪些固定抽头被使能 (`mFfeFixCoeffEn`)、哪些抽头参与训练 (`mFfeFixCoeffTrainEn`) 以及一些抽头的初始“提示”值 (`mFfeCoeffHintC24`)。
*   这些值被写入到接收器 (RX) 模块内相应的 FFE 配置和训练寄存器中（如 `RX__FFE_CONFIG0`, `RX__FFE_TRAINING0` 等）。
*   `FFE_TAP_EN_UPD` 和 `FFE_COEFF_EN_UPD` 是更新控制位，通过产生一个脉冲（0->1->0）来使硬件加载新的使能配置。

### 2. 浮动抽头索引搜索：`ffeFloatIndexSearch()`

这是 FFE 自适应中非常精妙的一部分，用于确定浮动抽头应该放置在哪些位置以最大程度地消除码间干扰。它是一个状态机，逐步完成搜索过程。

```c
// 文件: adapt_ffe.c (简化片段)

// 浮动抽头状态机结构体 (简化)
struct tRxFloatingTap_t {
    enum eFloatingTapState_t mFloatingTapState; // 当前状态
    uint32_t mIter;                             // 当前迭代次数 (搜索不同位置组)
    uint32_t mFloatingTapCorr[eFloatingTapConst_NumTap]; // 存储所有可能位置的相关性值
    // ... 其他成员 ...
};

// 浮动抽头状态枚举 (简化)
enum eFloatingTapState_t {
    eFloatingTapState_Init,         // 初始化
    eFloatingTapState_Setup,        // 设置MUX并开始相关性测量
    eFloatingTapState_AwaitCorr,    // 等待相关性测量完成
    eFloatingTapState_AwaitAdapt,   // 等待一轮硬件自适应完成
    eFloatingTapState_FindOptimal   // 找到最佳位置并应用
};

bool ffeFloatIndexSearch(uint32_t aCorrIter) // aCorrIter: 相关性测量的迭代次数
{
    bool vDone = false;
    struct tRxFloatingTap_t* vpFsm = &gRx[gActiveLane].mAdapt.mFloatingTap;

    switch (vpFsm->mFloatingTapState)
    {
        case eFloatingTapState_Init:
            vpFsm->mIter = 0; // 初始化迭代，用于扫描不同的浮动抽头组配置
            // 初始禁用浮动抽头系数，然后通过脉冲更新使能
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG0, FFE_FLOAT_COEFF_EN, 0);
            // ... 脉冲 FFE_COEFF_EN_UPD ...
            // 保存并修改 Mode 11 (一个特定的硬件自适应模式) 的配置
            // ...
            // 设置相关性累积的迭代次数
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING14, N_TOP_FLOATING_TAP_TRAIN, aCorrIter);
            vpFsm->mFloatingTapState = eFloatingTapState_Setup;
            break;

        case eFloatingTapState_Setup:
            // 设置浮动抽头复用器(MUX)选择，让浮动抽头连接到特定的物理抽头组进行测试
            // 这里的 vMuxSel 会随着 mIter 变化，以测试不同的候选位置
            uint32_t vMuxSel = vpFsm->mIter * eFloatingTapConst_IterMultiplier;
            setFloatingTapMuxSel(vMuxSel, vMuxSel, vMuxSel); // 来自 adapt_ffe_derived.c
            // 启动一个硬件自适应模式 (Mode 11) 来稳定信号并收集数据
            startRxModeCtlFsm(eFloatingTapConst_AdptMode, eFloatingTapConst_AdptMode);
            // 使能浮动抽头相关性累积硬件
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING1, FFE_FLOATING_TAP_CORR_EN, 1);
            vpFsm->mFloatingTapState = eFloatingTapState_AwaitCorr;
            break;

        case eFloatingTapState_AwaitCorr: // 等待硬件完成相关性测量
            if (!(uint32_t)READ_REG_FIELD_NEW(RX_REG_BASE, RX__STATUS9, FFE_FLOATING_TAP_CORR_DONE))
            {
                break; // 未完成，下次再来
            }
            // 禁用相关性累积
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING1, FFE_FLOATING_TAP_CORR_EN, 0);
            vpFsm->mFloatingTapState = eFloatingTapState_AwaitAdapt;
            break;

        case eFloatingTapState_AwaitAdapt: // 等待之前启动的硬件自适应模式 (Mode 11) 完成
            if (!updateRxModeCtlFsm(false)) // updateRxModeCtlFsm 检查自适应是否完成
            {
                break; // 未完成，下次再来
            }
            // 存储当前测试位置组的相关性值
            storeFloatingTapCorrStat(vpFsm->mIter);
            vpFsm->mIter++;
            if (vpFsm->mIter >= eFloatingTapConst_SearchIter) // 如果所有位置组都测试完了
            {
                vpFsm->mFloatingTapState = eFloatingTapState_FindOptimal;
            }
            else
            {
                vpFsm->mFloatingTapState = eFloatingTapState_Setup; // 继续测试下一组
            }
            break;

        case eFloatingTapState_FindOptimal:
            uint32_t vPos0, vPos1, vPos2;
            // 从所有测试过的位置中，找出相关性(通常代表ISI强度)最高的三个位置
            findOptimalFloatingTap(&vPos0, &vPos1, &vPos2);
            // 根据找到的最佳ISI位置，计算出实际应该配置给浮动抽头MUX的选择值
            findFloatingTapGroupInd(&vPos0, &vPos1, &vPos2);
            // 将计算出的MUX选择值设置到硬件，将浮动抽头连接到最佳位置
            setFloatingTapMuxSel(vPos0, vPos1, vPos2);
            // ... 恢复之前保存的 Mode 11 配置 ...
            // 正式使能浮动抽头系数参与工作
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG0, FFE_FLOAT_COEFF_EN, eFloatingTapConst_FloatCoeffEnMask);
            // ... 脉冲 FFE_COEFF_EN_UPD ...
            vpFsm->mFloatingTapState = eFloatingTapState_Init; // 重置状态机
            vDone = true; // 浮动抽头索引搜索完成
            break;
        default: /* ... */ vDone = true; break;
    }
    return vDone;
}
```
*   **状态机**：`ffeFloatIndexSearch` 函数通过 `mFloatingTapState` 在多个状态间切换，以完成复杂的浮动抽头定位过程。
*   **迭代测试 (Setup, AwaitCorr, AwaitAdapt)**：
    *   在 `eFloatingTapState_Setup` 状态，通过 `setFloatingTapMuxSel` (定义在 `adapt_ffe_derived.c` 中) 函数配置硬件，将浮动抽头暂时连接到一组特定的物理抽头位置。然后启动一个特殊的硬件自适应模式（Mode 11），并使能硬件的相关性累积功能。
    *   `eFloatingTapState_AwaitCorr` 等待硬件完成对当前抽头位置的信号相关性测量。相关性可以反映该位置的码间干扰强度。
    *   `eFloatingTapState_AwaitAdapt` 等待 Mode 11 自适应完成。然后调用 `storeFloatingTapCorrStat` 将硬件测量的相关性值读取并存到 `vpFsm->mFloatingTapCorr` 数组中。
    *   这个过程会迭代多次 (`eFloatingTapConst_SearchIter` 次)，每次测试一组不同的物理抽头位置。
*   **选择最佳位置 (FindOptimal)**：
    *   当所有候选位置都测试完毕后，进入 `eFloatingTapState_FindOptimal` 状态。
    *   `findOptimalFloatingTap`：遍历 `mFloatingTapCorr` 数组，找出相关性值（代表ISI量）最大的三个物理抽头索引。
    *   `findFloatingTapGroupInd`：根据这三个ISI最强的物理抽头索引，再经过一次转换（具体算法参考代码注释中提到的文档），得到最终要配置给三个浮动抽头组的MUX选择值。这是因为物理抽头和浮动抽头组之间可能存在一种映射关系。
    *   `setFloatingTapMuxSel`：将最终计算出的MUX选择值写入硬件，从而将浮动抽头“固定”在能够最有效消除ISI的位置。
    *   最后，正式使能浮动抽头 (`FFE_FLOAT_COEFF_EN`)，让它们参与后续的FFE系数训练。

#### 辅助函数：浮动抽头的数据处理

*   `storeFloatingTapCorrStat(uint32_t aFloatingTapPosRange)`:
    这个函数从特定的硬件状态寄存器 (`RX__STATUS13` 到 `RX__STATUS24`) 中读取一批（12个）相关性累积值。这些值是硬件在 `FFE_FLOATING_TAP_CORR_EN` 使能期间，对选定抽头位置的信号进行分析得到的。函数将这些值（取绝对值后）存储到 `gRx[gActiveLane].mAdapt.mFloatingTap.mFloatingTapCorr` 数组的相应位置。

    ```c
    // 文件: adapt_ffe.c (简化片段)
    static void storeFloatingTapCorrStat(uint32_t aFloatingTapPosRange)
    {
        struct tRxFloatingTap_t* vpFsm = &gRx[gActiveLane].mAdapt.mFloatingTap;
        // 计算在 mFloatingTapCorr 数组中开始存储的索引
        const uint32_t vStartIdx = aFloatingTapPosRange * eFloatingTapConst_CorrAccCnt;
        // vpCorr 指向 RX__STATUS13 寄存器的地址，连续读取多个寄存器
        const uint32_t* vpCorr = (uint32_t*)READ_REG_ADDR(RX_REG_BASE, RX__STATUS13);

        for (uint32_t vI = 0; vI < eFloatingTapConst_CorrAccCnt; ++vI)
        {
            int32_t vVal = signExtend32(vpCorr[vI], eFloatingTapConst_CorrAccBits); // 符号扩展
            if (vVal < 0) vVal = -vVal; // 取绝对值
            vpFsm->mFloatingTapCorr[vStartIdx + vI] = vVal;
        }
        // ... (一些用于编译器检查的空操作，确保寄存器名正确)
    }
    ```

*   `findOptimalFloatingTap(uint32_t* apFloatingTapPos0, ...)`:
    这个函数非常直接，它遍历 `mFloatingTapCorr` 数组中存储的所有相关性值，找到其中最大的三个值，并将它们的**索引**（代表物理抽头位置）存储到输出参数 `apFloatingTapPos0` (第三大), `apFloatingTapPos1` (第二大), `apFloatingTapPos2` (最大) 中。

*   `findFloatingTapGroupInd(uint32_t* apFloatingTapPos0, ...)`:
    这个函数的逻辑比较复杂（如代码注释中提到的，具体算法有专门文档说明）。它接收 `findOptimalFloatingTap` 找到的三个具有最高ISI的物理抽头**索引**作为输入。然后，它根据这些索引和浮动抽头分组的规则，计算出应该配置给硬件浮动抽头MUX的三个**选择值** (Group Index)。这些选择值将决定每个浮动抽头组实际连接到哪个范围的物理抽头。

#### 辅助函数：设置浮动抽头 MUX

*   `setFloatingTapMuxSel(uint32_t aFloatingTapMuxSel0, ...)` (位于 `adapt_ffe_derived.c`):
    这个函数接收 `findFloatingTapGroupInd` 计算出的三个MUX选择值，并将它们写入到 `RX__FFE_TRAINING9`, `RX__FFE_TRAINING12`, `RX__FFE_TRAINING13`, `RX__FFE_TRAINING18` 等寄存器的特定字段中。这些字段控制着浮动抽头硬件内部的多路选择器，从而将浮动抽头逻辑上连接到期望的物理抽头位置。

    ```c
    // 文件: x812_rel2p1\adapt_ffe_derived.c (简化片段)
    void setFloatingTapMuxSel(uint32_t aFloatingTapMuxSel0, uint32_t aFloatingTapMuxSel1, uint32_t aFloatingTapMuxSel2)
    {
        // 读取相关寄存器的当前值
        RX__FFE_TRAINING9_T vTraining9 = READ_REG(RX_REG_BASE, RX__FFE_TRAINING9);
        // ... (读取 vTraining12, vTraining13, vTraining18)

        // 根据输入的 MUX 选择值，设置相应寄存器字段
        // 例如，为浮动抽头组0 (Floating Group 0) 的所有4个子抽头设置MUX选择
        vTraining12.mFields.FFE_FLOATING_GROUP0_TAP0_MUX_SEL = aFloatingTapMuxSel0;
        vTraining12.mFields.FFE_FLOATING_GROUP0_TAP1_MUX_SEL = aFloatingTapMuxSel0;
        // ... (设置 Group0 Tap2, Tap3)

        // 为浮动抽头组1 (Floating Group 1) 设置MUX选择
        vTraining12.mFields.FFE_FLOATING_GROUP1_TAP0_MUX_SEL = aFloatingTapMuxSel1;
        // ... (设置 Group1 Tap1, Tap2, Tap3 - 注意Tap3可能在不同寄存器如 vTraining18)

        // 为浮动抽头组2 (Floating Group 2) 设置MUX选择
        // ... (类似地设置 Group2 的所有子抽头)

        // 将修改后的值写回寄存器
        WRITE_REG(RX_REG_BASE, RX__FFE_TRAINING9, vTraining9);
        // ... (写回 vTraining12, vTraining13, vTraining18)
    }
    ```

一旦浮动抽头的位置确定，并且固定抽头也已根据配置使能，[接收器自适应引擎](01_接收器自适应引擎_.md)就会启动相应的硬件自适应模式 (通过 `runAdaptModes` 函数)。在这些模式下，FFE 硬件会使用其内部的训练算法（通常是基于LMS的变种）来自动调整所有已使能抽头（包括固定和浮动）的系数值，以最小化输出信号的误差，从而达到最佳的均衡效果。

### 3. FFE 复位：`resetFfeAdapt()`

在某些情况下，例如链路重新初始化或模式改变时，可能需要将 FFE 的设置恢复到一组已知的默认状态。`resetFfeAdapt()` 函数就用于此目的。

```c
// 文件: adapt_ffe.c (简化片段)
void resetFfeAdapt()
{
    // 重置 CDR FFE (CDR内部的小FFE) 抽头训练使能
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING2, CDR_FFE_TAP_EN, eFfeReset_CdrFfeEn);
    // ... (脉冲 CDR_FFE_TAP_EN_UPD) ...

    // 重置主 FFE 固定抽头训练使能
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING0, FFE_FIXED_TAP_EN, eFfeReset_FfeEn0);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING1, FFE_FIXED_TAP_EN, eFfeReset_FfeEn1);
    // ... (脉冲 FFE_TAP_EN_UPD) ...

    // 重新使能 FFE 固定抽头系数 (使用预设的默认掩码)
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG0, FFE_FIX_COEFF_EN, eFfeReset_FfeCoeffEn0);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_CONFIG1, FFE_FIX_COEFF_EN, eFfeReset_FfeCoeffEn1);

    // 重置 CDR FFE 和主 FFE 所有抽头系数的 "提示" 值为预设的默认值 (通常很多为0，主抽头为某个值)
    // 例如，CDR FFE Cm1 (C11) 和 C0 (C10)
    RX__CDR_FFE_TRAINING4_T vRxCdrFfeTraining4 = READ_REG(RX_REG_BASE, RX__CDR_FFE_TRAINING4);
    vRxCdrFfeTraining4.mFields.CDR_FFE_COEFF_HINT_C11 = 0;   // Cm1
    vRxCdrFfeTraining4.mFields.CDR_FFE_COEFF_HINT_C10 = eFfeReset_CdrFfeHintC0; // C0
    WRITE_REG(RX_REG_BASE, RX__CDR_FFE_TRAINING4, vRxCdrFfeTraining4);
    // ... (重置 CDR FFE 和主 FFE 其他所有抽头的 HINT 值) ...

    // 通过脉冲加载位，使硬件使用这些重置后的提示值
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__FFE_TRAINING14, CDR_FFE_COEFF_HINT_LOAD, 1); // 脉冲
    // ... (同样为主 FFE 的提示值进行加载) ...

    // ... (其他复位操作，如 DFE 模式等) ...
}
```
*   `eFfeReset_CdrFfeEn`, `eFfeReset_FfeEn0`, `eFfeReset_FfeCoeffEn0`, `eFfeReset_CdrFfeHintC0` 等是以 `eFfeReset_` 开头的枚举或宏，它们定义了复位时应使用的默认值。
*   此函数将 FFE 的抽头使能、训练使能以及所有抽头的系数提示值都恢复到一组已知的初始状态。这为后续的重新自适应提供了一个干净的起点。

### FFE 自适应的配置参数

FFE 自适应算法的许多行为都受到 `fw_adapt_config.c` 文件中 `gFwAdaptConfig` 结构体的影响。

```c
// 文件: x812_rel2p1\fw_adapt_config.c (部分摘录)
__attribute__((used)) const volatile struct tFwAdaptConfig_t gFwAdaptConfig =
{
    // ... (其他模块如 CDR, CTLE 的参数) ...

    // FFE / DFE
    0,          // mDfeReserved0
    4,          // mDfeTrainGainPostLock (DFE 锁定后训练增益)
    5,          // mDfeTrainGainPreLock (DFE 锁定前训练增益)

    0,          // mFfeReserved0
    4,          // mFfeTrainGainPostLock (FFE 锁定后训练增益)
    5,          // mFfeTrainGainPreLock (FFE 锁定前训练增益)

    0,          // mCdrFfeReserved0
    4,          // mCdrFfeTrainGainPostLock (CDR FFE 锁定后训练增益)
    5,          // mCdrFfeTrainGainPreLock (CDR FFE 锁定前训练增益)

    0xFDFFFFFF, // mFfeFixCoeffEn (FFE 固定抽头使能掩码，几乎全使能)
    0xFDFFFFFF, // mFfeFixCoeffTrainEn (FFE 固定抽头参与训练的使能掩码)
    0x01000000, // mFfeFixCoeffHintLoadEn (控制哪些抽头的提示值可以被加载)

    0,          // mFfeReserved1
    256,        // mFfeCoeffHintC24 (FFE 第24个后置抽头的提示值, 0.5, Q0.9格式)
    // ... 其他参数 ...
};
```
这些参数在 `initFfeAdapt()` 中被读取并写入硬件，为 FFE 模块设定了基础的工作特性和自适应算法的行为。例如，训练增益会影响 FFE 系数调整的快慢和稳定性。使能掩码决定了哪些抽头真正参与工作和训练。

## 总结

在本章中，我们一起探索了“FFE 自适应”的奇妙世界。我们了解到：

*   FFE（前馈均衡器）像一副“矫正眼镜”，通过调整其抽头系数来补偿信道引起的高频衰减和码间干扰 (ISI)。
*   FFE 自适应是动态调整这些抽头系数的过程，目的是使信号波形恢复清晰。
*   `hw` 项目中的 FFE 支持**固定抽头**和灵活的**浮动抽头**。浮动抽头可以被智能地放置到 ISI 最严重的位置。
*   `initFfeAdapt()` 函数负责从配置中加载 FFE 的初始参数，如训练增益、抽头使能等。
*   `ffeFloatIndexSearch()` 是一个复杂的状态机，它通过迭代测试不同的物理抽头位置，收集信号相关性数据，最终找到最佳位置来安放浮动抽头。这个过程涉及 `setFloatingTapMuxSel`, `storeFloatingTapCorrStat`, `findOptimalFloatingTap` 和 `findFloatingTapGroupInd` 等辅助函数。
*   一旦浮动抽头定位完成，并且固定抽头使能后，[接收器自适应引擎](01_接收器自适应引擎_.md)会启动硬件自适应模式，让 FFE 硬件自动训练所有抽头的系数值。
*   `resetFfeAdapt()` 用于将 FFE 恢复到默认状态。
*   FFE 自适应的参数来源于 `gFwAdaptConfig` 等配置结构。

FFE 自适应是确保在各种复杂信道条件下都能获得高质量信号的关键技术之一。它与我们之前学到的 [CDR 自适应 (CDR Adaptation)](04_cdr_自适应__cdr_adaptation__.md) 以及后续将要学习的其他自适应模块协同工作，共同保障了数据传输的可靠性。

下一章，我们将学习接收路径上的另一个重要均衡器：[CTLE 自适应 (CTLE Adaptation)](06_ctle_自适应__ctle_adaptation__.md)，看看它是如何通过模拟电路来初步提升信号的高频分量的。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)