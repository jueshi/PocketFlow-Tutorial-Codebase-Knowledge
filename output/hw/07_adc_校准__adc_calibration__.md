# Chapter 7: ADC 校准 (ADC Calibration)


欢迎来到 `hw` 项目教程的第七章！在上一章 [CTLE 自适应 (CTLE Adaptation)](06_ctle_自适应__ctle_adaptation__.md) 中，我们学习了 CTLE 如何像一个“高音助推器”一样，在模拟信号的早期阶段就对其进行初步的优化，补偿高频损耗。经过 CTLE 处理后，模拟信号的“轮廓”变得更加清晰了。现在，这个优化过的模拟信号需要被转换成数字信号，才能被后续的数字电路进一步处理和解读。这个关键的转换任务就由 ADC (Analog-to-Digital Converter, 模数转换器) 来完成。

但是，就像我们现实世界中的测量工具一样，ADC 也不是完美无缺的。它自身的物理特性会导致转换结果出现一些固有的偏差。如果不对这些偏差进行校准，那么无论我们后续的数字处理多么强大，最终得到的数据都可能是不准确的。

本章，我们将一起探索 **ADC 校准 (ADC Calibration)** 的奥秘。

## 什么是 ADC 校准？为什么它如此重要？

想象一下你有一把尺子。如果这把尺子的零刻度线没有对准尺子的起始边缘（**失调错误 Offset Error**），或者尺子上的刻度本身就不均匀，比如标称的1厘米实际上是0.9厘米或1.1厘米（**增益错误 Gain Error**），那么用这把尺子测量出来的长度就会不准确。

ADC 就像一把将模拟电压“测量”并转换成数字值的“尺子”。一个理想的 ADC 应该能够精确地反映模拟输入和数字输出之间的线性关系。然而，由于制造工艺的差异、工作环境（如温度）的变化等因素，实际的 ADC 会存在固有的偏差。

**ADC 校准** 模块的任务就是修正这些 ADC 固有的偏差，确保转换的准确性。它主要处理以下三种类型的错误：

1.  **失调 (Offset) 校准**：确保当 ADC 的输入为零（例如，输入端接地）时，其数字输出也应该为零。就像校准尺子的零点一样。
2.  **增益 (Gain) 校准**：确保 ADC 在其整个输入范围内，模拟输入电压的变化与数字输出值的变化之间的比例（即“刻度”）是一致和准确的。就像确保尺子的刻度是均匀且标准的。
3.  **时间交织采样时间偏差 (Skew) 校准**：在高速 ADC 设计中，为了达到更高的采样率，经常使用多个并行的子 ADC 以“时间交织 (Time-Interleaved)”的方式工作。每个子 ADC 在不同的时刻对输入信号进行采样，然后将结果合并。如果这些子 ADC 的采样时刻没有精确对齐（即存在时间偏差或 Skew），就会像多个摄影师用略微不同步的相机拍摄同一个快速运动的物体一样，合成出来的图像会产生失真。Skew 校准的目的就是精确调整这些子 ADC 的采样时钟相位，使它们的采样时刻严格对齐。

通过 ADC 校准，我们可以大大提高模数转换的精度，为后续所有数字信号处理步骤（如 [FFE 自适应 (FFE Adaptation)](05_ffe_自适应__ffe_adaptation__.md)、[CDR 自适应 (CDR Adaptation)](04_cdr_自适应__cdr_adaptation__.md)）提供可靠的数据基础。

## ADC 校准是如何工作的？

ADC 校准通常是[接收器自适应引擎](01_接收器自适应引擎_.md)在系统初始化或特定条件下（如温度变化显著时）执行的一个校准序列。其基本流程可以概括为：

1.  **进入校准模式**：ADC 被配置进入特定的校准模式。例如，在失调校准时，ADC 的输入可能会被内部接地。在增益校准时，可能会施加已知的参考电压。
2.  **测量偏差**：硬件测量 ADC 在当前校准模式下的输出值，并与期望值进行比较，从而得到偏差量。
3.  **计算校准码**：根据测量到的偏差，固件或专用的校准逻辑计算出相应的校准调整值（通常称为“校准码”）。
4.  **应用校准码**：将计算得到的校准码写入到 ADC 内部的校准寄存器中。这些校准码会调整 ADC 内部的模拟电路（例如，通过微调参考电压、电流或时钟相位），以补偿检测到的偏差。
5.  **迭代与验证 (可选)**：某些校准过程可能是迭代的，即重复进行“测量-计算-应用”的步骤，直到偏差被减小到可接受的范围内。校准完成后，可能还会进行一次验证测量。

