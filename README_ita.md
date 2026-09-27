<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | 🇮🇹 <b>Italiano</b> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a></p>

### 📦 Rileva, installa e aggiorna manualmente l'intero ecosistema URTC

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="stdlib-only CLI core">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="PySide6 Qt Quick desktop GUI">
</p>

> **Modalità desktop visiva:** l'interfaccia desktop predefinita usa ora
> **Qt Quick / QML** con il runtime GUI opzionale `PySide6`. Il nucleo e
> `--cli` restano solo libreria standard per una CM5 senza schermo.
>
> **Avvio Windows ed evidenze:** apri `run-gui.vbs` (o `run.bat` senza
> argomenti) per il client grafico senza console. Il pannello di aggiornamento
> mostra checkpoint reali di preflight, sorgente, manifest, build-test e fine
> con evidenze catturate; `run.bat --cli ...` conserva il terminale diagnostico.
> Installa è attivo solo senza checkout e Aggiorna solo se GitHub è più recente.
> Durante un'azione approvata i checkpoint sostituiscono i controlli del
> progetto; selezionare un altro progetto li ripristina.
> **Installa tutti i mancanti** e **Aggiorna tutti gli obsoleti** sono azioni
> in blocco sequenziali, confermate separatamente e basate sullo stesso stato
> reale e percorso di sicurezza.

**Verifica di onestà - cosa funziona davvero oggi:** la logica di discovery/versione a livello di ecosistema (`registry.py`, `project_manifest.py`, `ecosystem_catalog.py`, `version_parse.py`, `detect.py`), il vero client GitHub raw-content con retry/backoff (`github_client.py`) e la logica clona-prepara-verifica-promuovi della pipeline di installazione/aggiornamento (`install.py`) sono reali e testati - 64 test superati (`pytest tests/`), incluso un server HTTP fittizio che dimostra l'isolamento tra un catalogo malformato e un singolo progetto malformato, più veri round-trip di clone/build git in directory temporanee. `--cli status`/`install`/`update` eseguono lo stesso nucleo testato end-to-end contro il vero host GitHub raw-content live (non un mock) ogni volta che li esegui davvero. La GUI desktop Qt Quick (`qt_gui.py`, `qml/Main.qml`) e il fallback Tkinter legacy (`gui.py`) collegano quello stesso nucleo testato a una finestra reale e sono stati eseguiti su veri checkout dell'ecosistema, ma nessuna delle due ha un test automatico proprio - non esiste `test_gui.py`/`test_qt_gui.py`, poiché qui non si tenta di guidare un vero event loop Qt/Tk. La copertura a 7 lingue di `i18n.py` è verificata da test (`test_i18n.py`), ma solo per la parità delle chiavi tra lingue, non per la qualità della traduzione. Vedi `CHANGELOG.md` per sapere esattamente cosa è stato consegnato finora.

---

## 1. 🛠️ PANORAMICA TECNICA

URTC-UPDATER è un piccolo strumento - GUI con finestra per
impostazione predefinita, CLI completa con `--cli` - pensato per girare
sia sul vero CM5 sia sulla macchina Windows/Linux/macOS personale di uno
sviluppatore (qualsiasi workspace con lo stesso tipo di checkout) che
risponde a tre domande per ogni altro progetto reale che scopre tramite
il proprio manifesto `urtc.project.json` di ciascun checkout
vicino - il numero stesso non è mai codificato in modo fisso qui, perché
cresce insieme all'ecosistema:

1. **Cosa c'è realmente installato qui, e in quale versione?**
2. **Qual è l'ultima versione pubblicata su GitHub?**
3. **Se GitHub ha una versione più recente, fammi scegliere un progetto o un lotto sequenziale confermato.**

