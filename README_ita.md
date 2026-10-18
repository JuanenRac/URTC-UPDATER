<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | 🇮🇹 <b>Italiano</b> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 📦 Rileva, installa e aggiorna manualmente l'intero ecosistema URTC

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0 or later">
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

**Verifica di onestà - cosa funziona davvero oggi:** **Maturità: consolidato (un'esecuzione completa documentata, non un uso prolungato).** Questo progetto adatta il design già collaudato di HYDRA-UMC-UPDATER (stessa scoperta tramite manifest, installazione/aggiornamento con clone temporaneo verificato in modo atomico e registro delle evidenze) ai soli repository dell'ecosistema URTC. È stato eseguito end to end contro GitHub in un'area di lavoro isolata: un'installazione pulita e un successivo aggiornamento di un repository reale sono stati clonati, compilati e promossi correttamente, conservando la copia precedente come backup. La logica di scoperta e di versione (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), il client GitHub raw-content con retry/backoff ed elenco dei repository in cache (`github_client.py`), il confronto per commit (`commits.py`) e la pipeline clona-prepara-verifica-promuovi (`install.py`) sono coperti da test (`python -m pytest`), compreso un server HTTP di prova locale e veri repository git temporanei con un remoto bare locale. La logica propria del bridge Qt gira senza schermo nei test; le schermate QML in sé non hanno un test automatico. La copertura a 8 lingue di `i18n.py` è verificata da test per chiavi e segnaposto, non per la qualità della traduzione. Vedi `CHANGELOG.md` per sapere esattamente cosa è stato consegnato finora.

---

> **Stato di sicurezza (safety e security):** questo ecosistema non è un sistema di sicurezza certificato e non esiste ancora alcuna scheda URTC assemblata. I bootloader controllano le immagini firmware con CRC32 e un HMAC-SHA256 a chiave condivisa, non con una firma asimmetrica (prevista); le immagini applicative pubblicate sono firmate con la chiave pubblica di sviluppo (`signing_key_kind: dev`), quindi chiunque può produrre un'immagine accettata dal bootloader; nulla è stato trasmesso a una scheda reale. Leggi la [base di sicurezza](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) e il [modello delle minacce](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md) prima di fidarti di qualsiasi affermazione qui per la sicurezza di una persona.

## 📋 In breve

| | |
|---|---|
| Versione | `0.1.5` |
| Maturità | Consolidato |
| Tecnologia | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Destinazione | Il PC di chi lo usa |
| Su hardware reale | Non applicabile: nulla qui gira su hardware |

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

Avviare `urtc-updater` senza argomenti (o con doppio clic) apre la
stessa informazione in una finestra - una tabella di progetti, un filtro
per obiettivo di distribuzione, e pulsanti Installa/Aggiorna per la riga
selezionata.

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
  `<nome>.backup-xxxxxxxx`, mai cancellata) solo se quella build di staging ha
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
  checkout `.backup-xxxxxxxx` conservato. In ogni caso questo esegue il
  `build-test.sh`/`build-test.bat` proprio di quel progetto (il
  controllo non-versionante - vedi sezione 3) se ce l'ha. Questo
  strumento non reimplementa mai i passi di build propri di un
  progetto.

**Cosa può rispondere il build-test:** il codice di uscita 0 significa convalidato e qualsiasi altro significa fallito, tranne 75, che significa che la convalida è *non disponibile* (manca uno strumento necessario). Viene segnalato come tale e l'aggiornamento viene rifiutato, a meno che tu non lo accetti impostando `validation_unavailable` su `accept` nelle impostazioni (o `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). Un build-test deve lasciare l'albero come l'ha trovato: se cambia un file tracciato da git, il file viene riportato al contenuto registrato prima della promozione e i passaggi dicono quale.

