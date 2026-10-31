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

---

**Ehrlichkeitscheck - was heute wirklich funktioniert:** **Reifegrad: etabliert (ein dokumentierter Durchlauf, keine nachhaltige Nutzung).** Dieses Projekt überträgt das bewährte Design von HYDRA-UMC-UPDATER (gleiche Manifest-Erkennung, Installation/Aktualisierung über einen atomar geprüften temporären Klon und Nachweisprotokoll) nur auf die Repositories des URTC-Ökosystems. Es wurde Ende-zu-Ende gegen GitHub in einem isolierten Arbeitsbereich ausgeführt: Eine saubere Installation und eine spätere Aktualisierung eines echten Repositorys wurden korrekt geklont, gebaut und übernommen, die vorherige Kopie blieb als Sicherung erhalten. Die Erkennungs- und Versionslogik (`registry.py`, `project_manifest.py`, `version_parse.py`, `detect.py`), der GitHub-Raw-Content-Client mit Retry/Backoff und zwischengespeicherter Repository-Liste (`github_client.py`), der Commit-Vergleich (`commits.py`) und die Pipeline Klonen-Vorbereiten-Prüfen-Übernehmen (`install.py`) sind durch Tests abgedeckt (`python -m pytest`), darunter ein lokaler HTTP-Testserver und echte temporäre Git-Repositories mit lokalem Bare-Remote. Die eigene Logik der Qt-Brücke läuft in den Tests ohne Bildschirm, und das Fenster mit seinen Dialogen wird ohne Bildschirm geladen, um zu prüfen, dass es sich öffnet und antwortet; sein Aussehen wird mit dem Auge geprüft, nicht durch einen Test. Die 8-Sprachen-Abdeckung von `i18n.py` wird per Test auf Schlüssel und Platzhalter geprüft, nicht auf Übersetzungsqualität. Siehe `CHANGELOG.md` für genau das, was bisher ausgeliefert wurde.

---

