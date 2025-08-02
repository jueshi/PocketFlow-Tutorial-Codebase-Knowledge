# Chapter 3: 链路训练 (Link Training)


在上一章 [配置管理 (Configuration Management)](02_配置管理__configuration_management__.md) 中，我们学习了系统如何为硬件模块加载一套初始的“推荐参数”，就像为乐器校准音准一样。配置完成后，硬件有了一个不错的起点，但这并不意味着它就能立即与网络中的其他设备完美通信，尤其是在高速数据传输的场景下。

想象一下，你和一位朋友第一次通过一个很长、可能有些干扰的电话线通话。你们可能需要先互相大声说“喂？听得到吗？”，然后根据对方的反馈调整自己说话的音量和清晰度，直到双方都能清楚地听到对方。高速串行通信中的设备也面临类似的情况。仅仅加载了默认配置，就像你只是清了清嗓子，但还没有和对方真正“对上话”。

这就是**链路训练 (Link Training)** 发挥作用的地方。

## 什么是链路训练？

**链路训练 (Link Training)** 是高速串行通信中建立稳定可靠连接的关键过程。它就像两个设备（比如你电脑的网卡和交换机端口）之间的“**握手**”和“**协商**”。在这个过程中，通信双方会：

1.  **交换特定的训练序列**：这些是预定义的、双方都知道的数据模式，就像说一些约定的口令“芝麻开门”。
2.  **交换控制信息**：基于接收到的训练序列的质量，一方会告诉另一方如何调整其发送参数。
3.  **自动调整各自的发送和接收参数**：最常见的是调整发送端的 **FFE (Feed-Forward Equalizer, 前馈均衡器)** 系数。FFE 我们将在 [FFE 自适应 (FFE Adaptation)](05_ffe_自适应__ffe_adaptation__.md) 章节详细学习，它能帮助补偿信号在传输路径（信道）中产生的失真。

整个链路训练过程旨在：

*   **补偿信道损耗和失真**：不同长度、不同质量的线缆，或者电路板上的走线，都会对高速信号产生不同程度的衰减和变形。链路训练帮助“修复”这些信号。
*   **找到最佳配置**：通过一系列的尝试和调整，找到一组能让双方以最低错误率进行数据传输的参数。
*   **确保数据能够稳定可靠地传输**：最终目标是建立一个高质量的通信链路。

我们 `hw` 项目中的链路训练模块实现了 IEEE (电气和电子工程师协会) 标准中定义的链路训练协议，确保了其兼容性和可靠性。

## 链路训练是如何工作的？

链路训练通常在设备上电初始化后、连接建立时，或者当系统检测到链路质量下降需要重新训练时启动。它是一个由通信双方（我们称之为本地设备 Local Device, LD 和远端设备 Remote Device, RD）共同参与的协作过程。

我们可以将链路训练大致分为以下几个阶段：

1.  **启动与同步 (Initiation and Synchronization)**：
    *   本地设备和远端设备都同意开始链路训练，并进入训练模式。
    *   它们会开始发送一些基本的同步信号，让双方知道训练开始了。

2.  **初始参数交换与预设尝试 (Initial Parameter Exchange & Preset Trial)**：
    *   通信的一方（通常是本地设备）会要求远端设备的发送器 (Transmitter, TX) 使用一组预定义的 FFE 系数（称为“预设值”，Preset）来发送训练码型。这些预设值是根据经验选定的，通常能适用于多种常见场景。
    *   本地设备的接收器 (Receiver, RX) 会接收这些训练码型，并评估信号质量。

3.  **反馈与迭代优化 (Feedback and Iterative Optimization)**：
    *   本地接收器会分析接收到的训练信号。这个分析过程可能涉及到内部的[接收器自适应引擎](01_接收器自适应引擎_.md)来优化本地接收设置。
    *   然后，本地设备会向远端设备发送反馈信息。这个反馈包含了对远端发送器 FFE 系数的调整建议，比如：“请把你的 C0 系数调大一点，C-1 系数调小一点”。（C0, C-1, C+1 等是 FFE 的抽头系数）。
    *   远端发送器根据收到的请求调整其 FFE 系数，并继续发送训练码型。
    *   这个“发送-接收-评估-反馈-调整”的过程会迭代进行多次，就像两个人不断调整音量和语速，直到听清为止。本地设备会尝试不同的预设值，或者在某个预设的基础上进行微调。

