<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | 🇫🇷 <b>Français</b> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a></p>

### 📦 Détecte, installe et met à jour à la main tout l'écosystème URTC

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="stdlib-only CLI core">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="PySide6 Qt Quick desktop GUI">
</p>

> **Mode bureau visuel :** l'interface bureau par défaut utilise maintenant
> **Qt Quick / QML** avec le runtime GUI optionnel `PySide6`. Le cœur et le
> mode `--cli` restent uniquement basés sur la bibliothèque standard pour une CM5 headless.
>
> **Démarrage Windows et preuves :** ouvrez `run-gui.vbs` (ou `run.bat` sans
> argument) pour le client graphique sans console. Le panneau de mise a jour
> affiche les étapes réelles de contrôle, source, manifeste, build-test et fin
> avec les preuves capturées ; `run.bat --cli ...` conserve le terminal de diagnostic.
> Installer n'est actif que sans checkout et Mettre à jour seulement si GitHub
> est plus récent. Pendant une action approuvée, les checkpoints remplacent les
> contrôles du projet ; choisir un autre projet les restaure.
> **Installer tous les manquants** et **Mettre à jour tous les dépassés** sont
> des actions par lot séquentielles, confirmées séparément et fondées sur le
> même état réel et parcours de sécurité.

**Vérification d'honnêteté - ce qui fonctionne réellement aujourd'hui :** la logique de découverte/version à l'échelle de l'écosystème (`registry.py`, `project_manifest.py`, `ecosystem_catalog.py`, `version_parse.py`, `detect.py`), le vrai client GitHub raw-content avec retry/backoff (`github_client.py`), et la logique clone-prépare-vérifie-promeut du pipeline d'installation/mise à jour (`install.py`) sont réels et testés - 64 tests qui passent (`pytest tests/`), y compris un serveur HTTP fictif prouvant l'isolation entre un catalogue malformé et un seul projet malformé, plus de vrais aller-retours de clonage/build git dans des répertoires temporaires. `--cli status`/`install`/`update` font tourner ce même noyau testé de bout en bout contre le vrai hôte GitHub raw-content en direct (pas un mock) chaque fois que vous les exécutez réellement. La GUI de bureau Qt Quick (`qt_gui.py`, `qml/Main.qml`) et le repli Tkinter hérité (`gui.py`) branchent ce même noyau testé sur une vraie fenêtre et ont été exécutés sur de vrais checkouts de l'écosystème, mais aucun des deux n'a de test automatisé propre - aucun `test_gui.py`/`test_qt_gui.py` n'existe, car faire tourner une vraie boucle d'événements Qt/Tk n'est pas tenté ici. La couverture 7 langues de `i18n.py` est vérifiée par test (`test_i18n.py`), mais seulement pour la parité des clés entre langues, pas pour la qualité de la traduction. Voir `CHANGELOG.md` pour savoir exactement ce qui a été livré jusqu'à présent.

---

## 1. 🛠️ VUE TECHNIQUE

URTC-UPDATER est un petit outil - GUI avec fenêtre par défaut, CLI
complète avec `--cli` - destiné à tourner aussi bien sur le vrai CM5 que
sur la propre machine Windows/Linux/macOS d'un développeur (n'importe
quel workspace avec le même type de checkout) qui répond à trois
questions pour chaque autre projet réel qu'il découvre via le propre
manifeste `urtc.project.json` de chaque checkout voisin - le nombre
lui-même n'est jamais codé en dur ici, car il croît avec l'écosystème :

1. **Qu'est-ce qui est réellement installé ici, et dans quelle version ?**
2. **Quelle est la dernière version publiée sur GitHub ?**
3. **Si GitHub est plus récent, laisse-moi choisir un projet ou un lot séquentiel confirmé.**

Ce dernier point est délibéré et non négociable : cet outil ne modifie jamais
un projet de sa propre initiative. Une action sur un projet sélectionné exige
toujours une confirmation explicite. La GUI peut aussi proposer **Installer
tous les manquants** ou **Mettre à jour tous les dépassés** ; ce sont des lots
séquentiels confirmés séparément, soumis aux mêmes contrôles de manifeste, de
version et de sécurité. Il n'existe aucune mise à jour nocturne automatique.