Quest'ultimo punto è deliberato e non negoziabile: questo strumento non
modifica mai un progetto di propria iniziativa. Un'azione sul progetto
selezionato richiede sempre una conferma esplicita. La GUI può anche offrire
**Installa tutti i mancanti** o **Aggiorna tutti gli obsoleti**: sono lotti
sequenziali confermati separatamente e soggetti agli stessi controlli di
manifest, versione e sicurezza. Non esiste alcun aggiornamento automatico
notturno senza approvazione umana.

Nemmeno ogni progetto scoperto appartiene al CM5 - la maggior parte dei
repository con prefisso URTC e alcuni di HYDRA-UMC sono strumenti che uno
sviluppatore esegue dal proprio PC (il firmware viene compilato e
flashato DAL posto di lavoro, non costruito SULLA cella), oppure app
installate su un telefono/orologio. Il proprio campo `deploy` di
`registry.py` registra quale è quale (vedi sezione 3), e la tabella dei
progetti della GUI filtra su di esso - per impostazione predefinita
mostra "solo CM5" quando rileva di girare su Linux (il proprio SO del
vero CM5), e "mostra tutto" su Windows/macOS.

Esempio illustrativo (il numero esatto di progetti e ogni numero di
versione qui sotto sono inventati per la forma dell'output, non
un'esecuzione realmente catturata - il numero reale è sempre quello che
`registry.py` scopre oggi, mai una cifra fissa in questo documento):

```
$ urtc-updater --cli status
Workspace root: /home/pi/HYDRA-UMC
Checking GitHub... 59/59
PROJECT                        STACK       LOCAL     GITHUB    STATE
--------------------------------------------------------------------
HYDRA-UMC                      firmware-c  0.0.7     0.0.7     up to date
HYDRA-UMC-SERVER               node        0.0.5     0.0.9     OUTDATED
HYDRA-UMC-STUDIO               node        0.0.8     0.1.3     OUTDATED
...
59/59 installed, 2 outdated

$ urtc-updater --cli update HYDRA-UMC-SERVER
Updating HYDRA-UMC-SERVER into /home/pi/HYDRA-UMC ...
OK  Pulled latest into /home/pi/HYDRA-UMC/HYDRA-UMC-SERVER
OK  build.sh completed successfully.
```

Avviare `urtc-updater` senza argomenti (o con doppio clic) apre la
stessa informazione in una finestra - una tabella di progetti, un filtro
per obiettivo di distribuzione, e pulsanti Installa/Aggiorna per la riga
selezionata.

<p align="center">
  <img src="images/" alt="Panoramica reale desktop di URTC-UPDATER" width="100%">
</p>

## 2. 🔄 COME FUNZIONA DAVVERO UN CONTROLLO/AGGIORNAMENTO

- **Origine della versione**: la convenzione "contachilometri" di
  auto-incremento di questo ecosistema (ogni build reale incrementa un
  numero di versione che vive DENTRO un file sorgente - `pyproject.toml`,
  `Cargo.toml`, `version.go`, `package.json`, `version.properties`,
  `pubspec.yaml`, o un `#define` di firmware, a seconda dello stack del
  progetto) non ha mai creato un tag git né una GitHub Release per
  quell'incremento. Questo strumento legge quindi lo STESSO file che il
  proprio `bump_version.py`/script di build di ogni progetto già scrive,
  direttamente dal branch predefinito del repo tramite l'host di
  contenuto raw di GitHub - non l'API delle Releases, che riporterebbe
  che tutti i progetti non hanno alcuna release.
- **Rilevamento locale**: per ogni progetto scoperto,
  controlla se esiste una directory con quel nome esatto sotto la radice
  del workspace (la disposizione standard dell'ecosistema - ogni
  progetto come directory sorella, esattamente ciò che già presuppongono
  build-frontend.sh e il proprio discovery di HYDRA-UMC-SUITE), e se sì,
  legge la propria copia locale di quello stesso file di versione.
