# Chapter 10: FTDI/JTAG 通信 (FTDI/JTAG Communication)


欢迎来到 `python_env` 教程的最后一章！在上一章[《通信包装器 (Communication Wrapper)》](09_通信包装器__communication_wrapper__.md)中，我们学习了通信包装器如何作为适配层，将来自[《寄存器文件 (Register File)》](03_寄存器文件__register_file__.md)的通用请求翻译成特定硬件 API 服务器能理解的格式。这种包装使得上层代码可以用统一的方式与不同的硬件后端进行交互。

现在，我们将目光投向更底层的硬件通信方式。虽然上一章讨论的 `wrapper_driver_E112MP` 是通过网络 API 与服务器通信，但那个服务器最终可能就是通过诸如 FTDI 或 JTAG 这样的接口与物理硬件直接对话的。此外，在某些情况下，我们的 Python 应用程序可能也需要绕过高级 API 服务器，直接通过这些底层接口与硬件进行“亲密接触”。本章将简要介绍这些直接的硬件通信方法：FTDI 和 JTAG。

## 1. 什么是 FTDI/JTAG 通信？为什么需要它？

想象一下，你正在开发一块全新的电路板，或者需要对芯片进行非常底层的调试，比如在操作系统或高级 API 服务器还未运行起来之前。在这种情况下，你无法依赖网络 API。你需要一种更直接、更原始的方式来与硬件对话。FTDI 和 JTAG 就是实现这种底层通信的常用技术。

*   **FTDI (Future Technology Devices International)**：这是一家公司，以其生产的 USB 接口转换芯片而闻名。这些芯片可以将 USB 信号转换成其他串行或并行接口信号，如 RS232、SPI、I2C，以及非常重要的 JTAG。对于许多开发板来说，FTDI 芯片就像一个“通用翻译器”，让你的电脑可以通过 USB 端口与板上的各种芯片进行低级别通信。
*   **JTAG (Joint Test Action Group)**：这是一个行业标准，最初是为测试印刷电路板和集成电路而设计的。但它逐渐发展成为一种强大的调试和编程接口。通过 JTAG，你可以：
    *   **访问芯片内部的寄存器**：直接读取和修改芯片的内部状态和配置，即使芯片的核心功能未完全启动。
    *   **编程和调试**：为微控制器、FPGA 等可编程芯片加载程序（固件）并进行单步调试。
    *   **边界扫描 (Boundary Scan)**：测试芯片引脚之间的连接以及与电路板上其他组件的连接。

可以把 FTDI/JTAG 通信看作是与硬件直接对话的“专用线路”或“诊断端口”。它通常用于：
*   **硬件调试**：在硬件开发初期，检查和修复问题。
*   **固件烧录**：向微控制器或 FPGA 加载初始固件。
*   **边界扫描测试**：在生产过程中测试电路板的完整性。
*   **访问特殊寄存器**：读取或写入一些通过高级 API 可能无法访问的底层寄存器。

`python_env` 项目中的某些代码库（尤其是在 `api_client/UREFE/common/prototype_com/` 目录下）包含了通过 FTDI 芯片或 JTAG 接口与硬件进行低级别通信的逻辑。

## 2. FTDI 驱动和 `ftd2xx`

要通过 FTDI 芯片与硬件通信，你的电脑需要安装相应的驱动程序。FTDI 公司提供了名为 `D2XX` 的驱动程序和库，允许开发者编写程序来控制 FTDI 芯片的行为。

在 Python 中，通常会使用一个名为 `ftd2xx` 的库（如 `python_env` 项目中 `api_client/UREFE/common/prototype_com/ftdi/ftd2xx/` 目录下所示），它是对 D2XX 驱动 C 语言库的一个封装。这个库提供了一系列函数，用于：

*   **设备发现**：找到连接到电脑的 FTDI 设备。
*   **打开连接**：与指定的 FTDI 设备建立通信会话。
*   **配置模式**：将 FTDI 芯片设置为特定工作模式，例如 MPSSE (Multi-Protocol Synchronous Serial Engine) 模式，该模式常用于实现 JTAG 或 SPI 通信。
*   **发送和接收数据**：通过 FTDI 芯片发送指令字节流和接收来自硬件的数据。
*   **关闭连接**：结束通信会话。

