<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | 🇩🇪 <b>Deutsch</b> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a></p>

### 📦 Erkennt, installiert und aktualisiert das gesamte URTC-Ökosystem von Hand

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0">
  <img src="https://img.shields.io/badge/Language-Python%203.10%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="stdlib-only CLI core">
  <img src="https://img.shields.io/badge/Desktop-PySide6%20%7C%20Qt%20Quick-367BF5.svg" alt="PySide6 Qt Quick desktop GUI">
</p>

> **Visueller Desktopmodus:** die Standard-Desktopoberfläche nutzt jetzt
> **Qt Quick / QML** mit der optionalen GUI-Laufzeit `PySide6`. Kern und
> `--cli` bleiben für eine headless CM5 reine Standardbibliothek.
>
> **Windows-Start und Nachweise:** öffnen Sie `run-gui.vbs` (oder `run.bat`
> ohne Argumente) für den konsolenfreien Desktop-Client. Das Update-Panel zeigt
> echte Checkpoints für Vorabprüfung, Quelle, Manifest, Build-test und Abschluss
> mit erfassten Nachweisen; `run.bat --cli ...` behält das Diagnose-Terminal.
> Installieren ist nur ohne Checkout aktiv, Aktualisieren nur bei neuerer
> GitHub-Version. Während einer bestätigten Aktion ersetzen Checkpoints die
> Projektsteuerung; eine neue Projektauswahl stellt sie wieder her.
> **Alle fehlenden installieren** und **Alle veralteten aktualisieren** sind
> separat bestätigte, sequenzielle Sammelaktionen auf Basis desselben realen
> Zustands und Sicherheitswegs.

**Ehrlichkeitscheck - was heute wirklich funktioniert:** die ökosystemweite Discovery-/Versionslogik (`registry.py`, `project_manifest.py`, `ecosystem_catalog.py`, `version_parse.py`, `detect.py`), der echte GitHub-Raw-Content-Client mit Retry/Backoff (`github_client.py`) und die Clone-Stage-Verify-Promote-Logik der Installations-/Update-Pipeline (`install.py`) sind real und getestet - 64 bestandene Tests (`pytest tests/`), einschließlich eines Fixture-HTTP-Servers, der die Isolation zwischen einem fehlerhaften Katalog und einem einzelnen fehlerhaften Projekt beweist, plus echter Temp-Verzeichnis-Git-Clone/Build-Round-Trips. `--cli status`/`install`/`update` durchlaufen denselben getesteten Kern end-to-end gegen den echten, live GitHub-Raw-Content-Host (kein Mock), sobald man sie tatsächlich ausführt. Die Qt-Quick-Desktop-GUI (`qt_gui.py`, `qml/Main.qml`) und der alte Tkinter-Fallback (`gui.py`) verdrahten denselben getesteten Kern mit einem echten Fenster und wurden auf echten Ökosystem-Checkouts ausgeführt, aber keine der beiden hat einen eigenen automatisierten Test - es gibt kein `test_gui.py`/`test_qt_gui.py`, da hier keine echte Qt/Tk-Ereignisschleife angesteuert wird. Die 7-Sprachen-Abdeckung von `i18n.py` wird durch einen Test erzwungen (`test_i18n.py`), aber nur für Schlüssel-Parität zwischen Sprachen, nicht für Übersetzungsqualität. Siehe `CHANGELOG.md` für das, was bisher genau ausgeliefert wurde.

---

## 1. 🛠️ TECHNISCHER ÜBERBLICK

URTC-UPDATER ist ein kleines Tool - Fenster-GUI standardmäßig, volle
CLI mit `--cli` - das sowohl auf dem echten CM5 als auch auf dem eigenen
Windows/Linux/macOS-Rechner eines Entwicklers laufen soll (jeder
Workspace mit demselben Checkout-Layout) und drei Fragen für jedes
andere echte Projekt beantwortet, das es über das eigene
`urtc.project.json`-Manifest jedes Nachbar-Checkouts entdeckt - die
Anzahl selbst ist hier nie fest codiert, da sie mit dem Ökosystem wächst:

1. **Was ist hier tatsächlich installiert, und in welcher Version?**
2. **Was ist die neueste auf GitHub veröffentlichte Version?**
3. **Falls GitHub neuer ist, lass mich ein Projekt oder eine bestätigte sequenzielle Sammelaktion wählen.**

