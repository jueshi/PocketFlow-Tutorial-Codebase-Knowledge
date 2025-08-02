# Chapter 4: 时钟调理校准 (Clk Cond Cal)


在上一章 [PMD层请求与状态机](03_pmd层请求与状态机_.md) 中，我们学习了固件是如何利用状态机来处理复杂的PMD层（物理介质相关层）请求的。我们看到，这些状态机能够将一个大任务分解成一系列小步骤，在不阻塞系统的前提下有序执行。时钟调理校准（Clk Cond Cal）正是这样一个通过精密状态机来完成的关键校准过程。

## 4.1 完美节拍：为什么需要时钟调理校准？

想象一下你正在听一支乐队演奏。如果鼓手的鼓点时快时慢（占空比不对），或者不同乐器演奏的节拍有偏差（相位偏移），那么整个乐曲听起来就会混乱不堪。在数字通信系统中，尤其是高速信号传输的场景下，模拟数字转换器（ADC）就是一位至关重要的“音乐家”，它负责将接收到的模拟信号转换成数字信号。这位“音乐家”也需要一个极其精准的“节拍器”——也就是时钟信号。

**时钟调理校准 (Clk Cond Cal)** 就是确保ADC使用的时钟信号质量达到最佳状态的关键过程。它主要做两件事：

1.  **调整时钟的占空比 (Duty Cycle)**：确保时钟信号高电平持续的时间和低电平持续的时间比例是我们期望的（通常是理想的50/50）。
2.  **调整时钟的相位偏移/去歪斜 (Deskew)**：如果ADC内部使用了多个相关的时钟相位，这个过程能确保这些相位之间的相对时间关系是准确的，没有超前或滞后。

如果时钟信号的“节拍”不准，ADC就可能在错误的时间点对模拟信号进行采样，导致转换出来的数字数据失真，最终影响通信质量。因此，时钟调理校准对于保证数据转换的精确性至关重要，尤其是在需要高速稳定运行的PHY芯片中。

本章，我们将探讨 `source` 项目中时钟调理校准是如何通过状态机一步步实现的。

## 4.2 核心概念解析

在我们深入代码之前，先来了解几个相关的核心概念：

*   **ADC (Analog-to-Digital Converter, 模拟数字转换器)**：将连续的模拟信号转换为离散的数字信号的电子元件。它的采样时刻依赖于输入时钟。
*   **时钟占空比 (Clock Duty Cycle)**：在一个时钟周期内，高电平时间所占的比例。例如，一个理想方波的占空比是50%。不正确的占空比会影响信号采样的精度。
*   **时钟去歪斜 (Clock Deskew)**：校正多个并行时钟路径之间由于各种原因（如布线长度、负载差异）引入的时间延迟差异。目标是让相关的时钟边沿能够精确对齐或保持预期的相位关系。
*   **TDC (Time-to-Digital Converter, 时间数字转换器)**：一种可以测量极短时间间隔并将其转换为数字值的电路。在校准过程中，TDC被用来精确测量当前时钟的占空比和相位偏移等特性。
*   **DCA (Duty Cycle Correction Array, 占空比校正阵列)**：一种可编程调整电路，用于修正时钟信号的占空比。
*   **Deskew 调整电路**：类似地，这也是一种可编程电路，用于调整时钟信号的相位，以补偿偏移。
*   **校准模式 (Calibration Mode)**：校准过程通常分为粗调（Coarse）和精调（Fine）。粗调快速将参数调整到目标附近，精调则进行更细致的微调。有时还有CCA（Continuous Calibration and Adaptation，连续校准与自适应）模式，用于在系统运行时持续监控和调整。

## 4.3 时钟调理校准如何工作？

在 `source` 项目中，时钟调理校准主要通过 `clk_cond_cal.c` 文件中的函数来实现。这个过程通常包含两个主要步骤，分别由两个核心函数（状态机）管理：

