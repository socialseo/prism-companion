# PRISM Companion — prima configurazione guidata

Prototipo essenziale gratuito, senza dipendenze aggiuntive: Python 3.9 o successivo e un browser moderno. App autonoma, non un blocco WordPress.


## Cosa cambia in questa versione

Grafica nera e viola, testi chiari, numeri grandi. Nessuna pixel art.

Il percorso ora è: **crea il tavolo → invita → prepara le schede → conferma → gioca**.

1. Il Master crea una sessione e condivide il codice.
2. Ogni giocatore entra e segue sei passi: identità, personaggio, pilota, mecha, competenze e conferma.
3. “Salva bozza” conserva i valori anche se la preparazione non è conclusa. “Continua” cambia passo, ma non salva da solo.
4. Nell’ultimo passo si controllano nome e risorse e si conferma che i valori sono stati concordati con il Master. Gli esempi non sono una creazione ufficiale del personaggio.
5. Il Master vede quante schede sono confermate. “Inizia la partita” funziona solo quando almeno un giocatore è presente e tutte le schede sono confermate.
6. Durante il gioco si lanciano dadi fisici e si aggiornano le risorse manualmente. Per aggiungere un giocatore, il Master usa “Riapri preparazione”.

“Scheda pronta” significa che il partecipante dichiara di aver controllato i valori con il Master: non certifica il bilanciamento e non inventa regole di creazione.

**Per aggiornare una vecchia installazione:** ferma il server e fai una copia della cartella. Sostituisci solo i file del programma, conservando `prism.sqlite3`. Al riavvio l’app aggiunge i nuovi stati senza cancellare schede o registri. Le vecchie schede richiedono una prima conferma.

Verificati anche: blocco dell’avvio senza schede pronte, conferma esplicita dei valori, avvio riservato al Master, blocco degli ingressi durante il gioco, riapertura della preparazione e aggiornamento di un archivio precedente. Provati nel browser ingresso, bozza, conferma e avvio partita.

## Avvio su Mac

1. Apri `Avvia-PRISM.command` nella stessa cartella degli altri file. Lascia aperta la finestra del Terminale.
2. Apri http://localhost:8765 nel browser.
3. Crea una sessione come Master. Il codice invito appare in alto.
4. Apri una **nuova scheda** (non duplicare quella del Master) e inserisci il codice nella sezione Giocatore, con un nome diverso.
5. Cambia gli HP umani da 15 a 12 e salva. La vista Master si aggiorna entro circa 2 secondi.
6. Dal Master modifica gli HP a 14, indica un motivo e salva. Il giocatore riceve la correzione.
7. Nel registro del Master premi **Prepara ripristino** sulla modifica: controlla i valori proposti e salva. La correzione precedente resta nel registro.

Se il doppio clic non apre il programma, apri il Terminale nella cartella e usa:

```sh
python3 server.py --host 0.0.0.0
```

Per un test limitato al solo computer usa `python3 server.py`.
Per fermare il server: Ctrl+C nella finestra del Terminale.

## Due dispositivi sulla stessa rete

Avvia con `Avvia-PRISM.command`. Sul secondo dispositivo usa `http://INDIRIZZO-IP-DEL-MAC:8765`, con l'indirizzo locale del Mac (visibile nei dettagli della connessione di rete), non `localhost`. Poi inserisci il codice della sessione. Il Mac deve restare acceso; eventuali firewall e reti Wi-Fi ospiti possono impedire il collegamento. Non è necessario aprire porte sul router.

## Cosa funziona davvero

- Sessioni separate e codice invito casuale di 8 caratteri.
- Ruolo Master assegnato dal server alla creazione; ingresso sempre come Giocatore.
- Ogni giocatore modifica soltanto il proprio personaggio e mecha. Il server impedisce di leggere o modificare schede altrui.
- Il Master legge e corregge tutte le schede della propria sessione, con motivo obbligatorio.
- Registro persistente con autore, ora, campo, valore precedente e nuovo. Il giocatore legge il proprio registro; il Master legge l'intera sessione.
- Sincronizzazione tramite richieste al server ogni 2 secondi. Non è una simulazione con memoria del singolo browser.
- Salvataggio SQLite: i dati restano dopo un riavvio del server.
- Conflitti fra versioni: un salvataggio superato viene rifiutato. La bozza resta visibile; annotala se vuoi conservarla e usa “Scarta bozza e ricarica” prima di reinserire la modifica.
- Ripristino selettivo dei campi di una modifica tramite nuova correzione, senza cancellare eventi.