Dieser letzte Punkt ist bewusst und nicht verhandelbar: Dieses Tool ändert
nie ein Projekt aus eigener Initiative. Eine Aktion für ein ausgewähltes
Projekt verlangt immer eine ausdrückliche Bestätigung. Die GUI kann auch
**Alle fehlenden installieren** oder **Alle veralteten aktualisieren**
anbieten; beides sind getrennt bestätigte, sequenzielle Sammelaktionen mit
denselben Manifest-, Versions- und Sicherheitsprüfungen. Es gibt kein
unbeaufsichtigtes nächtliches Auto-Update.

Auch gehört nicht jedes entdeckte Projekt auf den CM5 - die meisten
URTC-präfixierten Repos und einige von HYDRA-UMC sind Werkzeuge, die ein
Entwickler auf dem eigenen PC ausführt (Firmware wird VOM Arbeitsplatz
kompiliert und geflasht, nicht AUF der Zelle gebaut), oder Apps, die auf
einem Handy/einer Uhr installiert werden. Das eigene `deploy`-Feld von
`registry.py` verzeichnet, welches welches ist (siehe Abschnitt 3), und
die Projekttabelle der GUI filtert danach - standardmäßig wird nur "CM5"
angezeigt, wenn erkannt wird, dass sie unter Linux läuft (dem eigenen OS
des echten CM5), und "alles anzeigen" unter Windows/macOS.

Illustratives Beispiel (die genaue Projektanzahl und jede Versionsnummer
unten sind für die Form der Ausgabe frei erfunden, kein echter erfasster
Lauf - die echte Anzahl ist immer das, was `registry.py` heute entdeckt,
niemals eine in diesem Dokument fest codierte Zahl):

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

`urtc-updater` ohne Argumente aufzurufen (oder per Doppelklick)
öffnet dieselbe Information in einem Fenster - eine Projekttabelle, ein
Filter nach Deployment-Ziel, und Installieren/Aktualisieren-Schaltflächen
für die ausgewählte Zeile.

<p align="center">
  <img src="images/" alt="Echte URTC-UPDATER Desktop-Übersicht" width="100%">
</p>

## 2. 🔄 WIE EINE PRÜFUNG/AKTUALISIERUNG WIRKLICH FUNKTIONIERT

- **Versionsquelle**: Die "Kilometerzähler"-Auto-Inkrement-Konvention
  dieses Ökosystems (jeder echte Build erhöht eine Versionsnummer, die
  IN einer Quelldatei lebt - `pyproject.toml`, `Cargo.toml`,
  `version.go`, `package.json`, `version.properties`, `pubspec.yaml`
  oder ein Firmware-`#define`, je nach Stack des Projekts) hat nie einen
  Git-Tag oder ein GitHub-Release für diesen Sprung erzeugt. Dieses Tool
  liest daher DIESELBE Datei, die das eigene `bump_version.py`/
  Build-Skript jedes Projekts bereits schreibt, direkt vom
  Standard-Branch des Repos über GitHubs Raw-Content-Host - nicht die
  Releases-API, die melden würde, dass alle Projekte keinerlei Releases
  haben.
- **Lokale Erkennung**: Für jedes entdeckte Projekt wird
  geprüft, ob ein Verzeichnis mit genau diesem Namen unter der
  Workspace-Wurzel existiert (das Standard-Layout des Ökosystems - jedes
  Projekt als Geschwisterverzeichnis, genau das, was build-frontend.sh/
  HYDRA-UMC-SUITEs eigene Discovery bereits voraussetzen), und falls ja,
  wird dessen eigene lokale Kopie derselben Versionsdatei gelesen.
- **Eine einzige Parsing-Implementierung** (`version_parse.py`) wird
  zwischen dem lokalen Lesen und dem GitHub-Abruf geteilt, sodass ein
  lokaler Checkout und ein GitHub-Abruf niemals von zwei unabhängig
  auseinanderdriftenden Regexes interpretiert werden.