4.  **选择最佳参数与链路稳定 (Selecting Best Parameters and Link Stabilization)**：
    *   在迭代过程中，本地设备会记录下哪组远端 FFE 参数能带来最佳的接收信号质量（通常用一个称为“品质因数” FOM - Figure of Merit 的指标来衡量）。
    *   当训练过程判定找到了最佳参数组合，或者满足了协议规定的结束条件后，双方会锁定这些参数。

5.  **完成训练，进入数据传输模式 (Training Completion and Data Transmission Mode)**：
    *   链路训练成功结束，双方退出训练模式，开始使用优化后的参数进行正常的业务数据传输。

下面是一个简化的链路训练交互流程图：

```mermaid
sequenceDiagram
    participant 本地设备 (Local Device)
    participant 远端设备 (Remote Device)

    本地设备->>远端设备: 请求开始链路训练
    远端设备-->>本地设备: 同意，进入训练模式
    本地设备->>远端设备: 请求使用预设 P_n 发送训练序列
    远端设备->>远端设备: 设置发送器FFE为P_n, 发送训练序列
    本地设备->>本地设备: 接收并评估信号质量 (FOM)
    loop 反复优化 (尝试不同预设或微调)
        本地设备-->>远端设备: 请求调整FFE系数 (如: C0++, C-1--)
        远端设备->>远端设备: 调整FFE, 发送训练序列
        本地设备->>本地设备: 接收并评估信号质量 (FOM)
    end
    本地设备->>本地设备: 已找到最佳FFE设置
    本地设备->>远端设备: 通知训练完成，使用最终参数
    远端设备-->>本地设备: 确认
    Note over 本地设备,远端设备: 链路建立成功，开始数据传输!
end
```

## 深入探索：代码中的链路训练

现在，让我们深入代码，看看链路训练是如何在 `hw` 项目中实现的。我们会重点关注 `adapt_link_training.c` 和 `adapt_link_training_derived.c` 这两个文件。

### 1. 链路训练总指挥：`fwLinkTraining()` 状态机

链路训练的核心逻辑通常由一个状态机（Finite State Machine, FSM）来管理。在 `adapt_link_training.c` 文件中，`fwLinkTraining()` 函数就是这个状态机的实现。它负责按步骤执行链路训练的各个阶段。