Chaque projet découvert n'appartient pas non plus forcément au CM5 - la plupart des
dépôts préfixés URTC et quelques-uns de HYDRA-UMC sont des outils qu'un
développeur exécute depuis son propre PC (le firmware est compilé et
flashé DEPUIS un poste de travail, pas construit SUR la cellule), ou des
applications installées sur un téléphone/une montre. Le propre champ
`deploy` de `registry.py` enregistre lequel est lequel (voir section 3),
et le tableau de projets de la GUI filtre dessus - par défaut il
n'affiche que "CM5" quand il détecte tourner sous Linux (le propre OS du
vrai CM5), et "tout afficher" sous Windows/macOS.

Exemple illustratif (le nombre exact de projets et chaque numéro de
version ci-dessous sont inventés pour la forme de la sortie, pas une
exécution réellement capturée - le vrai nombre est toujours ce que
`registry.py` découvre aujourd'hui, jamais un chiffre figé dans ce
document) :

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

Lancer `urtc-updater` sans argument (ou double-cliquer dessus) ouvre
la même information dans une fenêtre - un tableau de projets, un filtre
par cible de déploiement, et des boutons Installer/Mettre à jour pour la
ligne sélectionnée.

<p align="center">
  <img src="images/" alt="Vue générale réelle du bureau URTC-UPDATER" width="100%">
</p>

## 2. 🔄 COMMENT FONCTIONNE VRAIMENT UNE VÉRIFICATION/MISE À JOUR

- **Source de la version** : la convention "compteur kilométrique"
  d'auto-incrémentation de cet écosystème (chaque build réel incrémente
  un numéro de version qui vit DANS un fichier source -
  `pyproject.toml`, `Cargo.toml`, `version.go`, `package.json`,
  `version.properties`, `pubspec.yaml`, ou un `#define` de firmware,
  selon la stack du projet) n'a jamais créé de tag git ni de GitHub
  Release pour cet incrément. Cet outil lit donc le MÊME fichier que le
  propre `bump_version.py`/script de build de chaque projet écrit déjà,
  directement depuis la branche par défaut du dépôt via l'hébergeur de
  contenu brut de GitHub - pas l'API des Releases, qui indiquerait que
  tous les projets n'ont aucune release.
- **Détection locale** : pour chaque projet découvert, vérifie si
  un répertoire portant ce nom exact existe sous la racine du workspace
  (la disposition standard de l'écosystème - chaque projet en tant que
  répertoire voisin, exactement ce que supposent déjà build-frontend.sh
  et la propre découverte de HYDRA-UMC-SUITE), et si oui, lit sa propre
  copie locale de ce même fichier de version.
- **Une seule implémentation d'analyse** (`version_parse.py`) est
  partagée entre la lecture locale et la récupération GitHub, donc un
  checkout local et une récupération GitHub ne sont jamais interprétés
  par deux regex pouvant diverger indépendamment.
