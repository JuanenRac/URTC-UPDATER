<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="Banner do URTC-UPDATER" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | 🇵🇹 <b>Português</b></p>

### 📦 Detetar, Instalar e Atualizar Manualmente Todo o Ecossistema URTC

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
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

---

**Verificação de honestidade - o que realmente funciona hoje:** **Maturidade: estabelecido (uma execução completa documentada, não uma utilização continuada).** Este projeto adapta o desenho já comprovado do HYDRA-UMC-UPDATER (a mesma deteção por manifesto, a instalação/atualização com clone temporário verificado de forma atómica e o registo de evidências) apenas aos repositórios do ecossistema URTC. Foi executado de ponta a ponta contra o GitHub numa área de trabalho isolada: uma instalação limpa e uma atualização posterior de um repositório real foram clonadas, compiladas e promovidas corretamente, ficando a cópia anterior guardada como cópia de segurança. A lógica de deteção e de versões (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), o cliente de conteúdo raw do GitHub com retry/backoff e lista de repositórios em cache (`github_client.py`), a comparação por commit (`commits.py`) e o pipeline clonar-preparar-verificar-promover (`install.py`) estão cobertos por testes (`python -m pytest`), incluindo um servidor HTTP de teste local e repositórios git temporários reais com um remoto bare local. A lógica própria da ponte Qt corre sem ecrã nos testes, e a janela com os seus diálogos é carregada sem ecrã para verificar que abre e responde; o seu aspeto verifica-se à vista, não com um teste. A cobertura de 8 idiomas do `i18n.py` é verificada por teste quanto a chaves e marcadores, não quanto à qualidade da tradução. Consulte o `CHANGELOG.md` para saber exatamente o que foi entregue até agora.

---

> **Estado de segurança (safety e security):** este ecossistema não é um sistema de segurança certificado e ainda não existe nenhuma placa URTC montada. Os bootloaders verificam as imagens de firmware com CRC32 e um HMAC-SHA256 de chave partilhada, não com uma assinatura assimétrica (prevista); as imagens de aplicação publicadas estão assinadas com a chave pública de desenvolvimento (`signing_key_kind: dev`), pelo que qualquer pessoa pode produzir uma imagem que o bootloader aceita; nada foi transmitido a uma placa real. Leia a [base de segurança](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) e o [modelo de ameaças](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md) antes de confiar em qualquer afirmação aqui para a segurança de uma pessoa.

## 📋 Num relance

| | |
|---|---|
| Versão | `0.2.0` |
| Maturidade | Estabelecido |
| Testes | 482 (`python -m pytest`) |
| Tecnologia | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Destino | O PC de quem o usa |
| Em hardware real | Não aplicável: nada aqui corre em hardware |

