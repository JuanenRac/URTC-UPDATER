<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | 🇨🇳 <b>简体中文</b> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 📦 检测、安装并手动更新整个 URTC 生态系统

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="stdlib-only CLI core">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="PySide6 Qt Quick desktop GUI">
</p>

> **可视化桌面模式：** 默认桌面界面现通过可选的 `PySide6` GUI 运行时使用
> **Qt Quick / QML**。更新器核心与 `--cli` 模式仍仅使用标准库，适合无桌面的 CM5。
>
> **Windows 启动和操作证据：** 双击 `run-gui.vbs`（或不带参数运行
> `run.bat`）即可启动无控制台图形客户端。更新面板会显示真实的预检查、源更新、
> 清单验证、构建测试和完成检查点及捕获的证据；`run.bat --cli ...` 保留诊断终端。
> 仅在缺少检出时启用安装，仅在 GitHub 版本更高时启用更新。已批准操作期间，
> 检查点会替换项目控制区；选择其他项目即可恢复控制区。
> **安装全部缺失项目**和**更新全部过期项目**是分别确认的顺序批量操作，使用相同的
> 实时状态和安全流程。

---

**诚实核查 - 今天真正能运行的部分：** **成熟度：成熟（established，仅有一次有记录的完整运行，并非持续使用）。** 本项目把 HYDRA-UMC-UPDATER 已验证的设计（同样的清单发现、通过原子验证的临时克隆进行安装/更新，以及证据日志）仅用于 URTC 生态系统的仓库。它已在隔离的工作区中针对 GitHub 完整地端到端运行过：一次全新安装和随后对真实仓库的一次更新都正确地完成了克隆、构建和提升，并把之前的副本保留为备份。发现与版本逻辑（`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`）、带重试/退避并缓存仓库列表的 GitHub raw-content 客户端（`github_client.py`）、按提交比较（`commits.py`）以及克隆-暂存-验证-提升流水线（`install.py`）都有测试覆盖（`python -m pytest`），包括本地 HTTP 测试服务器，以及带本地 bare 远程的真实临时 git 仓库。Qt 桥接层自身的逻辑在测试中无界面运行，窗口及其对话框也会在无屏幕模式下加载，以检查它能打开并作出响应；外观靠人眼检查，没有测试。`i18n.py` 的 8 种语言覆盖通过测试检查键和占位符是否一致，而不检查翻译质量。具体已交付的内容请见 `CHANGELOG.md`。

---

> **安全与安防现状:**本生态系统不是经认证的安全系统,目前也不存在已组装的 URTC 电路板。引导程序使用 CRC32 和共享密钥的 HMAC-SHA256 校验固件映像,而非非对称签名(计划中);已发布的应用映像使用公开的开发密钥签名(`signing_key_kind: dev`),因此任何人都可以生成引导程序接受的映像;尚未向任何真实电路板发送过任何内容。在依赖此处任何说法来保障人身安全之前,请先阅读[安全基线](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md)和[威胁模型](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md)。

## 📋 速览

| | |
|---|---|
| 版本 | `0.1.9` |
| 成熟度 | 成熟 |
| 测试 | 482 (`python -m pytest`) |
| 技术栈 | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| 目标 | 使用者的电脑 |
| 真实硬件 | 不适用：这里的内容不在硬件上运行 |

