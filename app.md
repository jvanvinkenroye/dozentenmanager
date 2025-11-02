# Konzept
Ich möchte ein Tool zur Verwaltung von Studierenden.
- Studierende gehören zu Hochschulen.
- Dort besuchen sie Lehrveranstaltungen.
- Sie erbringen Prüfungsleistungen, die entweder aus einem oder mehreren Teilen bestehen.
- Diese Prüfungsleistungen müssen erfasst werden (eingereicht/nicht eingereicht), mit Punkten versehen und in Noten umgewandelt werden. 
- Ich möchte überwachen können, ob noten eingetragen wurden
-Ich möchte Änderungen in den Noten notieren können.
- Studierende sollen importiert und exportiert werden können.
- Studierende haben Vor- und Nachnamen, Studiengänge, E-Mail-Adressen und Matrikelnummern.
- Studierenden können an einer oder mehreren Lehrveranstaltungen teilnhemen. 
- Man muss sie an- und abmelden können. 
- Ich möchte einen Parser für E-Mails, der überprüft, ob Anhänge enthalten sind.
Die Anhänge sollen automatisch zugeordnet werden können. Wenn das nicht geht, möchte ich das manuell tun können.
- Ich möchte einen Parser für PDF- und Word-Dokumente. Die Anhänge sollen automatisch zugeordnet werden können. Wenn das nicht geht, möchte ich das manuell tun können.
- Alle Änderungen sollen geloggt werden.
- Die Produkte sollen nach dieser Struktur abgelegt sein:
	Hochschule/Semester/Lehrveranstaltung/NachnameVorname
	th-kolen/2023_SoSe/EinführungStatsitik/MuellerMIke/

# Technik
- Das Ganze soll als Flask-Anwendung laufen.
- Die Datenbank soll SQLite sein.
- Technisch soll das Ganze mit Python und UV laufen.
- Als CSS-Framework möchte ich Bulma CSS verwenden.
- Die einzelenen Tools sollen erst als cli vorliegen, dann als flask-route

# Workflow
- ich möchte erst die einzlenen features
- Dann linter
- Dann commit