- **Un'unica implementazione di parsing** (`version_parse.py`) è
  condivisa tra la lettura locale e il recupero da GitHub, così un
  checkout locale e un recupero da GitHub non vengono mai interpretati
  da due regex che potrebbero divergere indipendentemente.
- **Installare/aggiornare**: `git clone` (installazione) compila poi
  come passo separato. Aggiornare un checkout GIA' ESISTENTE è invece
  atomico-per-verifica: il candidato viene clonato, unito con
  fast-forward (mai un reset forzato, così vere modifiche locali
  falliscono rumorosamente invece di essere scartate), e compilato/
  verificato PRIMA in un clone di staging completamente indipendente -
  l'installazione reale viene toccata (tramite due rinomine di
  directory consecutive, con l'installazione precedente conservata in
  `<nome>.backup`, mai cancellata) solo se quella build di staging ha
  davvero successo. Un fallimento di build, un checkout divergente/
  sporco, un crash o un disco pieno in qualsiasi momento prima di
  quella promozione finale lasciano l'installazione precedente
  completamente intatta e ancora operativa - vedi il docstring proprio
  di `clone_or_pull` in `install.py`. Il remote git proprio del clone di
  staging viene ripristinato verso il repository GitHub reale subito
  dopo la sua creazione (un semplice clone locale lo lascerebbe invece
  puntare al vecchio percorso di installazione, terminando in silenzio
  tutti i futuri aggiornamenti una volta promosso), e i dati locali
  reali propri del checkout installato (tutto ciò che git considera non
  tracciato o ignorato - `data/settings.json` e simili, esclusi gli
  artefatti di build rigenerabili) vengono trasferiti nel clone di
  staging prima che venga compilato, così lo stato operativo reale di un
  progetto sopravvive a un aggiornamento invece di restare bloccato nel
  checkout `.backup` conservato. In ogni caso questo esegue il
  `build-test.sh`/`build-test.bat` proprio di quel progetto (il
  controllo non-versionante - vedi sezione 3) se ce l'ha. Questo
  strumento non reimplementa mai i passi di build propri di un
  progetto.

<p align="center">
  <img src="images/" alt="Checkpoint reali durante installazione o aggiornamento di URTC-UPDATER" width="100%">
</p>

## 3. 🧱 ARCHITETTURA E DECISIONI DI DESIGN

- **GUI Qt Quick predefinita, `--cli` per headless.** `main.py` controlla
  `--cli` prima di importare il runtime PySide6 opzionale. La CLI funziona su
  una CM5 senza schermo né dipendenze desktop; senza argomenti avvia QML quando
  disponibile e Tkinter resta solo un fallback temporaneo.
- **La GUI con finestra è reale, multilingue in 7 lingue (`i18n.py`) - `--cli` deliberatamente non lo è.** Ogni widget reale si ri-etichetta dal vivo da una `Combobox` di lingua (en/es/fr/it/de/zh/ja, le stesse 7 pubblicate dalla dashboard pubblica e da ogni README), rilevata da una preferenza salvata o dalla locale propria del sistema operativo. I nomi di progetti/famiglie e il testo reale `notes`/`tech` di ciascun progetto restano non tradotti - `registry.py` è la loro unica fonte di verità, e 7 copie parallele di documentazione ingegneristica reale impedirebbero che lo restasse. L'output di `--cli` resta volutamente solo in inglese: è pensato per essere scriptato/reindirizzato, dove un testo stabile e grep-abile conta più della localizzazione.
- **`deploy` è una classificazione, non una restrizione.** Trattare ogni
  progetto scoperto come "una cosa che appartiene al CM5" era sbagliato - i
  repository di firmware vengono compilati e flashati DA un PC (il CM5
  ha bisogno solo del binario risultante via CAN-OTA, mai del codice
  sorgente di questo repository), e diversi strumenti (URTC-FLASHER,
  HYDRA-UMC-SUITE, HYDRA-UMC-TOOL-CLI, ...) sono pensati per girare sul
  proprio posto di lavoro di un operatore, non dentro la cella stessa.
  Il campo `deploy` di `registry.py` ("cm5" / "user-pc" / "mobile" /
  "wearable" / "dev-server") registra questo, e il filtro della GUI lo usa come punto di
  partenza ragionevole - mai come restrizione rigida, dato che questo
  stesso strumento è anche pensato per girare sul PC personale di uno
  sviluppatore, dove ogni progetto scoperto è ugualmente valido da ispezionare.