下面是一个简化的 ADC 校准流程示意图：

```mermaid
sequenceDiagram
    participant AdaptEngine as "接收器自适应引擎"
    participant ADCCal as "ADC校准模块"
    participant ADCHardware as "ADC硬件"
    participant CalParams as "校准参数寄存器"

    AdaptEngine->>ADCCal: 请求启动ADC校准 (例如 失调校准)
    ADCCal->>ADCHardware: (1) 配置ADC进入校准模式 (如输入接地)
    ADCCal->>ADCHardware: (2) 触发ADC进行测量
    ADCHardware-->>ADCCal: (3) 返回测量结果 (如偏差值)
    ADCCal->>ADCCal: (4) 计算校准码 (例如新的失调码)
    ADCCal->>CalParams: (5) 更新ADC失调校准码
    Note over AdaptEngine, ADCCal: (类似流程进行增益和Skew校准)
    ADCCal-->>AdaptEngine: ADC校准完成
end
```

## 深入探索：代码中的 ADC 校准

现在，让我们深入代码，看看 `hw` 项目中 ADC 校准是如何实现的。我们将主要关注 `cal_adc.c` 文件（负责失调和增益校准）以及 `cal_adc_skew.c` 和 `deskew_code.c` 文件（负责时间交织 Skew 校准）。

### 1. 失调 (Offset) 校准：对准“零刻度”

失调校准的目标是消除 ADC 的零点漂移。函数 `rxSarOffset()` (SAR 指的是逐次逼近型ADC，一种常见的ADC架构) 负责执行这个任务。

```c
// 文件: cal_adc.c (简化片段)

// ... (tRxAdcOffsetCal_t 结构体和状态枚举定义，此处省略) ...

/*!
 * @brief 调整ADC失调码以纠正所有ADC之间的失调。
 * @param[in] aFast 快速/慢速模式
 * @return 如果为 true，则完成；否则，进行中。
 */
bool rxSarOffset(bool aFast)
{
    // 根据 aFast 选择迭代次数 (vNTop) 和调整步长 (vMu)
    int8_t vNTop = aFast ? eAdcOffsetCal_NTopFast : eAdcOffsetCal_NTopSlow;
    int8_t vMu = aFast ? eAdcOffsetCal_MuFast : eAdcOffsetCal_MuSlow;

    bool vDone = false;
    tRxAdcOffsetCal_t* vpFsm = &gRx[gActiveLane].mAdapt.mOffsetCal; // 获取当前通道的状态机

    switch (vpFsm->mState)
    {
        case eAdcOffsetCal_Init: // 初始化状态
        {
            if (aFast) // 快速模式下，清除已有的失调码
            {
                for (uint32_t vI = 0; vI < eHwConst_AdcCnt; ++vI)
                {
                    vpFsm->mOffsetCode[vI] = 0;
                }
                saveOffsetRestoreCode(vpFsm->mOffsetCode); // 将清零的失调码写入硬件
            }
            // ... (慢速模式下，如果硬件覆盖未使能，则加载当前硬件中的失调码) ...
            vpFsm->mIter = 0; // 重置迭代计数器
            vpFsm->mAdcStep = getAdcStep(); // 获取ADC的步进值（取决于ADC工作模式）
            vpFsm->mState = eAdcOffsetCal_Meas; // 进入测量状态
            break;
        }
        case eAdcOffsetCal_Meas: // 测量与调整状态
        {
            int32_t* vMeas; // 用于存储测量结果的指针
            // 调用 adcMeas 进行测量，通常输入接地 (eAdcOffsetCal_DataSel 会选择接地输入)
            if (adcMeas((uint32_t**)&vMeas, vpFsm->mAdcStep, eAdcOffsetCal_DataSel, eAdcOffsetCal_Avg))
            {
                // 对每个 (或每组) ADC 进行失调校正
                for (uint32_t vI = 0; vI < eHwConst_AdcCnt; vI += vpFsm->mAdcStep)
                {
                    int32_t vOffsetCode = vpFsm->mOffsetCode[vI]; // 当前失调码
                    // vAvgMeas 是ADC在零输入下的平均输出，理想应为0
                    int32_t vAvgMeas = (vMeas[vI] >> eAdcOffsetCal_AvgExp);

                    // 如果平均输出偏离零点超过阈值，则调整失调码
                    if (abs_int32(vAvgMeas) > eAdcOffsetCal_OffsetThresh)
                    {
                        if (vAvgMeas > 0) // 输出偏正，失调码需要减小
                        {
                            vOffsetCode -= vMu;
                        }
                        else // 输出偏负，失调码需要增大
                        {
                            vOffsetCode += vMu;
                        }
                    }
                    // 限制失调码在允许范围内
                    vpFsm->mOffsetCode[vI] = clamp_int32(vOffsetCode, eAdcOffsetCal_OffsetCodeMin, eAdcOffsetCal_OffsetCodeMax);
                }
                saveOffsetRestoreCode(vpFsm->mOffsetCode); // 保存调整后的失调码到硬件

                vpFsm->mIter++;
                if (vpFsm->mIter >= vNTop) // 如果达到迭代次数上限
                {
                    vpFsm->mState = eAdcOffsetCal_Done; // 校准结束
                }
                // 否则，继续下一次测量和调整 (状态不变，下次调用时仍在 eAdcOffsetCal_Meas)
            }
            break;
        }
        case eAdcOffsetCal_Done: // 完成状态
        default:
        {
            vpFsm->mState = eAdcOffsetCal_Init; // 重置状态机
            vDone = true;
            break;
        }
    }
    return vDone;
}
```