- **Installieren/Aktualisieren**: `git clone` (Installation) baut
  danach als separaten Schritt. Das Aktualisieren eines BEREITS
  BESTEHENDEN Checkouts ist stattdessen atomar-durch-Verifikation: der
  Kandidat wird geklont, per Fast-Forward gemergt (nie ein erzwungener
  Reset, sodass echte lokale Änderungen laut fehlschlagen statt verworfen
  zu werden) und ZUERST in einem vollständig unabhängigen Staging-Klon
  gebaut/verifiziert - die laufende Installation wird nur (über zwei
  aufeinanderfolgende Verzeichnis-Umbenennungen, die vorherige
  Installation bleibt unter `<name>.backup` erhalten, statt gelöscht zu
  werden) angefasst, wenn dieser Staging-Build tatsächlich erfolgreich
  ist. Ein Build-Fehler, ein divergierender/schmutziger Checkout, ein
  Absturz oder eine volle Festplatte an jedem Punkt vor dieser
  endgültigen Beförderung lassen die vorherige Installation vollständig
  unangetastet und weiterhin betriebsbereit - siehe den eigenen
  Docstring von `clone_or_pull` in `install.py`. Das eigene Git-Remote
  des Staging-Klons wird gleich nach dessen Erstellung auf das echte
  GitHub-Upstream zurückgesetzt (ein einfacher lokaler Klon würde
  andernfalls weiterhin auf den alten Installationspfad zeigen und nach
  der Beförderung still alle künftigen Updates beenden), und die echten
  lokalen Daten des installierten Checkouts (alles, was Git als
  unversioniert oder ignoriert betrachtet - `data/settings.json` und
  Ähnliches, ohne regenerierbare Build-Artefakte) werden vor dem Bauen
  in den Staging-Klon übernommen, sodass der echte Betriebszustand eines
  Projekts ein Update übersteht, statt im aufbewahrten `.backup`-
  Checkout gestrandet zu bleiben. So oder so wird das
  eigene `build-test.sh`/`build-test.bat` dieses Projekts (die nicht-
  versionierende Prüfung - siehe Abschnitt 3) ausgeführt, falls
  vorhanden. Dieses Tool reimplementiert nie die eigenen Build-Schritte
  eines Projekts.

<p align="center">
  <img src="images/" alt="Echte URTC-UPDATER Checkpoints während Installation oder Aktualisierung" width="100%">
</p>

## 3. 🧱 ARCHITEKTUR UND DESIGN-ENTSCHEIDUNGEN

- **Qt-Quick-GUI standardmäßig, `--cli` für Headless.** `main.py` prüft
  `--cli`, bevor die optionale PySide6-Laufzeit importiert wird. Die CLI
  funktioniert auf einer CM5 ohne Display und Desktop-Abhängigkeit; ohne
  Argumente startet QML, sofern verfügbar, und Tkinter bleibt nur Fallback.
- **Die Fenster-GUI ist echt und mehrsprachig in 7 Sprachen (`i18n.py`) - `--cli` ist es absichtlich nicht.** Jedes echte Widget benennt sich live aus einer Sprach-`Combobox` neu (en/es/fr/it/de/zh/ja, dieselben 7, die das öffentliche Dashboard und jede README ausliefern), erkannt aus einer gespeicherten Präferenz oder dem eigenen Locale des Betriebssystems. Projekt-/Familiennamen sowie der echte `notes`/`tech`-Text jedes Projekts bleiben unübersetzt - `registry.py` ist ihre einzige Quelle der Wahrheit, und 7 parallele Kopien echter Engineering-Dokumentation würden genau das verhindern. Die `--cli`-Ausgabe bleibt absichtlich nur auf Englisch: Sie ist zum Skripten/Weiterleiten gedacht, wo stabiler, grep-barer Text mehr zählt als Lokalisierung.
- **`deploy` ist eine Klassifizierung, keine Einschränkung.** Jedes
  entdeckte Projekt als "ein Ding, das auf den CM5 gehört" zu behandeln, war falsch
  - Firmware-Repos werden VON einem PC kompiliert und geflasht (der CM5
  braucht nur die resultierende Binärdatei über CAN-OTA, nie den
  eigenen Quellcode dieses Repos), und mehrere Werkzeuge (URTC-FLASHER,
  HYDRA-UMC-SUITE, HYDRA-UMC-TOOL-CLI, ...) sollen auf dem eigenen
  Arbeitsplatz eines Bedieners laufen, nicht innerhalb der Zelle selbst.
  Das `deploy`-Feld von `registry.py` ("cm5" / "user-pc" / "mobile" /
  "wearable" / "dev-server") verzeichnet das, und der GUI-Filter verwendet es als
  sinnvollen Ausgangspunkt - nie als harte Einschränkung, da dieses
  selbe Tool auch auf dem eigenen PC eines Entwicklers laufen soll, wo
  jedes entdeckte Projekt gleichermaßen zulässig zu inspizieren ist.