**Ir para:** [Visão geral](#-visão-geral) · [Arquitetura](#-arquitetura) · [Segurança](#-segurança-e-proteção) · [Interfaces](#-interfaces) · [Início rápido](#-início-rápido) · [Testes](#-testes) · [Problemas](#-resolução-de-problemas) · [Estrutura](#-estrutura-do-repositório) · [Relacionados](#-projetos-relacionados)

<!-- urtc-section:status_updater -->
## 🚦 Estado do projeto

🟢 feito e verificado · 🟡 funciona, com limites conhecidos · 🟠 a meio ou por verificar · 🔴 por fazer ou a não funcionar. Nada é verde se nunca correu em hardware real.

| Parte | Estado | O que o repositório consegue demonstrar |
| --- | :---: | --- |
| Software | 🟡 | Funciona num PC e contra o simulador; nunca foi usado com uma placa real. |
| Interface | 🟡 | A janela funciona e é verificada contra uma placa simulada; não foi experimentada com um adaptador real. |
| Testes | 🟢 | A bateria de testes passa na CI em cada envio. |
| Atualizações | 🟡 | Instala a partir de pacotes assinados com retrocesso; experimentado só num PC. |
| Segurança | 🟡 | As versões são assinadas com Ed25519 e verificadas antes de usar; o tratamento das chaves não foi revisto por mais ninguém. |
| Documentação | 🟡 | README em oito línguas e documentos de referência; as traduções não foram revistas por falantes nativos. |

<!-- /urtc-section:status_updater -->

## 🎯 Visão geral

O URTC-UPDATER é uma pequena ferramenta - GUI em janela por predefinição, CLI
completo com `--cli` - pensada para correr na máquina Windows/Linux/macOS do
próprio programador (qualquer workspace obtido da mesma forma) e que responde
a três perguntas sobre cada outro projeto real que deteta através do
manifesto `urtc.project.json` do respetivo checkout irmão - o número em si
nunca está fixado aqui, pois cresce com o ecossistema:

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

Executar `urtc-updater` sem argumentos (ou fazer duplo clique) abre a mesma
informação numa superfície de controlo desktop escura: um painel **Local
Ecosystem** com métricas de deteção/instalação/atualização em direto, uma
árvore **Project Registry** orientada por manifesto e um painel **Safe
Update** para o projeto selecionado. O layout torna visíveis as proteções
reais: deteção por manifesto, uma única ação explícita sobre um projeto,
confirmação manual, build opcional e um rasto de atividade no ecrã; o registo completo também é escrito num ficheiro em `~/.urtc_updater/logs` (ficam os 20 mais recentes).

## 🧩 Papel no URTC

O URTC-UPDATER é o programa que mantém atualizado um PC com os repositórios URTC. Encontra cada projeto junto de si pelo manifesto que cada repositório traz, diz que versão está instalada e qual tem o GitHub, e instala ou atualiza um projeto de cada vez depois de uma confirmação explícita, executando o script `build-test` desse projeto e sem compilar nada por si. Não altera nada por iniciativa própria: uma célula de controlo de robôs nunca deve atualizar-se de madrugada sem que uma pessoa aprove a ação exata. Também instala os programas de secretária (o gravador, o testador e ele próprio) a partir do pacote assinado da sua release, e pode entregar ao URTC-FLASHER, que faz a gravação, uma imagem de firmware cuja assinatura de release verificou.

## 🏛️ Arquitetura

<p align="center">
  <img src="images/architecture.svg" alt="Arquitetura de URTC-UPDATER: quem o usa, o que contém e de que depende" width="100%">
</p>

Como as partes deste repositório se encaixam: quem o usa, o que contém e de que depende. A imagem é desenhada a partir de `docs/architecture.json` e verificada com o código.

### COMO FUNCIONA REALMENTE UMA VERIFICAÇÃO/ATUALIZAÇÃO

- **Fonte da versão**: a versão de um projeto vive num ficheiro de código desse projeto (`pyproject.toml`, `Cargo.toml`, `version.go`, `package.json`, `version.properties`, `pubspec.yaml` ou um `#define` de firmware, consoante a tecnologia) que o seu próprio passo `bump.py` escreve, e esse passo nunca criou uma etiqueta git nem uma Release do GitHub. Por isso esta ferramenta lê esse mesmo ficheiro diretamente do ramo predefinido do repositório através do servidor de conteúdo bruto do GitHub, e não pela API de Releases, que diria que nenhum projeto tem releases.
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
  `<name>.backup-xxxxxxxx`, não apagada) se essa compilação de staging for bem-sucedida.
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
  checkout `.backup-xxxxxxxx` mantido.
  Em ambos os casos executa o `build-test.sh`/`build-test.bat` do próprio
  projeto (a verificação sem versionamento - ver secção 3) que ele realmente
  tiver. Esta ferramenta nunca reimplementa os passos de build de um projeto.

### ARQUITETURA E DECISÕES DE DESIGN

- **GUI Qt Quick por predefinição, `--cli` para modo sem ecrã.** `main.py`
  verifica `--cli` antes de importar o runtime opcional PySide6, pelo que o
  modo CLI funciona numa máquina genuinamente sem ecrã, sem display nem
  dependência de desktop. A invocação simples inicia o cliente QML onde o
  runtime estiver instalado; a antiga shell Tkinter permanece apenas como
  alternativa temporária de compatibilidade.