```c
// 文件: adapt_link_training.c (简化片段)

// fwLinkTraining 是链路训练的主状态机函数
// 它会在每个调度周期被调用，直到返回 true 表示训练完成
bool fwLinkTraining()
{
    // 获取当前通道的链路训练状态机结构体指针
    struct tLtFSM_t* vpFsm = &gRx[gActiveLane].mAdapt.mLt;
    bool vDone = false; // 链路训练是否完成的标志

    // 根据当前状态 (vpFsm->mLtState) 执行不同操作
    switch (vpFsm->mLtState)
    {
        case eFwLtState_Init: // 初始状态
        {
            ltInit(); // 执行链路训练的初始化设置

            // ... 设置FFE预设扫描的初始参数 ...
            // 例如，选择一个预设值开始 (通常是 Preset 2 或 Initial Condition)
            // 并将状态切换到下一个：设置初始条件
            vpFsm->mLtState = eFwLtState_SetIc;
            break;
        }

        case eFwLtState_SetIc: // 设置初始条件 (Initial Condition)
        {
            // 选择一个 FFE 预设值 (Preset)
            enum tLtPreset_t vPRST = vpFsm->mPresetSweep.mpPresetSeq[vpFsm->mPresetSweep.mPresetSeqIdx];
            // ... (处理选择最佳预设的逻辑) ...

            // 请求远端发送器使用选定的预设值
            ltSetFetxPreset(vPRST); // 这个函数会通过寄存器操作来通知远端

            vpFsm->mLtState = eFwLtState_AwaitTrainStart; // 等待远端开始发送训练信号
            break;
        }

        // ... (省略了 eFwLtState_AwaitTrainStart, eFwLtState_SetModulationType, eFwLtState_IcUpdate 等状态) ...

        case eFwLtState_RunAdapt: // 运行本地接收器自适应
        {
            // 调用接收器自适应引擎优化本地接收器
            // runAdaptModes 会执行在 adapt_mode.c 中定义的自适应模式序列
            // 我们在 [接收器自适应引擎] 章节讲过
            if (!runAdaptModes(0, 10)) // 模式 0 到 10
            {
                break; // 自适应未完成，下次再来
            }

            // 如果预设扫描完成，则进入最终的系数调优阶段
            // 否则，继续测量当前预设下的信号质量
            if (vpFsm->mPresetSweep.mPresetDone)
            {
                vpFsm->mLtState = eFwLtState_AwaitFetxCnFsmReady; // 准备开始系数调优
            }
            else
            {
                vpFsm->mLtState = eFwLtState_FomMeas; // 测量品质因数 (FOM)
            }
            break;
        }

        case eFwLtState_FomMeas: // 测量品质因数 (Figure of Merit)
        {
            uint32_t vFom;
            // fomMeas 会测量当前接收信号的质量，得到一个数值 vFom
            // FOM 值越小通常表示信号质量越好
            if (fomMeas(&vFom)) // 如果测量完成
            {
                // 如果当前 FOM 比已记录的最佳 FOM 更好，则更新最佳 FOM 和对应的预设
                if (vFom < vpFsm->mPresetSweep.mBestFom)
                {
                    vpFsm->mPresetSweep.mBestFom = vFom;
                    vpFsm->mPresetSweep.mBestFomIdx = vpFsm->mPresetSweep.mCurrFomIdx;
                }
                // 准备尝试下一个预设或重启训练以应用新的预设
                vpFsm->mLtState = eFwLtState_RestartTraining;
            }
            break; // 等待 FOM 测量完成
        }

        // ... (省略了 eFwLtState_RestartTraining, eFwLtState_AwaitFetxCnFsmReady 等状态) ...

        case eFwLtState_RunTraining: // 运行远端发送器系数调优
        {
            // ltCnTune 会根据本地接收到的信号质量，
            // 通过发送控制帧来请求远端发送器微调其 FFE 系数
            if (!ltCnTune(vpFsm->mLtMode))
            {
                break; // 系数调优未完成，下次再来
            }

            // 系数调优完成，通知 PMD 链路训练过程结束
            ltSetCnTrainDone(1); // 设置训练完成标志

            vpFsm->mLtState = eFwLtState_AwaitSendData; // 等待远端确认并准备发送数据
            break;
        }

        // ... (省略了 eFwLtState_AwaitSendData 状态) ...

        case eFwLtState_Done: // 完成状态
        {
            ltExit(); // 执行链路训练退出清理工作
            vDone = true; // 标记整个链路训练过程完成
            break;
        }

        default: // 未知状态处理
        {
            vpFsm->mLtState = eFwLtState_Init; // 重置状态机
            break;
        }
    }
    return vDone; // 返回是否完成
}
```
*   `fwLinkTraining()` 函数通过内部的 `vpFsm->mLtState` 变量来跟踪和控制链路训练的进度。
*   它包含了多个状态，如初始化 (`eFwLtState_Init`)、设置初始条件/预设 (`eFwLtState_SetIc`)、运行本地自适应 (`eFwLtState_RunAdapt`)、测量信号质量 (`eFwLtState_FomMeas`)、执行远端FFE调优 (`eFwLtState_RunTraining`) 直到完成 (`eFwLtState_Done`)。
*   在每个状态中，它会调用相应的辅助函数来执行具体任务，并根据结果转换到下一个状态。
*   这个函数会被周期性调用，直到它返回 `true`，表示链路训练成功结束。