1.  **ADC时钟占空比校准 (`processAdcCndInitDcSkewCal`)**: 调整ADC时钟的占空比。
2.  **ADC时钟去歪斜校准 (`processAdcClkDeskew`)**: 调整ADC各时钟相位间的偏移。

这两个函数都遵循在 [PMD层请求与状态机](03_pmd层请求与状态机_.md) 中学到的状态机模式：它们被PMD层的上层状态机（例如 `processRxPstateCmds` 或 `processTxPstateCmds`）调用，并且只有当其内部所有步骤完成后才返回 `true`。

### 4.3.1 快速模式的影响

正如我们在 [固件配置管理](01_固件配置管理_.md) 中学到的，固件配置 `gFwCfg` 可以影响校准流程。时钟调理校准也受其影响。例如，如果启用了全局快速模式或特定的时钟校准快速模式，校准过程可能会被跳过或使用简化的参数。

```c
// 来自 clk_cond_cal.c (processAdcCndInitDcSkewCal 函数片段)
// vpFsm 指向当前通道和目标（RX或TX）的状态机结构体
// aTarget 表示是为 RX 还是 TX 进行校准

if (aTarget == eTxRxTarget_Rx)
{
    vpFsm = &gRx[gActiveLane].mAdcCndInitDcSkewCalFsm; // 获取RX状态机
    // 检查快速模式标志
    if (gFwCfg.mGlobalFastMode == eFastMode_PmdSkip || gFwCfg.mRxAdcClkCondCalFastMode == eFastMode_PmdSkip)
    {
        vpFsm->mState = eAdcCndInitDcSkewCalState_Skip; // 如果启用快速模式，则跳过校准
    }
}
else // (aTarget == eTxRxTarget_Tx)
{
    vpFsm = &gTxCalVals[gActiveLane].mAdcCndInitDcSkewCalFsm; // 获取TX状态机
    if (gFwCfg.mGlobalFastMode == eFastMode_PmdSkip || gFwCfg.mTxAdcClkCondCalFastMode == eFastMode_PmdSkip)
    {
        vpFsm->mState = eAdcCndInitDcSkewCalState_Skip; // 跳过TX校准
    }
}
```
这段代码展示了在校准开始时，固件会首先检查 `gFwCfg` 中的相关快速模式标志。如果设置了跳过，状态机的状态 (`vpFsm->mState`) 会被直接设置为 `eAdcCndInitDcSkewCalState_Skip`，从而绕过实际的校准步骤。

### 4.3.2 函数调用接口 (`gClkCondCalVTable`)

为了让校准代码能够同时适用于接收器（RX）和发送器（TX）——它们可能有略微不同的硬件接口——代码使用了一个函数指针表（也称为虚函数表或VTable）。

```c
// 来自 clk_cond_cal.c
struct tClkCondCalVTable_t
{
    void (*mDcoSetupCal) (uint32_t, uint32_t);         // DCO（数字控制振荡器）设置
    bool (*mTdcRead) (enum tTdcCal_t, enum tTdcCfg_t, uint32_t, uint32_t*); // 读取TDC
    void (*mDeskewRead) (int32_t*);                    // 读取Deskew码
    void (*mDeskewWrite) (const int32_t*);             // 写入Deskew码
    void (*mDcaRead) (int32_t*);                       // 读取DCA码
    void (*mDcaWrite) (const int32_t*);                // 写入DCA码
};

// 为TX和RX分别定义实际的函数实现
struct tClkCondCalVTable_t gClkCondCalVTable[] = {
/*Tx*/{&dcoTxSetupCal, &tdcTxRead, &deskewTxRead, &deskewTxWrite, &dcaTxRead, &dcaTxWrite},
/*Rx*/{&dcoRxSetupCal, &tdcRxRead, &deskewRxRead, &deskewRxWrite, &dcaRxRead, &dcaRxWrite}
};
```
这里 `gClkCondCalVTable` 是一个包含两个 `tClkCondCalVTable_t` 结构体的数组，一个用于TX，一个用于RX。每个结构体包含指向具体硬件操作函数的指针。例如，`dcoTxSetupCal` 和 `dcoRxSetupCal` 分别是TX和RX的DCO设置函数（定义在 `dco.c` 中）。`tdcTxRead` 和 `tdcRxRead` 则是TX和RX的TDC读取函数（定义在 `tdc.c` 中）。