`ftd2xx` 库中的 `defines.py` 文件定义了许多常量（如状态码、设备类型、标志位等），而 `ftd2xx.py` 文件则封装了实际调用底层驱动 DLL 的函数。

```python
# 简化示例，展示 ftd2xx 库的基本用法 (概念性)
# 实际代码在 ftdi/ftd2xx/ftd2xx.py 中
import utils.ftd2xx as ftd # 假设 ftd2xx 库以这种方式导入

try:
    # 1. 列出连接的 FTDI 设备
    devices = ftd.listDevices()
    if not devices:
        print("未找到 FTDI 设备。")
        # exit()

    # 2. 打开第一个找到的 FTDI 设备
    # d = ftd.open(0) # 0 代表第一个设备
    # print(f"已打开 FTDI 设备: {d.description}")

    # 3. 配置设备 (例如，设置为 MPSSE 模式用于 JTAG)
    # d.setBitMode(0x00, 0x00) # Reset MPSSE
    # d.setBitMode(0x0B, 0x02) # Enable MPSSE mode (ADBUS0-2 for JTAG TCK,TDI,TMS)
    
    # 4. 设置时钟频率
    # d.write(b'\x86\x05\x00') # 设置 TCK 分频器 (示例，产生约 6MHz 时钟)

    # 5. 发送 JTAG 命令 (将字节序列写入 FTDI 芯片)
    # jtag_command_sequence = [0x4B, 0x04, 0x06] # 示例：导航到 Shift-IR 的部分 TMS 命令
    # d.write(bytes(jtag_command_sequence))
    
    # 6. 从 FTDI 芯片读取数据 (来自 TDO)
    # response_bytes = d.read(num_bytes_to_read)
    # print(f"从 TDO 读取到: {response_bytes}")

    # 7. 关闭设备
    # d.close()
    pass # 只是概念性展示

except ftd.DeviceError as e:
    print(f"FTDI 设备错误: {e}")
# except Exception as e:
#    print(f"发生其他错误: {e}")
```
**代码解释**：
上面的代码只是一个概念性的演示，展示了与 FTDI 设备交互的基本步骤。实际的 JTAG 通信会涉及更复杂的命令序列来控制 JTAG 状态机和移位寄存器。

## 3. `Py_JTAG`：使用 FTDI 实现 JTAG 通信

在 `python_env` 项目中，`api_client/UREFE/common/prototype_com/Py_JTAG_dev4.py` 文件定义了一个名为 `Py_JTAG` 的类。这个类封装了通过 FTDI 芯片（使用 `ftd2xx` 库）与硬件进行 JTAG 通信的复杂细节。

你可以把 `Py_JTAG` 类看作是一个“JTAG 通信专家”。它知道如何：
*   初始化 FTDI 芯片并将其配置为 JTAG 主机。
*   构造和发送 JTAG 命令序列，以导航 JTAG TAP (Test Access Port) 控制器的状态机。
*   通过 JTAG 接口向目标芯片的指令寄存器 (IR) 或数据寄存器 (DR) 移入数据。
*   从目标芯片的数据寄存器 (DR) 移出数据。
*   最终实现对目标芯片上特定地址寄存器的读写。

### 3.1. 初始化 `Py_JTAG`