- **Installer/mettre à jour** : `git clone` (installation) compile
  ensuite comme une étape séparée. Mettre à jour un checkout DÉJÀ
  EXISTANT est atomique-par-vérification à la place : le candidat est
  cloné, fusionné en fast-forward (jamais un reset forcé, donc de
  vraies modifications locales échouent bruyamment plutôt que d'être
  écrasées), puis construit/vérifié dans un clone de staging
  entièrement indépendant D'ABORD - l'installation réelle n'est touchée
  (via deux renommages de répertoire consécutifs, l'installation
  précédente étant conservée dans `<nom>.backup`, jamais supprimée) que
  si cette compilation de staging réussit vraiment. Un échec de
  compilation, un checkout divergent/sale, un plantage ou un disque
  plein à n'importe quel moment avant cette promotion finale laissent
  l'installation précédente complètement intacte et toujours
  opérationnelle - voir la docstring propre de `clone_or_pull` dans
  `install.py`. Le remote git propre du clone de staging est restauré
  vers le dépôt GitHub réel juste après sa création (un simple clone
  local le laisserait sinon pointer vers l'ancien chemin d'installation,
  mettant fin silencieusement à toutes les futures mises à jour une fois
  promu), et les données locales réelles propres au checkout installé
  (tout ce que git considère comme non suivi ou ignoré - `data/settings.json`
  et similaires, à l'exclusion des artefacts de build régénérables) sont
  transférées dans le clone de staging avant sa compilation, afin que
  l'état opérationnel réel d'un projet survive à une mise à jour au lieu
  de rester bloqué dans le checkout `.backup` conservé. Dans tous les cas, cela exécute le `build-test.sh`/
  `build-test.bat` propre à ce projet (la vérification non-versionnante
  - voir section 3) s'il en a un. Cet outil ne réimplémente jamais les
  étapes de build propres à un projet.

<p align="center">
  <img src="images/" alt="Checkpoints réels pendant une installation ou mise à jour URTC-UPDATER" width="100%">
</p>

## 3. 🧱 ARCHITECTURE ET DÉCISIONS DE CONCEPTION

- **GUI Qt Quick par défaut, `--cli` pour le headless.** `main.py` vérifie
  `--cli` avant d'importer le runtime PySide6 optionnel. La CLI fonctionne
  sur une CM5 sans écran ni dépendance desktop ; sans argument QML démarre
  lorsqu'il est disponible et Tkinter reste seulement un fallback temporaire.
- **L'interface graphique fenêtrée est réelle, multilingue en 7 langues (`i18n.py`) - `--cli` ne l'est délibérément pas.** Chaque widget réel se réétiquette en direct depuis un `Combobox` de langue (en/es/fr/it/de/zh/ja, les 7 mêmes que publient le tableau de bord public et chaque README), détecté à partir d'une préférence enregistrée ou de la locale propre du système d'exploitation. Les noms de projets/familles et le propre texte réel `notes`/`tech` de chaque projet restent non traduits - `registry.py` en est leur unique source de vérité, et 7 copies parallèles de documentation d'ingénierie réelle empêcheraient cela. La sortie de `--cli` reste volontairement en anglais uniquement : elle est destinée à être scriptée/redirigée, où un texte stable et grep-able compte plus que la localisation.
- **`deploy` est une classification, pas une restriction.** Traiter
  chaque projet découvert comme "une chose qui appartient au CM5" était une
  erreur - les dépôts de firmware sont compilés et flashés DEPUIS un PC
  (le CM5 n'a besoin que du binaire résultant via CAN-OTA, jamais du code
  source de ce dépôt), et plusieurs outils (URTC-FLASHER,
  HYDRA-UMC-SUITE, HYDRA-UMC-TOOL-CLI, ...) sont destinés à tourner sur
  le propre poste de travail d'un opérateur, pas dans la cellule
  elle-même. Le champ `deploy` de `registry.py` ("cm5" / "user-pc" /
  "mobile" / "wearable" / "dev-server") enregistre cela, et le filtre de la GUI l'utilise
  comme point de départ raisonnable - jamais comme une restriction dure,
  puisque cet outil est aussi destiné à tourner sur le propre PC d'un
  développeur, où chaque projet découvert est tout aussi légitime à inspecter.
- **Aucune logique de build par stack dans cet outil.** L'écosystème
  couvre 7 chaînes d'outils (Python, Rust, Go, Node/TS, Android/Kotlin,
  Flutter, firmware ARM). Réimplémenter `npm install && npm run build` /
  `cargo build --release` / `./gradlew assembleDebug` / etc. ICI créerait
  un second endroit prétendant savoir comment compiler chaque projet,
  garanti de diverger du `build.sh`/`.bat` réel (et déjà correct) de ce
  projet. `install.py` recherche plutôt un nom de script de build connu
  (`build.sh`, `build_firmware.sh`, `build_exe.sh`, `build-android.sh`,
  et leurs équivalents `.bat` - les noms réels utilisés à travers les
  propres projets découverts de l'écosystème) et exécute celui qui existe.
- **Contenu brut de GitHub, pas l'API des Releases.** Voir la section 2 -
  la convention de versionnage de cet écosystème ne crée jamais de
  tag/release, donc l'API des Releases serait activement fausse ici, pas
  seulement moins pratique.
- **Un échec réseau transitoire reçoit un vrai réessai ; une réponse
  définitive jamais.** Chaque requête GitHub réelle (`_urlopen_with_retries`
  de `github_client.py`) réessaie jusqu'à 3 fois avec un backoff, mais
  uniquement quand la connexion n'a jamais obtenu de réponse du tout
  (DNS/timeout/reset). Un statut HTTP réel que GitHub a effectivement
  renvoyé - 404, 403, 500 - n'est jamais réessayé : GitHub a déjà
  répondu, et insister ne ferait que consommer davantage de quota pour le
  même résultat.
- **Un catalogue distant malformé échoue bruyamment ; un seul projet
  malformé non.** Si le listing des dépôts GitHub lui-même est
  injoignable ou illisible, `discover_remote_projects()` lève une
  exception - `gui.py` et `main.py` la capturent déjà tous les deux et
  retombent sur la liste de projets découverts localement plutôt que
  d'afficher un scan cassé ou vide. Le manifeste malformé d'un seul dépôt,
  en revanche, est isolé dans la liste `errors` de ce scan et n'interrompt
  jamais la découverte du reste - un vrai test avec serveur de fixtures
  (`tests/test_github_client.py`) prouve les deux chemins.
- **La CLI reste explicite ; les lots GUI restent confirmés.** Les commandes
  CLI `install`/`update` prennent un nom de projet. La GUI peut exécuter
  **Installer tous les manquants** ou **Mettre à jour tous les dépassés**,
  uniquement après confirmation séparée et de façon séquentielle par les mêmes
  contrôles de sécurité. Aucune mise à jour automatique non surveillée n'existe.
- **Bibliothèque standard uniquement.** `urllib` pour les récupérations
  GitHub (`github_client.py`), `subprocess` pour les appels git/scripts
  de build (`install.py`), rien d'autre - qu'un outil responsable de
  maintenir saines les dépendances de TOUS les autres projets reste
  lui-même sans dépendances est délibéré.
- **Simplification connue** : HYDRA-UMC et URTC sont de vrais dépôts de
  firmware multi-composants (6 et 4 binaires versionnés indépendamment
  chacun - voir leur propre `VERSION_CHECKLIST.txt`/`build_firmware.sh`)
  sans numéro de version unique. `registry.py` suit UN composant
  représentatif par dépôt - suffisant pour répondre "ce dépôt est-il à
  peu près à jour ?", pas un remplacement du propre
  `firmware_manifest.json` de `build_firmware.sh` pour un vrai flashage.

## 📂 STRUCTURE DES RÉPERTOIRES

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - aucun catalogue statique ; construit au moment de la découverte depuis le manifeste propre de chaque dépôt
│   ├── project_manifest.py # Lit/valide un urtc.project.json propre au dépôt
│   ├── ecosystem_catalog.py # Parseur du catalogue public de découverte de l'écosystème JuanenRac
│   ├── version_parse.py   # UNE implémentation d'extraction regex, local+GitHub
│   ├── detect.py          # Scanne une racine de workspace pour ce qui est installé
│   ├── github_client.py   # Récupération concurrente du contenu brut + réessai/backoff réel pour les erreurs réseau transitoires
│   ├── install.py         # git clone/pull + délègue au script de build propre
│   ├── i18n.py             # Vraies traductions complètes de la GUI (7 langues)
│   ├── qt_gui.py           # Pont Qt Quick vers les services réels de découverte/mise à jour
│   ├── qml/Main.qml        # Shell desktop theme avec checkpoints et About
│   ├── gui.py              # Fallback Tkinter si PySide6 est indisponible
│   └── main.py             # Répartition : GUI par défaut, --cli pour status/install/update
├── tests/                  # Tests réels : github_client, i18n, install, project_manifest, registry
├── docs/
│   ├── CLI_REFERENCE.md     # Référence des commandes
│   └── QML_DESKTOP_GUI.md   # Architecture de la GUI Qt Quick
├── images/                 # Médias, icônes de l'app et captures de l'interface
├── tools/
│   ├── build_test.py        # Vérification de build sans versionnage
│   ├── ci_validate.py       # Validation manifeste/CHANGELOG/docs utilisée par CI
│   ├── generate_app_icon.py # Génère l'icône utilisée par Windows à partir du SVG public HYDRA-UMC
│   ├── migrate_project_manifests.py  # Audite un workspace après la migration ponctuelle des manifestes
│   └── validate_project_manifests.py # Valide les manifestes propres à chaque dépôt + les versions natives de build
├── .env.example            # Modèle de variables d'environnement
├── build.sh / build.bat    # venv + installation éditable + compile-check
├── run.sh / run.bat        # GUI par défaut / entrée CLI
├── run-gui.vbs             # Lanceur graphique Windows sans console
├── bump_version.py         # Incrément "compteur kilométrique" de l'écosystème (pyproject.toml + __init__.py)
└── bump_manifest_version.py # Synchronise la version de urtc.project.json avec la version native (--sync)
```

## ⚙️ COMPILATION ET EXÉCUTION

```bash
chmod +x build.sh   # une seule fois
./build.sh          # crée .venv, pip install -e ., compile-check de tout
./run.sh                              # GUI avec fenêtre (par défaut)
./run.sh --cli status                 # ce qui est installé, version locale vs. GitHub
./run.sh --cli status --offline       # pareil, sans vérifier GitHub
./run.sh --cli install <NOM-PROJET>   # clone + compile un projet pas encore installé
./run.sh --cli update  <NOM-PROJET>   # met à jour + recompile un projet déjà installé
```

Sous Windows : `build.bat`, puis `run.bat` (GUI) / `run.bat --cli status`
/ `run.bat --cli install <nom>` / `run.bat --cli update <nom>`.

La GUI préférée requiert le runtime Qt optionnel (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` l'installent déjà). `--cli` n'a pas de dépendance GUI et
convient à une CM5 headless. Sans Qt, l'ancienne fenêtre Tkinter reste un
fallback de compatibilité uniquement.

**Dépannage**

- `status` affiche `?` pour la version locale ou GitHub d'un projet : son
  fichier de version existe mais la convention de ce projet a changé
  depuis la dernière mise à jour de `registry.py` - vérifiez l'entrée de
  ce projet dans `registry.py` par rapport à son fichier de version réel
  actuel.
- `status` affiche `-` pour GitHub sans erreur affichée : lancez `status`
  (sans `--offline`) - `-` n'apparaît que quand la vérification GitHub a
  été complètement sautée.
- `install`/`update` échoue avec "No build.sh/.bat found" : ce projet
  utilise un nom de script de build que cet outil ne reconnaît pas encore
  - consultez son propre README pour le vrai nom, et envisagez de
  l'ajouter aux listes `BUILD_SCRIPT_CANDIDATES_*` propres à `install.py`.
- `git pull --ff-only` échoue : le checkout local a des modifications non
  commitées ou l'historique a divergé - résolvez cela manuellement (`git
  status` dans le répertoire propre du projet) avant de réessayer
  `update`. Cet outil ne force jamais un reset d'un checkout.

## 🚀 FEUILLE DE ROUTE

- Un exécutable GUI autonome packagé (PyInstaller, suivant la propre
  convention `build_exe.bat`/`.sh` de HYDRA-UMC-SUITE) pour une
  installation en double-clic sans aucune étape `pip`/venv - aujourd'hui
  la GUI a encore besoin de `./build.sh` d'abord, comme la CLI.
- Vérification préalable optionnelle des dépendances par projet
  (signaler les chaînes d'outils manquantes - pas de Rust/Go/SDK
  Android/Flutter installé - avant qu'un `install` échoue en cours de
  route).
- Un mode de sortie `--json` pour `status`, pour pouvoir le scripter.
- Suivi par composant pour le firmware multi-binaire propre de
  HYDRA-UMC/URTC (voir la "simplification connue" de la section 3), dès
  qu'un besoin réel se fera sentir au-delà du seul composant
  représentatif suivi aujourd'hui.

## 🔗 Projets Lies

**URTC** (Universal Robot Tool Controller) est une veritable plateforme physique de changement d'outils robotiques, du meme auteur (JuanenRac / Electro Hobby 3D). Chaque depot a sa propre version, ses propres tests et son propre README ; voici toute la famille :

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware du PCB physique Universal Robot Tool Controller, 25+ profils d'outils sur bus CAN
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - Outil de bureau pour flasher les cartes URTC, CAN-OTA plus SWD/JTAG complet
* **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** - Firmware pour un rack de montage d'outils avec decodage reel d'ID et prechauffage Smart Idle
* **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** - Outil de diagnostic CAN en direct pour cartes URTC, un panneau par profil d'outil
* **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** - Firmware plus un compagnon de vision reel en Python pour une tete d'inspection thermique/RGB
* **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** - Alternative navigateur a URTC-TESTER via la Web Serial API, sans installation locale
* **URTC-UPDATER** (ce depot) - Detecte, installe et met a jour les propres depots de l'ecosysteme

La conception de cet outil (decouverte par manifeste, installation/mise a jour atomique-par-verification, journal de preuves) est partagee avec **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** et **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** - les propres updaters du meme auteur pour les ecosystemes HYDRA-UMC et A.R.M.O.R., chacun limite a ses propres depots.

## 📚 Documentation et Communaute

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — chaque sous-commande `--cli`, sortie reelle capturee depuis une installation reelle, et le contrat des codes de sortie.
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — comment le client de bureau Qt Quick/QML est structure, et comment il reste une vraie surface de controle sur le meme backend que `--cli` utilise, pas une seconde implementation.
* **[Historique des modifications de ce depot](CHANGELOG.md)**
* Questions, idees et rapports : electrohobby3d@gmail.com

## 👤 AUTEUR
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENCE

GPL-3.0-or-later - voir [LICENSE](LICENSE).
