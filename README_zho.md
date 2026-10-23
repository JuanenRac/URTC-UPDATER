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

**诚实核查 - 今天真正能运行的部分：** **成熟度：成熟（established，仅有一次有记录的完整运行，并非持续使用）。** 本项目把 HYDRA-UMC-UPDATER 已验证的设计（同样的清单发现、通过原子验证的临时克隆进行安装/更新，以及证据日志）仅用于 URTC 生态系统的仓库。它已在隔离的工作区中针对 GitHub 完整地端到端运行过：一次全新安装和随后对真实仓库的一次更新都正确地完成了克隆、构建和提升，并把之前的副本保留为备份。发现与版本逻辑（`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`）、带重试/退避并缓存仓库列表的 GitHub raw-content 客户端（`github_client.py`）、按提交比较（`commits.py`）以及克隆-暂存-验证-提升流水线（`install.py`）都有测试覆盖（`python -m pytest`），包括本地 HTTP 测试服务器，以及带本地 bare 远程的真实临时 git 仓库。Qt 桥接层自身的逻辑在测试中无界面运行；QML 界面本身没有自动化测试。`i18n.py` 的 8 种语言覆盖通过测试检查键和占位符是否一致，而不检查翻译质量。具体已交付的内容请见 `CHANGELOG.md`。

---

> **安全与安防现状:**本生态系统不是经认证的安全系统,目前也不存在已组装的 URTC 电路板。引导程序使用 CRC32 和共享密钥的 HMAC-SHA256 校验固件映像,而非非对称签名(计划中);已发布的应用映像使用公开的开发密钥签名(`signing_key_kind: dev`),因此任何人都可以生成引导程序接受的映像;尚未向任何真实电路板发送过任何内容。在依赖此处任何说法来保障人身安全之前,请先阅读[安全基线](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md)和[威胁模型](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md)。

## 📋 速览

| | |
|---|---|
| 版本 | `0.1.7` |
| 成熟度 | 成熟 |
| 技术栈 | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| 目标 | 使用者的电脑 |
| 真实硬件 | 不适用：这里的内容不在硬件上运行 |

## 1. 🛠️ 技术概述

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

不带任何参数运行 `urtc-updater`（或直接双击它）会在窗口中打开同样
的信息——一个可排序的项目表格、一个部署目标筛选器，以及针对当前所选行
的安装/更新按钮。

## 2. 🔄 检查/更新实际是如何工作的

- **版本来源**：本生态系统自身的"里程表"式自动递增惯例（每次真实构建都会递增一个存在于源文件*内部*的版本号——根据项目所用技术栈的不同，可能是 `pyproject.toml`、`Cargo.toml`、`version.go`、`package.json`、`version.properties`、`pubspec.yaml`，或一个固件 `#define`）从未为该次递增创建过 git 标签或 GitHub Release。因此本工具直接通过 GitHub 的原始内容托管，读取每个项目自身的 `bump_version.py`/构建脚本已经在写入的那个*同一个*文件的仓库默认分支版本——而非 Releases API，后者会把每个项目都报告为"完全没有发布记录"。
- **本地检测**：对于每一个发现的项目，检查工作区根目录下是否存在一个与该项目名称完全一致的目录（标准的生态系统布局——每个项目作为同级目录，这正是 `build-frontend.sh`/HYDRA-UMC-SUITE 自身的发现逻辑已经假定的方式），如果存在，则读取该项目*自身*的本地版本文件副本。
- **单一解析实现**（`version_parse.py`）在本地读取和 GitHub 抓取之间共享，因此本地检出和 GitHub 抓取绝不会被两个独立漂移的正则表达式分别解读。
- **安装/更新**：`git clone`（安装）之后作为单独的一步再编译。更新一个已存在的检出则改为「通过验证实现原子性」：候选版本先被克隆、进行快进合并（绝不使用强制重置，因此真实的本地修改会明确失败，而非被丢弃），然后首先在一个完全独立的暂存克隆中编译/验证——只有当那次暂存编译真正成功时，实际安装才会被触碰（通过两次连续的目录重命名，之前的安装会被保留在 `<name>.backup-xxxxxxxx` 中，而不是被删除）。在最终提升之前的任何时刻发生编译失败、检出分叉/存在未提交修改、崩溃或磁盘写满，都会让之前的安装完全不受影响、继续保持可运行——详见 `install.py` 自身 `clone_or_pull` 的 docstring。暂存克隆自身的 git 远程仓库会在创建后立即恢复为真实的 GitHub 上游（否则一个普通的本地克隆会指向旧的安装路径，一旦被提升就会在不知不觉中终止所有未来的更新），并且已安装检出自身真实的本地数据（任何 git 视为未跟踪或被忽略的内容——`data/settings.json` 及类似文件，不包括可重新生成的构建产物）会在编译前被带入暂存克隆，这样一个项目自身真实的运行状态就能在更新后保留下来，而不是被困在保留的 `.backup-xxxxxxxx` 检出中。无论哪种情况，只要该项目自身实际拥有 `build-test.sh`/`build-test.bat`（不递增版本号的检查——见第 3 节），就会运行它。本工具从不重新实现某个项目自身的构建步骤。