- **Nessuna logica di build per stack in questo strumento.**
  L'ecosistema copre 7 toolchain (Python, Rust, Go, Node/TS,
  Android/Kotlin, Flutter, firmware ARM). Reimplementare `npm install &&
  npm run build` / `cargo build --release` / `./gradlew assembleDebug` /
  ecc. QUI creerebbe un secondo posto che pretende di sapere come
  compilare ogni progetto, garantito a divergere dal `build.sh`/`.bat`
  reale (e già corretto) di quel progetto. `install.py` invece cerca un
  nome di script di build conosciuto (`build.sh`, `build_firmware.sh`,
  `build_exe.sh`, `build-android.sh`, e i loro equivalenti `.bat` - i
  nomi reali usati nei propri progetti scoperti dell'ecosistema) ed esegue quello che esiste.
- **Contenuto raw di GitHub, non l'API delle Releases.** Vedi la sezione
  2 - la convenzione di versionamento di questo ecosistema non crea mai
  un tag/release, quindi l'API delle Releases sarebbe attivamente
  sbagliata qui, non solo meno comoda.
- **Un errore di rete transitorio riceve un vero ritentativo; una
  risposta definitiva mai.** Ogni richiesta reale a GitHub
  (`_urlopen_with_retries` di `github_client.py`) riprova fino a 3 volte
  con backoff, ma solo quando la connessione non ha mai ottenuto alcuna
  risposta (DNS/timeout/reset). Uno stato HTTP reale che GitHub ha
  effettivamente restituito - 404, 403, 500 - non viene mai riprovato:
  GitHub ha già risposto, e insistere consumerebbe solo altro rate limit
  per lo stesso risultato.
- **Un catalogo remoto malformato fallisce rumorosamente; un singolo
  progetto malformato no.** Se l'elenco stesso dei repository GitHub è
  irraggiungibile o non analizzabile, `discover_remote_projects()`
  solleva un'eccezione - sia `gui.py` che `main.py` la catturano già e
  ricadono sull'elenco dei progetti scoperti localmente invece di
  mostrare una scansione rotta o vuota. Il manifest malformato di un
  singolo repository, invece, viene isolato nella lista `errors` di
  quella scansione e non interrompe mai la scoperta del resto - un vero
  test con server di fixture (`tests/test_github_client.py`) dimostra
  entrambi i percorsi.
- **La CLI resta esplicita; i lotti GUI restano confermati.** I comandi CLI
  `install`/`update` richiedono un nome di progetto. La GUI può eseguire
  **Installa tutti i mancanti** o **Aggiorna tutti gli obsoleti**, ma solo dopo
  una conferma separata e in sequenza attraverso gli stessi controlli di
  sicurezza. Non esiste aggiornamento automatico non supervisionato.
- **Solo libreria standard.** `urllib` per i recuperi da GitHub
  (`github_client.py`), `subprocess` per le chiamate a git/script di
  build (`install.py`), nient'altro - che uno strumento responsabile di
  mantenere sane le dipendenze di TUTTI gli altri progetti resti esso
  stesso senza dipendenze è deliberato.
- **Semplificazione nota**: HYDRA-UMC e URTC sono veri repo di firmware
  multi-componente (6 e 4 binari versionati in modo indipendente
  ciascuno - vedi il proprio `VERSION_CHECKLIST.txt`/`build_firmware.sh`)
  senza un unico numero di versione. `registry.py` segue UN componente
  rappresentativo per repo - sufficiente per rispondere "questo repo è
  più o meno aggiornato?", non un sostituto del proprio
  `firmware_manifest.json` di `build_firmware.sh` per un flash reale.

## 📂 STRUTTURA DELLE DIRECTORY

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - nessun catalogo statico; costruito a tempo di scoperta dal manifesto proprio di ogni repo
│   ├── project_manifest.py # Legge/valida un urtc.project.json proprio del repository
│   ├── ecosystem_catalog.py # Parser del catalogo pubblico di scoperta dell'ecosistema di JuanenRac
│   ├── version_parse.py   # UN'implementazione di estrazione regex, locale+GitHub
│   ├── detect.py          # Scansiona una radice di workspace per ciò che è installato
│   ├── github_client.py   # Recupero concorrente del contenuto raw + ritentativo/backoff reale per errori di rete transitori
│   ├── install.py         # git clone/pull + delega allo script di build proprio
│   ├── i18n.py             # Traduzioni reali e complete della GUI (7 lingue)
│   ├── qt_gui.py           # Bridge Qt Quick verso i servizi reali di scoperta/aggiornamento
│   ├── qml/Main.qml        # Shell desktop a tema con checkpoint e About
│   ├── gui.py              # Fallback Tkinter se PySide6 non è disponibile
│   └── main.py             # Dispatch: GUI predefinita, --cli per status/install/update
├── tests/                  # Test reali: github_client, i18n, install, project_manifest, registry
├── docs/
│   ├── CLI_REFERENCE.md     # Riferimento comandi
│   └── QML_DESKTOP_GUI.md   # Architettura della GUI Qt Quick
├── images/                 # Media, icone dell'app e screenshot dell'interfaccia
├── tools/
│   ├── build_test.py        # Controllo build senza versionamento
│   ├── ci_validate.py       # Validazione manifest/CHANGELOG/docs usata dalla CI
│   ├── generate_app_icon.py # Renderizza l'SVG pubblico di HYDRA-UMC nell'icona usata da Windows
│   ├── migrate_project_manifests.py  # Verifica un workspace dopo la migrazione una tantum dei manifesti
│   └── validate_project_manifests.py # Valida i manifesti propri dei repo + le versioni native di build
├── .env.example            # Modello delle variabili d'ambiente
├── build.sh / build.bat    # venv + installazione editabile + compile-check
├── run.sh / run.bat        # GUI predefinita / ingresso CLI
├── run-gui.vbs             # Launcher grafico Windows senza console
├── bump_version.py         # Incremento "contachilometri" dell'ecosistema (pyproject.toml + __init__.py)
└── bump_manifest_version.py # Sincronizza la versione di urtc.project.json con quella nativa (--sync)
```

## ⚙️ COMPILAZIONE ED ESECUZIONE

```bash
chmod +x build.sh   # una tantum
./build.sh          # crea .venv, pip install -e ., compile-check di tutto
./run.sh                               # GUI con finestra (predefinita)
./run.sh --cli status                  # cosa è installato, versione locale vs. GitHub
./run.sh --cli status --offline        # lo stesso, senza controllare GitHub
./run.sh --cli install <NOME-PROGETTO> # clona + compila un progetto non ancora installato
./run.sh --cli update  <NOME-PROGETTO> # aggiorna + ricompila un progetto già installato
```

Su Windows: `build.bat`, poi `run.bat` (GUI) / `run.bat --cli status` /
`run.bat --cli install <nome>` / `run.bat --cli update <nome>`.

La GUI preferita richiede il runtime Qt opzionale (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` lo installano già). `--cli` non ha dipendenze GUI ed è
l'ingresso corretto per una CM5 headless. Senza Qt, la vecchia finestra
Tkinter resta solo un fallback di compatibilità.

