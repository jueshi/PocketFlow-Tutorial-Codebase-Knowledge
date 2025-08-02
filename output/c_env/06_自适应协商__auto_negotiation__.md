# Chapter 6: 自适应协商 (Auto-Negotiation)


欢迎来到 `c_env` 教程的第六章！在上一章 [第 5 章：PHY SDK API](05_phy_sdk_api_.md) 中，我们学习了如何使用一套高级的软件开发工具包 (SDK) 函数来配置和控制 PHY 的各种复杂功能，这使得我们与 PHY 的交互更加便捷。现在，我们的 PHY 已经具备了执行具体任务的能力。但设想一下，当我们将一个网络设备（比如一台电脑或交换机）接入网络时，它如何知道应该以多快的速度、采用何种通信方式（例如是否启用某些高级纠错功能）与对端设备进行交流呢？如果每次都需要手动为链路两端的设备配置这些参数，那将是一项非常繁琐且容易出错的工作，尤其是在复杂的网络环境中。

为了解决这个问题，现代网络设备普遍采用了一种智能的自动化机制——这就是我们本章要探讨的“自适应协商”(Auto-Negotiation)。

## 什么是自适应协商？—— 网络设备的“初次握手”

**自适应协商**，顾名思义，就是通信链路两端的设备**自动地**、**互相地**协商出一套双方都能接受并支持的最佳通信参数的过程。

**打个比方：**
想象两个人初次见面，想要开始交谈。
*   **自适应协商前的情况**：你需要提前告诉A：“你必须用中文，语速每分钟120字，讨论天气。” 同时告诉B：“你也必须用中文，语速每分钟120字，讨论天气。” 如果任何一方的设置稍有差错，他们可能就无法顺畅交流。
*   **有了自适应协商**：A 会先做自我介绍：“你好！我会说中文、英文和法文。我语速可以快也可以慢。我们可以聊天气、体育或技术。” B 听了之后，也会回应：“你好！我会说中文和日文。我语速正常。我喜欢聊天气和美食。”
    然后，他们会根据双方都能接受的语言（中文）、共同感兴趣的话题（天气），以及合适的语速来开始对话。

对于网络设备（比如 PHY 芯片），这个过程非常相似：
1.  当两个设备通过网线连接起来时，它们会各自广播自己的“能力名片”。
2.  这张“名片”上写着它们支持的各种通信模式，例如：
    *   速率 (Speed)：比如 1 Gbps, 10 Gbps, 25 Gbps, 100 Gbps 等。
    *   双工模式 (Duplex Mode)：全双工 (Full-duplex) 或半双工 (Half-duplex)。
    *   前向纠错 (Forward Error Correction - FEC)：例如 RS-FEC (Reed-Solomon FEC) 是否启用，以及支持哪种类型的 RS-FEC。
    *   暂停帧 (Pause Frames)：一种流量控制机制。
    *   其他高级特性或厂商特定功能。
3.  双方交换了“名片”后，会按照一套预定义的“优先级规则”（通常由 IEEE 标准规定，例如 IEEE 802.3 Clause 73），从双方都支持的模式中挑选出一个“最佳”的共同模式。这个最佳模式被称为“**最高公共指示**”(Highest Common Denominator - HCD)。
4.  一旦 HCD 确定，双方设备就会自动配置到这个模式下开始正常通信。

自适应协商使得不同厂家、不同型号、不同能力的设备也能方便地互联互通，大大简化了网络部署和管理。

## 核心概念解析

在我们深入了解如何使用 SDK API 进行自适应协商之前，先来熟悉几个关键概念：

1.  **链路伙伴 (Link Partner - LP)**:
    *   **是什么？** 指连接在通信链路另一端的设备。在自适应协商过程中，我们的本地设备 (Local Device - LD) 就是在和这个链路伙伴进行协商。
    *   **好比什么？** 你打电话时，电话另一头的那个人。

2.  **能力页面 (Capability Pages)**:
    *   **是什么？** 设备用来宣告自身能力的“数据包”。这些页面通过链路在设备间传递。
    *   **好比什么？** 前面提到的“能力名片”。
    *   主要有两种类型的页面：
        *   **基本页面 (Base Page - BP)**: 这是自适应协商的第一阶段交换的页面。它包含了设备最核心的能力，比如支持的以太网速率 (10M, 100M, 1G, 10G, 40G, 100G 等)、是否支持全双工、是否支持某种类型的 FEC (如 Clause 74 FEC for 10GBASE-KR, Clause 91 RS-FEC for 25G/100GBASE-KR/CR)、以及是否支持下一页 (Next Page) 等。
        *   **下一页 (Next Page - NP)**: 如果基本页面表明双方都支持下一页，并且有更高级或厂商特定的功能需要协商，就会进入下一页交换阶段。下一页可以是“消息页”(Message Page)，用于传递标准化的扩展能力，也可以是“未格式化页”(Unformatted Page)，用于传递厂商自定义的信息。一个设备可以发送多个下一页。