### 2. 预设值：加速训练的起点

为了让链路训练更快地收敛到最佳点，协议通常会定义一些“预设（Preset）”的FFE系数值。这些预设值是针对典型信道特性预先优化好的。

`adapt_link_training.c` 文件中定义了这些预设：

```c
// 文件: adapt_link_training.c (片段)

// 不同链路训练模式 (如 C72, C136 对应不同速率或标准) 的预设序列
// eLtPRST_1, eLtPRST_2 等是预设的枚举值
enum tLtPreset_t gPresetSeqC72[eLtConst_PresetSeqSizeC72] = {eLtPRST_2, eLtPRST_1, eLtPRST_Best};
// ... 其他模式的预设序列 ...

// C72 模式下，不同预设对应的默认 FFE 系数值
// 每一行对应一个预设 (Preset 2, Preset 1), `minusOne` 是因为数组索引从0开始而预设编号可能从1开始
// 列分别对应 C+1 (超前一个符号的抽头), C0 (主抽头), C-1 (滞后一个符号的抽头) 的系数值
uint32_t gPresetCoeffDefaultC72[eLtConst_PresetSeqSizeC72-1][eLtConst_PresetCoeffSizeC72] =
{   // C1, C0, CM1  (这里的 C1 代表 CP1 即 C+1, CM1 代表 C-1)
    {  0 , 64, 0  }, // 对应 eLtPRST_2 (通常是初始条件 Initial Condition)
    {  6 , 43, 3  }  // 对应 eLtPRST_1 (一个常用的预设值)
};
// ... 其他模式的预设系数值 ...
```
*   `gPresetSeqC72`：定义了在 C72 模式（一种链路训练模式，通常用于较低速率如10G/25G）下，尝试预设的顺序。`eLtPRST_Best` 表示在尝试完列表中的预设后，选用效果最好的那个。
*   `gPresetCoeffDefaultC72`：存储了 C72 模式下每个预设的具体 FFE 系数值。例如，预设2 (Initial) 的 (C+1, C0, C-1) 系数是 (0, 64, 0)。这些值会被加载到远端发送器的 FFE 中。

在 `fwLinkTraining()` 的 `eFwLtState_SetIc` 状态中，会通过 `ltSetFetxPreset(vPRST)` 函数（定义在 `adapt_link_training_derived.c`）请求远端发送器应用这些预设值。

```c
// 文件: adapt_link_training_derived.c (片段)

// 请求远端发送器 (FETX - Far End TX) 使用指定的预设值
void ltSetFetxPreset(enum tLtPreset_t aPreset)
{
    // 将预设值写入 PMD (Physical Medium Dependent) 层的特定寄存器字段
    // KRT_FETX_INIT_FFE_CFG (KR Training, Far End TX Initial FFE Configuration)
    // 硬件会自动将这个请求通过链路发送给远端设备
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__FETX_FFE_TRAIN_CFG2, KRT_FETX_INIT_FFE_CFG, aPreset);
}
```
`PMD_LANE_RX_REG_BASE` 是PMD模块中每个通道（Lane）的接收器寄存器基地址。

### 3. 远端发送器 FFE 系数调优：精细打磨

在尝试了几个预设之后，链路训练会进入一个更精细的调优阶段，试图在最佳预设的基础上进一步优化远端发送器的 FFE 系数。这个过程由 `ltCnTune()` 函数（"Cn" 通常指 Coefficient，即系数）和其子函数 `ltCnTuneOne()` 控制。