**build-test 可以返回什么：** 退出码 0 表示已验证，其他任何退出码都表示失败，唯独 75 表示验证*不可用*（缺少它需要的工具）。这会如实报告并拒绝更新，除非你在设置中把 `validation_unavailable` 设为 `accept`（或设置 `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`）来接受。build-test 应让目录树保持原样：如果它修改了 git 跟踪的文件，该文件会在提升之前恢复为已提交的内容，步骤中会说明是哪些文件。

**已签名提交（默认仅警告；强制要求属于可选项，默认关闭）：** 没有有效签名的修订（`git verify-commit`：GPG 密钥环，或使用 `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS` 的 SSH）仍会安装，窗口和命令行的步骤会说明它未签名。在 `~/.urtc_updater_settings.json` 中设置 `"signature_policy": "require"`（或 `URTC_UPDATER_REQUIRE_SIGNED=1`；旧的 `"require_signed_commits": true` 含义相同）后，候选版本 - 新克隆的 `HEAD` 或更新所获取的 `FETCH_HEAD` - 必须在读取其清单或构建任何内容之前通过 `git verify-commit`，被拒绝的候选版本不会改动已安装的检出。

**安全选项（两者默认都关闭；可通过窗口的“安全”按钮、`security` 命令、设置文件、环境变量和命令行修改）：** 除了要求已签名的提交，更新器还可以在运行候选版本的构建检查*之前先询问*（`"confirm_before_build": true`、`URTC_UPDATER_CONFIRM_BUILD=1`、`--confirm-build`）。它获取并验证候选版本，显示项目、提交、作者、签名以及已更改的构建或工具脚本，在你回答之前不运行任何东西；如果没有窗口也没有终端可询问，则什么都不运行（脚本可用 `--yes` 代为回答）。`--require-signed` / `--no-require-signed` 和 `--confirm-build` / `--no-confirm-build` 只对一次运行有效，关闭已保存设置中开启的保护的运行会明确提示；窗口以及 `urtc-updater --cli security --require-signed off` 在保存较低级别之前会要求确认。存在但无法读取的设置文件会被视为“要求签名”，直到它被修复或删除。构建检查还会收到 `URTC_PYTHON`（运行更新器的解释器），因此项目用该 Python 测试，而不是系统最先找到的那个。

## 3. 🧱 架构与设计决策

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