3.  **优先级规则 (Priority Rules)**:
    *   **是什么？** 一套标准化的规则，用于在本地设备和链路伙伴都声称支持多种共同的通信模式时，决定选择哪一种。通常，规则会优先选择速率更高、功能更强的模式。
    *   **好比什么？** 两个人都会说多种语言，但为了最高效交流，他们可能会优先选择双方都最流利的那门语言。

4.  **最高公共指示 (Highest Common Denominator - HCD)**:
    *   **是什么？** 经过自适应协商后，双方设备共同确定下来的、并且根据优先级规则是最佳的通信模式。一旦 HCD 确定，双方设备就会按照这个模式进行配置并建立链路。
    *   **好比什么？** 两位外交官最终商定使用的官方会谈语言和议题。

5.  **FEC (Forward Error Correction - 前向纠错)**:
    *   **是什么？** 一种在数据发送端加入冗余信息（校验码），使得接收端在收到含有少量错误的数据时能够自动检测并纠正错误的技术。在高速串行通信中（如 25 Gbps 及以上速率），由于信道噪声和损耗更容易导致数据出错，FEC 变得尤为重要。自适应协商过程中通常会协商是否启用 FEC 以及启用哪种类型的 FEC。
    *   **好比什么？** 你寄一封重要的信，除了信本身，还附带了一份摘要或关键信息的校验。如果信件在邮寄过程中有几个字迹模糊了，收件人可以通过摘要和校验来尝试恢复。

## 自适应协商是如何工作的？—— SDK API 视角

`c_env` 项目中的 PHY SDK 提供了一系列 API 函数来帮助我们管理和执行自适应协商过程。这些函数通常定义在 `ipname_sdk_autoneg.c` (这里的 `ipname` 是具体 PHY 型号的占位符) 文件中。

让我们看看使用 SDK API 进行自适应协商的主要步骤和相关函数。核心的数据结构是 `ipname_an_context_t` (用于保存协商过程的上下文信息) 和 `ipname_an_status_t` (用于获取协商状态)。

**主要流程：**

1.  **初始化本地设备能力 (Programming Local Capabilities)**:
    *   首先，你需要告诉你的 PHY 芯片它自己具备哪些能力，希望向链路伙伴宣告什么。
    *   这通过填充 `ipname_an_context_t` 结构体中的 `bp` (Base Page) 和 `pmd_np` (PMD Next Page，如果需要) 成员来完成。
    *   然后调用 `ipname_sdk_an_program_bp()` 函数将这些 Base Page 能力编程到 PHY 的寄存器中。
    *   如果需要交换 Next Page，则类似地填充 `pmd_np` 并调用 `ipname_sdk_an_program_next_page()`。

2.  **启动/重启自适应协商 (Starting/Restarting Auto-Negotiation)**:
    *   配置好本地能力后，需要启动或重启 PHY 的自适应协商逻辑。这通常通过设置 PHY 的接收器配置 (`ipname_sdk_rx_cfg()`，其中有个 `an_en` 字段) 或调用一个专门的重启函数如 `ipname_sdk_an_restart()` 来实现。

3.  **监控协商过程 (Monitoring the Process)**:
    *   自适应协商是一个动态的过程，需要一些时间来完成页面交换和决策。你需要轮询 PHY 的状态来了解进展。
    *   `ipname_sdk_an_check_page_received()`: 用于检查是否从链路伙伴那里收到了新的页面（Base Page 或 Next Page）。
    *   `ipname_sdk_an_read_lp_bp()`: 当收到 Base Page 后，用此函数读取链路伙伴宣告的 Base Page 能力，结果会存入 `ipname_an_status_t` 结构体的 `lp_bp` 成员。
    *   `ipname_sdk_an_read_lp_np()`: 类似地，读取链路伙伴的 Next Page 能力，存入 `lp_np`。

4.  **计算 HCD (Calculating HCD)**:
    *   当双方都交换完必要的信息后 (至少是 Base Page)，SDK 可以帮助计算 HCD。
    *   `ipname_sdk_an_calculate_hcd()`: 此函数会比较之前编程的本地能力 (`cfg->bp`, `cfg->local_rates` 等) 和从链路伙伴读取到的能力 (`status->lp_bp`, `status->lp_np`)，并根据内置的优先级规则确定 HCD。协商结果 (HCD 对应的速率枚举值) 会存储在 `status->hcd_rate` 中。

5.  **应用 HCD (Applying HCD)**:
    *   一旦 HCD 确定，就需要将这个结果配置到 PHY 的硬件中，使其按照协商出的模式工作。
    *   `ipname_sdk_an_program_resolved_rate()`: 将 `status->hcd_rate` (或 `cfg->hcd_rate`) 写入 PHY 内部的速率配置寄存器，并通常会触发一个加载机制使新速率生效。

6.  **完成协商 (Finalizing Negotiation)**:
    *   `ipname_sdk_an_finalize()`: 用于检查整个自适应协商过程是否已经完成，并清除相关的中断状态。

### 示例：一个简化的自适应协商流程