在校准函数内部，会根据 `aTarget` (RX 或 TX) 选择合适的 `vpVTable`：
```c
// 来自 clk_cond_cal.c (processAdcCndInitDcSkewCal 函数片段)
struct tClkCondCalVTable_t* vpVTable = &gClkCondCalVTable[aTarget];
// ... 之后就可以通过 vpVTable->mTdcRead(...) 来调用特定于目标 (RX/TX) 的 TDC 读取函数了
```
这种设计使得校准逻辑本身可以保持通用，而将与具体硬件交互的细节封装在各自的函数中。

### 4.3.3 ADC时钟占空比校准 (`processAdcCndInitDcSkewCal`)

这个函数是一个状态机，负责迭代地测量和调整ADC时钟的占空比，直到达到预设的目标值。

其主要状态和流程如下：

1.  **`eAdcCndInitDcSkewCalState_Init` (初始化状态)**:
    *   根据目标是RX还是TX，以及校准模式（粗调/精调/CCA），设置各种参数，如DCO种子值、TDC目标、占空比阈值、目标占空比、迭代次数、调整步进 (`mDcMu`) 等。这些参数很多来自 `gFwRxCalConfig` 或 `gFwTxCalConfig` 结构体（这些是固件预定义的校准配置）。
    *   如果启用了更细致的快速模式（如 `eFastMode_Fast1`），还会覆盖一些参数以加快校准。
    *   调用 `vpVTable->mDcoSetupCal()` 初始化DCO。
    *   调用 `vpVTable->mDcaRead()` 读取当前DCA（占空比调整）的设置值，存入 `vpFsm->mVcm`。
    *   转换到 `eAdcCndInitDcSkewCalState_DcConfig0` 状态。

    ```c
    // 来自 clk_cond_cal.c (eAdcCndInitDcSkewCalState_Init 简化片段)
    case eAdcCndInitDcSkewCalState_Init:
    {
        // ... 设置各种参数 vpFsm->mDcoSeedLsb, vpFsm->mDcTarget, 等 ...
        // 例如：从固件校准配置中获取目标值和阈值
        if (aTarget == eTxRxTarget_Rx) {
            vpFsm->mDcThrs = gFwRxCalConfig.mAdcClkCondDcCalThreshold;
            vpFsm->mDcTarget = gFwRxCalConfig.mAdcClkCondDcCalTarget;
        } else {
            // ... TX的类似设置 ...
        }
        // ... 根据校准模式 (aMode) 和快速模式调整参数 ...

        vpVTable->mDcoSetupCal(vpFsm->mDcoSeedLsb, vpFsm->mDcoCrs); // 设置DCO
        vpVTable->mDcaRead(vpFsm->mVcm);                           // 读取当前DCA值

        vpFsm->mState = eAdcCndInitDcSkewCalState_DcConfig0;
        return false; // 返回false表示校准未完成，主循环下次会再调用
    }
    ```