*   **状态机**：`rxSarOffset` 函数通过一个简单的状态机 (`eAdcOffsetCal_Init`, `eAdcOffsetCal_Meas`, `eAdcOffsetCal_Done`) 来管理校准流程。
*   **测量**：在 `eAdcOffsetCal_Meas` 状态中，核心是调用 `adcMeas()` 函数。这个辅助函数（我们稍后会简要介绍）负责配置ADC的输入（对于失调校准，`eAdcOffsetCal_DataSel` 通常会选择一个接地或零电平输入），然后启动ADC进行多次转换并累加结果，最后返回每个ADC的平均输出值。
*   **调整**：固件根据 `adcMeas()` 返回的平均输出值 `vAvgMeas` 来调整对应的失调校准码 `vOffsetCode`。如果 `vAvgMeas` 显著偏离0，就以步长 `vMu` 对 `vOffsetCode` 进行反向调整。
*   **保存**：调整后的失调校准码通过 `saveOffsetRestoreCode()` 函数写入到硬件的特定寄存器中。这些寄存器（如 `RX__OFFSET_N_GAIN_CAL10` 等）保存了可以被ADC硬件用来补偿失调的值。
*   **迭代**：这个“测量-调整-保存”的过程会重复 `vNTop` 次，以逐步逼近最佳的失调校准。

#### 辅助函数：`adcMeas()`