下面的代码片段展示了如何使用这些 SDK API 来执行一个基本的自适应协商流程。这只是一个概念性的演示，实际应用中会更复杂，并包含更完善的错误处理和超时机制。

```c
#include "ipname_sdk_autoneg.h" // 包含自适应协商相关的 API
#include "ipname_sdk_platform.h"  // 平台函数，例如寄存器读写
#include <stdio.h>              // 用于 printf

// 假设 phy_base_addr 是 PHY 的基地址
// 假设 target_lane_no 是要进行自适应协商的通道号
uint32_t phy_base_addr = 0xYOUR_PHY_BASE_ADDRESS;
uint8_t target_lane_no = 0;

int main_an_example() {
    ipname_an_context_t an_context; // AN 上下文，用于输入配置
    ipname_an_status_t  an_status;  // AN 状态，用于获取结果
    ipname_error_code   result;

    // --- 1. 初始化本地设备能力 ---
    an_context.phy_base_addr = phy_base_addr;
    an_context.lane_no       = target_lane_no;

    // 设置 Base Page 参数 (示例，具体值取决于你的设备能力)
    an_context.bp.selector_field           = 0x1; // 表示 IEEE 802.3
    an_context.bp.transmitted_nonce_field  = 0x1A; // 一个随机数
    an_context.bp.np                       = 1;    // 表明支持 Next Page
    // 设置技术能力位域 (示例: 支持 100GBASE-KR1 和 50GBASE-KR)
    // 这些宏 (如 IPNAME_E100G, IPNAME_E50G) 代表速率枚举或掩码
    // local_rates 也是一个位掩码，用于 HCD 计算
    an_context.bp.tech_ability_field = (1 << 16) | (1 << 13); // 假设位16是100G, 位13是50G
    an_context.local_rates = (1 << IPNAME_E100G) | (1 << IPNAME_E50G);

    // 设置 Next Page 参数 (如果 bp.np = 1)
    an_context.pmd_np.message_field          = 0x5; // 假设是 consortium (联盟规范) 类型的 Next Page
    an_context.pmd_np.unformatted_code_field = 0x04DF0353; // 厂商特定的 OUI 或数据
    an_context.pmd_np.xnp_np                 = 0; // 这是最后一个 Next Page

    printf("步骤 1: 编程本地 Base Page 和 Next Page...\n");
    result = ipname_sdk_an_program_bp(&an_context, &an_status); // an_status.local_rates 会被填充
    if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
    if (an_context.bp.np) {
        result = ipname_sdk_an_program_next_page(&an_context);
        if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
    }
    
    // --- 2. 启动/重启自适应协商 ---
    // 通常在配置完 RX 后，AN 会自动开始。如果需要显式重启：
    // result = ipname_sdk_an_restart(&an_context);
    // if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
    printf("步骤 2: 自适应协商已启动 (或等待链路伙伴响应)...\n");

    // --- 3. 监控协商过程 (这是一个简化的轮询循环) ---
    printf("步骤 3: 等待并读取链路伙伴 (LP) 的页面...\n");
    bool lp_bp_received = false;
    bool lp_np_received = false;
    int retries = 10; // 示例超时

    // 等待 LP 的 Base Page
    while (retries-- > 0 && !lp_bp_received) {
        result = ipname_sdk_an_check_page_received(&an_context, &an_status);
        if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
        if (an_status.page_received) {
            result = ipname_sdk_an_read_lp_bp(&an_context, &an_status);
            if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
            printf("  已收到并读取 LP Base Page。\n");
            lp_bp_received = true;
            // 打印 LP Base Page 的内容 (使用 ipname_print_base_page)
            ipname_print_base_page(&(an_status.lp_bp), target_lane_no);
        } else {
            // ipname_sdk_plat_usleep(100000); // 等待一段时间
        }
    }
    if (!lp_bp_received) { printf("  错误: 未能收到 LP Base Page。\n"); return -1; }

    // 如果双方都支持 Next Page，则等待 LP 的 Next Page
    if (an_context.bp.np && an_status.lp_bp.np) {
        retries = 10;
        while (retries-- > 0 && !lp_np_received) {
            result = ipname_sdk_an_check_page_received(&an_context, &an_status);
            if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
            if (an_status.page_received) { // 假设收到的就是 Next Page
                result = ipname_sdk_an_read_lp_np(&an_context, &an_status);
                if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
                printf("  已收到并读取 LP Next Page。\n");
                lp_np_received = true;
                // 打印 LP Next Page 的内容
                ipname_print_next_page(&(an_status.lp_np), target_lane_no); 
            } else {
                // ipname_sdk_plat_usleep(100000); 
            }
        }
        if (!lp_np_received) { printf("  警告: 未能收到 LP Next Page (但仍可能基于 BP 协商)。\n");}
    }

    // --- 4. 计算 HCD ---
    printf("步骤 4: 计算 HCD...\n");
    // 实际应用中，an_context 可能需要填充更多从 LP 读取到的 NP 信息，如 lp_extend_ability_en_page
    // 这里简化，假设 HCD 主要基于 BP 和已读取的第一个 NP (如果存在)
    an_context.consort_rate = (an_context.pmd_np.message_field == 0x5); // 示例：如果 NP 是联盟类型
    an_context.extend_ability_rate = (an_context.pmd_np.message_field == 0x1); // 示例：如果 NP 是扩展能力类型
    
    result = ipname_sdk_an_calculate_hcd(&an_context, &an_status);
    if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }

    if (an_status.an_status == IPNAME_AN_LINK_INCOMPATIBLE || an_status.hcd_rate == (uint32_t)-1) {
        printf("  协商失败：链路不兼容，或无共同支持的模式。\n");
        // 可选：设置链路不兼容并重启 AN (ipname_sdk_an_set_link_incompatible, ipname_sdk_an_restart)
        return -1;
    } else {
        printf("  HCD 计算成功！协商速率枚举值: %u\n", an_status.hcd_rate);
        an_context.hcd_rate = an_status.hcd_rate; // 将HCD结果存回context供下一步使用
    }

    // --- 5. 应用 HCD ---
    printf("步骤 5: 应用协商出的 HCD 速率...\n");
    result = ipname_sdk_an_program_resolved_rate(&an_context);
    if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }

    // --- 6. 完成协商 ---
    printf("步骤 6: 等待并最终确认 AN 完成...\n");
    retries = 10;
    bool an_completed = false;
    while(retries-- > 0 && !an_completed) {
        result = ipname_sdk_an_finalize(&an_context, &an_status);
        if (result != IPNAME_NO_ERROR) { /* 错误处理 */ return -1; }
        if (an_status.an_complete) {
            printf("  自适应协商成功完成！\n");
            an_completed = true;
        } else {
            // ipname_sdk_plat_usleep(100000);
        }
    }
    if (!an_completed) { printf("  错误: AN 未能最终完成。\n"); return -1;}

    return 0;
}
```
**代码解释**：
*   **`ipname_an_context_t`**: 这个结构体用于保存自适应协商的配置和中间状态，例如本地设备宣告的基本页面 (`bp`)、下一页 (`pmd_np`)、已计算出的 HCD 速率 (`hcd_rate`) 等。
*   **`ipname_an_status_t`**: 这个结构体用于从 SDK 函数获取协商的结果和状态，例如链路伙伴的基本页面 (`lp_bp`)、下一页 (`lp_np`)、协商状态 (`an_status`)、协商出的 HCD 速率 (`hcd_rate`)，以及页面接收标志 (`page_received`) 等。
*   **`ipname_sdk_an_program_bp()`**: 将 `an_context.bp` 中定义的本地能力写入 PHY 的相关寄存器。`an_status.local_rates` 成员也会被 SDK 内部根据 `bp.tech_ability_field` 计算并填充，用于后续的 HCD 计算。
*   **`ipname_sdk_an_program_next_page()`**: 类似地，编程下一页。
*   **`ipname_sdk_an_check_page_received()`**: 查询 PHY 状态，看是否有新的页面从链路伙伴处接收到。结果会更新 `an_status.page_received`。
*   **`ipname_sdk_an_read_lp_bp()` / `..._np()`**: 如果 `page_received` 为真，调用这些函数来读取并解析链路伙伴宣告的能力，并填充到 `an_status.lp_bp` 或 `an_status.lp_np`。
*   **`ipname_print_base_page()` / `..._next_page()`**: 这些是 SDK 提供的辅助函数，用于以可读的格式打印出 Base Page 或 Next Page 的内容，方便调试。
*   **`ipname_sdk_an_calculate_hcd()`**: 这是核心的决策函数。它会综合本地能力和从链路伙伴读取到的能力，按照 IEEE 标准定义的优先级规则，计算出双方都支持的最佳通信模式 (HCD)。结果通常是一个代表速率的枚举值，存入 `an_status.hcd_rate`。如果无法达成一致，`an_status.an_status` 可能会被设为 `IPNAME_AN_LINK_INCOMPATIBLE`。
*   **`ipname_sdk_an_program_resolved_rate()`**: 将计算出的 `hcd_rate` (从 `an_context.hcd_rate` 获取) 配置到 PHY 的硬件寄存器中，使 PHY 按照协商结果工作。
*   **`ipname_sdk_an_finalize()`**: 检查 AN 过程是否最终完成，并做一些清理工作。