```python
# 简化自 api_client/UREFE/common/prototype_com/Py_JTAG_dev4.py
import utils.ftd2xx as ftd # 导入 ftd2xx 库
from time import sleep

# JTAG 命令常量 (部分)
cmd_TMS = 0x4B      # Clock Data to TMS pin
cmd_TDI_bytes = 0x19 # Clock Data Bytes Out on TDI
cmd_TDO_bytes_drv_TDI = 0x39 # Clock Data Bytes In, drive TDI

class Py_JTAG():
    def __init__(self, IR_vector, RTI_vector, CR_cmd_vector):
        # self.logs = Logs() # 日志记录
        self.ftHandleB = 0 # FTDI 设备句柄
        self.IR_vector = IR_vector # 每个设备的指令寄存器长度
        self.RTI_vector = RTI_vector # 每个设备从RTI状态需要的TCK周期
        self.CR_cmd_vector = CR_cmd_vector # 每个设备的控制寄存器访问命令
        self.ndevices = len(IR_vector) # JTAG链上的设备数量
        # print("Py_JTAG 对象已创建。")

    def jtag_open(self, speed=0.5e6): # speed 单位 Hz
        # ... (此处省略了查找特定 FTDI 设备的详细逻辑) ...
        try:
            # 假设已经找到了 FTDI 设备B 的索引 ft_device_index_b
            # (ftStatusB, self.ftHandleB) = self.FT_Open_py(ft_device_index_b)
            # 简化：直接打开第一个设备进行演示
            self.ftHandleB = ftd.open(0) 
            if not self.ftHandleB:
                 print("FTDI 设备 B 打开失败。")
                 return

            self.ftHandleB.resetDevice()
            self.ftHandleB.setUSBParameters(16384, 16384) # 设置USB传输缓冲区大小
            self.ftHandleB.setLatencyTimer(1) # 设置延迟计时器 (ms)
            self.ftHandleB.setBitMode(0x00, 0x00) # Reset MPSSE
            self.ftHandleB.setBitMode(0x00, 0x02) # Enable MPSSE mode
            self.ftHandleB.purge(ftd.defines.PURGE_RX | ftd.defines.PURGE_TX)
            
            self.setup_interface(speed) # 配置接口和时钟
            print("JTAG 接口已打开并配置。")
        except Exception as e:
            print(f"打开 JTAG 接口时出错: {e}")
            if self.ftHandleB: self.ftHandleB.close()

    def setup_interface(self, speed=1e6): # 配置MPSSE接口和时钟
        # ... (省略了设置各种 MPSSE 模式命令的细节) ...
        # 例如：禁用环回，设置GPIO方向等
        # 设置 TCK 时钟频率
        div = int((60000000 / (speed * 2)) - 1) # FTDI时钟计算公式
        clk_setup_cmd = bytes([0x86, div % 256, div // 256]) # 设置时钟分频器命令
        self.ftHandleB.write(clk_setup_cmd)
        # print(f"JTAG TCK 时钟频率已设置为约 {speed/1e6:.2f} MHz。")
```
**代码解释**：
*   `__init__`：构造函数保存了关于 JTAG 链上设备的一些配置信息，如指令寄存器长度等。
*   `jtag_open`：
    *   打开一个 FTDI 设备连接（这里简化为打开第一个找到的设备）。
    *   重置设备，设置 USB 参数和延迟。
    *   最关键的是调用 `setBitMode` 将 FTDI 芯片配置为 **MPSSE (Multi-Protocol Synchronous Serial Engine)** 模式。MPSSE 模式允许用户通过发送特定的命令字节来精确控制 FTDI 芯片的 IO 引脚，从而模拟出 JTAG（或其他同步串行协议如 SPI, I2C）的信号。
    *   调用 `setup_interface` 来进一步配置 MPSSE 接口，包括设置 JTAG 的 TCK 时钟频率。
*   `setup_interface`：发送一系列命令字节给 FTDI 芯片，以完成 MPSSE 模式的详细配置，例如设置 TCK 时钟分频器（`0x86` 命令）。

### 3.2. 读写寄存器 (简化概念)

`Py_JTAG` 类中的 `read_register(pid, addr)` 和 `write_register(pid, addr, data)` 方法是核心。它们内部包含了复杂的 JTAG 协议逻辑，通过向 FTDI 芯片发送精心构造的字节序列来操作目标硬件。