```c
// 文件: adapt_link_training.c (片段)

// FFE 系数更新序列，定义了调优时尝试调整哪些 FFE 抽头 (Cursor) 以及调整的力度
// {抽头类型, 更新次数, 增/减步数}
// eTxFfeCursor_Crsr (C0), eTxFfeCursor_Post (C+1), eTxFfeCursor_Pre1 (C-1) 等
struct tCursorUpdate_t gUpdateSeqC72[] =
{
    {eTxFfeCursor_Crsr, 10, 4}, // 粗调 C0 (主抽头)
    {eTxFfeCursor_Post, 8, 4},  // 粗调 C+1 (后标)
    // ... 更多粗调和精调步骤 ...
    {eTxFfeCursor_Post, 6, 2},  // 精调 C+1
    {eTxFfeCursor_Crsr, 6, 2},  // 精调 C0
    {0, 0, 0}, // 序列结束标记
};

// ltCnTuneOne 调优远端发送器的某一个 FFE 抽头系数，使其达到最佳 FOM
static bool ltCnTuneOne(enum tLtMode_t aMode, enum tTxFfeCursor_t aCursor, uint8_t aLoopCount, uint8_t aIncDecCount)
{
    // ... (状态机变量定义) ...
    switch (vpFsm->mState)
    {
        case eLtCnTuneOneState_Init:
            // ... 初始化迭代次数和方向 (增加或减少系数) ...
            vpFsm->mState = eLtCnTuneOneState_IncDecCn;
            break;

        case eLtCnTuneOneState_IncDecCn: // 增加或减少远端 TX 的系数
            // ltSetCn 会向远端发送请求，改变指定抽头 (aCursor) 的系数
            if (!ltSetCn(aMode, aCursor, vpFsm->mCnDir, &vpFsm->mFetxStatus))
            {
                break; // 请求未完成
            }
            // ... 更新迭代计数，如果达到指定步数 (aIncDecCount)，则去测量 FOM ...
            vpFsm->mState = eLtCnTuneOneState_MeasFom;
            break;

        case eLtCnTuneOneState_MeasFom: // 测量 FOM
            uint32_t vFom;
            if (!fomMeas(&vFom)) { break; } // FOM 测量未完成

            if (vFom > *vpPrevFom) // 如果 FOM 变差了 (值越大越差)
            {
                // 撤销刚才的系数改变
                switchDirection(&vpFsm->mCnDir); // 反方向
                vpFsm->mState = eLtCnTuneOneState_UndoChange1;
            }
            else // FOM 变好或不变
            {
                *vpPrevFom = vFom; // 更新记录的 FOM
                vpFsm->mState = eLtCnTuneOneState_IterEnd; // 当前抽头的一次迭代结束
            }
            break;
        // ... (省略 UndoChange1, UndoChange2, IterEnd 等状态) ...
    }
    return vDone;
}

// ltCnTune 遍历 gUpdateSeqC72/gUpdateSeqC136 中的序列，对每个指定的 FFE 抽头调用 ltCnTuneOne
static bool ltCnTune(enum tLtMode_t aMode)
{
    // ... (状态机变量定义) ...
    switch (vpFsm->mState)
    {
        case eLtCnTuneState_Init:
            // ... 初始化，选择合适的 gUpdateSeq (如 gUpdateSeqC72) ...
            vpFsm->mState = eLtCnTuneState_Run;
            break;

        case eLtCnTuneState_Run:
            // 从更新序列中取出一个条目，调用 ltCnTuneOne 进行调优
            if (!ltCnTuneOne(aMode, vpFsm->mpUpdateSeq->mCursor, ...)) { break; }
            // ... 移动到序列的下一个条目，直到序列结束 ...
            break;
    }
    return vDone;
}
```
*   `gUpdateSeqC72`：这是一个指令列表，告诉 `ltCnTune` 函数应该按什么顺序、以什么粒度（粗调/精调）去尝试调整远端发送器的 FFE 抽头（如 C0, C+1, C-1 等）。
*   `ltCnTuneOne()`：这个函数负责对远端发送器的某一个特定 FFE 抽头进行调优。它会尝试增加或减少该抽头的系数值，然后测量本地接收到的信号质量 (FOM)。如果 FOM 变好，就继续这个方向的调整；如果 FOM 变差，就撤销上一步操作，并可能尝试相反方向或者结束当前抽头的调整。
*   `ltSetCn()`：在 `ltCnTuneOne` 内部被调用，用于实际向远端发送一个“系数更新”请求。它会设置相应的寄存器，让硬件产生符合链路训练协议的控制帧，告诉远端设备：“请把你的 C0 系数增加/减少”。