**跳转到：** [概述](#-概述) · [架构](#-架构) · [安全](#-安全与防护) · [接口](#-接口) · [快速开始](#-快速开始) · [测试](#-测试) · [故障排除](#-故障排除) · [结构](#-仓库结构) · [相关项目](#-相关项目)

<!-- urtc-section:status_updater -->
## 🚦 项目状态

🟢 已完成并已验证 · 🟡 可用，但有已知限制 · 🟠 做了一半或未验证 · 🔴 未完成或不能用。从未在真实硬件上运行过的内容不会是绿色。

| 部分 | 状态 | 仓库能够证明的内容 |
| --- | :---: | --- |
| 软件 | 🟡 | 可在电脑上和模拟器上运行；从未在真实板子上运行过。 |
| 界面 | 🟡 | 窗口可运行，并用模拟板子检查；未用真实适配器试过。 |
| 测试 | 🟢 | 每次推送时测试套件都会在 CI 中通过。 |
| 更新 | 🟡 | 从已签名的软件包安装，并可回滚；仅在电脑上试过。 |
| 安全 | 🟡 | 发布版使用 Ed25519 签名，并在使用前检查；密钥的处理没有他人审阅过。 |
| 文档 | 🟡 | 提供八种语言的 README 和参考文档；翻译未经母语者审阅。 |

<!-- /urtc-section:status_updater -->

## 🎯 概述

URTC-UPDATER 是一个小型工具——默认为窗口化 GUI，通过 `--cli` 可
获得完整的 CLI——旨在运行在真实的 CM5 本机上，或运行在开发者自己的
Windows/Linux/macOS 计算机上（任何以相同方式检出的工作区），它为生态
系统中通过每个相邻检出自身的 `urtc.project.json` 清单发现的
每一个其他真实项目都回答三个问题——这个数量本身在此从不写死，
因为它会随着生态系统一起增长：

1. **这里实际安装了什么，版本是多少？**
2. **GitHub 上发布的最新版本是什么？**
3. **如果 GitHub 上的版本更新，让我选择一个项目或已确认的顺序批量操作。**

最后一点是刻意为之、不容妥协的：本工具绝不会自行更改任何项目。对选定
项目的操作始终需要明确确认。GUI 还可以提供**安装全部缺失项目**或**更新
全部过期项目**；二者都是分别确认的顺序批量操作，并经过相同的清单、版本
和安全检查。不存在无人批准的夜间自动更新。

发现的项目中也并非每一个都属于 CM5 本机——大多数以 URTC 为前缀的仓库和
少数 HYDRA-UMC 仓库，是开发者从自己的 PC 上运行的工具（固件是从工作站
编译/刷写的，而非在单元本机上构建的），或是安装在手机/手表上的应用。
`registry.py` 自身的 `deploy` 字段记录了哪个属于哪种（见第 3 节），
GUI 的项目表格会据此进行筛选——当检测到运行在 Linux（真实 CM5 自身的
操作系统）上时默认为"仅 CM5"，在 Windows/macOS 上则默认为"显示全部"。

示例说明（下面的项目数量和每个版本号都是为了展示输出格式而虚构的，
并非真实捕获的执行结果——真实数量始终是 `registry.py` 当下实际发现的
数量，绝不是写死在本文档中的固定数字）：

```
$ urtc-updater --cli status
Workspace root: /home/user/GitHub
PROJECT       MATURITY     ROLE      STACK           LOCAL     GITHUB    STATE
-------------------------------------------------------------------------------
URTC          functional   firmware  firmware-c      0.3.0     0.3.1     OUTDATED
URTC-FLASHER  functional   tool      python-qtquick  0.2.1     0.2.1     up to date
URTC-TESTER   functional   tool      python-qtquick  0.2.2     0.2.2     NEW COMMITS

3/3 installed, 1 outdated, 1 with new commits at the same version
Run `urtc-updater update <project>` to update one by hand - never automatic, see this tool's own README.

$ urtc-updater --cli update URTC
Updating URTC into /home/user/GitHub ...
OK  Updated /home/user/GitHub/URTC to v0.3.1 (commit 1a2b3c4d5e6f) after a verified build; previous installation kept at /home/user/GitHub/URTC.backup-1a2b3c4d
```

不带任何参数运行 `urtc-updater`（或直接双击它）会改为在深色桌面控制界面中
打开同样的信息：一个带有实时发现/安装/更新指标的 **Local Ecosystem** 面板、
一棵由清单驱动的 **Project Registry** 树，以及针对所选项目的 **Safe Update**
面板。该布局让真正的防护措施清晰可见：通过清单发现、一次只执行一个明确的
项目操作、手动确认、可选的构建，以及屏幕上的活动轨迹；完整日志还会写入
`~/.urtc_updater/logs` 下的文件（保留最新的 20 个）。

## 🧩 在 URTC 中的角色

URTC-UPDATER 是让装有 URTC 仓库的电脑保持最新的程序。它根据每个仓库自带的清单找到旁边的每个项目，说明已安装的版本和 GitHub 上的版本，并在明确确认之后一次安装或更新一个项目，运行该项目自己的 `build-test` 脚本，自己从不构建任何东西。它不会擅自改动任何东西：机器人控制单元绝不能在没有人批准确切操作的情况下于夜间自动更新。它还能从发布版的签名包安装桌面程序（刷写器、测试器和它自己），并可把已核对发布签名的固件镜像交给负责刷写的 URTC-FLASHER。

## 🏛️ 架构

<p align="center">
  <img src="images/architecture.svg" alt="URTC-UPDATER 的架构：谁在使用、包含什么、依赖什么" width="100%">
</p>

本仓库各部分如何协作：谁在使用它、它包含什么、它依赖什么。图片由 `docs/architecture.json` 绘制，并与代码核对。

### 检查/更新实际是如何工作的

- **版本来源**：项目的版本保存在该项目的一个源文件中（视技术栈而定，如 `pyproject.toml`、`Cargo.toml`、`version.go`、`package.json`、`version.properties`、`pubspec.yaml` 或固件的 `#define`），由它自己的 `bump.py` 步骤写入，而这一步从未创建过 git 标签或 GitHub Release。因此本工具通过 GitHub 的原始内容主机直接从仓库默认分支读取同一个文件，而不是使用 Releases API——后者会报告每个项目都没有发布版。
- **本地检测**：对于每一个发现的项目，检查工作区根目录下是否存在一个与该项目名称完全一致的目录（标准的生态系统布局——每个项目作为同级目录，这正是 `build-frontend.sh`/HYDRA-UMC-SUITE 自身的发现逻辑已经假定的方式），如果存在，则读取该项目*自身*的本地版本文件副本。
- **单一解析实现**（`version_parse.py`）在本地读取和 GitHub 抓取之间共享，因此本地检出和 GitHub 抓取绝不会被两个独立漂移的正则表达式分别解读。
- **安装/更新**：`git clone`（安装）之后作为单独的一步再编译。更新一个已存在的检出则改为「通过验证实现原子性」：候选版本先被克隆、进行快进合并（绝不使用强制重置，因此真实的本地修改会明确失败，而非被丢弃），然后首先在一个完全独立的暂存克隆中编译/验证——只有当那次暂存编译真正成功时，实际安装才会被触碰（通过两次连续的目录重命名，之前的安装会被保留在 `<name>.backup-xxxxxxxx` 中，而不是被删除）。在最终提升之前的任何时刻发生编译失败、检出分叉/存在未提交修改、崩溃或磁盘写满，都会让之前的安装完全不受影响、继续保持可运行——详见 `install.py` 自身 `clone_or_pull` 的 docstring。暂存克隆自身的 git 远程仓库会在创建后立即恢复为真实的 GitHub 上游（否则一个普通的本地克隆会指向旧的安装路径，一旦被提升就会在不知不觉中终止所有未来的更新），并且已安装检出自身真实的本地数据（任何 git 视为未跟踪或被忽略的内容——`data/settings.json` 及类似文件，不包括可重新生成的构建产物）会在编译前被带入暂存克隆，这样一个项目自身真实的运行状态就能在更新后保留下来，而不是被困在保留的 `.backup-xxxxxxxx` 检出中。无论哪种情况，只要该项目自身实际拥有 `build-test.sh`/`build-test.bat`（不递增版本号的检查——见第 3 节），就会运行它。本工具从不重新实现某个项目自身的构建步骤。

### 架构与设计决策

- **默认 Qt Quick GUI，`--cli` 用于无桌面环境。** `main.py` 会在导入可选 PySide6
  运行时之前检查 `--cli`。CLI 可在没有显示器或桌面依赖的 CM5 上工作；无参数时会在
  可用条件下启动 QML，Tkinter 仅保留为临时兼容回退。
- **带窗口的 GUI 是真实的，支持 8 种语言（`i18n.py`）—— `--cli` 则有意不支持。** 每个控件，以及安装或更新中每个检查点和每次失败的文字，都会以选择器中选定的语言显示（en/es/fr/it/de/zh/ja/pt，其中 pt 为葡萄牙的葡萄牙语），语言取自已保存的偏好或系统区域设置。安装和更新的步骤以消息代码加参数的形式传递，只有窗口把它们转换为文字，因此切换语言会重新渲染它们。项目名、家族名以及每个项目自己的 `notes`/`tech` 文本不翻译：清单是它们唯一的事实来源。`--cli` 的输出有意保持英文，因为它是为脚本和管道准备的。
- **`deploy` 是一种分类，而非一种限制。** 把每一个发现的项目都当作"属于 CM5 的东西"是错误的——固件仓库是从 PC 编译并刷写的（CM5 只需要通过 CAN-OTA 得到最终的二进制文件，从不需要本仓库自身的源代码），而若干工具（URTC-FLASHER、HYDRA-UMC-SUITE、HYDRA-UMC-TOOL-CLI……）本应运行在操作员自己的工作站上，而非单元本机内部。`registry.py` 的 `deploy` 字段（"cm5" / "user-pc" / "mobile" / "wearable" / "dev-server"）记录了这一点，GUI 的筛选器将其作为一个合理的起点使用——而非硬性限制，因为这个同一工具也可以运行在开发者自己的 PC 上，此时每一个发现的项目都可以被检查。
- **本工具中不包含针对特定技术栈的构建逻辑。** 本生态系统涉及多种工具链（Python、Rust、Go、Node/TS、Android/Kotlin、Flutter、ARM 固件）。在这里重新实现每个项目的构建，会多出第二个声称知道如何构建它的地方，必然与项目自己的脚本逐渐偏离。`install.py` 改为运行项目自己的、不改版本号的 `build-test.sh`（Windows 上为 `build-test.bat`），若某个副本没有它则安全地失败。会提升版本号的构建脚本（`build.sh` 等）本工具永远不会运行。
- **使用 GitHub 原始内容，而非 Releases API。** 见上方第 2 节——本生态系统的版本控制惯例从不创建标签/发布，因此在这里使用 Releases API 不仅不够方便，而且是彻底错误的做法。
- **临时性网络故障会获得真正的重试；确定性的回应则永远不会。** 每一次真实的 GitHub 请求（`github_client.py` 的 `_urlopen_with_retries`）最多重试 3 次并带有退避延迟，但仅限于连接从未获得任何响应的情况（DNS/超时/重置）。GitHub 实际返回的真实 HTTP 状态——404、403、500——永远不会被重试：GitHub 已经给出了答复，再次请求只会消耗更多的速率限制额度而得到相同的结果。
- **格式错误的远程目录会响亮地失败；单个格式错误的项目不会。** 如果 GitHub 的仓库列表本身无法访问或无法解析，`discover_remote_projects()` 会抛出异常——`gui.py` 和 `main.py` 都已经捕获了这一点，并回退到本地发现的项目列表，而不是显示一次损坏或空白的扫描。相反，单个仓库格式错误的清单会被隔离到该次扫描自己的 `errors` 列表中，绝不会中止对其余项目的发现——一个真实的、基于夹具服务器的测试（`tests/test_github_client.py`）证明了这两条路径。
- **CLI 操作保持明确；GUI 批量操作保持确认。** CLI 的 `install`/`update`
  命令需要一个项目名称。桌面 GUI 可以执行**安装全部缺失项目**或**更新全部
  过期项目**，但只会在独立确认后，并按顺序通过相同安全检查执行。不存在
  无人值守的自动更新。
- **仅使用标准库。** `urllib` 用于 GitHub 抓取（`github_client.py`），`subprocess` 用于 git/构建脚本调用（`install.py`），仅此而已——一个负责维护其他*所有*项目依赖健全性的工具，其自身保持零依赖，这是刻意为之的。
- **已知的简化处理：** 由多个独立版本的二进制文件组成的仓库（URTC 有四个：主控与从控、应用与引导程序）只用一个版本来跟踪，即其自身 `urtc.project.json` 在 `native_version` 中声明的版本。这回答的是“这个仓库大致是否最新”，并不能替代烧录时按组件进行的版本检查。

<!-- urtc-section:updates -->
### 如何更新

本程序可以查找自身的较新版本：“检查更新”按钮只向 GitHub 查询一次，只有当包适用于您的系统且更新时才会提供已签名的包。除非您打开检查，否则不会自行检查或安装，更新需要您的确认。包必须与其 SHA-256 以及程序中固定的发布密钥签名一致；上一版本会保留，新版本无法启动时会自动恢复。`urtc-updater --cli package list|check|install|rollback` 可在命令行中为刷写器和测试器完成同样的操作，`install --file` 无需网络即可使用。
<!-- /urtc-section:updates -->

## 🖼️ 屏幕截图

<!-- urtc-shots -->
在测试台上以 1920×1080 截取，使用示例数据，背后没有真实的安装。

<table>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/deck.png" alt="显示包含整个系列的工作区的窗口：每个项目的成熟度、技术栈和本地版本，以及安全更新操作。" width="100%"><br><sub>显示包含整个系列的工作区的窗口：每个项目的成熟度、技术栈和本地版本，以及安全更新操作。</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/packages.png" alt="软件包窗口：系列中以已签名软件包形式发布的程序，每个程序检查各自的发布版本。" width="100%"><br><sub>软件包窗口：系列中以已签名软件包形式发布的程序，每个程序检查各自的发布版本。</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/help.png" alt="帮助窗口：使用该程序的各个步骤，使用窗口的语言显示。" width="100%"><br><sub>帮助窗口：使用该程序的各个步骤，使用窗口的语言显示。</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/updates.png" alt="更新窗口：只有在你确认之后，才会安装较新的已签名软件包。" width="100%"><br><sub>更新窗口：只有在你确认之后，才会安装较新的已签名软件包。</sub></td>
</tr>
</table>
<!-- /urtc-shots -->

这些图片是真实的窗口，在没有屏幕的情况下按打开时的样子绘制（未检查任何内容，未安装任何东西）。指南依次介绍主窗口、帮助窗口、更新窗口和软件包窗口，并以程序的八种语言展示。

[图文指南](docs/WINDOW_GUIDE.md)

## 🔒 安全与防护

| 威胁 | 防御 |
|---|---|
| 没有人批准的更新，例如夜间在机器人控制单元上 | 不会自行更改任何东西：对项目的操作需要明确确认，批量操作单独确认并逐个项目运行 |
| 损坏或做了一半的更新让原本可用的安装无法使用 | 候选版本先被克隆、以快进方式合并（绝不强制重置，本地修改会明显报错），并先在暂存克隆中构建；只有该构建通过，才通过两次目录重命名替换正在使用的安装，之前的安装保留为 `<名称>.backup-xxxxxxxx` |
| 在这里无法运行的检查 | build-test 返回 75 表示验证不可用：除非此人在设置中接受，否则拒绝更新 |
| 没有人签名的提交 | 没有有效签名的修订会带警告安装；设置 `"signature_policy": "require"` 后会被拒绝 |
| 被篡改的包 | 只有大小、SHA-256 和 Ed25519 签名都匹配且来自 GitHub 下载主机的包才会被接受；确认后才安装，绝不在另一个安装运行时安装，并可恢复之前的版本 |
| 所做之事的痕迹丢失 | 每次安装、更新和恢复都会连同时间、主机和用户写入按哈希链接的日志 |

策略的其余部分如下，用的是程序自己的措辞。

**build-test 可以返回什么：** 退出码 0 表示已验证，其他任何退出码都表示失败，唯独 75 表示验证*不可用*（缺少它需要的工具）。这会如实报告并拒绝更新，除非你在设置中把 `validation_unavailable` 设为 `accept`（或设置 `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`）来接受。build-test 应让目录树保持原样：如果它修改了 git 跟踪的文件，该文件会在提升之前恢复为已提交的内容，步骤中会说明是哪些文件。

**已签名提交（默认仅警告；强制要求属于可选项，默认关闭）：** 没有有效签名的修订（`git verify-commit`：GPG 密钥环，或使用 `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS` 的 SSH）仍会安装，窗口和命令行的步骤会说明它未签名。在 `~/.urtc_updater_settings.json` 中设置 `"signature_policy": "require"`（或 `URTC_UPDATER_REQUIRE_SIGNED=1`；旧的 `"require_signed_commits": true` 含义相同）后，候选版本 - 新克隆的 `HEAD` 或更新所获取的 `FETCH_HEAD` - 必须在读取其清单或构建任何内容之前通过 `git verify-commit`，被拒绝的候选版本不会改动已安装的检出。

**安全选项（两者默认都关闭；可通过窗口的“安全”按钮、`security` 命令、设置文件、环境变量和命令行修改）：** 除了要求已签名的提交，更新器还可以在运行候选版本的构建检查*之前先询问*（`"confirm_before_build": true`、`URTC_UPDATER_CONFIRM_BUILD=1`、`--confirm-build`）。它获取并验证候选版本，显示项目、提交、作者、签名以及已更改的构建或工具脚本，在你回答之前不运行任何东西；如果没有窗口也没有终端可询问，则什么都不运行（脚本可用 `--yes` 代为回答）。`--require-signed` / `--no-require-signed` 和 `--confirm-build` / `--no-confirm-build` 只对一次运行有效，关闭已保存设置中开启的保护的运行会明确提示；窗口以及 `urtc-updater --cli security --require-signed off` 在保存较低级别之前会要求确认。存在但无法读取的设置文件会被视为“要求签名”，直到它被修复或删除。构建检查还会收到 `URTC_PYTHON`（运行更新器的解释器），因此项目用该 Python 测试，而不是系统最先找到的那个。

## 🔌 接口

不带参数运行时程序会打开 Qt Quick 窗口，并通过 `--cli` 提供完整的命令行（不需要显示器，也不需要 PySide6）：`status [--offline]`、`install 项目`、`update 项目 [--preview]`、`restore-backup 项目 [--list]`、`clean-backups [--keep N] [--dry-run]`、`check [--notify] [--quiet]`（有可更新内容时退出码为 10）、`package list|check|install|rollback`、`evidence [--export FILE]` 和 `security`。每个命令、选项和退出码以及真实输出见 [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)；窗口在 [docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md) 中说明。维护和工作站命令的作用如下：

- **保留的旧安装。** 每次更新都会把被替换的安装保留在 `<名称>.backup-xxxxxxxx` 中。每个项目保留最新的 2 份（在 `~/.urtc_updater_settings.json` 中设置 `"backups_to_keep"` 可更改数量），更新成功后会移除更旧的。`urtc-updater --cli clean-backups [--keep N] [--dry-run]` 可按需移除它们，同时移除因运行中断而遗留的隐藏暂存文件夹。
- **可选：从发布版的已签名包安装。** `urtc-updater --cli package list|check|install|rollback` 用发布版附带的 `.zip` / `.tar.gz` 安装程序（刷写器、测试器或本更新器），而不是克隆加构建。只提供严格更高的版本，只来自 GitHub 的下载主机，并且包必须与公布的大小和 SHA-256 以及程序中固定的发布密钥的 Ed25519 签名一致；任何检查未通过的包都会被删除。安装前会询问（`--yes` 为脚本代答），保留最近两个发布版，`rollback` 可退回上一个。`install --file 包` 可使用磁盘上的文件（旁边放着 `.sha256` 和 `.sig`），无需网络。窗口里有给更新器自身用的“检查更新”按钮，规则相同；启动时的自动检查是一个选项，默认关闭。已用在计算机上生成的软件包测试，尚未用已发布的版本测试。
- **软件包窗口和帮助窗口。** “软件包”按钮列出 flasher、tester 和本更新器的已签名软件包：按下“检查更新”后，每一行检查自己的版本，下载并验证软件包，安装前先询问，并可退回上一版本，规则和安全选项与 `package` 命令相同；有项目正在安装或更新时不会安装任何东西。“帮助”按钮以窗口所用语言打开五步指南。
- **恢复其中一份。** `urtc-updater --cli restore-backup <项目> [--backup 文件夹] [--list]` 会把保留的安装放回原位。被替换的安装也会被保留，因此这次互换可以撤销。 窗口中在“更新所选项”旁边提供同样的两个操作：预览更新（不更改任何内容，查看更新会带来什么）和恢复上一个版本。
- **版本相同，但有新提交。** 版本号只在发布构建时变化，所以 `status` 还会把每个已安装项目的提交与远程提交（`git ls-remote`）比较，当 GitHub 上有该副本没有的内容时显示 `NEW COMMITS`。窗口显示同样的状态并提供更新。
- **批准前先看。** `urtc-updater --cli update <项目> --preview` 会获取候选版本并显示其提交、作者、版本、签名状态以及它更改的构建或工具文件，而不触碰该副本。
- **仅通知。** `urtc-updater --cli check [--notify] [--quiet]` 列出可以更新的内容，但不做任何更改。有可更新内容时以代码 10 退出，便于计划任务通知相关人员；`--notify` 还会显示桌面通知。
- **证据。** 每次安装、更新和恢复都会连同时间、主机和用户记录在 `.urtc-updater/evidence.jsonl` 中，每一行都通过哈希与上一行链接。`urtc-updater --cli evidence [--export 文件]` 会验证该链，并可将其导出为一个 JSON 文档。
- **工作站配置档。** 设置文件中的 `"profiles"` 指明一台机器处理哪些项目以及是否允许批量操作；`--profile 名称`（或设置中的 `"profile"`）会把 `status`、`check`、`install` 和 `update` 限制在其中，窗口也遵循同一配置档。

## 🚀 快速开始

```bash
chmod +x build.sh   # 仅需一次
./build.sh          # 创建 .venv，pip install -e .，对一切进行编译检查
./run.sh                              # 窗口化 GUI（默认）
./run.sh --cli status                 # 已安装的内容，本地版本与 GitHub 版本对比
./run.sh --cli status --offline       # 相同，但跳过 GitHub 检查
./run.sh --cli install <PROJECT-NAME> # 克隆 + 构建一个尚未安装的项目
./run.sh --cli update  <PROJECT-NAME> # 拉取 + 重新构建一个已安装的项目
```

在 Windows 上：先 `build.bat`，然后 `run.bat`（GUI）/ `run.bat --cli
status` / `run.bat --cli install <name>` / `run.bat --cli update
<name>`。

首选 GUI 需要可选 Qt 运行时（`pip install -e ".[gui]"`；
`build.bat`/`build.sh` 已经安装它）。`--cli` 没有图形依赖，适合无桌面的
CM5。没有 Qt 时，旧 Tkinter 窗口仅作为兼容回退。

<!-- urtc-section:compatibility -->
### 要求与兼容性

哪些版本的 URTC 程序可以配合使用、各自使用哪个协议版本，列在 URTC-COMMON 生成的兼容性表中：[docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md)。
<!-- /urtc-section:compatibility -->

## 🧪 测试

测试套件共有 482 个测试（`QT_QPA_PLATFORM=offscreen python -m pytest tests -q`；缺少可选依赖时有些会被跳过）：发现和清单、唯一的版本解析器、针对本地服务器的 GitHub 客户端（重试、错误、格式错误的目录）、在真实本地 git 仓库上的安装和更新（暂存、提升、备份、拒绝情形、返回 75 的 build-test、工作区安全）、恢复和清理备份、签名提交策略、安全选项、签名包及其回滚、证据链、设置和配置档案、八种语言的窗口文本和 Qt 桥接，以及无需屏幕绘制的窗口指南图片。CI 中会运行 `python -m mypy` 和 `ruff check .`。

## 🏗️ 构建与发布

`build.sh` / `build.bat` 创建 `.venv`、安装软件包（`pip install -e .`，并为窗口安装 Qt 运行时）并编译检查所有内容；`build-test.sh` / `build-test.bat` 只检查不安装；`run.sh` / `run.bat` 打开窗口，或用 `--cli` 打开命令行；`run-gui.vbs` 在 Windows 上无控制台窗口地打开它。目前还没有构建打包的独立可执行文件。

## 🩺 故障排除

- `status` 在某个项目的 GitHub 版本处显示 `?`：无法为它读取 GitHub。STATE 列会说明原因（例如 `installed, GitHub unknown (HTTP 404)` 或请求限额提示）。
- `status` 对 GitHub 显示 `-` 但没有显示任何错误：运行 `status`（不带 `--offline`）——`-` 只会在 GitHub 检查被完全跳过时出现。
- `install`/`update` 失败并提示 "No non-versioning build-test.sh/.bat found"：该副本没有 `build-test.sh`（Windows 上为 `build-test.bat`）。请更新项目本身，或手动验证；本工具绝不会改为运行会提升版本号的构建脚本。
- `git pull --ff-only` 失败：本地检出存在未提交的修改，或历史已分叉——请手动解决该问题（在该项目自身的目录中运行 `git status`）后再重试 `update`。本工具从不对检出进行强制重置。

## 📂 仓库结构

<p align="center">
  <img src="images/repository-structure.svg" alt="URTC-UPDATER 的仓库结构" width="100%">
</p>

<details>
<summary>目录树的文本版</summary>

```text
URTC-UPDATER/
├── src/urtc_updater/                                  程序：发现、版本、安装和更新、安全、签名包、Qt Quick 窗口及其八种语言的文本
├── tests/                                             每个模块的真实测试
├── docs/                                              命令参考、界面和窗口指南
├── tools/                                             构建检查、截图、图标和共用工具
├── images/                                            横幅和本 README 的图片
├── .github/                                           CI 工作流以及 Issue 和 Pull Request 模板
├── build.sh build.bat                                 构建脚本
├── build-test.sh build-test.bat                       构建并测试的脚本，不会修改仓库内容
├── test.sh test.bat                                   运行测试
├── run.sh run.bat                                     启动程序
├── urtc.project.json                                  清单：版本、角色、成熟度和构建命令
├── CHANGELOG.md                                       每个版本的变更
├── SECURITY.md SUPPORT.md LICENSE                     安全政策、支持和许可证
├── CONTRIBUTING.md CODE_OF_CONDUCT.md                 如何参与贡献和行为准则
├── .gitattributes .gitignore                          Git 设置
├── run-gui.vbs                                        无控制台窗口的 Windows 启动器
├── bump.py bump_version.py bump_manifest_version.py   提升版本号的脚本
├── urtc_i18n.lock.json                                窗口文本的锁文件
├── LICENSE.md .env.example                            文档许可证和环境变量
└── pyproject.toml requirements-dev.lock ruff.toml     软件包、锁定的工具、lint 设置和文本锁文件
```

</details>

每个源文件的带注释清单（每个文件一行）见 [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md)。

## 🗺️ 路线图与已知限制

- 一个打包的独立 GUI 可执行文件（PyInstaller，与 HYDRA-UMC-SUITE 自身的 `build_exe.bat`/`.sh` 惯例一致），实现完全无需 `pip`/venv 步骤的双击安装——目前的 GUI 仍然需要像 CLI 一样先执行 `./build.sh`。
- 可选的逐项目依赖预检查（在 `install` 中途失败之前，报告缺失的工具链——未安装 Rust/Go/Android SDK/Flutter）。
- 针对 HYDRA-UMC/URTC 自身多二进制固件的逐组件跟踪（见第 3 节中的"已知的简化处理"），一旦出现超出目前所跟踪的单一代表性组件的真实需求。

## 🌍 语言

README 和文本提供英语、西班牙语、法语、意大利语、德语、汉语、日语和欧洲葡萄牙语版本。

## 🔗 相关项目

URTC 由相互独立的仓库组成，每个仓库都有自己的版本、测试和 README。以下是按组划分的家族：

* **URTC Tool Platform:**
  * [URTC](https://github.com/JuanenRac/URTC) - 工具头电路板的固件(25 个工具配置、CAN 引导程序)以及 CAN 协议参考。
  * [URTC-COMMON](https://github.com/JuanenRac/URTC-COMMON) - 只写一次的 CAN 协议数据(规范、生成的表格、一致性向量)以及各程序共享的代码。
  * [URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER) - 通过 CAN 或 SWD/JTAG 更新电路板固件的桌面工具。
  * [URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY) - 位于 CAN 总线前的网关:只放行列表中的标识符,限制其速率,并要求会话密钥。
  * [URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK) - 用于带预热和生命周期跟踪的工具架的、与硬件无关的 C 逻辑和命令协议。
  * [URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER) - 桌面实时 CAN 总线测试器,显示电路板所报告工具配置的控件和遥测。
  * [URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL) - C 语言的传感器帧协议,以及用于检测工具头的 Python 热成像/RGB 配套程序。
  * [URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO) - 通过 Web Serial 和 SLCAN 烧录并测试电路板的浏览器应用,无需安装。
* **Ecosystem Operations:**
  * [URTC-DEVTOOLS](https://github.com/JuanenRac/URTC-DEVTOOLS) - 家族共用的仓库工具，作为带版本的整套工具，并用锁文件区分被改动的副本和已过时的副本。
  * [URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS) - 生态系统的架构、接口、安全基线和生成的目录,以及比较所有仓库的工具。
  * **URTC-UPDATER** (本仓库) - 检测、安装并更新 URTC 家族仓库的桌面工具,每次只执行一个明确的操作。

**姊妹项目（相互独立，共用同一基础和工具）：**

* **[HYDRA-UMC-DOCS](https://github.com/JuanenRac/HYDRA-UMC-DOCS)** - 姊妹项目：HYDRA-UMC 的文档中心，一个独立的生态，与本生态共用基础和工具
* **[ARMOR-DOCS](https://github.com/JuanenRac/ARMOR-DOCS)** - 姊妹项目：A.R.M.O.R. 安全生态的文档中心，同样独立，建立在同一基础上
* **[JuanenRac](https://github.com/JuanenRac/JuanenRac)** - 所有生态的个人主页和状态面板

## 📚 文档

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — 每一个 `--cli` 子命令、从真实安装环境中获取的真实输出,以及退出码契约。
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — Qt Quick/QML 桌面客户端的真实结构,以及它为何始终是同一个后端之上的真实控制界面(与 `--cli` 共用后端),而不是第二套实现。
* **[本仓库的更新日志](CHANGELOG.md)**
* 问题、想法与报告:electrohobby3d@gmail.com

## 🤝 参与贡献与社区

* 提交 Pull Request 之前请运行 `URTC_CI=1 python tools/ci_validate.py`：必须通过。参见 [CONTRIBUTING.md](CONTRIBUTING.md) 和[行为准则](CODE_OF_CONDUCT.md)。
* README 有八种语言：修改文字时要同步修改全部八个文件，与其他仓库共用的章节由 URTC-COMMON 的 `tools/readme_sections.py` 写入。
* 对 CAN 协议的修改从 URTC-COMMON（`spec/can_protocol.json`）开始，并通过经过核对的副本进入本仓库。
* 不要把仅仅构建过的东西描述为已在板子上运行。
* 请私下报告漏洞：[SECURITY.md](SECURITY.md)。问题、想法和报告：electrohobby3d@gmail.com（[SUPPORT.md](SUPPORT.md)）。

## 👤 作者

**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 许可证

GPL-3.0-or-later —— 详见 [LICENSE](LICENSE)。