## Regolamento v0.3

Fonte letta: Prism_Roll_20_Manuale_Completo_v0_3.pdf, 25 pagine, 10 novembre 2026.

Applicati: caratteristiche umane 1–20; modificatore arrotondato per difetto; 20 competenze 0–5; HP massimi umani 5 + COS, HP negativi ammessi (p. 3, 6). Pilota con sei statistiche separate 1–100 (p. 8); SEN massimo assoluto 50; MOV separato da MOB; HP mecha standard 100 (p. 9).

ARM, EN, MOB, MOV e SEN iniziano a zero come **segnaposto da configurare**, non come modello ufficiale. Caratteristiche umane 10 e pilota 50 sono esempi. La distribuzione iniziale non è definita dal manuale: vale la decisione della campagna (p. 23). Massimi e valori macchina si impostano secondo il modello.

Non automatizzati: danni, cure, morte, distruzione, dadi, condizioni, armamenti, iniziativa, nemici, Analisi e Ricerca sensoriale. In questo passo l'app registra i valori decisi al tavolo.

**Non definitive / da completare** (p. 4, 24–25): iniziativa completa; arrotondamento del +50% critico mecha; componenti mirati; abbattimento, espulsione ed effetti sul pilota; riparazioni; cataloghi modelli, armi e sistemi. Nessuna di queste procedure è stata inventata nell'app. Sensori per piccoli bersagli: espansione sospesa.

I limiti numerici tecnici a 100.000 e il limite note a 4.000 caratteri proteggono il prototipo: non sono regole PRISM. L'app non implementa ancora tutte le sezioni delle schede originali; equipaggiamento e condizioni si possono annotare nel campo note.

## Limiti di accesso e pubblicazione

È un **server locale con multiplayer reale**, utilizzabile su rete fidata. Non è un servizio online pubblicato. Il traffico locale è HTTP; non inoltrare la porta su Internet. Mancano HTTPS, account recuperabili, revoca partecipanti, rate limiting, chiusura inviti e gestione del ciclo di vita delle sessioni.

L'accesso è conservato nella singola scheda del browser (`sessionStorage`). Ricaricare la pagina mantiene il ruolo. Uscire esplicitamente o perdere quella scheda può perdere l'accesso: non esiste ancora recupero della credenziale Master né riassegnazione di una scheda. I partecipanti elencati sono iscritti, non necessariamente online.

Dati nel file `prism.sqlite3`, generato al primo avvio nella cartella dell'app. Per backup, ferma il server e copia quel file. Conserva anche la scheda browser per poter rientrare con la stessa identità. Il codice invito permette solo di creare un nuovo giocatore, non di assumere un'identità esistente.

## Verifiche eseguite

Test d'integrazione con server HTTP e database temporaneo: creazione e ingresso, codice errato, nomi duplicati, ruoli, isolamento fra giocatori e sessioni, limiti di campo e risorse, correzione motivata, audit prima/dopo, ripristino, salvataggi simultanei e persistenza riaprendo il database.

Prova nel browser con due viste indipendenti: Master crea sessione, giocatore entra e salva 15 → 12 HP, Master vede 12 e corregge a 14, giocatore riceve 14 e il registro; ripristino Master salvato. Non verificato su un secondo dispositivo fisico o su una rete Wi-Fi reale.

Per ripetere i test: `python3 test_server.py`. I test usano un database temporaneo e non modificano le tue sessioni.

## Passo successivo proposto

Recupero degli accessi e riassegnazione delle schede, prima di una distribuzione online con HTTPS. In seguito, dadi e applicazione danni secondo le sole procedure confermate, mantenendo sempre la correzione Master.

## Visualizzazione smartphone

Aggiornati layout a 320, 390, 430 pixel, tablet 768 e desktop 1280. Pulsanti di almeno 44 pixel, campi fluidi su una o due colonne su smartphone, navigazione in griglia e salvataggio a larghezza piena. Verificate viste Master e Giocatore e salvataggio da viewport smartphone; nessuno scorrimento orizzontale nelle viste controllate. Test eseguiti nel browser con dimensioni simulate, non su dispositivi fisici né con tastiera iOS/Android.

La pagina iniziale propone ora prima la scelta Master/Giocatore e poi il modulo relativo.