`ltSetCn()` 函数最终会调用 `adapt_link_training_derived.c` 中的 `ltSetFetxCnChange()` 来完成实际的寄存器操作：
```c
// 文件: adapt_link_training_derived.c (片段)

// 设置请求远端 TX (FETX) 改变其 FFE 系数 (Cn)
// aCursor: 要改变的抽头 (pre, main, post)
// aDir: 方向 (increment, decrement, hold)
void ltSetFetxCnChange(enum tTxFfeCursor_t aCursor, enum tTxFfeDir_t aDir)
{
    // 将抽头和方向编码成一个值
    uint32_t vCoeffChange = (uint32_t)aDir << aCursor;
    // 通过覆盖 RX 模块的 PIN_OVRDVAL19 寄存器的特定字段，
    // 将这个系数改变请求传递给 PMA (Physical Medium Attachment) 层，
    // PMA 再将其编码成控制帧发给远端。
    // OVRD_EN_RX0_TXFFE_COEFF_CHANGE_O: 使能对 TXFFE 系数改变信号的覆盖
    // INT_RX0_TXFFE_COEFF_CHANGE_O: 覆盖的值
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__PIN_OVRDEN1, OVRD_EN_RX0_TXFFE_COEFF_CHANGE_O, 1);
    WRITE_REG_FIELD_NEW(RX_REG_BASE, RX__PIN_OVRDVAL19, INT_RX0_TXFFE_COEFF_CHANGE_O, vCoeffChange);
}
```

### 4. 链路训练的初始化与配置

在链路训练开始之前，需要进行一些初始化设置。`ltInit()` 和 `initLinkTraining()` 函数 (均在 `adapt_link_training.c`) 负责这些工作。

```c
// 文件: adapt_link_training.c (片段)

// 链路训练初始化 (每个通道在训练开始时调用)
static void ltInit()
{
    // ... (一些 FFE 和 PMA 边界信号的初始设置) ...

    // 根据当前数据速率配置链路训练模式 (C72, C136, C162 等) 和训练码型模式
    enum tTpatMode_t vTpatMode;
    ltRateConfig(&vpFsm->mLtMode, &vTpatMode); // ltRateConfig 在 adapt_link_training_derived.c

    // 设置训练码型 (Training Pattern) 的种子 (Seed) 和多项式 (Polynomial)
    // 这些码型是双方已知的，用于评估信道特性
    // gTpatSeed 和 gTpatPoly 是预定义的数组，存储不同模式下的种子和多项式
    // vIdentifier 通常是通道号，确保不同通道使用不同的种子以避免串扰
    uint32_t vIdentifier = gActiveLane;
    // 将种子值写入 PMD 的 PMD_TRAIN_SEED0/1 寄存器
    vSeed0.mFields.SEED_0 = gTpatSeed[vTpatMode][vIdentifier];
    // ... (设置其他 SEED 字段) ...
    WRITE_REG(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__PMD_TRAIN_SEED0, vSeed0);
    // ...

    // 设置训练码型的多项式选择 (通过 KRT_OVRD_VAL0 寄存器)
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__KRT_OVRD_VAL0, OVRD_VAL_TX_PATTERN_SEL, gTpatPoly[vTpatMode][vIdentifier]);

    // 设置链路训练模式 (C72, C136, C162) 到 PMD 寄存器
    ltSetMode(vpFsm->mLtMode); // ltSetMode 在 adapt_link_training_derived.c

    // ... (根据模式选择预设序列，如 gPresetSeqC72) ...
}

// 更早期的初始化，通常在系统启动，PLL 锁定前为所有通道调用一次
void initLinkTraining()
{
    // 静态配置，写入 FFE 系数的全局限制和预设默认值到 PMD 全局寄存器
    ltStaticConfig();

    // 在 PMD KRT (KR Training) 状态机中使能训练过程
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__BASER_PMD_CONTROL, TRAINING_ENABLE, 1);

    // 禁用训练超时定时器 (因为固件来控制整个流程)
    WRITE_REG_FIELD_NEW(PMD_LANE_RX_REG_BASE, PMD_LANE_RX__FETX_FFE_TRAIN_CFG2, NO_MAX_WAIT_TIMER_DONE, 1);

    // 让固件完全控制远端 TX FFE 状态机和系数更新状态机何时完成
    ltSetCnTrainDone(0); // 初始设为未完成
}
```
*   `ltRateConfig()` (在 `adapt_link_training_derived.c`)：根据当前的线路速率（例如 10G, 25G, 100G）来决定使用哪种链路训练模式（如 C72, C136, C162，这些是IEEE标准中定义的条款，对应不同类型的链路训练）和训练码型。
*   `ltSetMode()` (在 `adapt_link_training_derived.c`)：将选定的链路训练模式写入PMD控制寄存器，告诉硬件要遵循哪套规则进行训练。
*   `ltStaticConfig()`：这个函数（定义在 `adapt_link_training.c`）负责一次性地将链路训练所需的一些全局参数写入硬件寄存器，例如远端发送器 FFE 系数的允许范围（最大/最小值）以及在 [配置管理](02_配置管理__configuration_management__.md) 中提到的那些预设值（`gPresetCoeffDefaultC72` 等）会被写入到 PMD 的专用寄存器中，供硬件在处理预设请求时使用。这部分内容与 PMD 层的具体实现紧密相关，可以参考 [PMD 通道控制 (PMD Lane Control)](09_pmd_通道控制__pmd_lane_control__.md) 章节了解更多背景。