**Commit firmati (solo avviso per impostazione predefinita; richiederli è opzionale e disattivato per impostazione predefinita):** una revisione senza firma valida (`git verify-commit`: portachiavi GPG, o SSH con `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) viene installata comunque, e i passi della finestra e della riga di comando dicono che non è firmata. Con `"signature_policy": "require"` in `~/.urtc_updater_settings.json` (o `URTC_UPDATER_REQUIRE_SIGNED=1`; il vecchio `"require_signed_commits": true` significa lo stesso) il candidato - l'`HEAD` di un clone nuovo o il `FETCH_HEAD` scaricato di un aggiornamento - deve superare `git verify-commit` prima di leggere il suo manifest o costruire qualcosa, e un candidato rifiutato lascia intatto il checkout installato.

## 3. 🧱 ARCHITETTURA E DECISIONI DI DESIGN

- **GUI Qt Quick predefinita, `--cli` per headless.** `main.py` controlla
  `--cli` prima di importare il runtime PySide6 opzionale. La CLI funziona su
  una CM5 senza schermo né dipendenze desktop; senza argomenti avvia QML quando
  disponibile e Tkinter resta solo un fallback temporaneo.
- **La GUI con finestra è reale e parla 8 lingue (`i18n.py`) - `--cli` volutamente no.** Ogni widget, e il testo di ogni checkpoint e di ogni errore di un'installazione o aggiornamento, viene mostrato nella lingua scelta in un selettore (en/es/fr/it/de/zh/ja/pt, portoghese del Portogallo per pt), presa da una preferenza salvata o dalle impostazioni regionali del sistema. I passi di installazione e aggiornamento viaggiano come codici di messaggio più parametri e solo la finestra li trasforma in testo, quindi un cambio di lingua li ridisegna. I nomi di progetto e di famiglia e i testi `notes`/`tech` di ogni progetto non vengono tradotti: il manifest è la loro unica fonte di verità. L'output di `--cli` resta in inglese di proposito, perché è pensato per script e pipe.
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
- **Nessuna logica di build per stack in questo strumento.** L'ecosistema comprende diverse toolchain (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, firmware ARM). Reimplementare qui il build di ogni progetto creerebbe un secondo posto che pretende di saperlo compilare, destinato a divergere dallo script del progetto stesso. `install.py` esegue invece il `build-test.sh` senza versionamento del progetto (`build-test.bat` su Windows) e fallisce in modo sicuro se una copia non lo ha. Gli script di build che incrementano la versione (`build.sh` e simili) non vengono mai eseguiti da questo strumento.
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
- **Semplificazione nota:** un repository composto da più binari con versione indipendente (URTC ne ha quattro: principale e slave, applicazione e bootloader) viene seguito con UNA sola versione, quella che il suo `urtc.project.json` dichiara in `native_version`. Risponde a "questo repository è più o meno aggiornato?", non sostituisce il controllo di versione per componente di un flash.

## 📂 STRUTTURA DELLE DIRECTORY

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - nessun catalogo statico; costruito a tempo di scoperta dal manifesto proprio di ogni repo
│   ├── project_manifest.py # Legge/valida un urtc.project.json proprio del repository
│   ├── version_parse.py   # UN'implementazione di estrazione regex, locale+GitHub
│   ├── detect.py          # Scansiona una radice di workspace per ciò che è installato
│   ├── github_client.py   # Recupero concorrente del contenuto raw + ritentativo/backoff reale per errori di rete transitori
│   ├── install.py         # git clone/pull + delega allo script di build proprio
│   ├── signature.py       # Politica opzionale dei commit firmati (git verify-commit prima della build)
│   ├── commits.py          # Confronta una copia con il suo remoto per commit (git ls-remote)
│   ├── messages.py         # Messaggi di installazione/aggiornamento come codici più parametri
│   ├── evidence.py         # Registro concatenato con hash di ogni tentativo
│   ├── settings.py         # Preferenze ricordate (lingua, area di lavoro, conservazione, profili)
│   ├── profiles.py         # Profili di postazione con nome
│   ├── notify.py           # Notifica desktop per il controllo di sola segnalazione
│   ├── logs.py             # Rotazione dei file di log della finestra
│   ├── i18n.py             # Traduzioni reali e complete della GUI (8 lingue)
│   ├── qt_gui.py           # Bridge Qt Quick verso i servizi reali di scoperta/aggiornamento
│   ├── qml/Main.qml        # Shell desktop a tema con checkpoint e About
│   ├── gui.py              # Fallback Tkinter se PySide6 non è disponibile
│   └── main.py             # Dispatch: GUI predefinita, --cli per status/install/update
├── tests/                  # Test reali di ogni modulo (`python -m pytest`)
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
├── bump.py                 # Comando esplicito per alzare la versione (compilare non la alza mai)
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

- `status` mostra `?` nella versione GitHub di un progetto: non è stato possibile leggere GitHub per esso. La colonna STATE dice perché (per esempio `installed, GitHub unknown (HTTP 404)` o un avviso di limite di richieste).
- `status` mostra `-` per GitHub senza alcun errore mostrato: esegui
  `status` (senza `--offline`) - `-` appare solo quando il controllo
  GitHub è stato saltato del tutto.
- `install`/`update` fallisce con "No non-versioning build-test.sh/.bat found": quella copia non ha `build-test.sh` (`build-test.bat` su Windows). Aggiorna il progetto stesso o verificalo a mano; questo strumento non esegue mai al suo posto uno script di build che incrementa la versione.
- `git pull --ff-only` fallisce: il checkout locale ha modifiche non
  committate o la cronologia è divergente - risolvilo manualmente (`git
  status` nella directory propria del progetto) prima di riprovare
  `update`. Questo strumento non forza mai un reset di un checkout.

## 🧹 MANUTENZIONE E COMANDI DI POSTAZIONE

- **Installazioni precedenti conservate.** Ogni aggiornamento conserva l'installazione sostituita in `<nome>.backup-xxxxxxxx`. Vengono tenute le 2 più recenti per progetto (`"backups_to_keep"` in `~/.urtc_updater_settings.json` cambia il numero) e quelle più vecchie vengono rimosse dopo un aggiornamento riuscito. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` le rimuove su richiesta, insieme a ogni cartella temporanea nascosta lasciata da un'esecuzione interrotta.
- **Ripristinarne una.** `urtc-updater --cli restore-backup <PROGETTO> [--backup CARTELLA] [--list]` rimette a posto un'installazione conservata. Anche l'installazione sostituita viene conservata, quindi lo scambio si può annullare.
- **Stessa versione, nuovi commit.** La versione cambia solo in un build di rilascio, quindi `status` confronta anche il commit di ogni progetto installato con quello remoto (`git ls-remote`) e mostra `NEW COMMITS` quando GitHub ha lavoro che la copia non ha. La finestra mostra lo stesso stato e offre l'aggiornamento.
- **Guardare prima di approvare.** `urtc-updater --cli update <PROGETTO> --preview` scarica il candidato e mostra il suo commit, autore, versione, stato della firma e i file di build o di strumenti che modifica, senza toccare la copia.
- **Solo avviso.** `urtc-updater --cli check [--notify] [--quiet]` elenca ciò che si potrebbe aggiornare e non cambia nulla. Termina con codice 10 quando c'è qualcosa da aggiornare, così un'attività pianificata può avvisare una persona; `--notify` mostra anche una notifica desktop.
- **Evidenze.** Ogni installazione, aggiornamento e ripristino viene registrato con ora, macchina e utente in `.urtc-updater/evidence.jsonl`, con ogni riga concatenata alla precedente tramite hash. `urtc-updater --cli evidence [--export FILE]` verifica la catena e può esportarla come un unico documento JSON.
- **Profili di postazione.** `"profiles"` nel file delle impostazioni indica i progetti con cui lavora una macchina e se i lotti sono consentiti; `--profile NOME` (o `"profile"` nelle impostazioni) vi limita `status`, `check`, `install` e `update`, e la finestra segue lo stesso profilo.

## 🚀 TABELLA DI MARCIA

- Un eseguibile GUI autonomo pacchettizzato (PyInstaller, seguendo la
  propria convenzione `build_exe.bat`/`.sh` di HYDRA-UMC-SUITE) per
  un'installazione con doppio clic senza alcun passaggio `pip`/venv -
  oggi la GUI richiede ancora `./build.sh` prima, come la CLI.
- Controllo preliminare opzionale delle dipendenze per progetto
  (segnalare toolchain mancanti - nessun Rust/Go/SDK Android/Flutter
  installato - prima che un `install` fallisca a metà strada).
- Tracciamento per componente per il firmware multi-binario proprio di
  HYDRA-UMC/URTC (vedi la "semplificazione nota" nella sezione 3), non
  appena ci sarà una reale necessità oltre l'unico componente
  rappresentativo tracciato oggi.

## 🔗 Progetti Correlati

**URTC** (Universal Robot Tool Controller) e una piattaforma fisica reale di cambio utensile robotico, dello stesso autore (JuanenRac / Electro Hobby 3D). Ogni repository ha la propria versione, i propri test e il proprio README; questa e l'intera famiglia:

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware per il PCB fisico Universal Robot Tool Controller, 25+ profili utensile su bus CAN
* **[URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS)** - L'architettura, le interfacce, la base di sicurezza, la matrice delle capacita e il catalogo dei progetti generato dell'ecosistema, piu gli strumenti che confrontano tutti i repository
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