- **A GUI em janela é real e fala 8 idiomas (`i18n.py`) - o `--cli` deliberadamente não.** Cada widget, e o texto de cada ponto de controlo e de cada falha de uma instalação ou atualização, aparece no idioma escolhido num seletor (en/es/fr/it/de/zh/ja/pt, português de Portugal para pt), obtido de uma preferência guardada ou da configuração regional do sistema. Os passos de instalação e atualização viajam como códigos de mensagem mais parâmetros e só a janela os transforma em texto, pelo que mudar de idioma os volta a desenhar. Os nomes de projeto e de família e os textos `notes`/`tech` de cada projeto não são traduzidos: o manifesto é a sua única fonte de verdade. A saída do `--cli` fica em inglês de propósito, porque se destina a scripts e pipes.
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
- **Sem lógica de build por stack nesta ferramenta.** O ecossistema abrange várias toolchains (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, firmware ARM). Reimplementar aqui o build de cada projeto criaria um segundo sítio que diz saber compilá-lo, condenado a divergir do script do próprio projeto. O `install.py` executa antes o `build-test.sh` sem versionamento do próprio projeto (`build-test.bat` no Windows) e falha de forma segura se uma cópia não o tiver. Os scripts de build que aumentam a versão (`build.sh` e semelhantes) nunca são executados por esta ferramenta.
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
- **Simplificação conhecida:** um repositório formado por vários binários com versão independente (o URTC tem quatro: principal e escravo, aplicação e bootloader) é acompanhado por UMA só versão, a que o seu próprio `urtc.project.json` declara em `native_version`. Isso responde a "este repositório está mais ou menos atualizado?", não substitui a verificação de versão por componente de uma gravação.

<!-- urtc-section:updates -->
### Como se atualiza

Este programa pode procurar uma versão mais recente de si próprio: o botão «Procurar atualizações» pergunta uma vez ao GitHub e só propõe um pacote assinado se for para o seu sistema e mais recente. Nada é verificado nem instalado por si só, a não ser que ative a verificação, e uma atualização precisa da sua confirmação. O pacote tem de coincidir com o seu SHA-256 e com a assinatura da chave das versões fixada no programa; a versão anterior é guardada e reposta sozinha se a nova não arrancar. `urtc-updater --cli package list|check|install|rollback` faz o mesmo na linha de comandos para o flasher e o tester, e `install --file` funciona sem rede.
<!-- /urtc-section:updates -->

## 🖼️ Capturas de ecrã

<!-- urtc-shots -->
Capturadas a 1920×1080 numa bancada de testes, com dados de exemplo e sem qualquer instalação real por trás.

<table>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/deck.png" alt="A janela sobre uma área de trabalho com a família: cada projeto com a sua maturidade, pilha e versão local, e as ações de atualização segura." width="100%"><br><sub>A janela sobre uma área de trabalho com a família: cada projeto com a sua maturidade, pilha e versão local, e as ações de atualização segura.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/packages.png" alt="A janela de Pacotes: os programas da família que uma versão publica como pacote assinado, cada um a verificar a sua própria versão." width="100%"><br><sub>A janela de Pacotes: os programas da família que uma versão publica como pacote assinado, cada um a verificar a sua própria versão.</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/help.png" alt="A janela de Ajuda: os passos para utilizar o programa, escritos no idioma da janela." width="100%"><br><sub>A janela de Ajuda: os passos para utilizar o programa, escritos no idioma da janela.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/updates.png" alt="A janela de atualizações: um pacote assinado mais recente só é instalado depois de o confirmar." width="100%"><br><sub>A janela de atualizações: um pacote assinado mais recente só é instalado depois de o confirmar.</sub></td>
</tr>
</table>
<!-- /urtc-shots -->

