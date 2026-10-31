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

---

**Verifica di onestà - cosa funziona davvero oggi:** **Maturità: consolidato (un'esecuzione completa documentata, non un uso prolungato).** Questo progetto adatta il design già collaudato di HYDRA-UMC-UPDATER (stessa scoperta tramite manifest, installazione/aggiornamento con clone temporaneo verificato in modo atomico e registro delle evidenze) ai soli repository dell'ecosistema URTC. È stato eseguito end to end contro GitHub in un'area di lavoro isolata: un'installazione pulita e un successivo aggiornamento di un repository reale sono stati clonati, compilati e promossi correttamente, conservando la copia precedente come backup. La logica di scoperta e di versione (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), il client GitHub raw-content con retry/backoff ed elenco dei repository in cache (`github_client.py`), il confronto per commit (`commits.py`) e la pipeline clona-prepara-verifica-promuovi (`install.py`) sono coperti da test (`python -m pytest`), compreso un server HTTP di prova locale e veri repository git temporanei con un remoto bare locale. La logica propria del bridge Qt gira senza schermo nei test, e la finestra con le sue finestre di dialogo viene caricata senza schermo per verificare che si apra e risponda; il suo aspetto si controlla a occhio, non con un test. La copertura a 8 lingue di `i18n.py` è verificata da test per chiavi e segnaposto, non per la qualità della traduzione. Vedi `CHANGELOG.md` per sapere esattamente cosa è stato consegnato finora.

---

> **Stato di sicurezza (safety e security):** questo ecosistema non è un sistema di sicurezza certificato e non esiste ancora alcuna scheda URTC assemblata. I bootloader controllano le immagini firmware con CRC32 e un HMAC-SHA256 a chiave condivisa, non con una firma asimmetrica (prevista); le immagini applicative pubblicate sono firmate con la chiave pubblica di sviluppo (`signing_key_kind: dev`), quindi chiunque può produrre un'immagine accettata dal bootloader; nulla è stato trasmesso a una scheda reale. Leggi la [base di sicurezza](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) e il [modello delle minacce](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md) prima di fidarti di qualsiasi affermazione qui per la sicurezza di una persona.

## 📋 In breve

| | |
|---|---|
| Versione | `0.2.0` |
| Maturità | Consolidato |
| Test | 500 (`python -m pytest`) |
| Tecnologia | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Destinazione | Il PC di chi lo usa |
| Su hardware reale | Non applicabile: nulla qui gira su hardware |

**Vai a:** [Panoramica](#-panoramica) · [Architettura](#-architettura) · [Sicurezza](#-sicurezza-e-protezione) · [Interfacce](#-interfacce) · [Avvio rapido](#-avvio-rapido) · [Test](#-test) · [Problemi](#-risoluzione-dei-problemi) · [Struttura](#-struttura-del-repository) · [Correlati](#-progetti-correlati)

<!-- urtc-section:status_updater -->
## 🚦 Stato del progetto

🟢 fatto e verificato · 🟡 funziona, con limiti noti · 🟠 a metà o non verificato · 🔴 non fatto o non funzionante. Nulla è verde se non ha mai girato su hardware reale.

| Parte | Stato | Ciò che il repository può dimostrare |
| --- | :---: | --- |
| Software | 🟡 | Funziona su un PC e contro il simulatore; mai usato con una scheda reale. |
| Interfaccia | 🟡 | La finestra funziona ed è verificata con una scheda simulata; non provata con un adattatore reale. |
| Test | 🟢 | La suite di test passa nella CI a ogni push. |
| Aggiornamenti | 🟡 | Installa da pacchetti firmati con ripristino; provato solo su PC. |
| Sicurezza | 🟡 | Le versioni sono firmate con Ed25519 e verificate prima dell'uso; la gestione delle chiavi non è stata rivista da nessun altro. |
| Documentazione | 🟡 | README in otto lingue e documenti di riferimento; le traduzioni non sono state riviste da madrelingua. |

<!-- /urtc-section:status_updater -->

## 🎯 Panoramica

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

Avviare `urtc-updater` senza argomenti (o con doppio clic) apre invece la
stessa informazione in una superficie di controllo desktop scura: un pannello
**Local Ecosystem** con metriche di rilevamento/installazione/aggiornamento in
tempo reale, un albero **Project Registry** guidato dai manifesti e un
pannello **Safe Update** per il progetto selezionato. La disposizione rende
visibili le vere protezioni: rilevamento tramite manifesto, una sola azione
esplicita su un progetto, conferma manuale, compilazione opzionale e una
traccia di attività a schermo; l'intero registro viene scritto anche in un
file sotto `~/.urtc_updater/logs` (vengono conservati i 20 più recenti).

## 🧩 Ruolo in URTC

URTC-UPDATER è il programma che tiene aggiornato un PC con i repository URTC. Trova ogni progetto accanto a sé dal manifesto che ogni repository porta, dice quale versione è installata e quale ha GitHub, e installa o aggiorna un progetto alla volta dopo una conferma esplicita, eseguendo lo script `build-test` di quel progetto e senza compilare nulla da sé. Non cambia nulla di propria iniziativa: una cella di controllo robot non deve mai aggiornarsi di notte senza che una persona approvi l'azione esatta. Installa anche i programmi desktop (il flasher, il tester e se stesso) dal pacchetto firmato della loro release, e può passare a URTC-FLASHER, che esegue il flashing, un'immagine firmware di cui ha verificato la firma di release.

## 🏛️ Architettura

<p align="center">
  <img src="images/architecture.svg" alt="Architettura di URTC-UPDATER: chi lo usa, che cosa contiene e da che cosa dipende" width="100%">
</p>

Come si incastrano le parti di questo repository: chi lo usa, che cosa contiene e da che cosa dipende. L'immagine è disegnata da `docs/architecture.json` e verificata rispetto al codice.

### COME FUNZIONA DAVVERO UN CONTROLLO/AGGIORNAMENTO

- **Fonte della versione**: la versione di un progetto vive in un file sorgente di quel progetto (`pyproject.toml`, `Cargo.toml`, `version.go`, `package.json`, `version.properties`, `pubspec.yaml` o un `#define` del firmware, a seconda della tecnologia) che scrive il suo stesso passo `bump.py`, e quel passo non ha mai creato un tag git né una Release di GitHub. Per questo lo strumento legge quello stesso file direttamente dal ramo predefinito del repository tramite l'host dei contenuti grezzi di GitHub, non tramite l'API delle Release, che direbbe che nessun progetto ha release.
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

### ARCHITETTURA E DECISIONI DI DESIGN

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

<!-- urtc-section:updates -->
### Come si aggiorna

Questo programma può cercare una versione più recente di sé stesso: il pulsante «Cerca aggiornamenti» interroga GitHub una volta e propone un pacchetto firmato solo se è per il tuo sistema e più recente. Nulla viene controllato o installato da solo a meno che tu non attivi il controllo, e un aggiornamento richiede la tua conferma. Il pacchetto deve corrispondere al suo SHA-256 e alla firma della chiave delle release fissata nel programma; la versione precedente viene conservata e ripristinata da sola se la nuova non si avvia. `urtc-updater --cli package list|check|install|rollback` fa lo stesso da riga di comando per il flasher e il tester, e `install --file` funziona senza rete.
<!-- /urtc-section:updates -->

## 🖼️ Schermate

<!-- urtc-shots -->
Catturate a 1920×1080 su un banco di prova, con dati di esempio e senza alcuna installazione reale dietro.

<table>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/deck.png" alt="La finestra su uno spazio di lavoro con la famiglia: ogni progetto con maturità, stack e versione locale, e le azioni di aggiornamento sicuro." width="100%"><br><sub>La finestra su uno spazio di lavoro con la famiglia: ogni progetto con maturità, stack e versione locale, e le azioni di aggiornamento sicuro.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/packages.png" alt="La finestra dei pacchetti: i programmi della famiglia che una versione pubblica come pacchetto firmato, ciascuno con il controllo della propria versione." width="100%"><br><sub>La finestra dei pacchetti: i programmi della famiglia che una versione pubblica come pacchetto firmato, ciascuno con il controllo della propria versione.</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/help.png" alt="La finestra della Guida: i passi per usare il programma, scritti nella lingua della finestra." width="100%"><br><sub>La finestra della Guida: i passi per usare il programma, scritti nella lingua della finestra.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/updates.png" alt="La finestra degli aggiornamenti: un pacchetto firmato più recente viene installato solo dopo la tua conferma." width="100%"><br><sub>La finestra degli aggiornamenti: un pacchetto firmato più recente viene installato solo dopo la tua conferma.</sub></td>
</tr>
</table>
<!-- /urtc-shots -->

Queste immagini mostrano la finestra reale, disegnata senza schermo com'è quando si apre (niente controllato, niente installato). La guida percorre la finestra, l'aiuto, la finestra di aggiornamento e quella dei pacchetti, e le mostra nelle otto lingue del programma.

[Guida con immagini](docs/WINDOW_GUIDE.md)

## 🔒 Sicurezza e protezione

| Minaccia | Difesa |
|---|---|
| Un aggiornamento che nessuno ha approvato, per esempio di notte su una cella robot | Niente cambia da solo: un'azione su un progetto richiede una conferma esplicita, un lotto si conferma a parte e procede un progetto alla volta |
| Un aggiornamento rotto o a metà rende inutilizzabile un'installazione funzionante | Il candidato viene clonato, unito in fast-forward (mai un reset forzato, così le modifiche locali falliscono in modo evidente) e compilato prima in un clone di preparazione; l'installazione in uso viene sostituita, con due rinomine di cartella, solo se quella compilazione riesce, e la precedente resta come `<nome>.backup-xxxxxxxx` |
| Una verifica che qui non può essere eseguita | Un build-test che risponde 75 significa che la validazione non è disponibile: l'aggiornamento viene rifiutato salvo che la persona lo accetti nelle impostazioni |
| Un commit che nessuno ha firmato | Una revisione senza firma valida viene rifiutata per impostazione predefinita; con `"signature_policy": "warn"` viene installata con un avviso |
| Un pacchetto manomesso | Un pacchetto è accettato solo se dimensione, SHA-256 e firma Ed25519 coincidono e viene dagli host di download di GitHub; si installa solo dopo una conferma, mai mentre gira un'altra installazione, e la versione precedente si può ripristinare |
| Si perde la traccia di ciò che è stato fatto | Ogni installazione, aggiornamento e ripristino viene scritto, con ora, macchina e utente, in un registro concatenato da hash |

Il resto della politica segue, con le parole del programma.

**Cosa può rispondere il build-test:** il codice di uscita 0 significa convalidato e qualsiasi altro significa fallito, tranne 75, che significa che la convalida è *non disponibile* (manca uno strumento necessario). Viene segnalato come tale e l'aggiornamento viene rifiutato, a meno che tu non lo accetti impostando `validation_unavailable` su `accept` nelle impostazioni (o `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). Un build-test deve lasciare l'albero come l'ha trovato: se cambia un file tracciato da git, il file viene riportato al contenuto registrato prima della promozione e i passaggi dicono quale.

**Commit firmati (richiesti per impostazione predefinita; tornare a un semplice avviso è una scelta esplicita):** una revisione senza firma valida (`git verify-commit`: portachiavi GPG, o SSH con `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) viene rifiutata. Con `"signature_policy": "warn"` in `~/.urtc_updater_settings.json` (o `URTC_UPDATER_REQUIRE_SIGNED=0`, o `--no-require-signed` per una esecuzione; il vecchio `"require_signed_commits": false` significa lo stesso) viene installata comunque, e i passi della finestra e della riga di comando dicono che non è firmata. Con il valore predefinito (`"signature_policy": "require"` o `URTC_UPDATER_REQUIRE_SIGNED=1`; il vecchio `"require_signed_commits": true` significa lo stesso) il candidato - l'`HEAD` di un clone nuovo o il `FETCH_HEAD` scaricato di un aggiornamento - deve superare `git verify-commit` prima di leggere il suo manifest o costruire qualcosa, e un candidato rifiutato lascia intatto il checkout installato.

**Opzioni di sicurezza (entrambe attive per impostazione predefinita; modificabili dal pulsante Sicurezza della finestra, dal comando `security`, dal file delle impostazioni, dall'ambiente e dalla riga di comando):** oltre a richiedere commit firmati, l'updater può *chiedere prima di eseguire il controllo di build* di un candidato (`"confirm_before_build": true`, il valore predefinito; `URTC_UPDATER_CONFIRM_BUILD=1`, `--confirm-build`). Scarica e convalida il candidato, mostra il progetto, il commit, il suo autore, la sua firma e gli script di build o di strumenti modificati, e non esegue nulla finché non rispondi; senza finestra né terminale a cui chiedere, fallisce in chiuso: non esegue né installa nulla e dice come rispondere. Le esecuzioni non presidiate rispondono sì in modo esplicito con `--yes`, `URTC_UPDATER_ASSUME_YES=1` o l'impostazione "assume_yes_without_asking": true (disattivata per impostazione predefinita). Con `"signature_policy": "warn"` e `"confirm_before_build": false` si torna al comportamento precedente. `--require-signed` / `--no-require-signed` e `--confirm-build` / `--no-confirm-build` valgono per una sola esecuzione, e un'esecuzione che disattiva una protezione attiva nelle impostazioni salvate lo segnala; la finestra, e `urtc-updater --cli security --require-signed off`, chiedono conferma prima di salvare un livello più basso. Un file di impostazioni che esiste ma non può essere letto conta come «firme richieste» finché non viene riparato o rimosso. Al controllo di build viene passato anche `URTC_PYTHON`, l'interprete che esegue l'updater, così un progetto prova con quel Python e non con il primo che il sistema trova.

## 🔌 Interfacce

Il programma apre la finestra Qt Quick quando viene avviato senza argomenti e ha una riga di comando completa con `--cli` (senza schermo né PySide6): `status [--offline]`, `install PROGETTO`, `update PROGETTO [--preview]`, `restore-backup PROGETTO [--list]`, `clean-backups [--keep N] [--dry-run]`, `check [--notify] [--quiet]` (codice di uscita 10 quando qualcosa si può aggiornare), `package list|check|install|rollback`, `evidence [--export FILE]` e `security`. Ogni comando, opzione e codice di uscita, con output reale, è in [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md); la finestra è descritta in [docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md). Che cosa fanno i comandi di manutenzione e di postazione:

- **Installazioni precedenti conservate.** Ogni aggiornamento conserva l'installazione sostituita in `<nome>.backup-xxxxxxxx`. Vengono tenute le 2 più recenti per progetto (`"backups_to_keep"` in `~/.urtc_updater_settings.json` cambia il numero) e quelle più vecchie vengono rimosse dopo un aggiornamento riuscito. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` le rimuove su richiesta, insieme a ogni cartella temporanea nascosta lasciata da un'esecuzione interrotta.
- **In via opzionale, installazione dal pacchetto firmato di una release.** `urtc-updater --cli package list|check|install|rollback` installa un programma (il flasher, il tester o questo updater) dallo `.zip` / `.tar.gz` della sua release, invece di un clone e di una compilazione. Si propone solo una versione strettamente superiore, solo dagli host di download di GitHub, e il pacchetto deve corrispondere a dimensione e SHA-256 annunciati e alla firma Ed25519 della chiave delle release fissata nel programma; un pacchetto che non supera un controllo viene eliminato. Chiede prima di installare (`--yes` risponde per gli script), conserva le due ultime release e `rollback` torna alla precedente. `install --file PACCHETTO` funziona da un file su disco con `.sha256` e `.sig` accanto, senza rete. La finestra ha un pulsante «Cerca aggiornamenti» per l'updater stesso con le stesse regole; il controllo automatico all'avvio è un'opzione, spenta per impostazione predefinita. Provato con pacchetti generati su un computer, non ancora con una release pubblicata.
- **Una finestra Pacchetti e una finestra Aiuto.** Il pulsante «Pacchetti» elenca i pacchetti firmati del flasher, del tester e di questo updater: ogni riga controlla la sua versione quando premi «Cerca aggiornamenti», scarica e verifica il pacchetto, chiede prima di installare e torna alla versione precedente, con le stesse regole e opzioni di sicurezza del comando `package`; non si installa nulla mentre un progetto viene installato o aggiornato. Il pulsante «Aiuto» apre una guida in cinque passi nella lingua della finestra.
- **Ripristinarne una.** `urtc-updater --cli restore-backup <PROGETTO> [--backup CARTELLA] [--list]` rimette a posto un'installazione conservata. Anche l'installazione sostituita viene conservata, quindi lo scambio si può annullare. La finestra offre le stesse due azioni accanto ad Aggiorna selezionato: Anteprima dell'aggiornamento (cosa porterebbe, senza modificare nulla) e Ripristina la versione precedente.
- **Stessa versione, nuovi commit.** La versione cambia solo in un build di rilascio, quindi `status` confronta anche il commit di ogni progetto installato con quello remoto (`git ls-remote`) e mostra `NEW COMMITS` quando GitHub ha lavoro che la copia non ha. La finestra mostra lo stesso stato e offre l'aggiornamento.
- **Guardare prima di approvare.** `urtc-updater --cli update <PROGETTO> --preview` scarica il candidato e mostra il suo commit, autore, versione, stato della firma e i file di build o di strumenti che modifica, senza toccare la copia.
- **Solo avviso.** `urtc-updater --cli check [--notify] [--quiet]` elenca ciò che si potrebbe aggiornare e non cambia nulla. Termina con codice 10 quando c'è qualcosa da aggiornare, così un'attività pianificata può avvisare una persona; `--notify` mostra anche una notifica desktop.
- **Evidenze.** Ogni installazione, aggiornamento e ripristino viene registrato con ora, macchina e utente in `.urtc-updater/evidence.jsonl`, con ogni riga concatenata alla precedente tramite hash. `urtc-updater --cli evidence [--export FILE]` verifica la catena e può esportarla come un unico documento JSON.
- **Profili di postazione.** `"profiles"` nel file delle impostazioni indica i progetti con cui lavora una macchina e se i lotti sono consentiti; `--profile NOME` (o `"profile"` nelle impostazioni) vi limita `status`, `check`, `install` e `update`, e la finestra segue lo stesso profilo.

## 🚀 Avvio rapido

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

<!-- urtc-section:compatibility -->
### Requisiti e compatibilità

Quali versioni dei programmi URTC funzionano insieme, e quale versione del protocollo parla ciascuna, è elencato nella tabella di compatibilità generata da URTC-COMMON: [docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md).
<!-- /urtc-section:compatibility -->

## 🧪 Test

La suite ha 500 test (`QT_QPA_PLATFORM=offscreen python -m pytest tests -q`; alcuni vengono saltati se manca una dipendenza opzionale): il rilevamento e i manifesti, l'unico parser di versioni, il client GitHub contro un server locale (tentativi, errori, un catalogo malformato), installazione e aggiornamento su veri repository git locali (preparazione, promozione, backup, rifiuti, un build-test che risponde 75, sicurezza dell'area di lavoro), ripristino e pulizia dei backup, la politica dei commit firmati, le opzioni di sicurezza, i pacchetti firmati e il loro rollback, la catena delle prove, impostazioni e profili, i testi della finestra nelle otto lingue e il ponte Qt, e le immagini della guida della finestra, disegnate senza schermo. `python -m mypy` e `ruff check .` girano in CI.

## 🏗️ Compilazione e rilascio

`build.sh` / `build.bat` creano il `.venv`, installano il pacchetto (`pip install -e .`, con l'ambiente Qt per la finestra) e controllano la compilazione di tutto; `build-test.sh` / `build-test.bat` controllano senza installare; `run.sh` / `run.bat` aprono la finestra, o la riga di comando con `--cli`; `run-gui.vbs` la apre su Windows senza finestra di console. Un eseguibile autonomo confezionato non viene ancora costruito.

## 🩺 Risoluzione dei problemi

- `status` mostra `?` nella versione GitHub di un progetto: non è stato possibile leggere GitHub per esso. La colonna STATE dice perché (per esempio `installed, GitHub unknown (HTTP 404)` o un avviso di limite di richieste).
- `status` mostra `-` per GitHub senza alcun errore mostrato: esegui
  `status` (senza `--offline`) - `-` appare solo quando il controllo
  GitHub è stato saltato del tutto.
- `install`/`update` fallisce con "No non-versioning build-test.sh/.bat found": quella copia non ha `build-test.sh` (`build-test.bat` su Windows). Aggiorna il progetto stesso o verificalo a mano; questo strumento non esegue mai al suo posto uno script di build che incrementa la versione.
- `git pull --ff-only` fallisce: il checkout locale ha modifiche non
  committate o la cronologia è divergente - risolvilo manualmente (`git
  status` nella directory propria del progetto) prima di riprovare
  `update`. Questo strumento non forza mai un reset di un checkout.

## 📂 Struttura del repository

<p align="center">
  <img src="images/repository-structure.svg" alt="Struttura del repository URTC-UPDATER" width="100%">
</p>

<details>
<summary>Versione testuale dell'albero</summary>

```text
URTC-UPDATER/
├── src/urtc_updater/                                  il programma: rilevamento, versioni, installazione e aggiornamento, sicurezza, pacchetti firmati, la finestra Qt Quick e i suoi testi in otto lingue
├── tests/                                             test reali per ogni modulo
├── docs/                                              riferimento dei comandi, interfaccia e guida della finestra
├── tools/                                             controllo di compilazione, schermate, icona e strumenti condivisi
├── images/                                            banner e immagini di questo README
├── .github/                                           workflow di CI e modelli per issue e pull request
├── build.sh build.bat                                 script di compilazione
├── build-test.sh build-test.bat                       script di compilazione e test che non cambiano nulla nel repository
├── test.sh test.bat                                   eseguono i test
├── run.sh run.bat                                     avviano il programma
├── urtc.project.json                                  manifesto: versione, ruolo, maturità e comando di compilazione
├── CHANGELOG.md                                       che cosa è cambiato in ogni versione
├── SECURITY.md SUPPORT.md LICENSE                     politica di sicurezza, supporto e licenza
├── CONTRIBUTING.md CODE_OF_CONDUCT.md                 come contribuire e codice di condotta
├── .gitattributes .gitignore                          impostazioni di Git
├── run-gui.vbs                                        avvio per Windows senza finestra di console
├── bump.py bump_version.py bump_manifest_version.py   script che alzano la versione
├── urtc_i18n.lock.json                                blocco dei testi della finestra
├── LICENSE.md .env.example                            licenza della documentazione e variabili
└── pyproject.toml requirements-dev.lock ruff.toml     pacchetto, strumenti bloccati, impostazioni di lint e blocco dei testi
```

</details>

L'elenco annotato di ogni file sorgente, una riga per file, è in [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md).

## 🗺️ Roadmap e limiti noti

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

## 🌍 Lingue

Il README e i testi esistono in inglese, spagnolo, francese, italiano, tedesco, cinese, giapponese e portoghese europeo.

## 🔗 Progetti correlati

URTC è fatto di repository indipendenti, ciascuno con la propria versione, i propri test e il proprio README. Ecco la famiglia, per gruppi:

* **URTC Tool Platform:**
  * [URTC](https://github.com/JuanenRac/URTC) - firmware della scheda della testa utensile (25 profili utensile, bootloader CAN) e riferimento del protocollo CAN.
  * [URTC-COMMON](https://github.com/JuanenRac/URTC-COMMON) - il protocollo CAN scritto una sola volta come dati (specifica, tabelle generate, vettori di conformità) e il codice condiviso dai programmi.
  * [URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER) - strumento desktop che aggiorna il firmware della scheda via CAN o via SWD/JTAG.
  * [URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY) - gateway davanti al bus CAN: lascia passare solo gli identificatori di un elenco, ne limita la frequenza e chiede una chiave di sessione.
  * [URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK) - logica C indipendente dall'hardware e protocollo di comandi per un portautensili con preriscaldamento e tracciamento del ciclo di vita.
  * [URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER) - tester desktop del bus CAN in tempo reale che mostra i comandi e la telemetria del profilo utensile segnalato da una scheda.
  * [URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL) - protocollo di frame del sensore in C e un companion Python termico/RGB per una testa utensile di ispezione.
  * [URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO) - app per browser che programma e collauda la scheda via Web Serial e SLCAN, senza installare nulla.
* **Ecosystem Operations:**
  * [URTC-DEVTOOLS](https://github.com/JuanenRac/URTC-DEVTOOLS) - gli strumenti di repository condivisi della famiglia come un insieme versionato, con un file di lock che distingue una copia modificata da una rimasta indietro.
  * [URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS) - architettura, interfacce, base di sicurezza e catalogo generato dell'ecosistema, più gli strumenti che confrontano tutti i repository.
  * **URTC-UPDATER** (questo repository) - strumento desktop che rileva, installa e aggiorna i repository della famiglia URTC, un'azione esplicita alla volta.

**Progetti fratelli (indipendenti, con la stessa base e gli stessi strumenti):**

* **[HYDRA-UMC-DOCS](https://github.com/JuanenRac/HYDRA-UMC-DOCS)** - progetto fratello: il centro di documentazione di HYDRA-UMC, un ecosistema indipendente che condivide base e strumenti con questo
* **[ARMOR-DOCS](https://github.com/JuanenRac/ARMOR-DOCS)** - progetto fratello: il centro di documentazione di A.R.M.O.R., l'ecosistema di sicurezza, anch'esso indipendente e sulla stessa base
* **[JuanenRac](https://github.com/JuanenRac/JuanenRac)** - il profilo e il pannello di stato di tutti gli ecosistemi

## 📚 Documentazione

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — ogni sottocomando `--cli`, output reale catturato da un'esecuzione reale installata, e il contratto dei codici di uscita.
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — come e strutturato il client desktop Qt Quick/QML, e come resta una vera superficie di controllo sullo stesso backend usato da `--cli`, non una seconda implementazione.
* **[Changelog di questo repository](CHANGELOG.md)**
* Domande, idee e segnalazioni: electrohobby3d@gmail.com

## 🤝 Contribuire e comunità

* Prima di una pull request esegui `URTC_CI=1 python tools/ci_validate.py`: deve passare. Vedi [CONTRIBUTING.md](CONTRIBUTING.md) e il [codice di condotta](CODE_OF_CONDUCT.md).
* Il README esiste in otto lingue: una modifica del testo si fa in tutti e otto i file, e le sezioni condivise con altri repository le scrive `tools/readme_sections.py` di URTC-COMMON.
* Una modifica al protocollo CAN parte da URTC-COMMON (`spec/can_protocol.json`) e arriva in questo repository tramite la copia verificata.
* Non descrivere come funzionante su una scheda ciò che è stato solo compilato.
* Segnala una vulnerabilità in privato: [SECURITY.md](SECURITY.md). Domande, idee e segnalazioni: electrohobby3d@gmail.com ([SUPPORT.md](SUPPORT.md)).

## 👤 AUTORE

**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LICENZA

GPL-3.0-or-later - vedi [LICENSE](LICENSE).