**预期行为**：
如果一切顺利，调用这个流程后，本地 PHY 和链路伙伴 PHY 会成功协商出一个共同的通信模式（例如，都同意以 100 Gbps 速率、启用 RS-FEC 进行通信），并且链路会按照这个模式建立起来。如果协商失败（例如，双方没有任何共同支持的模式），则链路无法建立，相关状态寄存器会指示错误。

## 深入幕后：自适应协商的内部机制

当我们调用上述 SDK API 时，它们内部是如何与 PHY 硬件交互，并遵循 IEEE 标准来完成协商的呢？

### 非代码流程概览 (IEEE 802.3 Clause 73 简化流程)

1.  **使能 AN**: 链路两端的设备都使能了自适应协商功能。
2.  **发送 FLP (Fast Link Pulse) / Base Page**:
    *   设备开始发送一系列特殊的脉冲序列，称为 FLP (Fast Link Pulse) 突发。这些 FLP 中编码了设备的基本页面 (Base Page) 信息。
    *   Base Page 包含16位数据，其内容由 `ipname_sdk_an_program_bp()` 设置到 PHY 的 `AN_BP0` 和 `AN_BP1` 等寄存器中。
3.  **接收并解码 LP 的 Base Page**:
    *   设备同时也在监听来自链路伙伴的 FLP 突发。当收到足够的 FLP 后，会解码出链路伙伴的 Base Page。
    *   `ipname_sdk_an_read_lp_bp()` 会从 PHY 的 `AN0` 和 `AN1` 等状态寄存器中读取这些解码后的信息。