Estas imagens são a janela real, desenhada sem ecrã tal como abre (nada verificado, nada instalado). O guia percorre a janela, a ajuda, a janela de atualização e a dos pacotes, e mostra-as nas oito línguas do programa.

[Guia com imagens](docs/WINDOW_GUIDE.md)

## 🔒 Segurança e proteção

| Ameaça | Defesa |
|---|---|
| Uma atualização que ninguém aprovou, por exemplo de madrugada numa célula de robôs | Nada muda por si: uma ação sobre um projeto precisa de confirmação explícita, um lote é confirmado à parte e corre um projeto de cada vez |
| Uma atualização avariada ou a meio deixa inutilizável uma instalação que funcionava | O candidato é clonado, fundido em avanço rápido (nunca um reinício forçado, pelo que as edições locais falham de forma visível) e compilado primeiro num clone de preparação; a instalação em uso só é substituída, com duas mudanças de nome de pasta, se essa compilação passar, e a anterior fica guardada como `<nome>.backup-xxxxxxxx` |
| Uma verificação que aqui não pode ser executada | Um build-test que responde 75 significa que a validação não está disponível: a atualização é recusada, a não ser que a pessoa a aceite nas definições |
| Um commit que ninguém assinou | Uma revisão sem assinatura válida é instalada com um aviso; com `"signature_policy": "require"` é recusada |
| Um pacote adulterado | Um pacote só é aceite se o tamanho, o SHA-256 e a assinatura Ed25519 coincidirem e vier dos servidores de transferência do GitHub; só é instalado depois de uma confirmação, nunca enquanto outra instalação corre, e a versão anterior pode ser restaurada |
| Perde-se o rasto do que foi feito | Cada instalação, atualização e restauro é escrito, com hora, máquina e utilizador, num registo encadeado por hashes |

O resto da política segue, com as palavras do programa.

**O que o build-test pode responder:** o código de saída 0 significa validado e qualquer outro significa falhado, exceto o 75, que significa que a validação está *indisponível* (falta uma ferramenta de que precisa). É comunicado como tal e a atualização é recusada, a não ser que a aceite definindo `validation_unavailable` como `accept` nas definições (ou `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). Um build-test deve deixar a árvore como a encontrou: se alterar um ficheiro que o git segue, o ficheiro volta ao conteúdo confirmado antes da promoção e os passos dizem qual.

**Commits assinados (por defeito apenas avisa; exigi-los é opcional e está desativado por defeito):** uma revisão sem assinatura válida (`git verify-commit`: porta-chaves GPG, ou SSH com `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) é instalada na mesma, e os passos da janela e da linha de comandos dizem que não está assinada. Com `"signature_policy": "require"` em `~/.urtc_updater_settings.json` (ou `URTC_UPDATER_REQUIRE_SIGNED=1`; o antigo `"require_signed_commits": true` significa o mesmo) o candidato - o `HEAD` de um clone novo ou o `FETCH_HEAD` descarregado de uma atualização - tem de passar `git verify-commit` antes de ler o seu manifesto ou construir o que quer que seja, e um candidato recusado deixa intacto o checkout instalado.

**Opções de segurança (ambas desativadas por predefinição; alteráveis no botão Segurança da janela, no comando `security`, no ficheiro de definições, no ambiente e na linha de comandos):** além de exigir commits assinados, o atualizador pode *perguntar antes de executar a verificação de compilação* de um candidato (`"confirm_before_build": true`, `URTC_UPDATER_CONFIRM_BUILD=1`, `--confirm-build`). Obtém e valida o candidato, mostra o projeto, o commit, o seu autor, a sua assinatura e os scripts de compilação ou de ferramentas que mudaram, e não executa nada até responder; sem janela nem terminal a quem perguntar, não executa nada (`--yes` responde pelos scripts). `--require-signed` / `--no-require-signed` e `--confirm-build` / `--no-confirm-build` valem para uma só execução, e uma execução que desativa uma proteção ativa nas definições guardadas di-lo; a janela, e `urtc-updater --cli security --require-signed off`, pedem confirmação antes de guardar um nível mais baixo. Um ficheiro de definições que existe mas não pode ser lido conta como «assinaturas exigidas» até ser reparado ou removido. À verificação de compilação é também indicado `URTC_PYTHON`, o interpretador que executa o atualizador, de modo que o projeto testa com esse Python e não com o primeiro que o sistema encontre.