2.  **`eAdcCndInitDcSkewCalState_DcConfig0` (占空比测量阶段0)**:
    *   检查迭代次数是否已达上限 (`vpFsm->mDcNTop`)。如果达到，则校准结束，返回 `true`。
    *   清零累加器 `vpFsm->mCorr`。
    *   调用 `vpVTable->mTdcRead()`，使用 `eTdcCfg_Dc0` 配置来测量时钟占空比。`mTdcRead` 本身也是一个状态机（在 `tdc.c` 中实现），如果测量未完成，它会返回 `false`，那么 `processAdcCndInitDcSkewCal` 也会返回 `false`。
    *   如果测量完成，将TDC的累加结果 `vAccumVal` 按时钟相位累加到 `vpFsm->mCorr` 中。
    *   转换到 `eAdcCndInitDcSkewCalState_DcConfig1` 状态。

    ```c
    // 来自 clk_cond_cal.c (eAdcCndInitDcSkewCalState_DcConfig0 简化片段)
    case eAdcCndInitDcSkewCalState_DcConfig0:
    {
        if (vpFsm->mIterCnt >= vpFsm->mDcNTop) { /* ... 校准完成 ... */ return true; }

        // ... 清零 vpFsm->mCorr ...
        uint32_t vAccumVal[eHwConst_TdcAccumCnt];
        // 使用 TDC 配置0 进行测量
        if (!vpVTable->mTdcRead(vpFsm->mTdcCalTarget, eTdcCfg_Dc0, vpFsm->mRefSamples, vAccumVal))
        {
            return false; // TDC测量未完成，等待下一次调用
        }
        // ... 将 vAccumVal 累加到 vpFsm->mCorr ...
        vpFsm->mState = eAdcCndInitDcSkewCalState_DcConfig1;
        return false;
    }
    ```

3.  **`eAdcCndInitDcSkewCalState_DcConfig1` (占空比测量阶段1与调整)**:
    *   调用 `vpVTable->mTdcRead()`，使用 `eTdcCfg_Dc1` 配置（另一种TDC测量配置）再次测量。
    *   如果测量完成，将结果也累加到 `vpFsm->mCorr`。
    *   对所有相位的 `mCorr` 值进行平均，得到最终的测量占空比。
    *   **提前退出检查**：比较每个相位的测量占空比与目标占空比 (`vpFsm->mDcTarget`)。如果所有相位的误差都在阈值 (`vpFsm->mDcThrs`) 之内，并且这种情况连续发生了几次（`eAdcCndInitDcSkewCalConst_DcExitCnt`），则认为校准已足够好，可以提前结束，返回 `true`。
    *   **更新DCA码**：如果未提前退出，则根据测量值与目标值的差异，调整DCA的控制码 `vpFsm->mVcm`。
        *   如果测量值低于目标值 (e.g., `vpFsm->mCorr[vI] < vpFsm->mDcTarget`)，则增加 `vpFsm->mVcm[vI]` (通过加上步进 `vpFsm->mDcMu`)。
        *   如果测量值高于目标值，则减小 `vpFsm->mVcm[vI]`。
    *   调用 `dcaClamp()` 确保DCA码在有效范围内。
    *   调用 `vpVTable->mDcaWrite()` 将新的DCA码写入硬件。
    *   增加迭代计数器 `vpFsm->mIterCnt`。
    *   转换回 `eAdcCndInitDcSkewCalState_DcConfig0` 状态，开始下一次迭代。

    ```c
    // 来自 clk_cond_cal.c (eAdcCndInitDcSkewCalState_DcConfig1 简化片段)
    case eAdcCndInitDcSkewCalState_DcConfig1:
    {
        uint32_t vAccumVal[eHwConst_TdcAccumCnt];
        // 使用 TDC 配置1 进行测量
        if (!vpVTable->mTdcRead(vpFsm->mTdcCalTarget, eTdcCfg_Dc1, vpFsm->mRefSamples, vAccumVal))
        {
            return false; // TDC测量未完成
        }
        // ... 将 vAccumVal 累加到 vpFsm->mCorr 并计算平均值 ...

        // ... 检查是否可以提前退出 ...
        if (vDoEarlyExit) { /* ... 满足提前退出条件 ... */ return true; }

        // 更新DCA码
        for (vI = 0; vI < eHwConst_AdcClkCnt; ++vI) {
            if (vpFsm->mCorr[vI] < vpFsm->mDcTarget) { vpFsm->mVcm[vI] += vpFsm->mDcMu; }
            else if (vpFsm->mCorr[vI] > vpFsm->mDcTarget) { vpFsm->mVcm[vI] -= vpFsm->mDcMu; }
        }
        dcaClamp(vpFsm->mVcm);         // 限制DCA码范围
        vpVTable->mDcaWrite(vpFsm->mVcm); // 写入DCA码到硬件

        vpFsm->mIterCnt++;
        vpFsm->mState = eAdcCndInitDcSkewCalState_DcConfig0; // 回到状态DcConfig0进行下一轮
        return false;
    }
    ```