> **Stand von Sicherheit (Safety) und Security:** Dieses Ökosystem ist kein zertifiziertes Sicherheitssystem, und es existiert noch keine bestückte URTC-Platine. Die Bootloader prüfen Firmware-Images mit CRC32 und einem HMAC-SHA256 mit gemeinsamem Schlüssel, nicht mit einer asymmetrischen Signatur (geplant); die veröffentlichten Anwendungs-Images sind mit dem öffentlichen Entwicklungsschlüssel signiert (`signing_key_kind: dev`), sodass jeder ein vom Bootloader akzeptiertes Image erzeugen kann; an eine echte Platine wurde noch nichts gesendet. Lesen Sie die [Sicherheitsbasis](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/SECURITY_BASELINE.md) und das [Bedrohungsmodell](https://github.com/JuanenRac/URTC-DOCS/blob/main/docs/THREAT_MODEL.md), bevor Sie sich für die Sicherheit einer Person auf eine Aussage hier verlassen.

## 📋 Auf einen Blick

| | |
|---|---|
| Version | `0.2.0` |
| Reifegrad | Etabliert |
| Tests | 482 (`python -m pytest`) |
| Technik | Python 3.10+ / PySide6 / Qt Quick (QML) / Git / GitHub raw content |
| Ziel | Der PC der Person, die es benutzt |
| Auf echter Hardware | Nicht zutreffend: nichts hiervon läuft auf Hardware |

**Springe zu:** [Überblick](#-überblick) · [Architektur](#-architektur) · [Sicherheit](#-sicherheit-und-schutz) · [Schnittstellen](#-schnittstellen) · [Schnellstart](#-schnellstart) · [Tests](#-tests) · [Probleme](#-fehlerbehebung) · [Struktur](#-struktur-des-repositorys) · [Verwandte](#-verwandte-projekte)

<!-- urtc-section:status_updater -->
## 🚦 Projektstatus

🟢 fertig und überprüft · 🟡 funktioniert, mit bekannten Grenzen · 🟠 halb fertig oder nicht überprüft · 🔴 nicht gemacht oder funktioniert nicht. Nichts ist grün, wenn es nie auf echter Hardware lief.

| Teil | Status | Was das Repository belegen kann |
| --- | :---: | --- |
| Software | 🟡 | Läuft am PC und gegen den Simulator; nie an einer echten Platine ausgeführt. |
| Oberfläche | 🟡 | Das Fenster läuft und wird gegen eine simulierte Platine geprüft; nicht mit einem echten Adapter probiert. |
| Tests | 🟢 | Die Testsuite besteht bei jedem Push in der CI. |
| Aktualisierungen | 🟡 | Installiert aus signierten Paketen mit Rückgängig-Funktion; nur am PC erprobt. |
| Sicherheit | 🟡 | Releases werden mit Ed25519 signiert und vor der Nutzung geprüft; der Umgang mit den Schlüsseln wurde von niemand anderem geprüft. |
| Dokumentation | 🟡 | README in acht Sprachen und Referenzdokumente; die Übersetzungen wurden nicht von Muttersprachlern geprüft. |

<!-- /urtc-section:status_updater -->

## 🎯 Überblick

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

`urtc-updater` ohne Argumente aufzurufen (oder per Doppelklick) öffnet
stattdessen dieselbe Information in einer dunklen Desktop-Bedienoberfläche:
ein Bereich **Local Ecosystem** mit Live-Kennzahlen zu
Erkennung/Installation/Aktualisierung, ein manifestgesteuerter **Project
Registry**-Baum und ein Bereich **Safe Update** für das ausgewählte Projekt.
Das Layout macht die echten Schutzvorkehrungen sichtbar: Erkennung per
Manifest, genau eine ausdrückliche Projektaktion, manuelle Bestätigung,
optionaler Build und eine Aktivitätsspur auf dem Bildschirm; das gesamte
Protokoll wird außerdem in eine Datei unter `~/.urtc_updater/logs`
geschrieben (die neuesten 20 bleiben erhalten).

## 🧩 Rolle in URTC

URTC-UPDATER ist das Programm, das einen PC mit den URTC-Repositorys auf dem neuesten Stand hält. Es findet jedes Projekt neben sich anhand des Manifests, das jedes Repository trägt, sagt, welche Version installiert ist und welche GitHub hat, und installiert oder aktualisiert nach einer ausdrücklichen Bestätigung jeweils ein Projekt, indem es das `build-test`-Skript dieses Projekts ausführt und selbst nichts baut. Es ändert nichts aus eigener Initiative: Eine Robotersteuerungszelle darf nie über Nacht aktualisiert werden, ohne dass eine Person genau diese Aktion freigibt. Es installiert auch die Desktop-Programme (den Flasher, den Tester und sich selbst) aus dem signierten Paket ihres Releases und kann ein Firmware-Image, dessen Release-Signatur es geprüft hat, an URTC-FLASHER übergeben, das das Flashen übernimmt.

## 🏛️ Architektur

<p align="center">
  <img src="images/architecture.svg" alt="Architektur von URTC-UPDATER: wer es nutzt, was es enthält und wovon es abhängt" width="100%">
</p>

Wie die Teile dieses Repositorys zusammenpassen: wer es nutzt, was es enthält und wovon es abhängt. Das Bild wird aus `docs/architecture.json` gezeichnet und gegen den Code geprüft.

### WIE EINE PRÜFUNG/AKTUALISIERUNG WIRKLICH FUNKTIONIERT

- **Versionsquelle**: Die Version eines Projekts steht in einer Quelldatei dieses Projekts (`pyproject.toml`, `Cargo.toml`, `version.go`, `package.json`, `version.properties`, `pubspec.yaml` oder ein Firmware-`#define`, je nach Technik), die der eigene `bump.py`-Schritt schreibt, und dieser Schritt hat nie ein Git-Tag oder ein GitHub-Release erzeugt. Deshalb liest dieses Werkzeug genau diese Datei direkt vom Standard-Branch über den Raw-Content-Host von GitHub - nicht über die Releases-API, die jedes Projekt als ohne Releases melden würde.
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

### ARCHITEKTUR UND DESIGN-ENTSCHEIDUNGEN

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

<!-- urtc-section:updates -->
### So wird aktualisiert

Dieses Programm kann nach einer neueren Version seiner selbst suchen: Die Schaltfläche „Nach Updates suchen“ fragt GitHub einmal und bietet ein signiertes Paket nur an, wenn es für Ihr System ist und neuer. Nichts wird von selbst geprüft oder installiert, solange Sie die Prüfung nicht einschalten, und ein Update braucht Ihre Bestätigung. Das Paket muss zu seinem SHA-256 und zur Signatur des im Programm angehefteten Release-Schlüssels passen; die vorherige Version bleibt erhalten und wird von selbst wiederhergestellt, wenn die neue nicht startet. `urtc-updater --cli package list|check|install|rollback` macht dasselbe auf der Kommandozeile für Flasher und Tester, und `install --file` funktioniert ohne Netzwerk.
<!-- /urtc-section:updates -->

## 🖼️ Screenshots

<!-- urtc-shots -->
Aufgenommen mit 1920×1080 auf einem Prüfstand, mit Beispieldaten und ohne eine echte Anlage dahinter.

<table>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/deck.png" alt="Das Fenster über einem Arbeitsbereich mit der Familie darin: jedes Projekt mit Reifegrad, Stack und lokaler Version sowie die sicheren Aktualisierungsaktionen." width="100%"><br><sub>Das Fenster über einem Arbeitsbereich mit der Familie darin: jedes Projekt mit Reifegrad, Stack und lokaler Version sowie die sicheren Aktualisierungsaktionen.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/packages.png" alt="Das Paket-Fenster: die Programme der Familie, die ein Release als signiertes Paket veröffentlicht, jedes prüft sein eigenes Release." width="100%"><br><sub>Das Paket-Fenster: die Programme der Familie, die ein Release als signiertes Paket veröffentlicht, jedes prüft sein eigenes Release.</sub></td>
</tr>
<tr>
<td width="50%" valign="top"><img src="images/screenshots/help.png" alt="Das Hilfefenster: die Schritte zur Benutzung des Programms, in der Sprache des Fensters." width="100%"><br><sub>Das Hilfefenster: die Schritte zur Benutzung des Programms, in der Sprache des Fensters.</sub></td>
<td width="50%" valign="top"><img src="images/screenshots/updates.png" alt="Das Update-Fenster: ein neueres signiertes Paket wird erst nach deiner Bestätigung installiert." width="100%"><br><sub>Das Update-Fenster: ein neueres signiertes Paket wird erst nach deiner Bestätigung installiert.</sub></td>
</tr>
</table>
<!-- /urtc-shots -->

Diese Bilder zeigen das echte Fenster, ohne Bildschirm gezeichnet, so wie es sich öffnet (nichts geprüft, nichts installiert). Die Anleitung führt durch das Fenster, das Hilfefenster, das Update-Fenster und das Paketfenster und zeigt sie in den acht Sprachen des Programms.

[Anleitung mit Bildern](docs/WINDOW_GUIDE.md)

## 🔒 Sicherheit und Schutz

| Bedrohung | Abwehr |
|---|---|
| Eine Aktualisierung, die niemand freigegeben hat, etwa nachts auf einer Robotersteuerungszelle | Nichts ändert sich von selbst: Eine Aktion an einem Projekt braucht eine ausdrückliche Bestätigung, ein Stapel wird gesondert bestätigt und läuft Projekt für Projekt |
| Eine kaputte oder halbfertige Aktualisierung macht eine funktionierende Installation unbrauchbar | Der Kandidat wird geklont, per Fast-Forward zusammengeführt (nie ein erzwungenes Zurücksetzen, sodass lokale Änderungen laut scheitern) und zuerst in einem Staging-Klon gebaut; die laufende Installation wird nur durch zwei Ordnerumbenennungen ersetzt, wenn dieser Build besteht, und die vorherige bleibt als `<Name>.backup-xxxxxxxx` erhalten |
| Eine Prüfung, die hier nicht laufen kann | Ein build-test, der 75 meldet, bedeutet: Die Validierung ist nicht verfügbar; die Aktualisierung wird abgelehnt, außer die Person nimmt sie in den Einstellungen in Kauf |
| Ein Commit, den niemand signiert hat | Eine Revision ohne gültige Signatur wird mit einer Warnung installiert; mit `"signature_policy": "require"` wird sie abgelehnt |
| Ein manipuliertes Paket | Ein Paket wird nur akzeptiert, wenn Größe, SHA-256 und Ed25519-Signatur passen und es von den Download-Hosts von GitHub kommt; es wird nur nach einer Bestätigung installiert, nie während eine andere Installation läuft, und die vorherige Version lässt sich wiederherstellen |
| Die Spur dessen, was getan wurde, geht verloren | Jede Installation, Aktualisierung und Wiederherstellung wird mit Zeit, Rechner und Benutzer in ein durch Hashes verkettetes Protokoll geschrieben |

Der Rest der Richtlinie folgt, in den Worten des Programms.

**Was der Build-Test antworten darf:** Exit-Code 0 bedeutet validiert, jeder andere Code bedeutet fehlgeschlagen, außer 75: Das bedeutet, dass die Validierung *nicht verfügbar* ist (ein benötigtes Werkzeug ist nicht installiert). Das wird so gemeldet und das Update abgelehnt, es sei denn, Sie akzeptieren es, indem Sie `validation_unavailable` in den Einstellungen auf `accept` setzen (oder `URTC_UPDATER_ACCEPT_UNAVAILABLE_VALIDATION=1`). Ein Build-Test soll den Baum so hinterlassen, wie er ihn vorgefunden hat: Ändert er eine von git verfolgte Datei, wird sie vor der Übernahme auf den eingecheckten Inhalt zurückgesetzt, und die Schritte nennen sie.

**Signierte Commits (standardmäßig nur Warnung; sie zu verlangen ist optional und standardmäßig aus):** eine Revision ohne gültige Signatur (`git verify-commit`: GPG-Schlüsselbund oder SSH mit `"allowed_signers_file"` / `URTC_UPDATER_ALLOWED_SIGNERS`) wird trotzdem installiert, und die Schritte im Fenster und in der Kommandozeile sagen, dass sie nicht signiert ist. Mit `"signature_policy": "require"` in `~/.urtc_updater_settings.json` (oder `URTC_UPDATER_REQUIRE_SIGNED=1`; das ältere `"require_signed_commits": true` bedeutet dasselbe) muss der Kandidat - das `HEAD` eines neuen Klons oder das geladene `FETCH_HEAD` eines Updates - `git verify-commit` bestehen, bevor sein Manifest gelesen oder irgendetwas gebaut wird; ein abgelehnter Kandidat lässt den installierten Checkout unberührt.

**Sicherheitsoptionen (beide standardmäßig aus; änderbar über die Schaltfläche Sicherheit im Fenster, den Befehl `security`, die Einstellungsdatei, die Umgebung und die Kommandozeile):** Neben dem Verlangen signierter Commits kann der Updater *vor der Build-Prüfung* eines Kandidaten nachfragen (`"confirm_before_build": true`, `URTC_UPDATER_CONFIRM_BUILD=1`, `--confirm-build`). Er lädt und validiert den Kandidaten, zeigt Projekt, Commit, Autor, Signatur und die geänderten Build- oder Werkzeugskripte und führt nichts aus, bis Sie antworten; gibt es weder Fenster noch Terminal zum Fragen, führt er nichts aus (`--yes` antwortet für Skripte). `--require-signed` / `--no-require-signed` und `--confirm-build` / `--no-confirm-build` gelten für einen Lauf, und ein Lauf, der einen in den gespeicherten Einstellungen aktiven Schutz ausschaltet, sagt das; das Fenster und `urtc-updater --cli security --require-signed off` fragen nach, bevor eine niedrigere Stufe gespeichert wird. Eine Einstellungsdatei, die existiert, aber nicht gelesen werden kann, zählt als „Signaturen verlangt“, bis sie repariert oder entfernt wird. Der Build-Prüfung wird außerdem `URTC_PYTHON` mitgegeben, der Interpreter, der den Updater ausführt, damit ein Projekt mit diesem Python testet und nicht mit dem, das das System zuerst findet.

## 🔌 Schnittstellen

Das Programm öffnet das Qt-Quick-Fenster, wenn es ohne Argumente gestartet wird, und hat mit `--cli` eine vollständige Befehlszeile (ohne Bildschirm und ohne PySide6): `status [--offline]`, `install PROJEKT`, `update PROJEKT [--preview]`, `restore-backup PROJEKT [--list]`, `clean-backups [--keep N] [--dry-run]`, `check [--notify] [--quiet]` (Exit-Code 10, wenn etwas aktualisiert werden kann), `package list|check|install|rollback`, `evidence [--export FILE]` und `security`. Jeder Befehl, jede Option und jeder Exit-Code mit echter Ausgabe steht in [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md); das Fenster ist in [docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md) beschrieben. Was die Wartungs- und Arbeitsplatzbefehle tun:

- **Aufbewahrte frühere Installationen.** Jede Aktualisierung behält die ersetzte Installation in `<Name>.backup-xxxxxxxx`. Pro Projekt bleiben die 2 neuesten erhalten (`"backups_to_keep"` in `~/.urtc_updater_settings.json` ändert die Zahl), ältere werden nach einer erfolgreichen Aktualisierung entfernt. `urtc-updater --cli clean-backups [--keep N] [--dry-run]` entfernt sie auf Wunsch, zusammen mit jedem versteckten temporären Ordner, den ein abgestürzter Lauf hinterlassen hat.
- **Optional: Installation aus dem signierten Paket eines Releases.** `urtc-updater --cli package list|check|install|rollback` installiert ein Programm (den Flasher, den Tester oder diesen Updater) aus dem `.zip` / `.tar.gz` seines Releases statt aus Klon und Build. Angeboten wird nur eine strikt höhere Version, nur von den Download-Hosts von GitHub, und das Paket muss zu Größe und SHA-256 laut Ankündigung und zur Ed25519-Signatur des im Programm angehefteten Release-Schlüssels passen; ein Paket, das eine Prüfung nicht besteht, wird gelöscht. Vor der Installation wird gefragt (`--yes` antwortet für Skripte), die zwei neuesten Releases bleiben erhalten und `rollback` zeigt wieder auf das vorherige. `install --file PAKET` arbeitet mit einer Datei auf der Platte samt `.sha256` und `.sig` daneben, ohne Netzwerk. Das Fenster hat eine Schaltfläche „Nach Updates suchen“ für den Updater selbst mit denselben Regeln; die automatische Prüfung beim Start ist eine Option, standardmäßig aus. Mit auf einem Computer erzeugten Paketen getestet, noch nicht mit einer veröffentlichten Release.
- **Ein Fenster Pakete und ein Fenster Hilfe.** Die Schaltfläche „Pakete“ listet die signierten Pakete von Flasher, Tester und diesem Updater: Jede Zeile prüft ihre Version, wenn Sie „Nach Updates suchen“ drücken, lädt das Paket herunter und prüft es, fragt vor der Installation und kehrt zur vorherigen Version zurück, mit denselben Regeln und Sicherheitsoptionen wie der Befehl `package`; solange ein Projekt installiert oder aktualisiert wird, wird nichts installiert. Die Schaltfläche „Hilfe“ öffnet eine Anleitung in fünf Schritten in der Sprache des Fensters.
- **Eine wiederherstellen.** `urtc-updater --cli restore-backup <PROJEKT> [--backup ORDNER] [--list]` stellt eine aufbewahrte Installation wieder her. Die ersetzte Installation bleibt ebenfalls erhalten, der Tausch lässt sich also rückgängig machen. Das Fenster bietet neben Auswahl aktualisieren dieselben zwei Aktionen: Vorschau des Updates (was es bringen würde, ohne etwas zu ändern) und Vorherige Version wiederherstellen.
- **Gleiche Version, neue Commits.** Die Version ändert sich nur bei einem Release-Build; `status` vergleicht deshalb auch den Commit jedes installierten Projekts mit dem des Remotes (`git ls-remote`) und zeigt `NEW COMMITS`, wenn GitHub Arbeit hat, die der Kopie fehlt. Das Fenster zeigt denselben Zustand und bietet die Aktualisierung an.
- **Ansehen vor dem Bestätigen.** `urtc-updater --cli update <PROJEKT> --preview` lädt den Kandidaten und zeigt Commit, Autor, Version, Signaturstatus und die Build- oder Werkzeugdateien, die er ändert, ohne die Kopie anzufassen.
- **Nur benachrichtigen.** `urtc-updater --cli check [--notify] [--quiet]` listet auf, was aktualisiert werden könnte, und ändert nichts. Es endet mit Code 10, wenn etwas aktualisiert werden kann, damit eine geplante Aufgabe eine Person benachrichtigen kann; `--notify` zeigt zusätzlich eine Desktop-Benachrichtigung.
- **Nachweise.** Jede Installation, Aktualisierung und Wiederherstellung wird mit Zeit, Rechner und Benutzer in `.urtc-updater/evidence.jsonl` festgehalten, jede Zeile per Hash mit der vorherigen verkettet. `urtc-updater --cli evidence [--export DATEI]` prüft die Kette und kann sie als ein JSON-Dokument exportieren.
- **Stationsprofile.** `"profiles"` in der Einstellungsdatei nennt die Projekte, mit denen ein Rechner arbeitet, und ob Sammelaktionen erlaubt sind; `--profile NAME` (oder `"profile"` in den Einstellungen) beschränkt `status`, `check`, `install` und `update` darauf, und das Fenster folgt demselben Profil.

## 🚀 Schnellstart

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

<!-- urtc-section:compatibility -->
### Voraussetzungen und Kompatibilität

Welche Versionen der URTC-Programme zusammenarbeiten und welche Protokollversion jede spricht, steht in der Kompatibilitätstabelle, die URTC-COMMON erzeugt: [docs/COMPATIBILITY.md](https://github.com/JuanenRac/URTC/blob/main/docs/COMPATIBILITY.md).
<!-- /urtc-section:compatibility -->

## 🧪 Tests

Die Suite hat 482 Tests (`QT_QPA_PLATFORM=offscreen python -m pytest tests -q`; einige werden übersprungen, wenn eine optionale Abhängigkeit fehlt): die Erkennung und die Manifeste, der eine Versionsparser, der GitHub-Client gegen einen lokalen Server (Wiederholungen, Fehler, ein fehlerhafter Katalog), Installation und Aktualisierung auf echten lokalen Git-Repositorys (Staging, Übernahme, Sicherung, Ablehnungen, ein build-test, der 75 meldet, Sicherheit des Arbeitsbereichs), Wiederherstellen und Aufräumen von Sicherungen, die Richtlinie für signierte Commits, die Sicherheitsoptionen, signierte Pakete und ihr Zurückrollen, die Beweiskette, Einstellungen und Profile, die Fenstertexte in den acht Sprachen und die Qt-Brücke sowie die Bilder der Fensteranleitung, ohne Bildschirm gezeichnet. `python -m mypy` und `ruff check .` laufen in der CI.

## 🏗️ Build und Veröffentlichung

`build.sh` / `build.bat` erstellen die `.venv`, installieren das Paket (`pip install -e .`, mit der Qt-Laufzeit für das Fenster) und prüfen alles per Kompilierung; `build-test.sh` / `build-test.bat` prüfen ohne Installation; `run.sh` / `run.bat` öffnen das Fenster oder mit `--cli` die Befehlszeile; `run-gui.vbs` öffnet es unter Windows ohne Konsolenfenster. Eine verpackte eigenständige ausführbare Datei wird noch nicht gebaut.

## 🩺 Fehlerbehebung

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

## 📂 Struktur des Repositorys

<p align="center">
  <img src="images/repository-structure.svg" alt="Struktur des Repositorys URTC-UPDATER" width="100%">
</p>

<details>
<summary>Textversion des Baums</summary>

```text
URTC-UPDATER/
├── src/urtc_updater/                                  das Programm: Erkennung, Versionen, Installation und Aktualisierung, Sicherheit, signierte Pakete, das Qt-Quick-Fenster und seine Texte in acht Sprachen
├── tests/                                             echte Tests für jedes Modul
├── docs/                                              Befehlsreferenz, Oberfläche und Fensteranleitung
├── tools/                                             Build-Prüfung, Screenshots, Symbol und gemeinsame Werkzeuge
├── images/                                            Banner und Bilder dieses READMEs
├── .github/                                           CI-Workflow sowie Vorlagen für Issues und Pull Requests
├── build.sh build.bat                                 Build-Skripte
├── build-test.sh build-test.bat                       Build- und Testskripte, die im Repository nichts ändern
├── test.sh test.bat                                   führen die Tests aus
├── run.sh run.bat                                     starten das Programm
├── urtc.project.json                                  Manifest: Version, Rolle, Reifegrad und Build-Befehl
├── CHANGELOG.md                                       was sich in jeder Version geändert hat
├── SECURITY.md SUPPORT.md LICENSE                     Sicherheitsrichtlinie, Support und Lizenz
├── CONTRIBUTING.md CODE_OF_CONDUCT.md                 wie man mitwirkt, und der Verhaltenskodex
├── .gitattributes .gitignore                          Git-Einstellungen
├── run-gui.vbs                                        Windows-Starter ohne Konsolenfenster
├── bump.py bump_version.py bump_manifest_version.py   Skripte, die die Version erhöhen
├── urtc_i18n.lock.json                                Sperre der Fenstertexte
├── LICENSE.md .env.example                            Dokumentationslizenz und Variablen
└── pyproject.toml requirements-dev.lock ruff.toml     Paket, festgelegte Werkzeuge, Lint-Einstellungen und die Sperre der Texte
```

</details>

Die kommentierte Liste jeder Quelldatei, eine Zeile je Datei, steht in [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md).

## 🗺️ Roadmap und bekannte Grenzen

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

## 🌍 Sprachen

README und Texte gibt es auf Englisch, Spanisch, Französisch, Italienisch, Deutsch, Chinesisch, Japanisch und europäischem Portugiesisch.

## 🔗 Verwandte Projekte

URTC besteht aus unabhängigen Repositories mit jeweils eigener Version, eigenen Tests und eigenem README. Das ist die Familie, nach Gruppen:

* **URTC Tool Platform:**
  * [URTC](https://github.com/JuanenRac/URTC) - Firmware der Werkzeugkopf-Platine (25 Werkzeugprofile, CAN-Bootloader) und die Referenz des CAN-Protokolls.
  * [URTC-COMMON](https://github.com/JuanenRac/URTC-COMMON) - das CAN-Protokoll einmal als Daten geschrieben (Spezifikation, erzeugte Tabellen, Konformitätsvektoren) und der Code, den die Programme teilen.
  * [URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER) - Desktop-Werkzeug, das die Platinen-Firmware über CAN oder über SWD/JTAG aktualisiert.
  * [URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY) - Gateway vor dem CAN-Bus: lässt nur gelistete Kennungen durch, begrenzt ihre Rate und verlangt einen Sitzungsschlüssel.
  * [URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK) - hardwareunabhängige C-Logik und Befehlsprotokoll für eine Werkzeugablage mit Vorheizen und Lebenszyklusverfolgung.
  * [URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER) - Desktop-Live-Tester für den CAN-Bus, der die Bedienelemente und die Telemetrie des von einer Platine gemeldeten Werkzeugprofils zeigt.
  * [URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL) - Sensorrahmen-Protokoll in C und ein Python-Thermo-/RGB-Begleiter für einen Inspektions-Werkzeugkopf.
  * [URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO) - Browser-App, die die Platine über Web Serial und SLCAN flasht und testet, ohne Installation.
* **Ecosystem Operations:**
  * [URTC-DEVTOOLS](https://github.com/JuanenRac/URTC-DEVTOOLS) - die gemeinsamen Repository-Werkzeuge der Familie als versionierter Satz, mit einer Sperrdatei, die eine bearbeitete von einer veralteten Kopie unterscheidet.
  * [URTC-DOCS](https://github.com/JuanenRac/URTC-DOCS) - Architektur, Schnittstellen, Sicherheitsbasis und erzeugter Katalog des Ökosystems sowie die Werkzeuge, die alle Repositories vergleichen.
  * **URTC-UPDATER** (dieses Repository) - Desktop-Werkzeug, das die Repositories der URTC-Familie erkennt, installiert und aktualisiert, jeweils eine ausdrückliche Aktion.

**Schwesterprojekte (unabhängig, mit derselben Basis und denselben Werkzeugen):**

* **[HYDRA-UMC-DOCS](https://github.com/JuanenRac/HYDRA-UMC-DOCS)** - Schwesterprojekt: das Dokumentationszentrum von HYDRA-UMC, einem unabhängigen Ökosystem, das Basis und Werkzeuge mit diesem teilt
* **[ARMOR-DOCS](https://github.com/JuanenRac/ARMOR-DOCS)** - Schwesterprojekt: das Dokumentationszentrum von A.R.M.O.R., dem Sicherheits-Ökosystem, ebenfalls unabhängig und auf derselben Basis
* **[JuanenRac](https://github.com/JuanenRac/JuanenRac)** - das Profil und das Status-Dashboard aller Ökosysteme

## 📚 Dokumentation

* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — jeder `--cli`-Unterbefehl, echte Ausgabe aus einem echten installierten Lauf, und der Exit-Code-Vertrag.
* **[docs/QML_DESKTOP_GUI.md](docs/QML_DESKTOP_GUI.md)** — wie der Qt Quick/QML-Desktop-Client aufgebaut ist, und wie er eine echte Kontrolloberflaeche ueber demselben Backend bleibt, das auch `--cli` verwendet, statt einer zweiten Implementierung.
* **[Aenderungsprotokoll dieses Repositories](CHANGELOG.md)**
* Fragen, Ideen und Meldungen: electrohobby3d@gmail.com

## 🤝 Mitwirken und Community

* Führe vor einem Pull Request `URTC_CI=1 python tools/ci_validate.py` aus: es muss bestehen. Siehe [CONTRIBUTING.md](CONTRIBUTING.md) und den [Verhaltenskodex](CODE_OF_CONDUCT.md).
* Das README gibt es in acht Sprachen: Eine Textänderung wird in allen acht Dateien vorgenommen, und die mit anderen Repositorys geteilten Abschnitte schreibt `tools/readme_sections.py` von URTC-COMMON.
* Eine Änderung am CAN-Protokoll beginnt in URTC-COMMON (`spec/can_protocol.json`) und gelangt über die geprüfte Kopie in dieses Repository.
* Beschreibe nichts als auf einer Platine funktionierend, was nur gebaut wurde.
* Melde eine Schwachstelle privat: [SECURITY.md](SECURITY.md). Fragen, Ideen und Meldungen: electrohobby3d@gmail.com ([SUPPORT.md](SUPPORT.md)).

## 👤 AUTOR

**JuanenRac** (Electro Hobby 3D)
📧 electrohobby3d@gmail.com
📺 [youtube.com/@electrohobby3d](https://youtube.com/@electrohobby3d)

## 📜 LIZENZ

GPL-3.0-or-later - siehe [LICENSE](LICENSE).