```python
# 简化自 api_client/UREFE/common/prototype_com/Py_JTAG_dev4.py
class Py_JTAG():
    # ... (init, jtag_open, setup_interface 方法同上) ...

    def __build_jtag_sequence_for_read(self, pid, addr):
        # 这是一个高度简化的占位符函数
        # 实际代码会构造一系列字节命令来：
        # 1. 导航JTAG TAP到Test-Logic-Reset状态
        # 2. 导航到Shift-IR状态
        # 3. 移入目标设备(pid)的指令(例如，选择某个内部扫描链或配置寄存器访问命令)
        # 4. 导航到Shift-DR状态
        # 5. 移入要读取的地址(addr)
        # 6. (对于读操作) 移出数据，同时可能移入一些填充位
        # 这些命令会使用 cmd_TMS, cmd_TDI_bytes, cmd_TDO_bytes_drv_TDI 等FTDI MPSSE指令
        # 返回一个字节列表，准备发送给FTDI芯片
        print(f"  (模拟)为读取 PID={pid} 地址={hex(addr)} 构建JTAG命令序列...")
        # 示例：一个极度简化的假命令序列
        # 实际序列会复杂得多，包含TMS控制和数据移位
        mock_sequence = [cmd_TMS, 0x06, 0xFF] # 导航到 TLR
        mock_sequence += [cmd_TMS, 0x04, 0x06] # 导航到 Shift-IR
        # ... 更多步骤 ...
        # 移出16位数据的命令 (假设)
        mock_sequence += [0x2C, 1, 0] # 读取2个字节 (16位)
        return bytes(mock_sequence)

    def read_register(self, pid, addr):
        if not self.ftHandleB:
            print("JTAG 未打开。")
            return 0
        
        # 1. 构建读操作的JTAG命令序列
        tx_buffer = self.__build_jtag_sequence_for_read(pid, addr)
        
        # 2. 清除可能存在的旧数据
        self.ftHandleB.purge(ftd.defines.PURGE_RX | ftd.defines.PURGE_TX)
        
        # 3. 将命令序列写入FTDI芯片
        bytes_written = self.ftHandleB.write(tx_buffer)
        # print(f"  发送了 {bytes_written} 字节的JTAG命令。")
        
        # 4. 从FTDI芯片读取响应 (即从TDO移出的数据)
        #    需要知道期望读取多少字节 (例如，16位寄存器是2字节)
        #    实际代码会根据JTAG链的配置和操作计算精确的读取字节数
        bytes_to_read = 2 # 假设读取16位数据
        sleep(0.01) # 短暂延时等待FTDI处理和数据返回
        
        rx_buffer = self.ftHandleB.read(bytes_to_read)
        # print(f"  从JTAG读取到原始字节: {rx_buffer}")
        
        # 5. 解析读取到的字节数据，转换成期望的寄存器值
        if len(rx_buffer) == 2:
            # 假设数据是小端字节序 (LSB first)
            value = rx_buffer[0] + (rx_buffer[1] << 8)
            return value
        return 0 # 读取失败或数据不足

    # write_register 方法会类似地构建一个包含写入地址和数据的JTAG序列
    # 然后将其发送出去，通常不期待有大量数据返回。
    # def write_register(self, pid, addr, data):
    #     # ... 构建包含地址和数据的JTAG写命令序列 ...
    #     # ... 发送命令 ...
    #     pass

    def jtag_close(self):
        if self.ftHandleB:
            self.ftHandleB.close()
            self.ftHandleB = 0
            print("JTAG 接口已关闭。")
```
**代码解释**：
*   `read_register(pid, addr)`（高度简化版）：
    *   它首先调用一个辅助方法（这里是 `__build_jtag_sequence_for_read` 的占位符）来生成一串复杂的字节命令。这个命令序列的目标是让 FTDI 芯片通过 JTAG 引脚（TCK, TMS, TDI, TDO）与目标硬件进行交互，以读取指定地址的寄存器。
    *   实际的 `__build_jtag_sequence_for_read`（在 `Py_JTAG_dev4.py` 中是 `__DR_vector` 和其他导航函数）会精确控制 JTAG TAP 状态机的转换，以及通过 TDI 移入指令/地址，通过 TDO 移出数据。
    *   然后，它将这个命令序列通过 `self.ftHandleB.write()` 发送给 FTDI 芯片。
    *   接着，它调用 `self.ftHandleB.read()` 来获取从目标硬件 TDO 引脚移出的数据。
    *   最后，它解析这些原始字节数据，转换成用户期望的寄存器值（例如一个16位整数）。