4.  **`eAdcCndInitDcSkewCalState_Skip` (跳过状态)**:
    *   如果因为快速模式而进入此状态，直接将状态重置为 `_Init` 并返回 `true`，表示“完成”（即跳过）。

这个循环（Init -> DcConfig0 -> DcConfig1 -> DcConfig0 ...）会不断重复，直到占空比调整到目标范围内，或者达到最大迭代次数。

### 4.3.4 ADC时钟去歪斜校准 (`processAdcClkDeskew`)

`processAdcClkDeskew` 函数与 `processAdcCndInitDcSkewCal` 结构非常相似，它也是一个状态机，但其目标是调整不同ADC时钟相位之间的时间差（skew），使它们对齐或达到预期的相对相位。

其主要状态和流程：

1.  **`eAdcClkDeskewState_Init` (初始化状态)**:
    *   与占空比校准类似，设置各种参数，如参考采样数、迭代次数、调整步进 (`mSkewMu`)、歪斜阈值 (`mSkewThrs`) 等。
    *   初始化DCO (`vpVTable->mDcoSetupCal`)。
    *   读取初始的Deskew控制码 (`vpVTable->mDeskewRead` 存入 `vpFsm->mDeskewCode`) 和DCA码 (`vpVTable->mDcaRead` 存入 `vpFsm->mVcm`)。Deskew校准可能会同时调整相位和占空比以达到最佳效果。
    *   转换到 `eAdcClkDeskewState_CalcCorrFactors` 状态。

2.  **`eAdcClkDeskewState_CalcCorrFactors` (计算校正因子状态)**:
    *   调用辅助函数 `getAdcDeskewCorrFactor()`。这个函数本身也是一个小状态机，通过两次TDC测量（`eTdcCfg_C0` 和 `eTdcCfg_C1`）来计算一个校正因子 `vpFsm->mCorrectionFactors`。这个因子用于补偿TDC测量本身可能存在的一些系统误差。
    *   如果 `getAdcDeskewCorrFactor()` 未完成，则返回 `false`。
    *   完成后，转换到 `eAdcClkDeskewState_MeasEdgeInit` 状态。

3.  **`eAdcClkDeskewState_MeasEdgeInit` (边缘测量初始化状态)**:
    *   检查迭代次数是否已达上限 (`vpFsm->mSkewNTop`)。如果达到，则校准结束。
    *   重置平均计数器和累加器 `vpFsm->mC0Mean`。
    *   转换到 `eAdcClkDeskewState_MeasEdge` 状态。

4.  **`eAdcClkDeskewState_MeasEdge` (边缘测量状态)**:
    *   这是一个内部循环，用于多次测量以获取平均值，从而提高精度。循环次数由 `vpFsm->mNAvg` 控制。
    *   调用 `vpVTable->mTdcRead()` 使用 `eTdcCfg_C0` 配置测量各时钟相位间的上升沿到上升沿（R2R）和下降沿到下降沿（F2F）的时间差。
    *   将测量结果应用之前计算的 `mCorrectionFactors` 进行校正，并累加到 `vpFsm->mC0Mean`。
    *   如果测量未完成或平均循环未结束，则返回 `false`。
    *   平均循环结束后，转换到 `eAdcClkDeskewState_MeasEdgeDone` 状态。

