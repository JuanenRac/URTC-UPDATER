<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | 🇫🇷 <b>Français</b> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 📦 Détecte, installe et met à jour à la main tout l'écosystème URTC

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0 or later">
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

**Vérification d'honnêteté - ce qui fonctionne réellement aujourd'hui :** **Maturité : établi (une exécution complète documentée, pas un usage soutenu).** Ce projet adapte la conception éprouvée de HYDRA-UMC-UPDATER (même découverte par manifeste, installation/mise à jour avec clone temporaire vérifié de façon atomique, journal de preuves) aux seuls dépôts de l'écosystème URTC. Il a été exécuté de bout en bout contre GitHub dans un espace de travail isolé : une installation propre puis une mise à jour d'un vrai dépôt ont été clonées, compilées et promues correctement, la copie précédente étant conservée comme sauvegarde. La logique de découverte et de versions (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), le client GitHub raw-content avec réessai/backoff et liste de dépôts en cache (`github_client.py`), la comparaison par commit (`commits.py`) et le pipeline cloner-préparer-vérifier-promouvoir (`install.py`) sont couverts par des tests (`python -m pytest`), dont un serveur HTTP de test local et de vrais dépôts git temporaires avec un distant bare local. La logique propre au pont Qt s'exécute sans écran dans les tests ; les écrans QML eux-mêmes n'ont pas de test automatisé. La couverture en 8 langues de `i18n.py` est vérifiée par test pour les clés et les paramètres, pas pour la qualité de la traduction. Voir `CHANGELOG.md` pour savoir exactement ce qui a été livré jusqu'ici.

---

> **État de la sûreté et de la cybersécurité :** cet écosystème n'est pas un système de sécurité certifié et aucune carte URTC assemblée n'existe encore. Les bootloaders contrôlent les images de firmware par CRC32 et un HMAC-SHA256 à clé partagée, pas par une signature asymétrique (prévue) ; les images d'application publiées sont signées avec la clé publique de développement (`signing_key_kind: dev`), si bien que n'importe qui peut produire une image acceptée par le bootloader ; rien n'a été transmis à une carte réelle. Lisez la [base de sécurité](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) et le [modèle de menaces](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md) avant de vous fier à une affirmation d'ici pour la sécurité d'une personne.

## 📋 En un coup d'œil

| | |
|---|---|
| Version | `0.1.7` |
| Maturité | Établi |
| Technologie | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Cible | Le PC de la personne qui l'utilise |
| Sur matériel réel | Sans objet : rien ici ne s'exécute sur du matériel |

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

Lancer `urtc-updater` sans argument (ou double-cliquer dessus) ouvre
la même information dans une fenêtre - un tableau de projets, un filtre
par cible de déploiement, et des boutons Installer/Mettre à jour pour la
ligne sélectionnée.

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
  précédente étant conservée dans `<nom>.backup-xxxxxxxx`, jamais supprimée) que
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
  de rester bloqué dans le checkout `.backup-xxxxxxxx` conservé. Dans tous les cas, cela exécute le `build-test.sh`/
  `build-test.bat` propre à ce projet (la vérification non-versionnante
  - voir section 3) s'il en a un. Cet outil ne réimplémente jamais les
  étapes de build propres à un projet.

