<p align="center">
  <img src="images/URTC_UPDATER_BANNER.svg" alt="URTC-UPDATER banner" width="100%">
</p>

# 🛠️ URTC-UPDATER

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | 🇩🇪 <b>Deutsch</b> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | <a href="README_por.md">🇵🇹 Português</a></p>

### 📦 Erkennt, installiert und aktualisiert das gesamte URTC-Ökosystem von Hand

<p align="center">
  <img src="https://img.shields.io/badge/Licencia-GPL%203.0-blue.svg" alt="GPL 3.0 or later">
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

**Ehrlichkeitscheck - was heute wirklich funktioniert:** **Reifegrad: etabliert (ein dokumentierter Durchlauf, keine nachhaltige Nutzung).** Dieses Projekt überträgt das bewährte Design von HYDRA-UMC-UPDATER (gleiche Manifest-Erkennung, Installation/Aktualisierung über einen atomar geprüften temporären Klon und Nachweisprotokoll) nur auf die Repositories des URTC-Ökosystems. Es wurde Ende-zu-Ende gegen GitHub in einem isolierten Arbeitsbereich ausgeführt: Eine saubere Installation und eine spätere Aktualisierung eines echten Repositorys wurden korrekt geklont, gebaut und übernommen, die vorherige Kopie blieb als Sicherung erhalten. Die Erkennungs- und Versionslogik (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), der GitHub-Raw-Content-Client mit Retry/Backoff und zwischengespeicherter Repository-Liste (`github_client.py`), der Commit-Vergleich (`commits.py`) und die Pipeline Klonen-Vorbereiten-Prüfen-Übernehmen (`install.py`) sind durch Tests abgedeckt (`python -m pytest`), darunter ein lokaler HTTP-Testserver und echte temporäre Git-Repositories mit lokalem Bare-Remote. Die eigene Logik der Qt-Brücke läuft in den Tests ohne Bildschirm; die QML-Oberflächen selbst werden nicht automatisiert getestet. Die 8-Sprachen-Abdeckung von `i18n.py` wird per Test auf Schlüssel und Platzhalter geprüft, nicht auf Übersetzungsqualität. Siehe `CHANGELOG.md` für genau das, was bisher ausgeliefert wurde.

---

> **Stand von Sicherheit (Safety) und Security:** Dieses Ökosystem ist kein zertifiziertes Sicherheitssystem, und es existiert noch keine bestückte URTC-Platine. Die Bootloader prüfen Firmware-Images mit CRC32 und einem HMAC-SHA256 mit gemeinsamem Schlüssel, nicht mit einer asymmetrischen Signatur (geplant); die veröffentlichten Anwendungs-Images sind mit dem öffentlichen Entwicklungsschlüssel signiert (`signing_key_kind: dev`), sodass jeder ein vom Bootloader akzeptiertes Image erzeugen kann; an eine echte Platine wurde noch nichts gesendet. Lesen Sie die [Sicherheitsbasis](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) und das [Bedrohungsmodell](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md), bevor Sie sich für die Sicherheit einer Person auf eine Aussage hier verlassen.

## 📋 Auf einen Blick

| | |
|---|---|
| Version | `0.1.7` |
| Reifegrad | Etabliert |
| Technik | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Ziel | Der PC der Person, die es benutzt |
| Auf echter Hardware | Nicht zutreffend: nichts hiervon läuft auf Hardware |

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

`urtc-updater` ohne Argumente aufzurufen (oder per Doppelklick)
öffnet dieselbe Information in einem Fenster - eine Projekttabelle, ein
Filter nach Deployment-Ziel, und Installieren/Aktualisieren-Schaltflächen
für die ausgewählte Zeile.

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
  Installation bleibt unter `<name>.backup-xxxxxxxx` erhalten, statt gelöscht zu
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
  Projekts ein Update übersteht, statt im aufbewahrten `.backup-xxxxxxxx`-
  Checkout gestrandet zu bleiben. So oder so wird das
  eigene `build-test.sh`/`build-test.bat` dieses Projekts (die nicht-
  versionierende Prüfung - siehe Abschnitt 3) ausgeführt, falls
  vorhanden. Dieses Tool reimplementiert nie die eigenen Build-Schritte
  eines Projekts.