4.  **能力匹配与 HCD 初步确定**:
    *   每个设备将自己宣告的 Base Page 能力与从对方收到的 Base Page 能力进行比较。
    *   根据 IEEE Clause 73 定义的优先级表（例如，100GBASE-KR4 优先于 40GBASE-KR4，全双工优先于半双工等），确定一个双方都支持的最高优先级模式。这是初步的 HCD。
    *   `ipname_sdk_an_calculate_hcd()` 内部会执行这个比较和优先级判断逻辑。
5.  **Next Page 交换 (如果需要)**:
    *   如果 Base Page 中的“Next Page (NP)”位被置为1，表示双方都愿意或需要交换更多的信息，则进入 Next Page 交换阶段。
    *   设备会发送一个或多个 Next Page。Next Page 的内容（消息类型、厂商 OUI、扩展能力等）由 `ipname_sdk_an_program_next_page()` 设置到 PHY 的 `AN_XNP0` 和 `AN_XNP1` 等寄存器。
    *   同样，设备也会接收并解码来自链路伙伴的 Next Page，信息由 `ipname_sdk_an_read_lp_np()` 从 `AN2` 和 `AN3` 等寄存器读取。
    *   Next Page 交换会持续进行，直到一方发送的 Next Page 中 NP 位为0，表示这是它最后一个 Next Page。
    *   HCD 可能会根据 Next Page 的内容进一步完善。
6.  **完成协商 (Complete Acknowledge)**:
    *   当双方都认为协商已完成（通常是一方已发送 NP=0 的 Next Page，且收到了对方的 NP=0 的 Next Page，或者双方都只交换了 Base Page 且已达成一致），会进入“Complete Acknowledge”状态。
    *   此时，双方都已确定了最终的 HCD。
7.  **配置硬件并建立链路**:
    *   设备使用 `ipname_sdk_an_program_resolved_rate()` 将协商出的 HCD（如速率、FEC模式）配置到 PHY 的数据路径和 MAC 控制器。
    *   之后，链路会按照 HCD 模式进行训练（如果需要，例如 KR 链路训练）并最终建立。
    *   `ipname_sdk_an_finalize()` 用于确认这个过程已完成。

### 简化版序列图 (AN 流程)

```mermaid
sequenceDiagram
    participant 本地设备 (LD)
    participant SDK_AN_API as "SDK"
    participant PHY硬件 (LD侧)
    participant 链路伙伴 (LP)

    用户代码->>SDK: 调用 ipname_sdk_an_program_bp(本地能力)
    SDK->>PHY硬件 (LD侧): 通过 asr() 写入 AN_BP0, AN_BP1 等寄存器
    Note over PHY硬件 (LD侧), LP: PHY硬件开始发送FLP (编码了Base Page)

    loop 等待LP的Base Page
        用户代码->>SDK: 调用 ipname_sdk_an_check_page_received()
        SDK->>PHY硬件 (LD侧): 通过 agr() 读取 AN_UOR0 寄存器 (PAGE_RECEIVED 位)
        PHY硬件 (LD侧)-->>SDK: 返回状态
        alt 页面未收到
            SDK-->>用户代码: 返回 "未收到"
        else 页面已收到
            SDK-->>用户代码: 返回 "已收到"
            用户代码->>SDK: 调用 ipname_sdk_an_read_lp_bp()
            SDK->>PHY硬件 (LD侧): 通过 agr() 读取 AN0, AN1 寄存器 (LP的Base Page)
            PHY硬件 (LD侧)-->>SDK: 返回LP的Base Page数据
            SDK-->>用户代码: 返回LP的Base Page
            break
        end
    end

    Note over LP, PHY硬件 (LD侧): LP也在做类似操作，向LD发送其Base Page

    opt 如果需要 Next Page 交换
        用户代码->>SDK: 调用 ipname_sdk_an_program_next_page(本地NP能力)
        SDK->>PHY硬件 (LD侧): 写入 AN_XNP0, AN_XNP1 (本地NP)
        Note over PHY硬件 (LD侧), LP: PHY硬件发送编码了Next Page的FLP
        用户代码->>SDK: (类似地) 轮询并读取 LP 的 Next Page
        SDK-->>用户代码: 返回LP的Next Page
    end

    用户代码->>SDK: 调用 ipname_sdk_an_calculate_hcd(本地能力, LP能力)
    SDK-->>SDK: 内部逻辑：比较能力，应用优先级规则
    SDK-->>用户代码: 返回计算出的 HCD 速率

    用户代码->>SDK: 调用 ipname_sdk_an_program_resolved_rate(HCD速率)
    SDK->>PHY硬件 (LD侧): 通过 asr() 写入 AN_CFG0 (AN_FW_RESOLVED_RATE, CL73_AN_FW_RATE_LOAD)
    
    用户代码->>SDK: 调用 ipname_sdk_an_finalize()
    SDK->>PHY硬件 (LD侧): 通过 agr() 读取 AN4 (AN_COMPLETE位), 并通过 asr() 清除中断
    SDK-->>用户代码: 返回 AN 完成状态

    Note over PHY硬件 (LD侧), LP: 双方配置为HCD模式，链路建立
```
**图解**:
*   用户通过 SDK API 配置本地 PHY 的能力，这些能力通过 [寄存器访问抽象层](02_寄存器访问抽象层_.md) 的 `asr()` (在 SDK 内部的 `ipname_sdk_reg_write()` 中调用) 写入 PHY 硬件的特定寄存器。
*   PHY 硬件负责实际的 FLP 页面交换。
*   用户通过 SDK API 轮询状态并读取链路伙伴宣告的能力，SDK 内部使用 `agr()` (在 `ipname_sdk_reg_read()` 中调用) 从状态寄存器获取信息。
*   SDK API 辅助计算 HCD，并将最终结果配置回 PHY 硬件。