`adcMeas()` 是一个通用的ADC测量函数，也用于增益校准。它是一个状态机，负责：
1.  初始化ADC累加器相关的寄存器（如 `RX__GENERIC_CAL0` 中的 `ADC_ACCUM_DATA_SEL` 来选择输入源，`ADC_ACCUM_CLKCNT` 来设置累加时间）。
2.  依次选择每个（或每组）ADC (`ADC_ACCUM_SEL0`, `ADC_ACCUM_SEL1`)。
3.  为每个选定的ADC启动多次（`aNumAvg` 次）累加测量。
4.  等待测量完成 (`ADC_ACCUM_DONE` 状态位），读取累加结果 (`ADC_ACCUM_RESULT` 状态寄存器）。
5.  将所有ADC的累加结果（多次平均后）存储在 `vpFsm->mMeas` 数组中，并通过输出参数 `appMeas` 返回给调用者。

```c
// 文件: cal_adc.c (adcMeas 简化逻辑)
// static bool adcMeas(uint32_t** appMeas, uint8_t aAdcStep, uint8_t aDataSel, uint8_t aNumAvg)
// {
//     // ... 状态机 vpFsm ...
//     switch (vpFsm->mState)
//     {
//         case eAdcMeas_Init:
//             // 配置ADC累加器：选择数据源(aDataSel), 设置累加时钟数(eAdcMeas_ClkCnt)
//             // 启动第一次测量 (ADC_ACCUM_START = 1)
//             // vpFsm->mState = eAdcMeas_Meas1;
//             break;
//         case eAdcMeas_Meas1: // 等待测量完成
//             // if (ADC_ACCUM_DONE == 1)
//             //     读取 ADC_ACCUM_RESULT, 累加到 vpFsm->mMeas[vpFsm->mAdcIdx]
//             //     ADC_ACCUM_START = 0; // 清除启动位
//             //     vpFsm->mState = eAdcMeas_Meas2;
//             break;
//         case eAdcMeas_Meas2: // 等待启动位清零，然后判断是否继续平均或换下一个ADC
//             // if (ADC_ACCUM_DONE == 0)
//             //     vpFsm->mMeasIter++;
//             //     if (vpFsm->mMeasIter < aNumAvg) // 继续平均
//             //         ADC_ACCUM_START = 1; vpFsm->mState = eAdcMeas_Meas1;
//             //     else // 当前ADC平均完成
//             //         vpFsm->mAdcIdx += aAdcStep; // 换下一个ADC
//             //         if (vpFsm->mAdcIdx < eHwConst_AdcCnt) // 还有ADC未测
//             //             选择新的ADC, ADC_ACCUM_START = 1; vpFsm->mState = eAdcMeas_Meas1;
//             //         else // 所有ADC测量完毕
//             //             *appMeas = vpFsm->mMeas; vDone = true;
//             break;
//     }
//     return vDone;
// }
```

#### 辅助函数：`loadOffsetCode()` 和 `saveOffsetRestoreCode()`

*   `loadOffsetCode(int8_t* apOffsetCode)`：从一系列状态寄存器（`RX__STATUS30` 到 `RX__STATUS49`）中读取硬件当前为每个ADC（共80个）计算或使用的失调校准码，并存入 `apOffsetCode` 数组。
*   `saveOffsetRestoreCode(const int8_t* apOffsetCode)`：将 `apOffsetCode` 数组中的失调校准码写入到另一组配置寄存器（`RX__OFFSET_N_GAIN_CAL10` 到 `RX__OFFSET_N_GAIN_CAL42` 中的 `ADC_DATAx_OFFSET_RESTORE_CODE` 字段）。然后通过脉冲 `ADC_OFFSET_LOAD_RESTORE` 位，让硬件加载这些新的失调码。

### 2. 增益 (Gain) 校准：确保“刻度”均匀准确

增益校准的目标是确保ADC对于不同的输入幅度，其转换比例（增益）是一致且准确的。函数 `rxSarGain()` 负责此任务。其结构和逻辑与 `rxSarOffset()` 非常相似。

```c
// 文件: cal_adc.c (简化片段)

// ... (tRxAdcGainCal_t 结构体和状态枚举定义，此处省略) ...

/*!
 * @brief 调整ADC增益码以实现所有ADC之间的均匀增益。
 * @param[in] aFast 快速/慢速模式
 * @return 如果为 true，则完成；否则，进行中。
 */
bool rxSarGain(bool aFast)
{
    // 根据 aFast 和 gSwAdaptArg2 (来自 fw_adapt_config.c) 选择迭代次数和步长
    int8_t vNTop = aFast ? gSwAdaptArg2.mGainFastNTop : gSwAdaptArg2.mGainSlowNTop;
    int8_t vMu = aFast ? gSwAdaptArg2.mGainFastMu : gSwAdaptArg2.mGainSlowMu;

    bool vDone = false;
    tRxAdcGainCal_t* vpFsm = &gRx[gActiveLane].mAdapt.mGainCal; // 获取当前通道的状态机

    switch (vpFsm->mState)
    {
        case eAdcGainCal_Init: // 初始化状态
        {
            // 如果硬件覆盖未使能，则从硬件加载当前增益码
            if (READ_REG_FIELD_NEW(RX_REG_BASE, RX__OFFSET_N_GAIN_CAL0, ADC_GAIN_CODE_OVRD_MODE) == 0)
            {
                loadGainCode(vpFsm->mGainCode);
            }
            vpFsm->mIter = 0;
            vpFsm->mAdcStep = getAdcStep();
            vpFsm->mState = eAdcGainCal_Meas; // 进入测量状态
            break;
        }
        case eAdcGainCal_Meas: // 测量与调整状态
        {
            uint32_t* vMeas; // 用于存储测量结果的指针
            // 调用 adcMeas 进行测量。eAdcGainCal_DataSel 会选择一个特定的输入信号
            // (例如一个已知幅度的测试信号，或利用输入信号的统计特性)
            if (adcMeas(&vMeas, vpFsm->mAdcStep, eAdcGainCal_DataSel, eAdcGainCal_Avg))
            {
                // 计算所有被测ADC的平均“增益指示值”
                uint32_t vMeanGain = 0;
                for (uint32_t vI = 0; vI < eHwConst_AdcCnt; vI += vpFsm->mAdcStep)
                {
                    vMeas[vI] >>= eAdcGainCal_AvgExp; // 取平均
                    vMeanGain += vMeas[vI];
                }
                vMeanGain = (vMeanGain * vpFsm->mAdcStep) / eHwConst_AdcCnt; // 计算总平均

                // 根据每个ADC的增益与总平均增益的差异，调整其增益码
                for (uint32_t vI = 0; vI < eHwConst_AdcCnt; vI += vpFsm->mAdcStep)
                {
                    int32_t vGainCode = vpFsm->mGainCode[vI]; // 当前增益码
                    if (vMeas[vI] < vMeanGain) // 当前ADC增益偏低
                    {
                        vGainCode += vMu; // 增大增益码
                    }
                    else if (vMeas[vI] > vMeanGain) // 当前ADC增益偏高
                    {
                        vGainCode -= vMu; // 减小增益码
                    }
                    // 限制增益码在允许范围内
                    vpFsm->mGainCode[vI] = clamp_int32(vGainCode, eAdcGainCal_GainCodeMin, eAdcGainCal_GainCodeMax);
                }
                saveGainRestoreCode(vpFsm->mGainCode); // 保存调整后的增益码到硬件

                vpFsm->mIter++;
                if (vpFsm->mIter >= vNTop) // 如果达到迭代次数上限
                {
                    vpFsm->mState = eAdcGainCal_Done; // 校准结束
                }
            }
            break;
        }
        case eAdcGainCal_Done: // 完成状态
        default:
        {
            vpFsm->mState = eAdcGainCal_Init; // 重置状态机
            vDone = true;
            break;
        }
    }
    return vDone;
}
```
*   **核心逻辑**：与失调校准类似，`rxSarGain` 也使用 `adcMeas()` 来获取每个ADC的输出。不同的是，为了测量增益，`eAdcGainCal_DataSel` 会让ADC输入一个已知的非零信号，或者算法会分析输入信号的幅度特性。然后，它计算所有ADC的平均“增益指示值” (`vMeanGain`)。对于每个ADC，如果其“增益指示值”低于平均值，则增加其增益码；如果高于平均值，则减小增益码。
*   **参数来源**：增益校准的迭代次数 (`mGainFastNTop`, `mGainSlowNTop`) 和调整步长 (`mGainFastMu`, `mGainSlowMu`) 来自于 `gSwAdaptArg2` 结构体，该结构体通常在 `fw_adapt_config.c` 中定义，是固件自适应参数的一部分。
*   **辅助函数**：`loadGainCode()` 从状态寄存器 (`RX__STATUS50` 至 `RX__STATUS69`) 读取当前增益码。`saveGainRestoreCode()` 将新的增益码写入配置寄存器 (`RX__OFFSET_N_GAIN_CAL1` 至 `RX__OFFSET_N_GAIN_CAL38` 中的 `ADC_DATAx_GAIN_CAL_RESTORE_CODE` 字段) 并通过 `ADC_GAIN_LOAD_RESTORE` 脉冲加载。

### 3. 时间交织 Skew 校准：对齐“采样节拍”

在高速ADC中，通常采用多个子ADC以时间交织 (Time-Interleaved, TI) 的方式工作，每个子ADC负责在总采样周期中的一小段时间内进行采样。例如，一个总采样率为80GS/s的ADC，可能由80个以1GS/s速率采样但相位错开的子ADC构成。如果这些子ADC的采样时钟没有精确地对齐，就会引入失真。Skew校准的目的就是调整每个子ADC采样时钟的精细延迟，使它们严格同步。

`rxAdcIntlCal()` (ADC Interleave Calibration) 函数 (在 `cal_adc_skew.c` 中) 负责此任务。

```c
// 文件: cal_adc_skew.c (简化片段)

// ... (tRxAdcIntlCal_t 结构体和状态枚举定义，此处省略) ...

/*!
 * @brief 执行ADC交织校准。校准ADC时钟以具有相同的相位延迟。
 * @param[in] aMode 校准模式 (粗调/精调/CCA)
 * @return 如果为 true，则校准完成；否则，进行中。
 */
bool rxAdcIntlCal(enum tCalMode_t aMode)
{
    // 根据校准模式选择调整步长(vAdaptMu)、迭代次数(vNTop)、阈值(vMsePedDiffThresh)
    // ... (参数选择逻辑省略) ...

    bool vDone = false;
    struct tRxAdcIntlCal_t* vpFsm = &gRx[gActiveLane].mAdapt.mRxAdcIntlCal; // 获取状态机

    switch (vpFsm->mState)
    {
        case eRxAdcIntlCalState_Init: // 初始化状态
            // ... (初始化迭代计数器、历史记录等) ...
            // 配置ADC累加器用于Skew校准 (特定的数据选择和CDR数据模式)
            WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__GENERIC_CAL0, ADC_ACCUM_DATA_SEL, 9); // 选择Skew校准的输入数据
            // ...
            deskewRxRead(vpFsm->mDeskewCode); // 从硬件读取当前的Deskew码
            vpFsm->mState = eRxAdcIntlCalState_Loop; // 进入主循环
            break;

        case eRxAdcIntlCalState_Loop: // 主循环状态
            if (vpFsm->mIterCnt >= vNTop) { /* ... 完成 ... */ break; } // 达到迭代次数

            int32_t vIncDecClks[eHwConst_AdcClkCnt]; // 存储每个时钟相位需要调整的方向 (+1, -1, or 0)
            // 调用 calcClkPhaseError 测量每个ADC时钟相对于参考时钟的相位误差
            if (!calcClkPhaseError(vMsePedDiffThresh, vIncDecClks))
            {
                break; // 测量未完成，下次再来
            }

            // ... (将当前Deskew码存入历史记录，用于后续的退出条件判断 - 此处简化) ...
            // ... (基于历史记录检查是否提前退出 - 此处简化) ...

            // 根据测量到的相位误差，调整Deskew码
            for (uint32_t vI = 0; vI < eHwConst_AdcClkCnt; ++vI)
            {
                // vAdaptMu 是调整步长，vIncDecClks[vI] 是调整方向
                vpFsm->mDeskewCode[vI] += vAdaptMu * vIncDecClks[vI];
            }

            // ... (如果Deskew码接近边界，则整体平移所有Deskew码 - 此处简化) ...
            // ... (检查Deskew码是否来回抖动，如果是则提前退出 - 此处简化) ...

            deskewClamp(vpFsm->mDeskewCode); // 限制Deskew码在有效范围内
            deskewRxWrite(vpFsm->mDeskewCode); // 将新的Deskew码写入硬件

            vpFsm->mIterCnt++;
            vpFsm->mState = eRxAdcIntlCalState_Adapt; // 进入自适应稳定阶段
            break;

        case eRxAdcIntlCalState_Adapt: // 等待系统在新的Deskew码下稳定
            // 运行一些通用的接收器自适应模式，让其他模块适应新的时钟相位
            if (runAdaptModes(eRxAdcIntlCalConst_ModeStart, eRxAdcIntlCalConst_ModeEnd))
            {
                vpFsm->mState = eRxAdcIntlCalState_Loop; // 返回主循环，进行下一轮调整
            }
            break;

        case eRxAdcIntlCalState_Done: // 完成状态
        default:
            vpFsm->mState = eRxAdcIntlCalState_Init; vDone = true; break;
    }
    return vDone;
}
```
*   **核心思想**：`rxAdcIntlCal`通过迭代调整每个子ADC采样时钟的精细延迟（称为Deskew码），以最小化它们之间的相对时间偏差。
*   **相位误差测量 (`calcClkPhaseError`)**：这是Skew校准的关键。这个辅助函数（状态机）会：
    *   根据ADC的工作模式（如80个ADC全开，40个ADC等）选择一个合适的参考时钟相位（通常是相位0）。
    *   依次选择其他各个时钟相位，通过 `RX__ADC_INTLV_CAL5` 寄存器的 `ADC_ACCUM_SKEW_CAL_MUX` 字段配置ADC累加器，使其测量当前选定相位与参考相位之间的“误差信号”。这个误差信号间接反映了时间偏差。
    *   `gAdcClockMux...` 数组（如 `gAdcClockMux80i80o`）定义了不同ADC模式下，`ADC_ACCUM_SKEW_CAL_MUX` 应如何设置以选择特定的时钟相位进行测量。
    *   测量结果（`vpFsm->mMsePed`）被用来判断每个时钟相位是超前还是滞后于参考相位，并决定调整方向 (`apIncDecClks`)。

```c
// 文件: cal_adc_skew.c (calcClkPhaseError 简化逻辑)
// static bool calcClkPhaseError(uint32_t aMsePedDiffThresh, int32_t* apIncDecClks)
// {
//     // ... 状态机 vpFsm->mPhaseErrorFsm ...
//     switch (vpFsm->mState)
//     {
//         case eCalcClkPhaseErrorState_Init:
//             // 根据ADC模式选择mClkIncrement和mpPhaseToAdcIdx (如gAdcClockMux80i80o)
//             // 设置ADC_ACCUM_SKEW_CAL_MUX为参考相位 (通常是mpPhaseToAdcIdx[0])
//             // 启动测量 (ADC_ACCUM_START = 1)
//             break;
//         case eCalcClkPhaseErrorState_Meas1: // 等待测量完成
//             // if (ADC_ACCUM_DONE == 1)
//             //     读取ADC_ACCUM_RESULT (相位误差值), 累加到 vpFsm->mMsePed[vpFsm->mIterCnt]
//             //     ADC_ACCUM_START = 0;
//             break;
//         case eCalcClkPhaseErrorState_Meas2: // 等待清零后判断是否继续平均或换下一个相位
//             //     if (继续平均) ADC_ACCUM_START = 1;
//             //     else if (还有相位未测)
//             //         设置ADC_ACCUM_SKEW_CAL_MUX为下一个待测相位
//             //         ADC_ACCUM_START = 1;
//             //     else (所有相位测量完毕)
//             //         计算每个相位mMsePed相对于参考相位(mMsePed[0])的差值 vError[vI]
//             //         如果abs(vError[vI]) > aMsePedDiffThresh, 则设置apIncDecClks[vI]为+1或-1
//             //         vDone = true;
//             break;
//     }
//     return vDone;
// }
```

*   **Deskew码的读写与转换 (`deskew_code.c`)**：
    *   `deskewRxRead(int32_t* apDeskewCode)`: 从RX时钟模块的邮箱寄存器（如 `RX_CLK_MB__RX_CLK_MBOX8081`）中读取控制每个ADC时钟相位的VCP (Voltage Control P-channel) 和 VCN (Voltage Control N-channel) 值。然后调用 `vcToDeskewCode()` 将这些VCP/VCN值转换成一个更抽象的、线性的“Deskew码” (`apDeskewCode`)。
    *   `deskewRxWrite(const int32_t* apDeskewCode)`: 接收调整后的“Deskew码” (`apDeskewCode`)，调用 `deskewCodeToVc()` 将其转换回VCP和VCN值，然后将这些VCP/VCN值写入到RX时钟模块的邮箱寄存器中，从而实际调整硬件中可变延迟线的延迟量，校正时钟相位。
    *   `deskewClamp(int32_t* apDeskewCode)`: 确保Deskew码不会超出硬件允许的范围。

```c
// 文件: deskew_code.c (简化逻辑)

// 将 VCP/VCN 值转换为 Deskew 码
// void vcToDeskewCode(const uint32_t* restrict apVcp, const uint32_t* restrict apVcn, int32_t* restrict apDeskewCode) {
//     // Deskew码大致反映了 (VCP - VcpMin) - (VcnMax - VCN) 的线性组合
//     // 确保即使VCP/VCN的调整是非线性的，Deskew码也是一个近似线性的控制量
// }

// 将 Deskew 码转换为 VCP/VCN 值
// void deskewCodeToVc(uint32_t* restrict apVcp, uint32_t* restrict apVcn, const int32_t* restrict apDeskewCode) {
//     // 根据Deskew码计算出合适的VCP和VCN值，以产生期望的延迟
//     // apVcp[vI] = eHwConst_VcpMin + (apDeskewCode[vI] >> 1);
//     // apVcn[vI] = eHwConst_VcnMax - ((apDeskewCode[vI] + 1) >> 1);
// }

// 从RX时钟邮箱读取VCP/VCN并转换为Deskew码
// void deskewRxRead(int32_t* apDeskewCode) {
//     // 读取 RX_CLK_MB__RX_CLK_MBOX... 寄存器得到 vVcp 和 vVcn 数组
//     // vcToDeskewCode(vVcp, vVcn, apDeskewCode);
// }

// 将Deskew码转换为VCP/VCN并写入RX时钟邮箱
// void deskewRxWrite(const int32_t* apDeskewCode) {
//     // deskewCodeToVc(apDeskewCode, vVcp, vVcn);
//     // 将 vVcp 和 vVcn 数组写入 RX_CLK_MB__RX_CLK_MBOX... 寄存器
//     // 脉冲 RX_CLK_MB__RX_CLK_MBOX7071 寄存器的 ADC_ILO_CND_SDM_LD 位来加载新值
// }
```

*   **自适应稳定**：在 `eRxAdcIntlCalState_Adapt` 状态，会调用 `runAdaptModes()`。这是因为改变了ADC的采样时钟相位后，可能会影响到接收路径上其他依赖于时序的模块（如CDR、FFE）。运行一轮通用的自适应可以让整个系统重新稳定和优化。

通过这三个主要的校准步骤（失调、增益、Skew），ADC的性能可以得到显著提升，从而为整个接收链路提供更准确的数字信号。

### ADC 校准相关配置参数

ADC校准算法的行为会受到 `fw_adapt_config.c` 中定义的 `gFwAdaptConfig` 和 `gSwAdaptArg2` 等结构体的影响。这些结构体中包含了失调、增益和Skew校准所需的迭代次数、调整步长、阈值等参数。例如：
*   失调校准：`eAdcOffsetCal_NTopFast`, `eAdcOffsetCal_MuFast`, `eAdcOffsetCal_OffsetThresh` 等（这些常量通常在 `cal_adc.h` 中基于配置定义）。
*   增益校准：`gSwAdaptArg2.mGainFastNTop`, `gSwAdaptArg2.mGainFastMu` 等。
*   Skew校准：`eRxAdcIntlCalConst_AdaptMuCoarse`, `eRxAdcIntlCalConst_NTopCoarse`, `gSwAdaptArg2.mNumReadsExp` (控制相位误差测量的平均次数) 等。

这些参数为固件提供了灵活性，可以根据不同的芯片特性或系统要求来调整校准算法的细节。

## 总结

在本章中，我们一起学习了“ADC 校准”的重要性及其基本原理：

*   ADC 校准是修正 ADC 固有偏差（失调、增益、时间交织Skew）的关键过程，就像校准一把尺子，确保其零点准确、刻度均匀。
*   **失调校准 (`rxSarOffset`)** 确保零输入对应零输出，通过测量零输入下的ADC输出并调整失调码实现。
*   **增益校准 (`rxSarGain`)** 确保不同输入幅度下转换比例一致，通过测量已知输入下的ADC输出（或利用信号统计特性）并调整增益码，使其与平均增益对齐。
*   **时间交织Skew校准 (`rxAdcIntlCal`)** 确保多个并行子ADC的采样时刻精确对齐，通过测量各时钟相位间的相对误差并调整Deskew码（最终控制VCP/VCN电压）来实现。
*   这些校准过程通常涉及状态机控制、通过 `adcMeas` 或类似机制进行测量、计算校准码，并通过专用寄存器将校准码应用于硬件。
*   校准参数（如迭代次数、步长、阈值）通常由固件配置文件（如 `fw_adapt_config.c`）提供。

经过精确校准的 ADC 能够为后续的数字信号处理模块提供高质量、高保真的数据流，这对于实现稳定可靠的高速通信至关重要。

到目前为止，我们已经学习了链路建立、各种均衡器（CTLE, FFE）、时钟数据恢复（CDR）以及ADC校准等在链路稳定工作后进行的一次性或周期性的优化过程。但是，通信信道和环境条件是可能随时间动态变化的。那么，系统是如何在链路正常工作期间，持续地监控并微调这些参数以适应这些变化的呢？

下一章，我们将学习 [连续校准与自适应 (CCA)](08_连续校准与自适应__cca__.md)，看看系统是如何实现这种“在线”的、持续的优化能力的。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)