**Was der Build-Test antworten darf:** Exit-Code 0 bedeutet validiert, jeder andere Code bedeutet fehlgeschlagen, außer 75: Das bedeutet, dass die Validierung *nicht verfügbar* ist (ein benötigtes Werkzeug ist nicht installiert). Das wird so gemeldet und das Update abgelehnt, es sei denn, Sie akzeptieren es, indem Sie `validation_unavailable` in den Einstellungen auf `accept` setzen (oder `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). Ein Build-Test soll den Baum so hinterlassen, wie er ihn vorgefunden hat: Ändert er eine von git verfolgte Datei, wird sie vor der Übernahme auf den eingecheckten Inhalt zurückgesetzt, und die Schritte nennen sie.

**Signierte Commits (standardmäßig nur Warnung; sie zu verlangen ist optional und standardmäßig aus):** eine Revision ohne gültige Signatur (`git verify-commit`: GPG-Schlüsselbund oder SSH mit `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) wird trotzdem installiert, und die Schritte im Fenster und in der Kommandozeile sagen, dass sie nicht signiert ist. Mit `"signature_policy": "require"` in `~/.urtc_updater_settings.json` (oder `URTC_UPDATER_REQUIRE_SIGNED=1`; das ältere `"require_signed_commits": true` bedeutet dasselbe) muss der Kandidat - das `HEAD` eines neuen Klons oder das geladene `FETCH_HEAD` eines Updates - `git verify-commit` bestehen, bevor sein Manifest gelesen oder irgendetwas gebaut wird; ein abgelehnter Kandidat lässt den installierten Checkout unberührt.

**Sicherheitsoptionen (beide standardmäßig aus; änderbar über die Schaltfläche Sicherheit im Fenster, den Befehl `security`, die Einstellungsdatei, die Umgebung und die Kommandozeile):** Neben dem Verlangen signierter Commits kann der Updater *vor der Build-Prüfung* eines Kandidaten nachfragen (`"confirm_before_build": true`, `URTC_UPDATER_CONFIRM_BUILD=1`, `--confirm-build`). Er lädt und validiert den Kandidaten, zeigt Projekt, Commit, Autor, Signatur und die geänderten Build- oder Werkzeugskripte und führt nichts aus, bis Sie antworten; gibt es weder Fenster noch Terminal zum Fragen, führt er nichts aus (`--yes` antwortet für Skripte). `--require-signed` / `--no-require-signed` und `--confirm-build` / `--no-confirm-build` gelten für einen Lauf, und ein Lauf, der einen in den gespeicherten Einstellungen aktiven Schutz ausschaltet, sagt das; das Fenster und `urtc-updater --cli security --require-signed off` fragen nach, bevor eine niedrigere Stufe gespeichert wird. Eine Einstellungsdatei, die existiert, aber nicht gelesen werden kann, zählt als „Signaturen verlangt“, bis sie repariert oder entfernt wird. Der Build-Prüfung wird außerdem `URTC_PYTHON` mitgegeben, der Interpreter, der den Updater ausführt, damit ein Projekt mit diesem Python testet und nicht mit dem, das das System zuerst findet.

## 3. 🧱 ARCHITEKTUR UND DESIGN-ENTSCHEIDUNGEN

- **Qt-Quick-GUI standardmäßig, `--cli` für Headless.** `main.py` prüft
  `--cli`, bevor die optionale PySide6-Laufzeit importiert wird. Die CLI
  funktioniert auf einer CM5 ohne Display und Desktop-Abhängigkeit; ohne
  Argumente startet QML, sofern verfügbar, und Tkinter bleibt nur Fallback.