**Risoluzione dei problemi**

- `status` mostra `?` per la versione locale o GitHub di un progetto: il
  suo file di versione esiste ma la convenzione di quel progetto è
  cambiata dall'ultimo aggiornamento di `registry.py` - controlla la
  voce di quel progetto in `registry.py` rispetto al suo file di
  versione reale attuale.
- `status` mostra `-` per GitHub senza alcun errore mostrato: esegui
  `status` (senza `--offline`) - `-` appare solo quando il controllo
  GitHub è stato saltato del tutto.
- `install`/`update` fallisce con "No build.sh/.bat found": quel
  progetto usa un nome di script di build che questo strumento non
  riconosce ancora - controlla il suo proprio README per quello reale, e
  valuta di aggiungerlo alle liste `BUILD_SCRIPT_CANDIDATES_*` proprie di
  `install.py`.
- `git pull --ff-only` fallisce: il checkout locale ha modifiche non
  committate o la cronologia è divergente - risolvilo manualmente (`git
  status` nella directory propria del progetto) prima di riprovare
  `update`. Questo strumento non forza mai un reset di un checkout.

## 🚀 TABELLA DI MARCIA

- Un eseguibile GUI autonomo pacchettizzato (PyInstaller, seguendo la
  propria convenzione `build_exe.bat`/`.sh` di HYDRA-UMC-SUITE) per
  un'installazione con doppio clic senza alcun passaggio `pip`/venv -
  oggi la GUI richiede ancora `./build.sh` prima, come la CLI.