## 🔌 Interfaces

O programa abre a janela Qt Quick quando é executado sem argumentos e tem uma linha de comandos completa com `--cli` (não precisa de ecrã nem de PySide6): `status [--offline]`, `install PROJETO`, `update PROJETO [--preview]`, `restore-backup PROJETO [--list]`, `clean-backups [--keep N] [--dry-run]`, `check [--notify] [--quiet]` (código de saída 10 quando algo pode ser atualizado), `package list|check|install|rollback`, `evidence [--export FILE]` e `security`. Cada comando, opção e código de saída, com saída real, está em [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md); a janela é descrita em [docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md). O que fazem os comandos de manutenção e de posto:

- **Instalações anteriores guardadas.** Cada atualização guarda a instalação que substituiu em `<nome>.backup-xxxxxxxx`. Ficam as 2 mais recentes por projeto (`"backups_to_keep"` em `~/.urtc_updater_settings.json` altera o número) e as mais antigas são removidas após uma atualização bem-sucedida. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` remove-as quando pedido, juntamente com qualquer pasta temporária oculta deixada por uma execução interrompida.
- **Opcionalmente, instalação a partir do pacote assinado de uma versão.** `urtc-updater --cli package list|check|install|rollback` instala um programa (o flasher, o tester ou este updater) a partir do `.zip` / `.tar.gz` da sua versão, em vez de um clone e uma compilação. Só se propõe uma versão estritamente superior, só dos anfitriões de transferência do GitHub, e o pacote tem de coincidir com o tamanho e o SHA-256 anunciados e com a assinatura Ed25519 da chave das versões fixada no programa; um pacote que falhe uma verificação é eliminado. Pergunta antes de instalar (`--yes` responde para scripts), guarda as duas versões mais recentes e `rollback` volta à anterior. `install --file PACOTE` funciona a partir de um ficheiro no disco com o `.sha256` e o `.sig` ao lado, sem rede. A janela tem um botão «Procurar atualizações» para o próprio updater com as mesmas regras; a verificação automática ao arrancar é uma opção, desligada por defeito. Testado com pacotes gerados num computador, ainda não com uma release publicada.
- **Uma janela de Pacotes e uma de Ajuda.** O botão «Pacotes» lista os pacotes assinados do flasher, do tester e deste atualizador: cada linha verifica a sua versão quando carrega em «Procurar atualizações», transfere e verifica o pacote, pergunta antes de instalar e volta à versão anterior, com as mesmas regras e opções de segurança do comando `package`; não se instala nada enquanto um projeto estiver a ser instalado ou atualizado. O botão «Ajuda» abre um guia de cinco passos na língua da janela.
- **Restaurar uma.** `urtc-updater --cli restore-backup <PROJETO> [--backup PASTA] [--list]` repõe uma instalação guardada. A instalação que é substituída também fica guardada, pelo que a troca pode ser desfeita. A janela oferece as mesmas duas ações junto a Atualizar selecionado: Pré-visualizar a atualização (o que traria, sem alterar nada) e Restaurar a versão anterior.
- **Mesma versão, commits novos.** A versão só muda num build de lançamento, por isso o `status` também compara o commit de cada projeto instalado com o remoto (`git ls-remote`) e mostra `NEW COMMITS` quando o GitHub tem trabalho que a cópia não tem. A janela mostra o mesmo estado e oferece a atualização.
- **Ver antes de aprovar.** `urtc-updater --cli update <PROJETO> --preview` obtém o candidato e mostra o seu commit, autor, versão, estado da assinatura e os ficheiros de build ou de ferramentas que altera, sem tocar na cópia.
- **Só avisar.** `urtc-updater --cli check [--notify] [--quiet]` lista o que poderia ser atualizado e não altera nada. Termina com o código 10 quando há algo para atualizar, para que uma tarefa agendada avise uma pessoa; `--notify` mostra também uma notificação no ambiente de trabalho.
- **Evidências.** Cada instalação, atualização e restauro é registado com hora, máquina e utilizador em `.urtc-updater/evidence.jsonl`, com cada linha encadeada à anterior por hash. `urtc-updater --cli evidence [--export FICHEIRO]` verifica a cadeia e pode exportá-la como um único documento JSON.
- **Perfis de estação.** `"profiles"` no ficheiro de definições indica os projetos com que uma máquina trabalha e se são permitidos lotes; `--profile NOME` (ou `"profile"` nas definições) restringe `status`, `check`, `install` e `update` a esse perfil, e a janela segue o mesmo perfil.

## 🚀 Início rápido

```bash
chmod +x build.sh   # uma só vez
./build.sh          # cria o .venv, pip install -e ., verifica a compilação de tudo
./run.sh                              # interface gráfica com janela (por defeito)
./run.sh --cli status                 # o que está instalado, versão local vs. do GitHub
./run.sh --cli status --offline       # o mesmo, sem consultar o GitHub
./run.sh --cli install <PROJECT-NAME> # clona + compila um projeto ainda não instalado
./run.sh --cli update  <PROJECT-NAME> # atualiza + recompila um projeto já instalado
```

No Windows: `build.bat` e depois `run.bat` (GUI) / `run.bat --cli status` /
`run.bat --cli install <name>` / `run.bat --cli update <name>`.

A GUI preferida precisa do runtime Qt opcional (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` já o instalam). O `--cli` não tem dependência de GUI e
é o ponto de entrada correto para uma máquina sem ecrã. Se o Qt não estiver
disponível, a antiga shell Tkinter é apenas uma alternativa de
compatibilidade.