5.  **`eAdcClkDeskewState_MeasEdgeDone` (边缘测量完成与调整状态)**:
    *   计算 `mC0Mean` 的平均值，得到校正后的R2R和F2F时间差。
    *   在第一次迭代时，计算所有相位R2R和F2F时间差的平均值，作为校准的目标歪斜值 (`vpFsm->mSkewTargetR2r`, `vpFsm->mSkewTargetF2f`)。理想情况下，我们希望所有相位间的R2R时间差都相同，F2F时间差也都相同。
    *   计算当前每个相位的测量值与目标歪斜值之间的误差。
    *   **提前退出检查**：如果所有相位的R2R和F2F误差都在阈值 (`vpFsm->mSkewThrs`) 之内，并且这种情况连续发生了几次，则校准完成。
    *   **更新Deskew码和DCA码**：根据误差计算调整量。这部分的逻辑比较复杂，它会判断是需要调整相位（同时影响R2R和F2F），还是调整占空比（R2R和F2F反向变化），或是单独调整上升沿或下降沿。
        *   调整量会更新 `vpFsm->mDeskewCode` (主要用于相位调整) 和 `vpFsm->mVcm` (主要用于占空比/边沿调整)。
    *   调用 `deskewClamp()` 和 `dcaClamp()` 保证控制码在有效范围内。
    *   调用 `vpVTable->mDeskewWrite()` 和 `vpVTable->mDcaWrite()` 将新的控制码写入硬件。
    *   增加迭代计数器 `vpFsm->mIterCnt`。
    *   转换回 `eAdcClkDeskewState_MeasEdgeInit` 状态，开始下一次迭代。

6.  **`eAdcClkDeskewState_Skip` (跳过状态)**:
    *   与占空比校准中的跳过状态类似。

这个过程也是迭代进行的，直到时钟相位间的歪斜调整到满意为止。

## 4.4 内部实现探秘：校准如何一步步进行

为了更好地理解这些校准状态机是如何与上层PMD逻辑以及底层硬件接口协作的，我们可以看一个简化的工作流程。

### 4.4.1 非代码视角的工作流程

1.  **请求发起**：PMD层的某个状态机（比如在 `pmd_rx.c` 中的 `processRxPstateCmds`）收到一个需要执行时钟调理校准的命令（例如 `eRxFwCmd_PrClkCondDcCalCoarse`）。
2.  **调用校准函数**：PMD状态机调用相应的时钟校准函数，比如 `processAdcCndInitDcSkewCal(eTxRxTarget_Rx, eCalMode_Coarse)`。
3.  **校准状态机执行**：
    *   **初始化**：校准函数进入 `_Init` 状态，设置参数，准备DCO，读取当前DCA/Deskew值。然后返回 `false`。
    *   **测量**：在后续的调用中，状态机进入测量状态（如 `_DcConfig0`, `_DcConfig1`）。它会调用 `tdcRxRead`。
        *   `tdcRxRead` 函数本身也是一个小状态机（在 `tdc.c` 中）。它会配置TDC硬件，启动测量，等待硬件完成。在TDC硬件测量期间，`tdcRxRead` 会返回 `false`，导致上层的校准函数也返回 `false`。
        *   当TDC硬件测量完成后，`tdcRxRead` 返回 `true` 并带回测量数据。
    *   **计算与比较**：校准函数拿到TDC数据后，计算出实际的占空比或歪斜，并与目标值比较。
    *   **调整**：根据比较结果，计算出需要对DCA或Deskew电路做的调整量。
    *   **硬件写入**：调用 `dcaRxWrite` 或 `deskewRxWrite` 将新的调整值写入硬件寄存器。这些写入操作通常很快完成。
    *   **迭代**：校准函数再次返回 `false`，等待下一次被主循环调用以开始新的测量-调整迭代。
4.  **校准完成**：当测量结果达到目标精度（或达到最大迭代次数）时，校准函数返回 `true`。
5.  **PMD层响应**：PMD层的上层状态机收到 `true`后，知道这个校准步骤完成了，于是可以继续执行后续的命令步骤，或者向硬件发送完成应答。

### 4.4.2 序列图示例：占空比校准

下图展示了一个简化的占空比校准 (`processAdcCndInitDcSkewCal`) 的交互流程：