- Controllo preliminare opzionale delle dipendenze per progetto
  (segnalare toolchain mancanti - nessun Rust/Go/SDK Android/Flutter
  installato - prima che un `install` fallisca a metà strada).
- Una modalità di output `--json` per `status`, per poterlo scriptare.
- Tracciamento per componente per il firmware multi-binario proprio di
  HYDRA-UMC/URTC (vedi la "semplificazione nota" nella sezione 3), non
  appena ci sarà una reale necessità oltre l'unico componente
  rappresentativo tracciato oggi.

## 🔗 Progetti Correlati

**URTC** (Universal Robot Tool Controller) e una piattaforma fisica reale di cambio utensile robotico, dello stesso autore (JuanenRac / Electro Hobby 3D). Ogni repository ha la propria versione, i propri test e il proprio README; questa e l'intera famiglia:

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware per il PCB fisico Universal Robot Tool Controller, 25+ profili utensile su bus CAN
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - Strumento desktop per il flashing delle schede URTC, CAN-OTA piu SWD/JTAG completo
* **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** - Firmware per un rack di montaggio utensili con decodifica reale dell'ID e preriscaldamento Smart Idle
* **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** - Strumento di diagnostica CAN dal vivo per schede URTC, un pannello per profilo utensile
* **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** - Firmware piu un vero compagno di visione in Python per una testa di ispezione termica/RGB
* **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** - Alternativa basata su browser a URTC-TESTER tramite la Web Serial API, senza installazione locale
* **URTC-UPDATER** (questo repository) - Rileva, installa e aggiorna i repository dell'ecosistema stesso

Il design di questo strumento (scoperta tramite manifesto, installazione/aggiornamento atomico-per-verifica, registro delle prove) e condiviso con **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** e **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** - gli updater dello stesso autore per gli ecosistemi HYDRA-UMC e A.R.M.O.R., ciascuno limitato ai propri repository.

## 📚 Documentazione e Comunita

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — ogni sottocomando `--cli`, output reale catturato da un'esecuzione reale installata, e il contratto dei codici di uscita.
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — come e strutturato il client desktop Qt Quick/QML, e come resta una vera superficie di controllo sullo stesso backend usato da `--cli`, non una seconda implementazione.
* **[Changelog di questo repository](CHANGELOG.md)**
* Domande, idee e segnalazioni: electrohobby3d@gmail.com

## 👤 AUTORE
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENZA

GPL-3.0-or-later - vedi [LICENSE](LICENSE).
