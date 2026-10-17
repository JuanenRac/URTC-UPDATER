<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="Banner do URTC-UPDATER" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | 🇵🇹 <b>Português</b></p>

### 📦 Detetar, Instalar e Atualizar Manualmente Todo o Ecossistema URTC

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0-blue.svg" alt="GPL 3.0">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="CLI core apenas com stdlib">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="GUI desktop PySide6 Qt Quick">
</p>

> **Modo desktop visual:** a interface desktop predefinida é agora construída
> com **Qt Quick / QML** através do runtime de GUI opcional `PySide6`. O núcleo
> do atualizador e o modo `--cli` continuam a usar apenas a stdlib, para uma
> máquina sem ecrã.
>
> **Arranque no Windows e evidência de atualização:** faça duplo clique em
> `run-gui.vbs` (ou use `run.bat` simples) para obter o cliente desktop sem
> consola. O seu painel Safe Update mostra pontos de controlo reais de
> Preflight, Source refresh, Manifest validation, Build-test e Complete, com a
> evidência dos comandos capturada; `run.bat --cli ...` mantém deliberadamente
> um terminal para diagnóstico.
> A instalação só está disponível para um checkout em falta; a atualização só
> quando o GitHub tem uma versão mais recente. Durante uma ação aprovada, os
> pontos de controlo substituem os controlos do projeto selecionado, e
> selecionar outro projeto restaura-os.
> **Install all missing** e **Update all outdated** são ações em lote
> sequenciais, confirmadas em separado, construídas a partir do mesmo estado em
> direto e do mesmo caminho de segurança.

**Verificação de honestidade - o que realmente funciona hoje:** **Maturidade: scaffolding.** Este projeto adapta o design já comprovado do próprio HYDRA-UMC-UPDATER (a mesma deteção por manifesto, instalação/atualização com staging clone atómica por verificação, registo de evidência) apenas aos seis repositórios do ecossistema URTC. A lógica de deteção/versões (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), o cliente real de conteúdo raw do GitHub com retry/backoff (`github_client.py`) e a lógica de clone-stage-verify-promote do pipeline de instalação/atualização (`install.py`) são reais e estão testadas - 106 testes a passar (`pytest tests/`), incluindo um servidor HTTP de fixture que prova o isolamento entre catálogo malformado e projeto malformado, e ciclos completos reais de git clone/build em diretórios temporários. Nunca instalou nem atualizou de ponta a ponta um repositório URTC real. A cobertura de 7 idiomas de `i18n.py` é imposta por teste (`test_i18n.py`), mas apenas quanto à paridade de chaves entre idiomas, não quanto à qualidade da tradução. Consulte `CHANGELOG.md` para saber exatamente o que foi entregue até agora.

---

## 1. 🛠️ VISÃO TÉCNICA GERAL

O URTC-UPDATER é uma pequena ferramenta - GUI em janela por predefinição, CLI
completo com `--cli` - pensada para correr na máquina Windows/Linux/macOS do
próprio programador (qualquer workspace obtido da mesma forma) e que responde
a três perguntas sobre cada outro projeto real que deteta através do
manifesto `urtc.project.json` do respetivo checkout irmão - o número em si
nunca está fixado aqui, pois cresce com o ecossistema (seis repositórios
atualmente):

1. **O que está realmente instalado aqui e em que versão?**
2. **Qual é a última versão publicada no GitHub?**
3. **Se o GitHub tiver uma versão mais recente, deixar-me escolher um projeto ou um lote sequencial confirmado.**

Este último ponto é deliberado e inegociável: esta ferramenta nunca altera um
projeto por iniciativa própria. Uma ação sobre um projeto selecionado exige
sempre confirmação explícita. A GUI também pode oferecer **Install all
missing** ou **Update all outdated**; cada uma é um lote sequencial,
confirmado em separado, cujos projetos seguem os mesmos portões de manifesto,
versão e segurança. Uma célula de controlo de robôs nunca deve atualizar-se
automaticamente durante a noite sem que uma pessoa aprove a ação exata.

Todo o repositório URTC real declara `deployment_target: "user-pc"` -
não existe papel de CM5/servidor neste ecossistema, ao contrário do
HYDRA-UMC. Os repositórios de firmware (URTC, URTC-SMART-RACK,
URTC-VISION-TOOL) continuam a ser compilados e gravados A PARTIR de uma
estação de trabalho, apenas não correm lá depois; o próprio campo `deploy` de
`registry.py` regista isto (ver secção 3), e o filtro da tabela de projetos da
GUI começa sempre em "mostrar tudo", pois não há nenhum subconjunto específico
de plataforma que valha a pena usar como predefinição.