### 代码实现片段 (参考 `ipname_sdk_autoneg.c`)

让我们看一些关键 SDK 函数内部的简化逻辑，它们是如何操作寄存器的。

1.  **`ipname_sdk_an_program_bp()` (编程本地 Base Page)**

    ```c
    // 文件: sdk_api/design/src/ipname_sdk_autoneg.c (简化片段)
    // (内部函数 ipname_program_base_page 被 ipname_sdk_an_program_bp 调用)
    void ipname_program_base_page (uint32_t phy_base_addr, uint8_t lane_no, ipname_bp_t *bp) 
    {
       uint32_t reg_val;

       // 写入 AN_BP0 寄存器
       // PMD_LANE_RX_BASE_ADDR(lane_no) 计算通道基地址
       // PMD_LANE_RX__AN_BP0__ADDR 是 AN_BP0 寄存器的偏移量
       reg_val = ipname_sdk_reg_read(phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__AN_BP0__ADDR);
       
       // IPNAME_SET_FIELD 是一个宏，用于设置寄存器变量 reg_val 中的特定位域
       // 例如 PMD_LANE_RX__AN_BP0__SELECTOR_FIELD 定义了 selector_field 在寄存器中的位和宽度
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_BP0__SELECTOR_FIELD, bp->selector_field);
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_BP0__BP_REMOTE_FAULT, bp->remote_fault);
       // ... 设置其他 bp 成员到 reg_val 的相应位域 ...
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_BP0__BP_TRANSMIT_NONCE, bp->transmitted_nonce_field);
       
       ipname_sdk_reg_write((phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__AN_BP0__ADDR), reg_val);

       // 类似地写入 AN_BP1 寄存器 (包含 tech_ability_field)
       reg_val = ipname_sdk_reg_read(phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__AN_BP1__ADDR);
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_BP1__TECH_ABILITY_FIELD, bp->tech_ability_field);
       ipname_sdk_reg_write((phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(lane_no) + PMD_LANE_RX__AN_BP1__ADDR), reg_val);
       
       // ... 可能还会配置 AN_CFG0 中的页面接收超时等参数 ...
    }
    ```
    **代码解释**:
    *   函数首先读取目标寄存器（如 `AN_BP0`）的当前值。
    *   然后，使用 `IPNAME_SET_FIELD` 宏，将用户在 `bp` 结构体中提供的各个能力参数（如 `selector_field`, `transmitted_nonce_field`, `tech_ability_field`）设置到 `reg_val` 变量的正确位域。这些宏（如 `PMD_LANE_RX__AN_BP0__SELECTOR_FIELD`）通常在头文件中定义，它们精确描述了每个字段在32位寄存器中的起始位和长度。
    *   最后，将修改后的 `reg_val` 写回到寄存器。
    *   这个过程对 `AN_BP0` 和 `AN_BP1`（用于技术能力）都会执行。