### 链路训练与自适应引擎的关系

你可能已经注意到，在 `fwLinkTraining()` 的 `eFwLtState_RunAdapt` 状态中，调用了 `runAdaptModes(0, 10)`。这正是我们在 [接收器自适应引擎](01_接收器自适应引擎_.md) 章节中学习过的内容。

链路训练的主要目标是优化**远端发送器**的参数（主要是FFE系数），使得它发送过来的信号对**本地接收器**来说尽可能好。同时，**本地接收器**自身也需要进行自适应调整，以最好地匹配当前接收到的信号。因此，链路训练过程通常是远端发送器调优和本地接收器自适应交替或并行进行的过程。`runAdaptModes()` 就是用来触发本地接收器的自适应算法（如 CDR、CTLE、VGA、本地 FFE 等）进行优化。

## 总结

在本章中，我们一起探索了“链路训练 (Link Training)”的奥秘。我们了解到：

*   链路训练是高速串行通信中设备间为了建立稳定可靠连接而进行的“握手”和“协商”过程。
*   它通过双方交换特定的训练序列和控制信息，自动调整发送和接收参数（特别是远端发送器的FFE系数），以补偿信道损耗和失真。
*   链路训练遵循一个复杂的状态机 (`fwLinkTraining`)，包括初始化、尝试预设值、迭代优化远端FFE系数（通过 `ltCnTune` 等函数发送请求）、评估信号质量 (FOM) 等步骤。
*   在链路训练过程中，本地的[接收器自适应引擎](01_接收器自适应引擎_.md)也会参与工作，优化本地接收条件。
*   代码中通过大量的寄存器读写来控制PMD硬件，实现链路训练协议定义的各种操作，例如设置训练模式 (`ltSetMode`)、请求远端使用预设 (`ltSetFetxPreset`)、请求远端调整FFE系数 (`ltSetFetxCnChange`)。
*   链路训练的成功是后续稳定数据传输的基石。

理解了链路训练如何帮助设备间“校准对话”，我们就能更好地欣赏高速通信链路的精密与复杂。

在链路建立之后，接收器的各个部分仍然需要持续工作以保持信号的稳定和准确恢复。下一章，我们将深入了解其中一个关键模块：[CDR 自适应 (CDR Adaptation)](04_cdr_自适应__cdr_adaptation__.md)，看看它是如何从接收到的信号中精确地恢复时钟并对齐数据的。

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)