<!-- urtc-section:compatibility -->
### Requisitos e compatibilidade

As versões dos programas URTC que funcionam em conjunto, e a versão do protocolo que cada uma fala, constam da tabela de compatibilidade que o URTC-COMMON gera: [docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md).
<!-- /urtc-section:compatibility -->

## 🧪 Testes

O conjunto tem 482 testes (`QT_QPA_PLATFORM=offscreen python -m pytest tests -q`; alguns são ignorados quando falta uma dependência opcional): a deteção e os manifestos, o analisador de versões único, o cliente do GitHub contra um servidor local (repetições, erros, um catálogo mal formado), instalação e atualização em repositórios git locais reais (preparação, promoção, cópia de segurança, recusas, um build-test que responde 75, segurança da área de trabalho), restaurar e limpar cópias, a política de commits assinados, as opções de segurança, os pacotes assinados e a sua reversão, a cadeia de provas, as definições e perfis, os textos da janela nos oito idiomas e a ponte Qt, e as imagens do guia da janela, desenhadas sem ecrã. `python -m mypy` e `ruff check .` correm na CI.

## 🏗️ Compilação e publicação

`build.sh` / `build.bat` criam o `.venv`, instalam o pacote (`pip install -e .`, com o ambiente Qt para a janela) e verificam a compilação de tudo; `build-test.sh` / `build-test.bat` verificam sem instalar; `run.sh` / `run.bat` abrem a janela, ou a linha de comandos com `--cli`; `run-gui.vbs` abre-a no Windows sem janela de consola. Ainda não se constrói um executável autónomo empacotado.

## 🩺 Resolução de problemas

- `status` mostra `?` na versão do GitHub de um projeto: não foi possível ler o GitHub para ele. A coluna STATE diz porquê (por exemplo `installed, GitHub unknown (HTTP 404)` ou um aviso de limite de pedidos).
- `status` mostra `-` no GitHub sem nenhum erro: execute `status`
  (sem `--offline`) - `-` só aparece quando a verificação do GitHub foi
  totalmente ignorada.