```mermaid
sequenceDiagram
    participant PMD层状态机 as "PMD层状态机 (例如 processRxPstateCmds)"
    participant 占空比校准FSM as "占空比校准FSM (processAdcCndInitDcSkewCal)"
    participant TDC接口 as "TDC接口 (例如 tdcRxRead via vpVTable)"
    participant DCA接口 as "DCA接口 (例如 dcaRxWrite via vpVTable)"
    participant 硬件寄存器 as "硬件寄存器"

    PMD层状态机->>占空比校准FSM: 1. 请求执行占空比校准 (粗调)
    占空比校准FSM->>占空比校准FSM: 2. 状态: Init - 设置参数, DCO配置
    占空比校准FSM-->>PMD层状态机: 3. 返回 false (进行中)

    loop 校准迭代 (多次调用)
        PMD层状态机->>占空比校准FSM: 4. 再次调用
        占空比校准FSM->>TDC接口: 5. 状态: DcConfig0/DcConfig1 - 请求TDC读
        TDC接口->>硬件寄存器: 6. 配置TDC, 启动测量
        Note over TDC接口: TDC测量需要时间
        TDC接口-->>占空比校准FSM: 7. 返回 false (TDC测量进行中)
        占空比校准FSM-->>PMD层状态机: 8. 返回 false (进行中)

        PMD层状态机->>占空比校准FSM: 9. 再次调用 (TDC可能已完成)
        TDC接口-->>占空比校准FSM: 10. 返回 true (TDC测量完成), 附带数据
        占空比校准FSM->>占空比校准FSM: 11. 计算占空比, 与目标比较
        alt 未达到目标
            占空比校准FSM->>占空比校准FSM: 12. 计算DCA调整量
            占空比校准FSM->>DCA接口: 13. 写入新DCA值
            DCA接口->>硬件寄存器: 14. 更新DCA硬件设置
            占空比校准FSM->>占空比校准FSM: 15. 状态: 返回DcConfig0 (准备下次迭代)
            占空比校准FSM-->>PMD层状态机: 16. 返回 false (进行中)
        else 达到目标或最大迭代
            占空比校准FSM->>占空比校准FSM: 17. 状态: 返回Init (准备下次可能的校准)
            占空比校准FSM-->>PMD层状态机: 18. 返回 true (校准完成!)
            break
        end
    end
```
这个序列图突出了校准过程的非阻塞和迭代特性。每次调用校准函数时，它只执行状态机的一小部分工作，然后快速返回，使得主控制循环可以继续处理其他任务。

### 4.4.3 底层硬件交互函数

*   **DCO 设置 (`dcoRxSetupCal`, `dcoTxSetupCal` in `dco.c`)**:
    这些函数负责配置数字控制振荡器（DCO）。DCO是产生校准过程中所需参考时钟或测试信号的部件。它们通常会通过写入特定的邮箱寄存器（Mailbox Registers）来配置DCO的种子值（`aSeedLsb`）和粗调延时（`aCrs`）等。

    ```c
    // 来自 dco.c (dcoRxSetupCal 简化示例)
    void dcoRxSetupCal(uint32_t aSeedLsb, uint32_t aCrs)
    {
        // 禁用DCO输出和清除CRS，准备加载新种子
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_OUT_EN, 0);
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_CRS, 0);
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_SEED_LD, 1); // 准备加载

        // 加载种子值和CRS值
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_SEED_LSB, aSeedLsb);
        // ... 设置 MSB ...
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_CRS, aCrs);
        
        // 启动DCO
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_OUT_EN, 1);
        WRITE_REG_FIELD_NEW(RX_CLK_MB_REG_BASE, RX_CLK_MB__RX_CLK_MBOX45, RXCLK_DCO_SEED_LD, 0); // 完成加载
    }
    ```
    这些 `WRITE_REG_FIELD_NEW` 宏是 [硬件抽象与控制函数](06_硬件抽象与控制函数_.md) 的一部分，用于向特定硬件寄存器的特定字段写入值。