## 📂 目录结构

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry —— 没有静态目录;在发现时从每个仓库自身的清单构建
│   ├── project_manifest.py # 读取/校验仓库自身的 urtc.project.json
│   ├── version_parse.py   # 单一的正则表达式提取实现，本地+GitHub 通用
│   ├── detect.py          # 扫描工作区根目录，检测已安装的内容
│   ├── github_client.py   # 并发抓取原始内容 + 针对临时性网络错误的真实重试/退避机制
│   ├── install.py         # git clone/pull + 委托给项目自身的构建脚本
│   ├── signature.py       # 可选的已签名提交策略（构建前执行 git verify-commit）
│   ├── commits.py          # 按提交把副本与其远程进行比较（git ls-remote）
│   ├── messages.py         # 以代码加参数表示的安装/更新消息
│   ├── evidence.py         # 按哈希链接的每次尝试日志
│   ├── settings.py         # 记住的偏好（语言、工作区、保留数量、配置档）
│   ├── profiles.py         # 具名的工作站配置档
│   ├── notify.py           # 仅通知检查所用的桌面通知
│   ├── logs.py             # 窗口日志文件的轮转
│   ├── i18n.py             # 真实、完整的 GUI 翻译（8 种语言）
│   ├── translations_data.py # 窗口文本，由 URTC-COMMON 的目录生成
│   ├── qt_gui.py           # 通向真实发现/更新服务的 Qt Quick 桥接层
│   ├── packages_qt.py      # 软件包窗口：各发布版的已签名软件包
│   ├── qml/Main.qml        # 带主题、检查点和 About 的桌面界面
│   ├── gui.py              # PySide6 不可用时的 Tkinter 兼容回退
│   └── main.py             # 分发逻辑：默认 GUI，--cli 用于 status/install/update
├── tests/                  # 每个模块的真实测试（`python -m pytest`）
├── docs/
│   ├── CLI_REFERENCE.md     # 命令参考
│   └── QML_DESKTOP_GUI.md   # Qt Quick GUI 架构
├── images/                 # 媒体、应用图标与界面截图
├── tools/
│   ├── build_test.py        # 不递增版本号的构建检查
│   ├── ci_validate.py       # CI 使用的清单/CHANGELOG/文档校验
│   ├── generate_app_icon.py # 将公开的 HYDRA-UMC SVG 渲染为 Windows 使用的图标
│   ├── migrate_project_manifests.py  # 一次性清单迁移后对工作区的审计
│   └── validate_project_manifests.py # 校验仓库自身的清单 + 原生构建版本号
├── .env.example            # 环境变量模板
├── build.sh / build.bat    # venv + 可编辑安装 + 编译检查
├── run.sh / run.bat        # 默认 GUI / CLI 入口
├── run-gui.vbs             # 无控制台窗口的 Windows 图形启动器
├── bump.py                 # 显式的版本递增命令（编译从不递增）
├── bump_version.py         # 生态系统统一的里程表式版本递增（pyproject.toml + __init__.py）
└── bump_manifest_version.py # 将 urtc.project.json 的版本与原生版本同步(--sync)
```

## ⚙️ 构建与运行

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

**故障排查**

- `status` 在某个项目的 GitHub 版本处显示 `?`：无法为它读取 GitHub。STATE 列会说明原因（例如 `installed, GitHub unknown (HTTP 404)` 或请求限额提示）。
- `status` 对 GitHub 显示 `-` 但没有显示任何错误：运行 `status`（不带 `--offline`）——`-` 只会在 GitHub 检查被完全跳过时出现。
- `install`/`update` 失败并提示 "No non-versioning build-test.sh/.bat found"：该副本没有 `build-test.sh`（Windows 上为 `build-test.bat`）。请更新项目本身，或手动验证；本工具绝不会改为运行会提升版本号的构建脚本。
- `git pull --ff-only` 失败：本地检出存在未提交的修改，或历史已分叉——请手动解决该问题（在该项目自身的目录中运行 `git status`）后再重试 `update`。本工具从不对检出进行强制重置。

## 🧹 维护与工作站命令

- **保留的旧安装。** 每次更新都会把被替换的安装保留在 `<名称>.backup-xxxxxxxx` 中。每个项目保留最新的 2 份（在 `~/.urtc_updater_settings.json` 中设置 `"backups_to_keep"` 可更改数量），更新成功后会移除更旧的。`urtc-updater --cli clean-backups [--keep N] [--dry-run]` 可按需移除它们，同时移除因运行中断而遗留的隐藏暂存文件夹。
- **可选：从发布版的已签名包安装。** `urtc-updater --cli package list|check|install|rollback` 用发布版附带的 `.zip` / `.tar.gz` 安装程序（刷写器、测试器或本更新器），而不是克隆加构建。只提供严格更高的版本，只来自 GitHub 的下载主机，并且包必须与公布的大小和 SHA-256 以及程序中固定的发布密钥的 Ed25519 签名一致；任何检查未通过的包都会被删除。安装前会询问（`--yes` 为脚本代答），保留最近两个发布版，`rollback` 可退回上一个。`install --file 包` 可使用磁盘上的文件（旁边放着 `.sha256` 和 `.sig`），无需网络。窗口里有给更新器自身用的“检查更新”按钮，规则相同；启动时的自动检查是一个选项，默认关闭。已用在计算机上生成的软件包测试，尚未用已发布的版本测试。
- **软件包窗口和帮助窗口。** “软件包”按钮列出 flasher、tester 和本更新器的已签名软件包：按下“检查更新”后，每一行检查自己的版本，下载并验证软件包，安装前先询问，并可退回上一版本，规则和安全选项与 `package` 命令相同；有项目正在安装或更新时不会安装任何东西。“帮助”按钮以窗口所用语言打开五步指南。
- **恢复其中一份。** `urtc-updater --cli restore-backup <项目> [--backup 文件夹] [--list]` 会把保留的安装放回原位。被替换的安装也会被保留，因此这次互换可以撤销。 窗口中在“更新所选项”旁边提供同样的两个操作：预览更新（不更改任何内容，查看更新会带来什么）和恢复上一个版本。
- **版本相同，但有新提交。** 版本号只在发布构建时变化，所以 `status` 还会把每个已安装项目的提交与远程提交（`git ls-remote`）比较，当 GitHub 上有该副本没有的内容时显示 `NEW COMMITS`。窗口显示同样的状态并提供更新。
- **批准前先看。** `urtc-updater --cli update <项目> --preview` 会获取候选版本并显示其提交、作者、版本、签名状态以及它更改的构建或工具文件，而不触碰该副本。
- **仅通知。** `urtc-updater --cli check [--notify] [--quiet]` 列出可以更新的内容，但不做任何更改。有可更新内容时以代码 10 退出，便于计划任务通知相关人员；`--notify` 还会显示桌面通知。
- **证据。** 每次安装、更新和恢复都会连同时间、主机和用户记录在 `.urtc-updater/evidence.jsonl` 中，每一行都通过哈希与上一行链接。`urtc-updater --cli evidence [--export 文件]` 会验证该链，并可将其导出为一个 JSON 文档。
- **工作站配置档。** 设置文件中的 `"profiles"` 指明一台机器处理哪些项目以及是否允许批量操作；`--profile 名称`（或设置中的 `"profile"`）会把 `status`、`check`、`install` 和 `update` 限制在其中，窗口也遵循同一配置档。

## 🚀 路线图

- 一个打包的独立 GUI 可执行文件（PyInstaller，与 HYDRA-UMC-SUITE 自身的 `build_exe.bat`/`.sh` 惯例一致），实现完全无需 `pip`/venv 步骤的双击安装——目前的 GUI 仍然需要像 CLI 一样先执行 `./build.sh`。
- 可选的逐项目依赖预检查（在 `install` 中途失败之前，报告缺失的工具链——未安装 Rust/Go/Android SDK/Flutter）。
- 针对 HYDRA-UMC/URTC 自身多二进制固件的逐组件跟踪（见第 3 节中的"已知的简化处理"），一旦出现超出目前所跟踪的单一代表性组件的真实需求。

## 🔗 相关项目

**URTC**(通用机器人工具控制器)是同一作者(JuanenRac / Electro Hobby 3D)打造的真实物理换刀平台。每个仓库都有自己的版本、自己的测试和自己的 README;这是完整的项目家族:

* **[URTC](https://github.com/JuanenRac/URTC)** - 物理通用机器人工具控制器 PCB 的固件,基于 CAN 总线的 25+ 工具配置
* **[URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS)** - 生态的架构、接口、安全基线、能力矩阵和生成的项目目录,以及对所有仓库进行比较的工具
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - URTC 板卡的桌面刷写工具,CAN-OTA 加完整芯片 SWD/JTAG
* **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** - 位于 CAN 总线前的网关，只放行列表中的标识符，限制其速率，并要求会话密钥。
* **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** - 工具挂架固件,具备真实的工具 ID 解码和 Smart Idle 预热逻辑
* **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** - URTC 板卡的桌面实时 CAN 总线诊断工具,每个工具配置一个面板
* **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** - 固件加真实的 Python 视觉配套程序,用于热成像/RGB 检测工具头
* **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** - 通过 Web Serial API 实现的 URTC-TESTER 浏览器替代方案,无需本地安装
* **URTC-UPDATER**(本仓库)- 检测、安装并更新生态系统自身的仓库

本工具的设计(清单发现、以验证为准的原子安装/更新、证据日志)与同一作者为 HYDRA-UMC 和 A.R.M.O.R. 生态系统打造的 **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** 和 **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** 共享,二者各自仅限于自己的仓库。

## 📚 文档与社区

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — 每一个 `--cli` 子命令、从真实安装环境中获取的真实输出,以及退出码契约。
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — Qt Quick/QML 桌面客户端的真实结构,以及它为何始终是同一个后端之上的真实控制界面(与 `--cli` 共用后端),而不是第二套实现。
* **[本仓库的更新日志](CHANGELOG.md)**
* 问题、想法与报告:electrohobby3d@gmail.com

## 👤 作者
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

<!-- urtc-section:updates -->
## 🔄 如何更新

本程序可以查找自身的较新版本：“检查更新”按钮只向 GitHub 查询一次，只有当包适用于您的系统且更新时才会提供已签名的包。除非您打开检查，否则不会自行检查或安装，更新需要您的确认。包必须与其 SHA-256 以及程序中固定的发布密钥签名一致；上一版本会保留，新版本无法启动时会自动恢复。`urtc-updater --cli package list|check|install|rollback` 可在命令行中为刷写器和测试器完成同样的操作，`install --file` 无需网络即可使用。
<!-- /urtc-section:updates -->

<!-- urtc-section:compatibility -->
## 🧩 兼容性

哪些版本的 URTC 程序可以配合使用、各自使用哪个协议版本，列在 URTC-COMMON 生成的兼容性表中：[docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md)。
<!-- /urtc-section:compatibility -->

## 📜 许可证

GPL-3.0-or-later —— 详见 [LICENSE](LICENSE)。