2.  **`ipname_sdk_an_read_lp_bp()` (读取链路伙伴 Base Page)**

    ```c
    // 文件: sdk_api/design/src/ipname_sdk_autoneg.c (简化片段)
    ipname_error_code ipname_sdk_an_read_lp_bp (ipname_an_context_t *cfg, ipname_an_status_t *status) 
    {
       uint32_t reg_val;
       // ... 参数校验 ...

       // 读取 AN0 状态寄存器 (包含 LP Base Page 的一部分)
       reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__AN0__ADDR);
       
       // IPNAME_GET_FIELD 是一个宏，用于从寄存器值 reg_val 中提取特定位域的值
       // 例如 PMD_LANE_RX__AN0__LP_SELECTOR_FIELD 定义了 LP selector_field 的位和宽度
       status->lp_bp.selector_field = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__AN0__LP_SELECTOR_FIELD);
       status->lp_bp.remote_fault   = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__AN0__LP_BP_REMOTE_FAULT);
       // ... 提取其他 LP Base Page 字段 ...
       status->lp_bp.transmitted_nonce_field = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__AN0__LP_TRANSMIT_NONCE_FIELD);

       // 读取 AN1 状态寄存器 (包含 LP Base Page 的技术能力部分)
       reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__AN1__ADDR);
       status->lp_bp.tech_ability_field = IPNAME_GET_FIELD(reg_val, PMD_LANE_RX__AN1__LP_TECH_ABILITY_FIELD);
       
       return IPNAME_NO_ERROR;
    }
    ```
    **代码解释**:
    *   函数从 PHY 的状态寄存器（如 `AN0`, `AN1`）中读取原始数据。这些寄存器中包含了 PHY硬件解码出的、由链路伙伴发送过来的 Base Page 内容。
    *   使用 `IPNAME_GET_FIELD` 宏，从这些原始数据中提取出各个字段的值（如 `LP_SELECTOR_FIELD`, `LP_TECH_ABILITY_FIELD`），并存入 `status->lp_bp` 结构体中。

3.  **`ipname_sdk_an_calculate_hcd()` (计算 HCD)**

    ```c
    // 文件: sdk_api/design/src/ipname_sdk_autoneg.c (简化片段)
    ipname_error_code ipname_sdk_an_calculate_hcd (ipname_an_context_t *cfg, ipname_an_status_t *status) 
    {
       uint32_t lp_rates = 0; // 用于存储从 LP 能力转换来的速率位掩码
       uint32_t lp_ability = status->lp_bp.tech_ability_field; // LP 的技术能力字段
       // ... (如果LP支持NP, 还会用到 status->lp_np 或 status->lp_extend_ability_en_page 等)
       
       // 将 LP 的 tech_ability_field (一个位图) 转换为与 cfg->local_rates 格式相同的 lp_rates 位掩码
       // 例如: 如果 LP 的 tech_ability_field 的第16位是1 (代表100G), 且 IPNAME_E100G 是100G的枚举/掩码
       // 则 lp_rates 的 IPNAME_E100G 对应位会被置1
       // (实际代码中会有一长串的 if 或 case 语句，或者像下面这样的位映射转换)
       lp_rates |= ((lp_ability >> IPNAME_E1GKX_ENCODING & 0x1) << IPNAME_E1GKX) 
                | ((lp_ability >> IPNAME_E10GKR_ENCODING & 0x1) << IPNAME_E10GKR)
                // ... 对所有标准速率进行映射 ...
                | ((lp_ability >> IPNAME_E100G_ENCODING & 0x1) << IPNAME_E100G);
       
       // 如果有 Next Page，还会根据 LP 的 NP 内容更新 lp_rates
       // (例如，从 consortium NP 或 extended ability NP 中提取更多速率支持)
       if(cfg->consort_rate && status->lp_np.message_field == 0x5 /* consortium */) {
           // lp_rates |= (从 status->lp_np.unformatted_code_field 提取的联盟速率);
       }

       // 计算共同支持的速率：通过位与操作
       uint32_t common_supported_rates = cfg->local_rates & lp_rates;
       
       // 找出共同支持的速率中，优先级最高的那个
       // ipname_highest_bit() 函数会返回 common_supported_rates 中最高位的索引 (即优先级最高的速率枚举)
       status->hcd_rate = ipname_highest_bit(common_supported_rates);

       if (status->hcd_rate == (uint32_t)-1) { // -1 通常表示没有共同速率
          status->an_status = IPNAME_AN_LINK_INCOMPATIBLE;
       } else {
          cfg->hcd_rate = status->hcd_rate; // 保存 HCD 结果
          status->an_status = IPNAME_AN_LINK_GOOD;
       }
       return IPNAME_NO_ERROR;
    }
    ```
    **代码解释**:
    *   首先，函数将从链路伙伴 Base Page (以及可能的 Next Page) 中读取到的技术能力位域（通常是符合 IEEE 标准定义的位图）转换为一个内部统一的速率位掩码 `lp_rates`。
    *   然后，通过对本地设备支持的速率掩码 (`cfg->local_rates`) 和链路伙伴支持的速率掩码 (`lp_rates`) 进行**位与 (AND) 操作**，得到 `common_supported_rates`，这个掩码中为1的位就代表双方都支持的速率。
    *   最后，调用 `ipname_highest_bit()` (或类似的逻辑) 在 `common_supported_rates` 中找到**最高有效位**。由于这些速率掩码的位通常是按照优先级排列的（例如，更高位的速率优先级更高），所以最高有效位就代表了 HCD。
    *   如果 `common_supported_rates` 为0（即没有共同支持的速率），则协商失败。