Exemplo ilustrativo (o número exato de projetos e todos os números de versão
abaixo são inventados apenas para mostrar a forma da saída, não são uma
execução real capturada - o número real é o que `registry.py` deteta hoje,
nunca um número fixo gravado neste documento):

```
$ urtc-updater --cli status
Workspace root: /home/user/GitHub
Checking GitHub... 6/6
PROJECT                        STACK       LOCAL     GITHUB    STATE
--------------------------------------------------------------------
URTC                           firmware-c  0.3.0     0.3.1     OUTDATED
URTC-FLASHER                   python-qt   0.2.1     0.2.1     up to date
URTC-TESTER                    python-qt   0.2.2     0.2.2     up to date
...
6/6 installed, 1 outdated

$ urtc-updater --cli update URTC
Updating URTC into /home/user/GitHub ...
OK  Pulled latest into /home/user/GitHub/URTC
OK  build_firmware.sh completed successfully.
```

Executar `urtc-updater` sem argumentos (ou fazer duplo clique) abre a mesma
informação numa superfície de controlo desktop escura: um painel **Local
Ecosystem** com métricas de deteção/instalação/atualização em direto, uma
árvore **Project Registry** orientada por manifesto e um painel **Safe
Update** para o projeto selecionado. O layout torna visíveis as proteções
reais: deteção por manifesto, uma única ação explícita sobre um projeto,
confirmação manual, build opcional e um rasto de atividade no ecrã; a
evidência completa dos comandos continua a ser escrita no terminal de
arranque.

<p align="center">
  <img src="images/" alt="Visão geral real do desktop do URTC-UPDATER" width="100%">
</p>

## 2. 🔄 COMO FUNCIONA REALMENTE UMA VERIFICAÇÃO/ATUALIZAÇÃO

- **Origem da versão**: a convenção de auto-bump "odómetro" deste ecossistema
  (cada build real incrementa um número de versão que vive NUM ficheiro de
  código-fonte - `pyproject.toml`, `Cargo.toml`, `version.go`,
  `package.json`, `version.properties`, `pubspec.yaml` ou um `#define` de
  firmware, consoante a stack do projeto) nunca criou uma tag git nem uma
  GitHub Release para esse incremento. Por isso, esta ferramenta lê o MESMO
  ficheiro que o `bump_version.py`/script de build de cada projeto já
  escreve, diretamente do ramo predefinido do repositório através do host de
  conteúdo raw do GitHub - não a API de Releases, que indicaria que todos os
  projetos não têm releases.
- **Deteção local**: para cada projeto detetado, verifica se existe um
  diretório com esse nome exato na raiz do workspace (o layout padrão do
  ecossistema - cada projeto como diretório irmão, exatamente o que os
  próprios scripts de build do URTC-FLASHER/URTC-TESTER já assumem) e, se
  existir, lê a SUA própria cópia local desse mesmo ficheiro de versão.
- **Uma única implementação de parsing** (`version_parse.py`) é partilhada
  entre a leitura local e a obtenção no GitHub, para que um checkout local e
  uma obtenção do GitHub nunca sejam interpretados por duas regex que
  divergem de forma independente.
- **Instalar/atualizar**: `git clone` (instalação) compila depois, como passo
  separado. Atualizar um checkout EXISTENTE é, em vez disso, atómico por
  verificação: o candidato é clonado, integrado por fast-forward (nunca um
  force-reset, de modo que edições locais reais falhem de forma visível em
  vez de serem descartadas) e compilado/verificado PRIMEIRO num staging clone
  totalmente independente - a instalação em uso só é tocada (através de dois
  renomeamentos de diretório consecutivos, ficando a instalação anterior em
  `<name>.backup`, não apagada) se essa compilação de staging for bem-sucedida.
  Uma falha de build, um checkout divergente/sujo, um crash ou um disco cheio
  em qualquer momento antes dessa promoção final deixam a instalação anterior
  completamente intacta e operacional - ver o próprio docstring de
  `clone_or_pull` em `install.py`. O remote git do próprio staging clone é
  restaurado para o upstream real do GitHub logo após ser criado (um clone
  local simples apontá-lo-ia, caso contrário, para o caminho da instalação
  antiga, terminando silenciosamente todas as atualizações futuras depois de
  promovido), e os dados locais reais do checkout instalado (tudo o que o git
  considera não rastreado ou ignorado - `data/settings.json` e semelhantes,
  excluindo artefactos de build regeneráveis) são transportados para o
  staging clone antes de compilar, para que o estado operacional real do
  próprio projeto sobreviva a uma atualização em vez de ficar abandonado no
  checkout `.backup` mantido.
  Em ambos os casos executa o `build-test.sh`/`build-test.bat` do próprio
  projeto (a verificação sem versionamento - ver secção 3) que ele realmente
  tiver. Esta ferramenta nunca reimplementa os passos de build de um projeto.