- `install`/`update` falha com "No non-versioning build-test.sh/.bat found": essa cópia não tem `build-test.sh` (`build-test.bat` no Windows). Atualize o próprio projeto ou verifique-o manualmente; esta ferramenta nunca executa em vez disso um script de build que aumente a versão.
- `git pull --ff-only` falha: o checkout local tem alterações por
  submeter ou um histórico divergente - resolva-o manualmente (`git status`
  no diretório do próprio projeto) antes de tentar `update` novamente. Esta
  ferramenta nunca faz force-reset de um checkout.

## 📂 Estrutura do repositório

<p align="center">
  <img src="images/repository-structure.svg" alt="Estrutura do repositório URTC-UPDATER" width="100%">
</p>

<details>
<summary>Versão em texto da árvore</summary>

```text
URTC-UPDATER/
├── src/urtc_updater/                                  o programa: deteção, versões, instalação e atualização, segurança, pacotes assinados, a janela Qt Quick e os seus textos em oito idiomas
├── tests/                                             testes reais de cada módulo
├── docs/                                              referência de comandos, interface e guia da janela
├── tools/                                             verificação de compilação, capturas, ícone e ferramentas partilhadas
├── images/                                            faixa e imagens deste README
├── .github/                                           fluxo de CI e modelos de issues e pull requests
├── build.sh build.bat                                 scripts de compilação
├── build-test.sh build-test.bat                       scripts de compilação e testes que não alteram nada no repositório
├── test.sh test.bat                                   executam os testes
├── run.sh run.bat                                     arrancam o programa
├── urtc.project.json                                  manifesto: versão, papel, maturidade e comando de compilação
├── CHANGELOG.md                                       o que mudou em cada versão
├── SECURITY.md SUPPORT.md LICENSE                     política de segurança, suporte e licença
├── CONTRIBUTING.md CODE_OF_CONDUCT.md                 como contribuir e código de conduta
├── .gitattributes .gitignore                          definições do Git
├── run-gui.vbs                                        lançador do Windows sem janela de consola
├── bump.py bump_version.py bump_manifest_version.py   scripts que sobem a versão
├── urtc_i18n.lock.json                                bloqueio dos textos da janela
├── LICENSE.md .env.example                            licença da documentação e variáveis
└── pyproject.toml requirements-dev.lock ruff.toml     pacote, ferramentas fixadas, definições de lint e o bloqueio dos textos
```

</details>

A lista anotada de cada ficheiro de código, uma linha por ficheiro, está em [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md).

## 🗺️ Roteiro e limites conhecidos

- Um executável GUI autónomo empacotado (PyInstaller, seguindo a convenção
  `build_exe.bat`/`.sh` do próprio URTC-FLASHER/URTC-TESTER) para uma
  instalação com duplo clique, sem qualquer passo de `pip`/venv - a GUI de
  hoje ainda precisa primeiro de `./build.sh`, tal como o CLI.
- Verificação prévia opcional de dependências por projeto (indicar a falta de
  uma toolchain arm-none-eabi-gcc/Node antes de um `install` falhar a meio).
- Acompanhamento por componente do firmware multi-binário do próprio URTC
  (ver a "simplificação conhecida" na secção 3), quando houver uma
  necessidade real para além do único componente representativo que é
  acompanhado hoje.

## 🌍 Idiomas

O README e os textos existem em inglês, espanhol, francês, italiano, alemão, chinês, japonês e português europeu.

## 🔗 Projetos relacionados

O URTC é feito de repositórios independentes, cada um com a sua versão, os seus testes e o seu README. Esta é a família, por grupos:

* **URTC Tool Platform:**
  * [URTC](https://github.com/JuanenRac/URTC) - firmware da placa da cabeça de ferramenta (25 perfis de ferramenta, bootloader CAN) e a referência do protocolo CAN.
  * [URTC-COMMON](https://github.com/JuanenRac/URTC-COMMON) - o protocolo CAN escrito uma só vez como dados (especificação, tabelas geradas, vetores de conformidade) e o código que os programas partilham.
  * [URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER) - ferramenta de ambiente de trabalho que atualiza o firmware da placa por CAN ou por SWD/JTAG.
  * [URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY) - gateway à frente do barramento CAN: só deixa passar os identificadores de uma lista, limita a sua taxa e pede uma chave de sessão.
  * [URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK) - lógica em C independente do hardware e protocolo de comandos para um suporte de ferramentas com pré-aquecimento e acompanhamento do ciclo de vida.
  * [URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER) - testador de ambiente de trabalho do barramento CAN em direto que mostra os controlos e a telemetria do perfil de ferramenta que uma placa reporta.
  * [URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL) - protocolo de tramas de sensor em C e um companheiro em Python térmico/RGB para uma cabeça de ferramenta de inspeção.
  * [URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO) - aplicação de navegador que grava e testa a placa por Web Serial e SLCAN, sem instalar nada.
* **Ecosystem Operations:**
  * [URTC-DEVTOOLS](https://github.com/JuanenRac/URTC-DEVTOOLS) - as ferramentas de repositório partilhadas da família como um conjunto com versão e um ficheiro de bloqueio que distingue uma cópia editada de uma desatualizada.
  * [URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS) - arquitetura, interfaces, base de segurança e catálogo gerado do ecossistema, mais as ferramentas que comparam todos os repositórios.
  * **URTC-UPDATER** (este repositório) - ferramenta de ambiente de trabalho que deteta, instala e atualiza os repositórios da família URTC, uma ação explícita de cada vez.

**Projetos irmãos (independentes, com a mesma base e as mesmas ferramentas):**

* **[HYDRA-UMC-DOCS](https://github.com/JuanenRac/HYDRA-UMC-DOCS)** - projeto irmão: o centro de documentação do HYDRA-UMC, um ecossistema independente que partilha a base e as ferramentas com este
* **[ARMOR-DOCS](https://github.com/JuanenRac/ARMOR-DOCS)** - projeto irmão: o centro de documentação do A.R.M.O.R., o ecossistema de segurança, também independente e sobre a mesma base
* **[JuanenRac](https://github.com/JuanenRac/JuanenRac)** - o perfil e o painel de estado de todos os ecossistemas

## 📚 Documentação

- **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — todos os subcomandos de `--cli`, saída real capturada de uma execução instalada e o contrato de códigos de saída.
- **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — como o cliente desktop Qt Quick/QML está estruturado e como continua a ser uma superfície de controlo real sobre o mesmo backend que o `--cli` usa, em vez de uma segunda implementação.
- **[Changelog deste repositório](CHANGELOG.md)**
- Perguntas, ideias e relatórios: electrohobby3d@gmail.com

## 🤝 Contribuir e comunidade

* Antes de um pull request execute `URTC_CI=1 python tools/ci_validate.py`: tem de passar. Veja [CONTRIBUTING.md](CONTRIBUTING.md) e o [código de conduta](CODE_OF_CONDUCT.md).
* O README existe em oito idiomas: uma alteração ao texto faz-se nos oito ficheiros, e as secções partilhadas com outros repositórios são escritas por `tools/readme_sections.py` do URTC-COMMON.
* Uma alteração ao protocolo CAN começa no URTC-COMMON (`spec/can_protocol.json`) e chega a este repositório através da cópia verificada.
* Não descreva como a funcionar numa placa aquilo que só foi compilado.
* Comunique uma vulnerabilidade em privado: [SECURITY.md](SECURITY.md). Perguntas, ideias e relatórios: electrohobby3d@gmail.com ([SUPPORT.md](SUPPORT.md)).

## 👤 AUTOR

**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENÇA

GPL-3.0-or-later - ver [LICENSE](LICENSE).