*   `write_register` 方法的逻辑与此类似，但其 JTAG 命令序列会包含要写入的数据，并且通常不从 TDO 读取大量数据。
*   `jtag_close`：关闭与 FTDI 设备的连接。

这个过程非常底层，需要对 JTAG 协议和 FTDI MPSSE 编程有深入的理解。`Py_JTAG` 类的目的就是将这些复杂性封装起来。

## 4. FTDI/JTAG 在 `python_env` 中的应用场景

在 `api_client/UREFE/common/prototype_com/comms - back_up.py` 文件的 `prototype_comm` 类中，我们可以看到 `Py_JTAG` 是如何被用作一种底层通信驱动的。

```python
# 简化自 api_client/UREFE/common/prototype_com/comms - back_up.py
# from .registerfile import RegisterFile
# from .Py_JTAG_dev4 import Py_JTAG # Py_JTAG_dev4.py 定义了 Py_JTAG

class prototype_comm:
    def __init__(self, ..., tc_architecture, ip_dat_path=None, ...):
        self.tc_architecture = tc_architecture
        self.JTAG_list = ['C8', 'C10'] # 支持JTAG的架构类型

        if self.tc_architecture in self.JTAG_list:
            # 如果架构类型是 'C8' 或 'C10' (通常代表需要JTAG访问的芯片)
            # 创建 Py_JTAG 实例
            # 参数是特定于这些芯片的JTAG链配置
            self.ft = Py_JTAG([8,8,8],[110,110,110],[0x31,0x3,0x3]) 
            try:
                self.ft.jtag_open() # 打开并配置JTAG接口
            except Exception as error:
                print(f'打开JTAG时发生异常: {error}')
            
            # 为IP核、FPGA和TC（测试芯片）创建简单的包装器
            # 这些包装器会将 RegisterFile 的 readreg/writereg 请求
            # 直接转发给 Py_JTAG 实例的相应方法
            ip_wrapper = wrapper_driver(self.ft, pid=1) # pid 1 对应JTAG链上的第一个设备
            fpga_wrapper = wrapper_driver(self.ft, pid=2)
            tc_wrapper = wrapper_driver(self.ft, pid=3)
            
            # 创建 RegisterFile 实例
            self.ip_regfile = RegisterFile(16) 
            # ... 其他 RegisterFile 实例 ...

            # 将 RegisterFile 绑定到 JTAG 包装器
            self.ip_regfile.bind(ip_wrapper, 
                                 ip_wrapper.writereg, 
                                 ip_wrapper.readreg)
            # ... 为 fpga_regfile 和 tc_regfile 进行类似绑定 ...

        # elif self.tc_architecture in self.ISDS_16b_list or self.ISDS_32b_list:
            # ... (处理其他架构类型，可能使用不同的驱动和包装器) ...
        # elif self.tc_architecture == 'E112MP': (在主comms.py中)
            # ip_wrapper_PHYA = wrapper_driver_E112MP(None, pid=2)
            # self.phya_regfile.bind(ip_wrapper_PHYA, ...)

        # ... (加载 .dat 文件到 RegisterFile) ...
```
**代码解释**：
*   `prototype_comm` 类的构造函数会检查 `tc_architecture`（测试芯片架构类型）。
*   如果架构类型在 `self.JTAG_list` 中（例如 "C8", "C10"），它会：
    *   创建一个 `Py_JTAG` 实例 (`self.ft`)，并传入该架构特定的 JTAG 配置参数。
    *   调用 `self.ft.jtag_open()` 来初始化 FTDI/JTAG 通信。
    *   创建多个 `wrapper_driver` 实例（这是一个非常简单的包装器，定义在 `comms - back_up.py` 中，它仅仅是将 `readreg` 和 `writereg` 调用直接传递给 `self.ft` 的同名方法）。
    *   将[《寄存器文件 (Register File)》](03_寄存器文件__register_file__.md)实例（如 `self.ip_regfile`）绑定到这些 `wrapper_driver` 实例。