- **Die Fenster-GUI ist echt und spricht 8 Sprachen (`i18n.py`) - `--cli` absichtlich nicht.** Jedes Widget sowie der Text jedes Checkpoints und jedes Fehlers einer Installation oder Aktualisierung erscheint in der im Auswahlfeld gewählten Sprache (en/es/fr/it/de/zh/ja/pt, europäisches Portugiesisch für pt), entnommen einer gespeicherten Einstellung oder der Systemsprache. Installations- und Update-Schritte werden als Nachrichtencodes samt Parametern weitergegeben und erst das Fenster macht Text daraus, sodass ein Sprachwechsel sie neu darstellt. Projekt- und Familiennamen sowie die `notes`/`tech`-Texte jedes Projekts bleiben unübersetzt: Das Manifest ist ihre einzige Quelle der Wahrheit. Die Ausgabe von `--cli` bleibt absichtlich Englisch, weil sie für Skripte und Pipes gedacht ist.
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
- **Keine stack-spezifische Build-Logik in diesem Tool.** Das Ökosystem umfasst mehrere Toolchains (Python, Rust, Go, Node/TS, Android/Kotlin, Flutter, ARM-Firmware). Den Build jedes Projekts hier nachzubauen würde eine zweite Stelle schaffen, die behauptet, ihn zu kennen, und garantiert vom Skript des Projekts selbst abweicht. `install.py` führt stattdessen das versionsneutrale `build-test.sh` des Projekts aus (`build-test.bat` unter Windows) und scheitert sicher, wenn eine Kopie keines hat. Die Build-Skripte, die die Version erhöhen (`build.sh` und ähnliche), führt dieses Tool nie aus.
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
- **Bekannte Vereinfachung:** Ein Repository aus mehreren unabhängig versionierten Binärdateien (URTC hat vier: Haupt- und Slave-Controller, Anwendung und Bootloader) wird über EINE Version verfolgt, die sein eigenes `urtc.project.json` in `native_version` angibt. Das beantwortet "ist dieses Repository ungefähr aktuell", ersetzt aber nicht die komponentenweise Versionsprüfung eines Flashvorgangs.

## 📂 VERZEICHNISSTRUKTUR