4.  **`ipname_sdk_an_program_resolved_rate()` (应用协商速率)**

    ```c
    // 文件: sdk_api/design/src/ipname_sdk_autoneg.c (简化片段)
    ipname_error_code ipname_sdk_an_program_resolved_rate (ipname_an_context_t *cfg)
    {
       uint32_t reg_val;
       int8_t hcd_rate_to_program = cfg->hcd_rate; // 获取已计算出的 HCD 速率枚举值
       
       // ... 参数校验 ...

       // 读取 AN_CFG0 寄存器
       reg_val = ipname_sdk_reg_read(cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__AN_CFG0__ADDR);
       
       // 根据PHY型号不同，HCD速率可能写入不同的字段
       #if PLATFORM == x814_rel1p0 // 例如 x814 PHY
           // 可能需要将 HCD 速率枚举值映射到硬件寄存器具体使用的编码值
           uint8_t lane_rate_hw_code = lane_rate_mapping[hcd_rate_to_program]; 
           IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_CFG0__AN_LANE_RATE, lane_rate_hw_code);
       #elif PLATFORM == x812_rel2p1 // 例如 x812 PHY
           IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_CFG0__AN_FW_RESOLVED_RATE, hcd_rate_to_program);
       #endif
       
       // 先清除加载触发位，再写入包含新速率的配置值
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_CFG0__CL73_AN_FW_RATE_LOAD, 0);
       ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__AN_CFG0__ADDR), reg_val);

       // 设置加载触发位，使硬件应用新的速率配置
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_CFG0__CL73_AN_FW_RATE_LOAD, 1);
       ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__AN_CFG0__ADDR), reg_val);

       // 再次清除加载触发位 (通常这是一个自清除位，或需要手动清零)
       IPNAME_SET_FIELD(reg_val, PMD_LANE_RX__AN_CFG0__CL73_AN_FW_RATE_LOAD, 0);
       ipname_sdk_reg_write((cfg->phy_base_addr + IPNAME_PMD_LANE_RX_BASE_ADDR(cfg->lane_no) + PMD_LANE_RX__AN_CFG0__ADDR), reg_val);
       
       return IPNAME_NO_ERROR;
    }
    ```
    **代码解释**:
    *   函数获取先前计算出的 HCD 速率 (`cfg->hcd_rate`)。
    *   根据具体的 PHY 型号 (`PLATFORM` 宏)，这个 HCD 速率枚举值可能会被设置到 `AN_CFG0` 寄存器中不同的位域（例如 `AN_LANE_RATE` 或 `AN_FW_RESOLVED_RATE`）。有时还需要一个映射表 (`lane_rate_mapping`) 将通用的 HCD 速率枚举值转换为硬件寄存器能识别的特定编码。
    *   关键步骤是操作 `CL73_AN_FW_RATE_LOAD` 位。通常的序列是：先确保此位为0，然后写入包含新速率和 `CL73_AN_FW_RATE_LOAD=0` 的值；接着，将 `CL73_AN_FW_RATE_LOAD` 置为1并再次写入，以触发硬件加载新的速率配置；最后，再将此位清零。这确保了速率配置被正确应用。

这些 SDK 函数的内部实现，最终都依赖于我们在 [第 2 章：寄存器访问抽象层](02_寄存器访问抽象层_.md) 中学习的 `ipname_sdk_reg_read()` 和 `ipname_sdk_reg_write()` 函数（它们内部会调用更底层的 `agr()` 和 `asr()`），来完成对 PHY 硬件寄存器的实际读写操作。

## 总结与展望

在本章中，我们一起探索了“自适应协商 (Auto-Negotiation)”这个重要且有趣的过程。我们学习到：
*   自适应协商解决了通信链路两端设备如何自动匹配通信参数的问题，实现了即插即用的便利性。
*   核心概念包括链路伙伴 (LP)、能力页面 (Base Page, Next Page)、优先级规则以及最终目标——最高公共指示 (HCD)。
*   如何使用 `c_env` 的 PHY SDK API（如 `ipname_sdk_an_program_bp`, `ipname_sdk_an_read_lp_bp`, `ipname_sdk_an_calculate_hcd`, `ipname_sdk_an_program_resolved_rate` 等）来配置、执行和监控自适应协商过程。
*   自适应协商的内部机制大致遵循 IEEE 标准，通过交换页面、比较能力、应用优先级来确定最佳通信模式，并通过读写 PHY 寄存器来实现。

自适应协商是确保现代高速网络设备能够可靠互联的基础。理解它的原理和使用方法，对于网络通信领域的开发和调试工作非常有帮助。

在成功协商并建立起基本链路之后，我们可能还想了解链路的质量如何，例如信号的清晰程度。在下一章 [第 7 章：非破坏性眼图扫描 (NDES)](07_非破坏性眼图扫描__ndes__.md) 中，我们将学习一种高级的诊断技术，它可以在不中断正常数据传输的情况下，评估接收信号的质量。敬请期待！

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)