*   这意味着，对于 "C8" 或 "C10" 这样的硬件，当上层代码通过 `self.ip_regfile.agr(...)` 进行寄存器操作时，请求最终会通过 `wrapper_driver` 传递给 `Py_JTAG` 实例的 `read_register` 或 `write_register` 方法，从而通过 FTDI/JTAG 接口与物理硬件直接通信。

这与我们在上一章看到的 `wrapper_driver_E112MP` 形成了对比。`wrapper_driver_E112MP` 是通过网络 API 与一个远程服务器通信，而这里的 `wrapper_driver` + `Py_JTAG` 则是直接与本地连接的硬件通过 USB/FTDI/JTAG 通信。`prototype_comm` 类根据 `tc_architecture` 的不同，巧妙地选择了合适的底层通信驱动和包装器。

## 5. 总结与展望

在本章中，我们初步了解了 FTDI/JTAG 通信在 `python_env` 项目中的角色：

*   **FTDI 和 JTAG 是什么**：FTDI 芯片常用于通过 USB 提供 JTAG 等低级别接口，而 JTAG 是一种用于测试、调试和编程集成电路的强大标准。
*   **为何使用**：它们提供了绕过高级 API、直接与硬件底层进行交互的途径，对于硬件调试、固件烧录和访问特殊寄存器至关重要。
*   **`ftd2xx` 库**：这是与 FTDI 芯片交互的 Python 驱动库，`python_env` 利用它来发送和接收原始字节数据。
*   **`Py_JTAG` 类**：封装了使用 FTDI MPSSE 模式实现 JTAG 通信的复杂逻辑，提供了更高级别的 `read_register` 和 `write_register` 方法。
*   **在 `python_env` 中的集成**：`prototype_comm` 类能够根据硬件架构类型选择 `Py_JTAG` 作为底层驱动，并将其包装后绑定到[《寄存器文件 (Register File)》](03_寄存器文件__register_file__.md)，从而实现对特定硬件的直接 JTAG 访问。

FTDI/JTAG 通信代表了与硬件最直接的连接方式之一。理解这一层有助于我们认识到 `python_env` 项目如何能够灵活地适应和控制不同类型的硬件接口。

**教程总结**

恭喜你完成了 `python_env` 项目的入门教程！在过去的十章中，我们一起探索了这个项目从用户界面到最底层硬件通信的各个方面：

1.  [Python 图形用户界面 (Python GUI)](01_python_图形用户界面__python_gui__.md)：项目的“面孔”，提供了与硬件交互的控制台。
2.  [寄存器 (Register)](02_寄存器__register__.md)：硬件配置和状态的基本单元。
3.  [寄存器文件 (Register File)](03_寄存器文件__register_file__.md)：管理大量寄存器定义的“地址簿”。
4.  [DAT/CSV 文件解析器 (DAT/CSV Parser)](04_dat_csv_文件解析器__dat_csv_parser__.md)：从文件加载寄存器定义的“翻译官”。
5.  [API 客户端 (API Client)](05_api_客户端__api_client__.md)：与后端服务器通信的“电话机”。
6.  [寄存器访问函数 (agr/asr)](06_寄存器访问函数__agr_asr__.md)：便捷读写寄存器的快捷方式。
7.  [验证脚本 (Validation Scripts)](07_验证脚本__validation_scripts__.md)：自动化硬件功能测试的“体检项目”。
8.  [固件更新 (Firmware Update)](08_固件更新__firmware_update__.md)：给硬件“换脑”的工具。
9.  [通信包装器 (Communication Wrapper)](09_通信包装器__communication_wrapper__.md)：适配不同硬件通信接口的“翻译层”。
10. **FTDI/JTAG 通信 (FTDI/JTAG Communication)**：与硬件直接对话的“专用线路”。

希望这个教程能帮助你对 `python_env` 项目的结构和核心概念有一个清晰的理解。通过掌握这些构建模块，你将能更有效地使用和扩展这个项目，以满足你与复杂硬件系统交互的需求。

感谢你的学习，祝你在硬件探索的旅程中一切顺利！

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)