**Ce que le build-test peut répondre :** le code de sortie 0 signifie validé et tout autre code signifie échec, sauf 75, qui signifie que la validation est *indisponible* (un outil nécessaire n'est pas installé). C'est signalé comme tel et la mise à jour est refusée, sauf si vous l'acceptez en réglant `validation_unavailable` sur `accept` dans les réglages (ou `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). Un build-test doit laisser l'arbre comme il l'a trouvé : s'il modifie un fichier suivi par git, le fichier est remis au contenu validé avant la promotion et les étapes indiquent lequel.

**Commits signés (simple avertissement par défaut ; les exiger est optionnel et désactivé par défaut) :** une révision sans signature valide (`git verify-commit` : trousseau GPG, ou SSH avec `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) est installée quand même, et les étapes de la fenêtre et de la ligne de commande indiquent qu'elle n'est pas signée. Avec `"signature_policy": "require"` dans `~/.urtc_updater_settings.json` (ou `URTC_UPDATER_REQUIRE_SIGNED=1` ; l'ancien `"require_signed_commits": true` signifie la même chose) le candidat - le `HEAD` d'un clone neuf ou le `FETCH_HEAD` récupéré d'une mise à jour - doit passer `git verify-commit` avant la lecture de son manifeste ou tout build, et un candidat refusé laisse le checkout installé intact.

**Options de sécurité (toutes deux désactivées par défaut ; modifiables avec le bouton Sécurité de la fenêtre, la commande `security`, le fichier de réglages, l'environnement et la ligne de commande) :** en plus d'exiger des commits signés, l'outil peut *demander avant d'exécuter la vérification de build* d'un candidat (`"confirm_before_build": true`, `URTC_UPDATER_CONFIRM_BUILD=1`, `--confirm-build`). Il récupère et valide le candidat, montre le projet, le commit, son auteur, sa signature et les scripts de build ou d'outils modifiés, et n'exécute rien tant que vous n'avez pas répondu ; sans fenêtre ni terminal à qui demander, il n'exécute rien (`--yes` répond pour les scripts). `--require-signed` / `--no-require-signed` et `--confirm-build` / `--no-confirm-build` valent pour une seule exécution, et une exécution qui désactive une protection activée dans les réglages enregistrés le signale ; la fenêtre, et `urtc-updater --cli security --require-signed off`, demandent confirmation avant d'enregistrer un niveau plus bas. Un fichier de réglages qui existe mais ne peut pas être lu compte comme « signatures exigées » tant qu'il n'est pas réparé ou supprimé. La vérification de build reçoit aussi `URTC_PYTHON`, l'interpréteur qui exécute l'outil, afin qu'un projet teste avec ce Python et non avec celui que le système trouve en premier.

## 3. 🧱 ARCHITECTURE ET DÉCISIONS DE CONCEPTION

- **GUI Qt Quick par défaut, `--cli` pour le headless.** `main.py` vérifie
  `--cli` avant d'importer le runtime PySide6 optionnel. La CLI fonctionne
  sur une CM5 sans écran ni dépendance desktop ; sans argument QML démarre
  lorsqu'il est disponible et Tkinter reste seulement un fallback temporaire.
- **L'interface fenêtrée est réelle et parle 8 langues (`i18n.py`) - `--cli` volontairement non.** Chaque widget, ainsi que le texte de chaque checkpoint et de chaque échec d'une installation ou mise à jour, s'affiche dans la langue choisie dans un sélecteur (en/es/fr/it/de/zh/ja/pt, portugais du Portugal pour pt), issue d'une préférence enregistrée ou de la langue du système. Les étapes d'installation et de mise à jour circulent sous forme de codes de message plus paramètres et seule la fenêtre les transforme en texte, si bien qu'un changement de langue les réaffiche. Les noms de projet et de famille et les textes `notes`/`tech` de chaque projet ne sont pas traduits : le manifeste est leur seule source de vérité. La sortie de `--cli` reste en anglais volontairement, car elle est faite pour être scriptée et redirigée.
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
- **Aucune logique de build par stack dans cet outil.** L'écosystème couvre plusieurs chaînes d'outils (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, firmware ARM). Réimplémenter ici le build de chaque projet créerait un second endroit prétendant savoir le compiler, condamné à diverger du script du projet lui-même. `install.py` exécute à la place le `build-test.sh` sans versionnement du projet (`build-test.bat` sous Windows) et échoue de façon sûre si une copie n'en a pas. Les scripts de build qui incrémentent la version (`build.sh` et similaires) ne sont jamais lancés par cet outil.
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
- **Simplification connue :** un dépôt composé de plusieurs binaires versionnés indépendamment (URTC en a quatre : principal et esclave, application et bootloader) est suivi par UNE seule version, celle que son propre `urtc.project.json` déclare dans `native_version`. Cela répond à « ce dépôt est-il à peu près à jour ? », pas à la vérification de version par composant d'un flashage.

## 📂 STRUCTURE DES RÉPERTOIRES

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - aucun catalogue statique ; construit au moment de la découverte depuis le manifeste propre de chaque dépôt
│   ├── project_manifest.py # Lit/valide un urtc.project.json propre au dépôt
│   ├── version_parse.py   # UNE implémentation d'extraction regex, local+GitHub
│   ├── detect.py          # Scanne une racine de workspace pour ce qui est installé
│   ├── github_client.py   # Récupération concurrente du contenu brut + réessai/backoff réel pour les erreurs réseau transitoires
│   ├── install.py         # git clone/pull + délègue au script de build propre
│   ├── signature.py       # Politique optionnelle de commits signés (git verify-commit avant la compilation)
│   ├── commits.py          # Compare une copie à son distant par commit (git ls-remote)
│   ├── messages.py         # Messages d'installation/mise à jour sous forme de codes plus paramètres
│   ├── evidence.py         # Journal chaîné par hash de chaque tentative
│   ├── settings.py         # Préférences mémorisées (langue, espace de travail, rétention, profils)
│   ├── profiles.py         # Profils de poste nommés
│   ├── notify.py           # Notification de bureau pour la vérification d'information seule
│   ├── logs.py             # Rotation des fichiers journaux de la fenêtre
│   ├── i18n.py             # Vraies traductions complètes de la GUI (8 langues)
│   ├── translations_data.py # Les textes de la fenêtre, générés depuis le catalogue d'URTC-COMMON
│   ├── qt_gui.py           # Pont Qt Quick vers les services réels de découverte/mise à jour
│   ├── packages_qt.py      # La fenêtre Paquets : les paquets signés des versions
│   ├── qml/Main.qml        # Shell desktop theme avec checkpoints et About
│   ├── gui.py              # Fallback Tkinter si PySide6 est indisponible
│   └── main.py             # Répartition : GUI par défaut, --cli pour status/install/update
├── tests/                  # Tests réels de chaque module (`python -m pytest`)
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
├── bump.py                 # Commande explicite pour monter la version (compiler ne la monte jamais)
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

- `status` affiche `?` pour la version GitHub d'un projet : GitHub n'a pas pu être lu pour lui. La colonne STATE dit pourquoi (par exemple `installed, GitHub unknown (HTTP 404)` ou un avis de limite de requêtes).
- `status` affiche `-` pour GitHub sans erreur affichée : lancez `status`
  (sans `--offline`) - `-` n'apparaît que quand la vérification GitHub a
  été complètement sautée.
- `install`/`update` échoue avec "No non-versioning build-test.sh/.bat found" : cette copie n'a pas de `build-test.sh` (`build-test.bat` sous Windows). Mettez à jour le projet lui-même ou vérifiez-le à la main ; cet outil ne lance jamais à la place un script de build qui incrémente la version.
- `git pull --ff-only` échoue : le checkout local a des modifications non
  commitées ou l'historique a divergé - résolvez cela manuellement (`git
  status` dans le répertoire propre du projet) avant de réessayer
  `update`. Cet outil ne force jamais un reset d'un checkout.

## 🧹 ENTRETIEN ET COMMANDES DE POSTE

- **Installations précédentes conservées.** Chaque mise à jour garde l'installation qu'elle remplace dans `<nom>.backup-xxxxxxxx`. Les 2 plus récentes par projet sont conservées (`"backups_to_keep"` dans `~/.urtc_updater_settings.json` change ce nombre) et les plus anciennes sont supprimées après une mise à jour réussie. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` les supprime à la demande, ainsi que tout dossier temporaire caché laissé par une exécution interrompue.
- **En option, installation depuis le paquet signé d'une release.** `urtc-updater --cli package list|check|install|rollback` installe un programme (le flasher, le testeur ou cet updater) depuis le `.zip` / `.tar.gz` de sa release, au lieu d'un clone et d'une compilation. Seule une version strictement supérieure est proposée, uniquement depuis les hôtes de téléchargement de GitHub, et le paquet doit correspondre à la taille et au SHA-256 annoncés et à la signature Ed25519 de la clé des releases épinglée dans le programme ; un paquet qui échoue à une vérification est supprimé. Il demande avant d'installer (`--yes` répond pour les scripts), conserve les deux dernières releases et `rollback` revient à la précédente. `install --file PAQUET` fonctionne depuis un fichier sur le disque avec son `.sha256` et son `.sig` à côté, sans réseau. La fenêtre a un bouton « Rechercher une mise à jour » pour l'updater lui-même, avec les mêmes règles ; la vérification automatique au démarrage est une option, désactivée par défaut. Testé avec des paquets générés sur un ordinateur, pas encore avec une release publiée.
- **Une fenêtre Paquets et une fenêtre Aide.** Le bouton « Paquets » liste les paquets signés du flasher, du tester et de cet outil de mise à jour : chaque ligne vérifie sa version quand vous appuyez sur « Rechercher une mise à jour », télécharge et vérifie le paquet, demande avant d'installer et revient à la version précédente, avec les mêmes règles et options de sécurité que la commande `package` ; rien n'est installé pendant l'installation ou la mise à jour d'un projet. Le bouton « Aide » ouvre un guide en cinq étapes dans la langue de la fenêtre.
- **En restaurer une.** `urtc-updater --cli restore-backup <PROJET> [--backup DOSSIER] [--list]` remet en place une installation conservée. L'installation remplacée est conservée aussi, donc l'échange peut être annulé. La fenêtre propose les deux mêmes actions à côté de Mettre à jour la sélection : Aperçu de la mise à jour (ce qu'elle apporterait, sans rien modifier) et Restaurer la version précédente.
- **Même version, nouveaux commits.** La version ne change que lors d'un build de publication ; `status` compare donc aussi le commit de chaque projet installé à celui du distant (`git ls-remote`) et affiche `NEW COMMITS` quand GitHub a du travail que la copie n'a pas. La fenêtre affiche le même état et propose la mise à jour.
- **Regarder avant d'approuver.** `urtc-updater --cli update <PROJET> --preview` récupère le candidat et affiche son commit, son auteur, sa version, l'état de sa signature et les fichiers de build ou d'outils qu'il modifie, sans toucher à la copie.
- **Notifier seulement.** `urtc-updater --cli check [--notify] [--quiet]` liste ce qui pourrait être mis à jour et ne change rien. Il se termine avec le code 10 quand quelque chose peut l'être, afin qu'une tâche planifiée prévienne une personne ; `--notify` affiche aussi une notification de bureau.
- **Preuves.** Chaque installation, mise à jour et restauration est consignée avec l'heure, la machine et l'utilisateur dans `.urtc-updater/evidence.jsonl`, chaque ligne étant chaînée à la précédente par hash. `urtc-updater --cli evidence [--export FICHIER]` vérifie la chaîne et peut l'exporter en un seul document JSON.
- **Profils de poste.** `"profiles"` dans le fichier de réglages nomme les projets d'une machine et si les lots sont autorisés ; `--profile NOM` (ou `"profile"` dans les réglages) y limite `status`, `check`, `install` et `update`, et la fenêtre suit le même profil.

## 🚀 FEUILLE DE ROUTE

- Un exécutable GUI autonome packagé (PyInstaller, suivant la propre
  convention `build_exe.bat`/`.sh` de HYDRA-UMC-SUITE) pour une
  installation en double-clic sans aucune étape `pip`/venv - aujourd'hui
  la GUI a encore besoin de `./build.sh` d'abord, comme la CLI.
- Vérification préalable optionnelle des dépendances par projet
  (signaler les chaînes d'outils manquantes - pas de Rust/Go/SDK
  Android/Flutter installé - avant qu'un `install` échoue en cours de
  route).
- Suivi par composant pour le firmware multi-binaire propre de
  HYDRA-UMC/URTC (voir la "simplification connue" de la section 3), dès
  qu'un besoin réel se fera sentir au-delà du seul composant
  représentatif suivi aujourd'hui.

## 🔗 Projets Lies

**URTC** (Universal Robot Tool Controller) est une veritable plateforme physique de changement d'outils robotiques, du meme auteur (JuanenRac / Electro Hobby 3D). Chaque depot a sa propre version, ses propres tests et son propre README ; voici toute la famille :

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware du PCB physique Universal Robot Tool Controller, 25+ profils d'outils sur bus CAN
* **[URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS)** - L'architecture, les interfaces, le socle de securite, la matrice des capacites et le catalogue de projets genere de l'ecosysteme, ainsi que les outils qui comparent tous les depots
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - Outil de bureau pour flasher les cartes URTC, CAN-OTA plus SWD/JTAG complet
* **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** - une passerelle devant le bus CAN qui ne laisse passer que les identifiants d'une liste, limite leur débit et exige une clé de session.
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

<!-- urtc-section:updates -->
## 🔄 Comment il se met à jour

Ce programme peut chercher une version plus récente de lui-même : le bouton « Rechercher une mise à jour » interroge GitHub une fois et ne propose un paquet signé que s'il est pour votre système et plus récent. Rien n'est vérifié ni installé tout seul tant que vous n'activez pas la vérification, et une mise à jour demande votre confirmation. Le paquet doit correspondre à son SHA-256 et à la signature de la clé des releases épinglée dans le programme ; la version précédente est conservée et rétablie d'elle-même si la nouvelle ne démarre pas. `urtc-updater --cli package list|check|install|rollback` fait la même chose en ligne de commande pour le flasher et le testeur, et `install --file` fonctionne sans réseau.
<!-- /urtc-section:updates -->

<!-- urtc-section:compatibility -->
## 🧩 Compatibilité

Les versions des programmes URTC qui fonctionnent ensemble, et la version du protocole que parle chacune, figurent dans le tableau de compatibilité que génère URTC-COMMON : [docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md).
<!-- /urtc-section:compatibility -->

## 📜 LICENCE

GPL-3.0-or-later - voir [LICENSE](LICENSE).