<p align="center">
  <img src="images/" alt="Pontos de controlo de instalação ou atualização do URTC-UPDATER em curso" width="100%">
</p>

**Apenas commits assinados (opcional):** com `"require_signed_commits": true` em `~/.urtc_updater_settings.json` (ou `URTC_UPDATER_REQUIRE_SIGNED=1`), a revisão candidata - o `HEAD` de um clone novo ou o `FETCH_HEAD` obtido numa atualização - tem de passar `git verify-commit` (chaveiro GPG, ou SSH com `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) antes de o seu manifesto ser lido ou de qualquer coisa nela ser compilada. Um candidato recusado deixa o checkout instalado intacto. Desativado por predefinição, pois nem todos os repositórios do ecossistema estão ainda assinados.

## 3. 🧱 ARQUITETURA E DECISÕES DE DESIGN

- **GUI Qt Quick por predefinição, `--cli` para modo sem ecrã.** `main.py`
  verifica `--cli` antes de importar o runtime opcional PySide6, pelo que o
  modo CLI funciona numa máquina genuinamente sem ecrã, sem display nem
  dependência de desktop. A invocação simples inicia o cliente QML onde o
  runtime estiver instalado; a antiga shell Tkinter permanece apenas como
  alternativa temporária de compatibilidade.
- **A GUI em janela é real, multilingue em 7 idiomas (`i18n.py`) - o `--cli` deliberadamente não é.** Cada widget real muda de etiqueta em direto a partir de uma `Combobox` de idioma (en/es/fr/it/de/zh/ja, os mesmos 7 que o dashboard público e todos os README fornecem), detetado a partir de uma preferência guardada ou da própria localização do SO. Os nomes de projetos/famílias e o texto real de `notes`/`tech` de cada projeto permanecem sem tradução - `registry.py` é a sua única fonte de verdade, e 7 cópias paralelas de documentação de engenharia real deixariam de o ser. A saída do `--cli` permanece só em inglês de propósito: destina-se a ser usada em scripts/pipes, onde um texto estável e pesquisável com grep importa mais do que a localização.
- **`deploy` é uma classificação, não uma restrição.** Uma primeira versão
  desta adaptação copiou literalmente a predefinição da GUI do próprio
  HYDRA-UMC-UPDATER - definindo o filtro de deploy como `"cm5"` em Linux - sem
  verificar que nenhum repositório URTC real declara esse alvo de
  implementação (todos são `"user-pc"`: o firmware é compilado e gravado A
  PARTIR de uma estação de trabalho, nunca corre lá depois). A GUI teria
  aberto com uma tabela vazia em Linux. Corrigido: o filtro começa sempre em
  "mostrar tudo" aqui, pois não há papel de CM5/servidor neste ecossistema que
  justifique um tratamento especial.
  O campo `deploy` de `registry.py` ("cm5" / "user-pc" / "mobile" / "wearable" /
  "dev-server") continua a registar a classificação por manifesto de
  repositório - apenas nunca é usado como predefinição de arranque.
- **Sem lógica de build por stack nesta ferramenta.** O ecossistema abrange 7
  toolchains (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, firmware
  ARM). Reimplementar `npm install && npm run build` /
  `cargo build --release` / `./gradlew assembleDebug` / etc. AQUI criaria um
  segundo sítio que alega saber compilar cada projeto, com garantia de
  divergir do `build.sh`/`.bat` real (e já correto) desse projeto. Em vez
  disso, `install.py` procura um nome conhecido de script de build
  (`build.sh`, `build_firmware.sh`, `build_exe.sh`, `build-android.sh` e os
  seus equivalentes `.bat` - os nomes reais usados nos projetos detetados do
  próprio ecossistema) e executa o que existir.
- **Conteúdo raw do GitHub, não a API de Releases.** Ver a secção 2 acima -
  a convenção de versionamento deste ecossistema nunca cria tag/release,
  pelo que a API de Releases estaria ativamente errada aqui, e não apenas
  menos conveniente.
- **Uma falha de rede transitória recebe um retry real; uma resposta definitiva nunca.** Cada pedido real ao GitHub (`_urlopen_with_retries` em `github_client.py`) repete até 3 vezes com backoff, mas apenas para uma ligação que nunca obteve qualquer resposta (DNS/timeout/reset). Um estado HTTP real que o GitHub devolveu efetivamente - 404, 403, 500 - nunca é repetido: o GitHub já respondeu, e insistir apenas gastaria mais do limite de pedidos para o mesmo resultado.
- **Um catálogo remoto malformado falha de forma visível; um projeto malformado não.** Se a própria listagem de repositórios do GitHub estiver inacessível ou não for interpretável, `discover_remote_projects()` lança uma exceção e a bridge desktop recorre a uma lista de projetos detetados localmente em vez de mostrar uma deteção quebrada/vazia. O manifesto malformado de um único repositório, pelo contrário, é isolado na lista `errors` dessa deteção e nunca aborta a deteção dos restantes - um teste real com servidor de fixture (`tests/test_github_client.py`) prova ambos os caminhos.
- **As ações CLI continuam explícitas; os lotes da GUI continuam confirmados.** Os
  comandos CLI `install`/`update` recebem o nome de um único projeto. A GUI
  desktop também pode executar **Install all missing** ou **Update all
  outdated**, mas apenas após uma confirmação separada e de forma sequencial
  pelos mesmos portões de segurança. Não existe qualquer atualização
  automática sem supervisão.
- **Apenas stdlib.** `urllib` para as obtenções do GitHub (`github_client.py`),
  `subprocess` para as chamadas a git/scripts de build (`install.py`), nada
  mais - é deliberado que uma ferramenta responsável por manter saudáveis as
  dependências de todos os OUTROS projetos não tenha ela própria dependências.
- **Simplificação conhecida**: o URTC é um repositório de firmware real com
  vários componentes (4 binários com versões independentes - main + slave,
  cada um com app + bootloader - ver o seu próprio `build_firmware.sh`) sem um
  único número de versão "o" correto. `registry.py` acompanha UM componente
  representativo por repositório - suficiente para responder a "este
  repositório está aproximadamente atualizado", mas não substitui a
  verificação de versão por componente de uma gravação real.

## 📂 ESTRUTURA DE DIRETÓRIOS

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - no static catalogue; built at discovery time from each repo's own manifest
│   ├── project_manifest.py # Reads/validates a repository-owned urtc.project.json
│   ├── ecosystem_catalog.py # Parser for a public ecosystem discovery catalog (not yet wired into main.py)
│   ├── version_parse.py   # ONE regex-extraction implementation, local+GitHub
│   ├── detect.py          # Scans a workspace root for what's installed
│   ├── github_client.py   # Concurrent raw-content fetch + real retry/backoff for transient network errors
│   ├── install.py         # git clone/pull + delegate to the project's own build script
│   ├── signature.py       # Optional signed-commits policy (git verify-commit before building)
│   ├── i18n.py             # Real, complete GUI translations (7 languages)
│   ├── qt_gui.py           # Qt Quick bridge over the real discovery/update services
│   ├── qml/Main.qml        # Themed desktop shell: controls, checkpoints and About
│   ├── gui.py              # Legacy Tkinter fallback if PySide6 is unavailable
│   └── main.py             # Dispatch: GUI by default, --cli for status/install/update
├── tests/                  # Real tests: github_client, i18n, install, project_manifest, registry
├── docs/
│   ├── CLI_REFERENCE.md     # Command reference
│   └── QML_DESKTOP_GUI.md   # Qt Quick GUI architecture
├── images/                 # Media and app icons
├── tools/
│   ├── build_test.py        # Non-versioning build/compile check
│   ├── ci_validate.py       # Manifest/CHANGELOG/docs validation used by CI
│   └── generate_app_icon.py # Renders the public URTC SVG into the Windows-consumed icon
├── .env.example            # Environment variable template
├── build.sh / build.bat    # venv + editable install + compile-check
├── run.sh / run.bat        # GUI default / CLI entry point
├── run-gui.vbs             # Windows graphical launcher with no console window
├── bump_version.py         # Ecosystem-wide odometer bump (pyproject.toml + __init__.py)
└── bump_manifest_version.py # Syncs urtc.project.json's version to the native one (--sync)
```

## ⚙️ GUIA DE BUILD E EXECUÇÃO

```bash
chmod +x build.sh   # one-time
./build.sh          # creates .venv, pip install -e ., compile-checks everything
./run.sh                              # windowed GUI (default)
./run.sh --cli status                 # what's installed, local vs. GitHub version
./run.sh --cli status --offline       # same, skipping the GitHub check
./run.sh --cli install <PROJECT-NAME> # clone + build one project not yet installed
./run.sh --cli update  <PROJECT-NAME> # pull + rebuild one project already installed
```

No Windows: `build.bat` e depois `run.bat` (GUI) / `run.bat --cli status` /
`run.bat --cli install <name>` / `run.bat --cli update <name>`.

A GUI preferida precisa do runtime Qt opcional (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` já o instalam). O `--cli` não tem dependência de GUI e
é o ponto de entrada correto para uma máquina sem ecrã. Se o Qt não estiver
disponível, a antiga shell Tkinter é apenas uma alternativa de
compatibilidade.

**Resolução de problemas**

- `status` mostra `?` na versão local ou do GitHub de um projeto: o seu
  ficheiro de versão existe, mas a convenção do próprio projeto mudou desde
  a última atualização de `registry.py` - compare a entrada de `registry.py`
  desse projeto com o seu ficheiro de versão real e atual.
- `status` mostra `-` no GitHub sem nenhum erro: execute `status`
  (sem `--offline`) - `-` só aparece quando a verificação do GitHub foi
  totalmente ignorada.
- `install`/`update` falha com "No build.sh/.bat found": esse projeto
  usa um nome de script de build que esta ferramenta ainda não reconhece -
  consulte o README do próprio projeto para saber o nome real e considere
  adicioná-lo às listas `BUILD_SCRIPT_CANDIDATES_*` do próprio `install.py`.
- `git pull --ff-only` falha: o checkout local tem alterações por
  submeter ou um histórico divergente - resolva-o manualmente (`git status`
  no diretório do próprio projeto) antes de tentar `update` novamente. Esta
  ferramenta nunca faz force-reset de um checkout.

## 🚀 ROADMAP

- Um executável GUI autónomo empacotado (PyInstaller, seguindo a convenção
  `build_exe.bat`/`.sh` do próprio URTC-FLASHER/URTC-TESTER) para uma
  instalação com duplo clique, sem qualquer passo de `pip`/venv - a GUI de
  hoje ainda precisa primeiro de `./build.sh`, tal como o CLI.
- Verificação prévia opcional de dependências por projeto (indicar a falta de
  uma toolchain arm-none-eabi-gcc/Node antes de um `install` falhar a meio).
- Um modo de saída `--json` para `status`, para uso em scripts.
- Acompanhamento por componente do firmware multi-binário do próprio URTC
  (ver a "simplificação conhecida" na secção 3), quando houver uma
  necessidade real para além do único componente representativo que é
  acompanhado hoje.

## 🔗 Projetos Relacionados

O **URTC** (Universal Robot Tool Controller) é uma plataforma real de troca de ferramentas física do mesmo autor (JuanenRac / Electro Hobby 3D). Cada repositório tem a sua própria versão, os seus próprios testes e o seu próprio README; esta é a família completa:

- **[URTC](https://github.com/JuanenRac/URTC)** — firmware da PCB física do Universal Robot Tool Controller, mais de 25 perfis de ferramenta sobre barramento CAN.
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — ferramenta desktop com GUI para gravar placas URTC, CAN-OTA mais SWD/JTAG de chip completo.
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — firmware de um rack de montagem de placas com descodificação real do ID da ferramenta e lógica de pré-aquecimento Smart Idle.
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — ferramenta desktop de diagnóstico em direto do barramento CAN para placas URTC, um painel por perfil de ferramenta.
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — firmware mais um companheiro de visão real em Python para uma cabeça de ferramenta de inspeção térmica/RGB.
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — alternativa baseada em navegador ao URTC-TESTER através da Web Serial API, sem necessidade de instalação local.
- **URTC-UPDATER** (este repositório) — deteta, instala e atualiza os repositórios do próprio ecossistema.

O design desta ferramenta (deteção por manifesto, instalação/atualização atómica por verificação, registo de evidência) é partilhado com o **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** e o **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** - os atualizadores do mesmo autor para os ecossistemas HYDRA-UMC e A.R.M.O.R., cada um limitado apenas aos seus próprios repositórios.

---

## 📚 Documentação e Comunidade

- **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — todos os subcomandos de `--cli`, saída real capturada de uma execução instalada e o contrato de códigos de saída.
- **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — como o cliente desktop Qt Quick/QML está estruturado e como continua a ser uma superfície de controlo real sobre o mesmo backend que o `--cli` usa, em vez de uma segunda implementação.
- **[Changelog deste repositório](CHANGELOG.md)**
- Perguntas, ideias e relatórios: electrohobby3d@gmail.com

## 👤 AUTOR
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENÇA

GPL-3.0-or-later - ver [LICENSE](LICENSE).