- **Keine stack-spezifische Build-Logik in diesem Tool.** Das Ökosystem
  umfasst 7 Toolchains (Python, Rust, Go, Node/TS, Android/Kotlin,
  Flutter, ARM-Firmware). `npm install && npm run build` / `cargo build
  --release` / `./gradlew assembleDebug` / usw. HIER
  zu reimplementieren würde einen zweiten Ort schaffen, der
  vorgibt zu wissen, wie jedes Projekt gebaut wird - garantiert vom
  echten (und bereits korrekten) `build.sh`/`.bat` dieses Projekts
  abzudriften. `install.py` sucht stattdessen nach einem bekannten
  Build-Skript-Namen (`build.sh`, `build_firmware.sh`, `build_exe.sh`,
  `build-android.sh` und ihren `.bat`-Äquivalenten - die realen Namen,
  die über die eigenen entdeckten Projekte des Ökosystems hinweg
  verwendet werden) und führt aus, was existiert.
- **GitHub-Rohinhalt, nicht die Releases-API.** Siehe Abschnitt 2 oben -
  die Versionierungskonvention dieses Ökosystems erzeugt nie ein
  Tag/Release, daher wäre die Releases-API hier aktiv falsch, nicht nur
  weniger bequem.
- **Ein vorübergehender Netzwerkfehler bekommt einen echten
  Wiederholungsversuch; eine definitive Antwort nie.** Jede echte
  GitHub-Anfrage (`_urlopen_with_retries` in `github_client.py`)
  wiederholt bis zu 3-mal mit Backoff, aber nur, wenn die Verbindung
  überhaupt keine Antwort erhalten hat (DNS/Timeout/Reset). Ein echter
  HTTP-Status, den GitHub tatsächlich zurückgegeben hat - 404, 403, 500 -
  wird nie wiederholt: GitHub hat bereits geantwortet, und ein erneuter
  Versuch würde nur mehr Rate-Limit für dasselbe Ergebnis verbrauchen.
- **Ein fehlerhafter entfernter Katalog schlägt laut fehl; ein
  fehlerhaftes Projekt nicht.** Wenn die GitHub-Repository-Liste selbst
  nicht erreichbar oder nicht parsbar ist, löst `discover_remote_projects()`
  eine Ausnahme aus - sowohl `gui.py` als auch `main.py` fangen sie
  bereits ab und fallen auf die lokal entdeckte Projektliste zurück,
  statt einen defekten oder leeren Scan anzuzeigen. Das fehlerhafte
  Manifest eines einzelnen Repositorys wird dagegen in die eigene
  `errors`-Liste dieses Scans isoliert und bricht die Entdeckung des
  restlichen Katalogs nie ab - ein echter Test mit Fixture-Server
  (`tests/test_github_client.py`) belegt beide Pfade.
- **Die CLI bleibt explizit; GUI-Sammelaktionen bleiben bestätigt.** Die
  CLI-Befehle `install`/`update` erwarten einen Projektnamen. Die GUI kann
  **Alle fehlenden installieren** oder **Alle veralteten aktualisieren**, aber
  nur nach separater Bestätigung und nacheinander durch dieselben
  Sicherheitsprüfungen. Es gibt kein unbeaufsichtigtes automatisches Update.
- **Nur Standardbibliothek.** `urllib` für die GitHub-Abrufe
  (`github_client.py`), `subprocess` für git-/Build-Skript-Aufrufe
  (`install.py`), sonst nichts - dass ein Tool, das für die
  Abhängigkeits-Gesundheit ALLER anderen Projekte verantwortlich ist,
  selbst ohne Abhängigkeiten bleibt, ist bewusst.
- **Bekannte Vereinfachung**: HYDRA-UMC und URTC sind echte
  Mehrkomponenten-Firmware-Repos (6 bzw. 4 unabhängig versionierte
  Binärdateien - siehe deren eigene `VERSION_CHECKLIST.txt`/
  `build_firmware.sh`) ohne eine einzige "die" Versionsnummer.
  `registry.py` verfolgt EINE repräsentative Komponente pro Repo - genug,
  um "ist dieses Repo ungefähr aktuell?" zu beantworten, kein Ersatz für
  `build_firmware.sh`s eigene `firmware_manifest.json` für ein echtes
  Flashen.