*   **TDC 读取 (`tdcRxRead`, `tdcTxRead` in `tdc.c`)**:
    这些函数是与TDC硬件交互的核心。它们本身也是状态机，因为TDC测量需要时间。
    1.  **`eTdcMeasState_Init`**: 配置TDC，包括选择测量目标（`aCal`，例如 `eTdcRxCal_AdcCond` 用于ADC时钟调理），测量配置（`aCfg`，例如 `eTdcCfg_Dc0`），以及测量次数（`aTdcMeasCount`）。然后启动TDC测量，并转换到 `eTdcMeasState_AwaitMeas` 状态。
    2.  **`eTdcMeasState_AwaitMeas`**: 等待TDC硬件报告测量完成（通过读取状态寄存器中的完成标志，如 `TDC1_MEAS_DONE`）。在等待期间，函数返回 `false`。当测量完成后，读取TDC累加器的值到输出参数 `apAccumVal` 中，然后禁用TDC，重置状态机到 `_Init`，并返回 `true`。

    ```c
    // 来自 tdc.c (tdcRxRead 简化片段 - AwaitMeas 状态)
    case eTdcMeasState_AwaitMeas:
    {
        // 等待TDC测量完成标志
        if (READ_REG_FIELD_NEW(RX_REG_BASE, RX__STATUS78, TDC1_MEAS_DONE) == 0)
        {
            return false; // 测量未完成，下次再来
        }

        // 读取TDC累加器的值 (示例，实际会读取多个累加器)
        apAccumVal[0] = READ_REG_FIELD_NEW(RX_REG_BASE, RX__STATUS79, RX_0_CAL_OUT_ACC0);
        // ... 读取其他累加器 ...

        // 禁用TDC等清理工作
        WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__RX_TDC_CAL_CTL, TDC_MEAS_EN, 0);
        // ...

        *vpState = eTdcMeasState_Init; // 重置TDC读取状态机
        return true; // TDC读取完成
    }
    ```

*   **DCA/Deskew 读写**:
    `dcaRxRead`/`dcaTxRead` 和 `deskewRxRead`/`deskewTxRead` 通常直接读取相应的硬件寄存器来获取当前的DCA或Deskew控制码。
    `dcaRxWrite`/`dcaTxWrite` 和 `deskewRxWrite`/`deskewTxWrite` 则将计算出的新控制码写入硬件寄存器，以施加调整。这些操作一般是即时完成的。

通过这些精心设计的状态机和硬件抽象层，固件能够精确地、逐步地完成复杂的时钟调理校准任务。

## 4.5 总结

在本章中，我们深入探讨了**时钟调理校准 (Clk Cond Cal)** 的重要性和实现方式：

*   **目标**：确保ADC（模拟数字转换器）获得高质量的时钟信号，主要通过调整时钟的**占空比**和消除**相位偏移 (Deskew)** 来实现。这对于精确的数据转换和高速通信至关重要。
*   **核心过程**：主要包括占空比校准 (`processAdcCndInitDcSkewCal`) 和去歪斜校准 (`processAdcClkDeskew`)。两者都是基于**状态机**的迭代过程。
*   **实现机制**：
    *   校准函数是**非阻塞**的，每次调用执行一小步，通过返回 `true` (完成) 或 `false` (进行中) 来与上层PMD状态机协作。
    *   使用**函数指针表 (`gClkCondCalVTable`)** 来适配RX和TX的不同硬件接口。
    *   校准过程依赖**TDC**进行精确测量，并通过调整**DCA**（占空比）和**Deskew控制电路**（相位）来实现校正。
    *   固件配置（`gFwCfg`）可以影响校准行为，例如启用**快速模式**来跳过或简化校准。
*   **重要性**：如同给乐器调音，精确的时钟是数字系统和谐工作的基础。

理解了时钟调理校准这类精密校准是如何通过状态机一步步完成的，我们更能体会到固件在硬件控制中的复杂性和精妙之处。除了时钟，信号路径本身也需要精心的调整。

在下一章中，我们将学习另一个重要的校准/自适应过程：[信道估计 (Channel Estimation)](05_信道估计__channel_estimation__.md)，它关注的是如何根据信道特性优化信号处理。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)