```
URTC-UPDATER/
├── src/urtc_updater/
│   ├── registry.py         # ProjectEntry - kein statischer Katalog; wird zur Erkennungszeit aus dem eigenen Manifest jedes Repos gebaut
│   ├── project_manifest.py # Liest/validiert eine repository-eigene urtc.project.json
│   ├── version_parse.py   # EINE Regex-Extraktions-Implementierung, lokal+GitHub
│   ├── detect.py          # Scannt eine Workspace-Wurzel nach Installiertem
│   ├── github_client.py   # Nebenläufiger Abruf des Rohinhalts + echter Wiederholungsversuch/Backoff bei vorübergehenden Netzwerkfehlern
│   ├── install.py         # git clone/pull + delegiert an das eigene Build-Skript
│   ├── signature.py       # Optionale Richtlinie für signierte Commits (git verify-commit vor dem Build)
│   ├── commits.py          # Vergleicht eine Kopie per Commit mit ihrem Remote (git ls-remote)
│   ├── messages.py         # Installations-/Update-Meldungen als Codes plus Parameter
│   ├── evidence.py         # Per Hash verkettetes Protokoll jedes Versuchs
│   ├── settings.py         # Gespeicherte Einstellungen (Sprache, Arbeitsbereich, Aufbewahrung, Profile)
│   ├── profiles.py         # Benannte Stationsprofile
│   ├── notify.py           # Desktop-Benachrichtigung für die reine Hinweisprüfung
│   ├── logs.py             # Rotation der Logdateien des Fensters
│   ├── i18n.py             # Echte, vollständige GUI-Übersetzungen (8 Sprachen)
│   ├── translations_data.py # Die Texte des Fensters, aus dem Katalog von URTC-COMMON erzeugt
│   ├── qt_gui.py           # Qt-Quick-Brücke zu realen Erkennungs-/Update-Diensten
│   ├── packages_qt.py      # Das Fenster Pakete: die signierten Pakete der Releases
│   ├── qml/Main.qml        # Desktop-Shell mit Theme, Checkpoints und About
│   ├── gui.py              # Tkinter-Fallback falls PySide6 nicht verfügbar ist
│   └── main.py             # Dispatch: GUI standardmäßig, --cli für status/install/update
├── tests/                  # Echte Tests für jedes Modul (`python -m pytest`)
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
├── bump.py                 # Ausdrücklicher Befehl zum Erhöhen der Version (Kompilieren erhöht nie)
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

- `status` zeigt `?` bei der GitHub-Version eines Projekts: GitHub konnte dafür nicht gelesen werden. Die Spalte STATE nennt den Grund (zum Beispiel `installed, GitHub unknown (HTTP 404)` oder einen Hinweis auf das Anfragelimit).
- `status` zeigt `-` für GitHub ohne angezeigten Fehler: führen Sie
  `status` aus (ohne `--offline`) - `-` erscheint nur, wenn die
  GitHub-Prüfung komplett übersprungen wurde.
- `install`/`update` scheitert mit "No non-versioning build-test.sh/.bat found": Diese Kopie hat kein `build-test.sh` (`build-test.bat` unter Windows). Aktualisieren Sie das Projekt selbst oder prüfen Sie es von Hand; dieses Tool führt nie stattdessen ein Build-Skript aus, das die Version erhöht.
- `git pull --ff-only` schlägt fehl: Der lokale Checkout hat nicht
  committete Änderungen oder die Historie ist auseinandergelaufen -
  lösen Sie das manuell (`git status` im eigenen Verzeichnis des
  Projekts), bevor Sie `update` erneut versuchen. Dieses Tool erzwingt
  nie einen Reset eines Checkouts.

## 🧹 AUFRÄUMEN UND STATIONSBEFEHLE

- **Aufbewahrte frühere Installationen.** Jede Aktualisierung behält die ersetzte Installation in `<Name>.backup-xxxxxxxx`. Pro Projekt bleiben die 2 neuesten erhalten (`"backups_to_keep"` in `~/.urtc_updater_settings.json` ändert die Zahl), ältere werden nach einer erfolgreichen Aktualisierung entfernt. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` entfernt sie auf Wunsch, zusammen mit jedem versteckten temporären Ordner, den ein abgestürzter Lauf hinterlassen hat.
- **Optional: Installation aus dem signierten Paket eines Releases.** `urtc-updater --cli package list|check|install|rollback` installiert ein Programm (den Flasher, den Tester oder diesen Updater) aus dem `.zip` / `.tar.gz` seines Releases statt aus Klon und Build. Angeboten wird nur eine strikt höhere Version, nur von den Download-Hosts von GitHub, und das Paket muss zu Größe und SHA-256 laut Ankündigung und zur Ed25519-Signatur des im Programm angehefteten Release-Schlüssels passen; ein Paket, das eine Prüfung nicht besteht, wird gelöscht. Vor der Installation wird gefragt (`--yes` antwortet für Skripte), die zwei neuesten Releases bleiben erhalten und `rollback` zeigt wieder auf das vorherige. `install --file PAKET` arbeitet mit einer Datei auf der Platte samt `.sha256` und `.sig` daneben, ohne Netzwerk. Das Fenster hat eine Schaltfläche „Nach Updates suchen“ für den Updater selbst mit denselben Regeln; die automatische Prüfung beim Start ist eine Option, standardmäßig aus. Mit auf einem Computer erzeugten Paketen getestet, noch nicht mit einer veröffentlichten Release.
- **Ein Fenster Pakete und ein Fenster Hilfe.** Die Schaltfläche „Pakete“ listet die signierten Pakete von Flasher, Tester und diesem Updater: Jede Zeile prüft ihre Version, wenn Sie „Nach Updates suchen“ drücken, lädt das Paket herunter und prüft es, fragt vor der Installation und kehrt zur vorherigen Version zurück, mit denselben Regeln und Sicherheitsoptionen wie der Befehl `package`; solange ein Projekt installiert oder aktualisiert wird, wird nichts installiert. Die Schaltfläche „Hilfe“ öffnet eine Anleitung in fünf Schritten in der Sprache des Fensters.
- **Eine wiederherstellen.** `urtc-updater --cli restore-backup <PROJEKT> [--backup ORDNER] [--list]` stellt eine aufbewahrte Installation wieder her. Die ersetzte Installation bleibt ebenfalls erhalten, der Tausch lässt sich also rückgängig machen. Das Fenster bietet neben Auswahl aktualisieren dieselben zwei Aktionen: Vorschau des Updates (was es bringen würde, ohne etwas zu ändern) und Vorherige Version wiederherstellen.
- **Gleiche Version, neue Commits.** Die Version ändert sich nur bei einem Release-Build; `status` vergleicht deshalb auch den Commit jedes installierten Projekts mit dem des Remotes (`git ls-remote`) und zeigt `NEW COMMITS`, wenn GitHub Arbeit hat, die der Kopie fehlt. Das Fenster zeigt denselben Zustand und bietet die Aktualisierung an.
- **Ansehen vor dem Bestätigen.** `urtc-updater --cli update <PROJEKT> --preview` lädt den Kandidaten und zeigt Commit, Autor, Version, Signaturstatus und die Build- oder Werkzeugdateien, die er ändert, ohne die Kopie anzufassen.
- **Nur benachrichtigen.** `urtc-updater --cli check [--notify] [--quiet]` listet auf, was aktualisiert werden könnte, und ändert nichts. Es endet mit Code 10, wenn etwas aktualisiert werden kann, damit eine geplante Aufgabe eine Person benachrichtigen kann; `--notify` zeigt zusätzlich eine Desktop-Benachrichtigung.
- **Nachweise.** Jede Installation, Aktualisierung und Wiederherstellung wird mit Zeit, Rechner und Benutzer in `.urtc-updater/evidence.jsonl` festgehalten, jede Zeile per Hash mit der vorherigen verkettet. `urtc-updater --cli evidence [--export DATEI]` prüft die Kette und kann sie als ein JSON-Dokument exportieren.
- **Stationsprofile.** `"profiles"` in der Einstellungsdatei nennt die Projekte, mit denen ein Rechner arbeitet, und ob Sammelaktionen erlaubt sind; `--profile NAME` (oder `"profile"` in den Einstellungen) beschränkt `status`, `check`, `install` und `update` darauf, und das Fenster folgt demselben Profil.