## 📂 VERZEICHNISSTRUKTUR

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - kein statischer Katalog; wird zur Erkennungszeit aus dem eigenen Manifest jedes Repos gebaut
│   ├── project_manifest.py # Liest/validiert eine repository-eigene urtc.project.json
│   ├── ecosystem_catalog.py # Parser für den öffentlichen JuanenRac-Ökosystem-Erkennungskatalog
│   ├── version_parse.py   # EINE Regex-Extraktions-Implementierung, lokal+GitHub
│   ├── detect.py          # Scannt eine Workspace-Wurzel nach Installiertem
│   ├── github_client.py   # Nebenläufiger Abruf des Rohinhalts + echter Wiederholungsversuch/Backoff bei vorübergehenden Netzwerkfehlern
│   ├── install.py         # git clone/pull + delegiert an das eigene Build-Skript
│   ├── i18n.py             # Echte, vollständige GUI-Übersetzungen (7 Sprachen)
│   ├── qt_gui.py           # Qt-Quick-Brücke zu realen Erkennungs-/Update-Diensten
│   ├── qml/Main.qml        # Desktop-Shell mit Theme, Checkpoints und About
│   ├── gui.py              # Tkinter-Fallback falls PySide6 nicht verfügbar ist
│   └── main.py             # Dispatch: GUI standardmäßig, --cli für status/install/update
├── tests/                  # Echte Tests: github_client, i18n, install, project_manifest, registry
├── docs/
│   ├── CLI_REFERENCE.md     # Befehlsreferenz
│   └── QML_DESKTOP_GUI.md   # Qt-Quick-GUI-Architektur
├── images/                 # Medien, App-Icons und Interface-Screenshots
├── tools/
│   ├── build_test.py        # Nicht-versionierender Build-Check
│   ├── ci_validate.py       # Manifest/CHANGELOG/Docs-Validierung, von CI genutzt
│   ├── generate_app_icon.py # Rendert das öffentliche HYDRA-UMC-SVG in das von Windows genutzte Icon
│   ├── migrate_project_manifests.py  # Prüft einen Workspace nach der einmaligen Manifest-Migration
│   └── validate_project_manifests.py # Validiert repository-eigene Manifeste + native Build-Versionen
├── .env.example            # Umgebungsvariablen-Vorlage
├── build.sh / build.bat    # venv + editierbare Installation + Compile-Check
├── run.sh / run.bat        # Standard-GUI / CLI-Einstieg
├── run-gui.vbs             # Windows-GUI-Starter ohne Konsole
├── bump_version.py         # Ökosystemweiter "Kilometerzähler"-Sprung (pyproject.toml + __init__.py)
└── bump_manifest_version.py # Synchronisiert die Version von urtc.project.json mit der nativen (--sync)
```

## ⚙️ BUILD UND AUSFÜHRUNG

```bash
chmod +x build.sh   # einmalig
./build.sh          # erstellt .venv, pip install -e ., Compile-Check von allem
./run.sh                              # Fenster-GUI (standardmäßig)
./run.sh --cli status                 # was installiert ist, lokale vs. GitHub-Version
./run.sh --cli status --offline       # dasselbe, ohne GitHub-Prüfung
./run.sh --cli install <PROJEKT-NAME> # klont + baut ein noch nicht installiertes Projekt
./run.sh --cli update  <PROJEKT-NAME> # aktualisiert + baut ein bereits installiertes Projekt neu
```

Unter Windows: `build.bat`, dann `run.bat` (GUI) / `run.bat --cli status`
/ `run.bat --cli install <Name>` / `run.bat --cli update <Name>`.

Die bevorzugte GUI braucht die optionale Qt-Laufzeit (`pip install -e ".[gui]"`;
`build.bat`/`build.sh` installieren sie bereits). `--cli` hat keine GUI-
Abhängigkeit und ist der richtige Einstieg für eine headless CM5. Ohne Qt
bleibt das alte Tkinter-Fenster nur ein Kompatibilitäts-Fallback.

**Fehlerbehebung**

- `status` zeigt `?` für die lokale oder GitHub-Version eines Projekts:
  Dessen Versionsdatei existiert, aber die Konvention dieses Projekts hat
  sich seit der letzten Aktualisierung von `registry.py` geändert -
  prüfen Sie den Eintrag dieses Projekts in `registry.py` gegen dessen
  echte, aktuelle Versionsdatei.
- `status` zeigt `-` für GitHub ohne angezeigten Fehler: führen Sie
  `status` aus (ohne `--offline`) - `-` erscheint nur, wenn die
  GitHub-Prüfung komplett übersprungen wurde.
- `install`/`update` schlägt fehl mit "No build.sh/.bat found": Dieses
  Projekt verwendet einen Build-Skript-Namen, den dieses Tool noch nicht
  kennt - prüfen Sie dessen eigenes README für den echten Namen und
  erwägen Sie, ihn zu den eigenen `BUILD_SCRIPT_CANDIDATES_*`-Listen von
  `install.py` hinzuzufügen.
- `git pull --ff-only` schlägt fehl: Der lokale Checkout hat nicht
  committete Änderungen oder die Historie ist auseinandergelaufen -
  lösen Sie das manuell (`git status` im eigenen Verzeichnis des
  Projekts), bevor Sie `update` erneut versuchen. Dieses Tool erzwingt
  nie einen Reset eines Checkouts.

## 🚀 FAHRPLAN

- Eine gepackte eigenständige GUI-ausführbare Datei (PyInstaller, nach der
  eigenen `build_exe.bat`/`.sh`-Konvention von HYDRA-UMC-SUITE) für eine
  Doppelklick-Installation ganz ohne `pip`/venv-Schritt - heute braucht
  die GUI noch vorher `./build.sh`, genau wie die CLI.
- Optionale Abhängigkeits-Vorprüfung pro Projekt (fehlende Toolchains
  melden - kein Rust/Go/Android-SDK/Flutter installiert - bevor ein
  `install` mittendrin fehlschlägt).
- Ein `--json`-Ausgabemodus für `status`, um es skriptbar zu machen.
- Komponentenweise Nachverfolgung für die eigene Mehrbinär-Firmware von
  HYDRA-UMC/URTC (siehe die "bekannte Vereinfachung" in Abschnitt 3),
  sobald ein echter Bedarf über die heute verfolgte einzelne
  repräsentative Komponente hinaus besteht.

## 🔗 Verwandte Projekte

**URTC** (Universal Robot Tool Controller) ist eine echte physische Werkzeugwechsel-Plattform desselben Autors (JuanenRac / Electro Hobby 3D). Jedes Repository hat seine eigene Version, seine eigenen Tests und sein eigenes README; das ist die ganze Familie:

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware fuer die physische Universal-Robot-Tool-Controller-Platine, 25+ Werkzeugprofile ueber CAN-Bus
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - Desktop-GUI-Flash-Tool fuer URTC-Platinen, CAN-OTA plus vollstaendiges SWD/JTAG
* **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** - Firmware fuer ein Werkzeug-Montagerack mit echter Werkzeug-ID-Dekodierung und Smart-Idle-Vorheizung
* **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** - Desktop-Live-CAN-Bus-Diagnosetool fuer URTC-Platinen, ein Panel pro Werkzeugprofil
* **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** - Firmware plus ein echter Python-Vision-Begleiter fuer einen Thermal-/RGB-Inspektionskopf
* **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** - Browserbasierte Alternative zu URTC-TESTER ueber die Web Serial API, keine lokale Installation noetig
* **URTC-UPDATER** (dieses Repository) - Erkennt, installiert und aktualisiert die eigenen Repositories des Oekosystems

Das Design dieses Tools (Manifest-Erkennung, atomar-durch-Verifikation Installation/Aktualisierung, Nachweisprotokoll) wird geteilt mit **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** und **[ARMOR-UPDATER](https://github.com/JuanenRac/ARMOR-UPDATER)** - den eigenen Updatern desselben Autors fuer die Oekosysteme HYDRA-UMC und A.R.M.O.R., jeweils nur auf ihre eigenen Repositories beschraenkt.

## 📚 Dokumentation und Community

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — jeder `--cli`-Unterbefehl, echte Ausgabe aus einem echten installierten Lauf, und der Exit-Code-Vertrag.
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — wie der Qt Quick/QML-Desktop-Client aufgebaut ist, und wie er eine echte Kontrolloberflaeche ueber demselben Backend bleibt, das auch `--cli` verwendet, statt einer zweiten Implementierung.
* **[Aenderungsprotokoll dieses Repositories](CHANGELOG.md)**
* Fragen, Ideen und Meldungen: electrohobby3d@gmail.com

## 👤 AUTOR
**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LIZENZ

GPL-3.0-or-later - siehe [LICENSE](LICENSE).