## 🚀 FAHRPLAN

- Eine gepackte eigenständige GUI-ausführbare Datei (PyInstaller, nach der
  eigenen `build_exe.bat`/`.sh`-Konvention von HYDRA-UMC-SUITE) für eine
  Doppelklick-Installation ganz ohne `pip`/venv-Schritt - heute braucht
  die GUI noch vorher `./build.sh`, genau wie die CLI.
- Optionale Abhängigkeits-Vorprüfung pro Projekt (fehlende Toolchains
  melden - kein Rust/Go/Android-SDK/Flutter installiert - bevor ein
  `install` mittendrin fehlschlägt).
- Komponentenweise Nachverfolgung für die eigene Mehrbinär-Firmware von
  HYDRA-UMC/URTC (siehe die "bekannte Vereinfachung" in Abschnitt 3),
  sobald ein echter Bedarf über die heute verfolgte einzelne
  repräsentative Komponente hinaus besteht.

## 🔗 Verwandte Projekte

**URTC** (Universal Robot Tool Controller) ist eine echte physische Werkzeugwechsel-Plattform desselben Autors (JuanenRac / Electro Hobby 3D). Jedes Repository hat seine eigene Version, seine eigenen Tests und sein eigenes README; das ist die ganze Familie:

* **[URTC](https://github.com/JuanenRac/URTC)** - Firmware fuer die physische Universal-Robot-Tool-Controller-Platine, 25+ Werkzeugprofile ueber CAN-Bus
* **[URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS)** - Die Architektur, die Schnittstellen, die Sicherheitsbasis, die Faehigkeitenmatrix und der erzeugte Projektkatalog des Oekosystems sowie die Werkzeuge, die alle Repositories vergleichen
* **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** - Desktop-GUI-Flash-Tool fuer URTC-Platinen, CAN-OTA plus vollstaendiges SWD/JTAG
* **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** - ein Gateway vor dem CAN-Bus, das nur Kennungen einer Liste durchlässt, ihre Rate begrenzt und einen Sitzungsschlüssel verlangt.
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

<!-- urtc-section:updates -->
## 🔄 So wird aktualisiert

Dieses Programm kann nach einer neueren Version seiner selbst suchen: Die Schaltfläche „Nach Updates suchen“ fragt GitHub einmal und bietet ein signiertes Paket nur an, wenn es für Ihr System ist und neuer. Nichts wird von selbst geprüft oder installiert, solange Sie die Prüfung nicht einschalten, und ein Update braucht Ihre Bestätigung. Das Paket muss zu seinem SHA-256 und zur Signatur des im Programm angehefteten Release-Schlüssels passen; die vorherige Version bleibt erhalten und wird von selbst wiederhergestellt, wenn die neue nicht startet. `urtc-updater --cli package list|check|install|rollback` macht dasselbe auf der Kommandozeile für Flasher und Tester, und `install --file` funktioniert ohne Netzwerk.
<!-- /urtc-section:updates -->

<!-- urtc-section:compatibility -->
## 🧩 Kompatibilität

Welche Versionen der URTC-Programme zusammenarbeiten und welche Protokollversion jede spricht, steht in der Kompatibilitätstabelle, die URTC-COMMON erzeugt: [docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md).
<!-- /urtc-section:compatibility -->

## 📜 LIZENZ

GPL-3.0-or-later - siehe [LICENSE](LICENSE).
