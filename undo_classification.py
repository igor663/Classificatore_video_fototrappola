"""Script per annullare la classificazione dei video, riportando i file alla loro posizione originale.
Il processo si basa su un log JSON creato durante la classificazione, che tiene traccia dei percorsi originali e attuali dei video."""

import os
import shutil
import json

def annulla_classificazione():
    # Il log viene cercato nella stessa cartella dello script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, "spostamenti_log.json")

    if not os.path.exists(log_path):
        print(f"ERRORE: Il file di log non esiste in: {log_path}")
        print("Non ci sono operazioni da annullare.")
        return

    try:
        with open(log_path, "r") as f:
            history = json.load(f)
    except Exception as e:
        print(f"ERRORE nella lettura del log: {e}")
        return

    if not history:
        print("Il file di log è vuoto. Nessun file da ripristinare.")
        return

    print(f"Trovati {len(history)} file da riportare indietro.")
    conferma = input("Vuoi procedere con il ripristino totale? (s/n): ")
    if conferma.lower() != 's':
        print("Operazione annullata dall'utente.")
        return

    ripristinati = 0
    errori = 0
    mancanti = 0

    print("-" * 50)
    for record in history:
        perc_attuale = record["attuale"]
        perc_originale = record["originale"]

        # 1. Verifica se il file esiste ancora nella posizione classificata
        if not os.path.exists(perc_attuale):
            print(f"[NON TROVATO] Il file è sparito: {os.path.basename(perc_attuale)}")
            mancanti += 1
            continue

        try:
            # 2. Assicurati che la cartella di destinazione (quella originale) esista
            os.makedirs(os.path.dirname(perc_originale), exist_ok=True)

            # 3. Sposta il file indietro
            shutil.move(perc_attuale, perc_originale)
            print(f"[RIPRISTINATO] {os.path.basename(perc_originale)}")
            ripristinati += 1
        except Exception as e:
            print(f"[ERRORE] Impossibile spostare {os.path.basename(perc_attuale)}: {e}")
            errori += 1

    print("-" * 50)
    print(f"SINTESI OPERAZIONE:")
    print(f"- File ripristinati: {ripristinati}")
    print(f"- File non trovati: {mancanti}")
    print(f"- Errori tecnici: {errori}")

    if ripristinati > 0 and errori == 0:
        # Per sicurezza, rinominiamo il log invece di cancellarlo, 
        # così hai una traccia di quello che è successo
        backup_log = log_path.replace(".json", f"_annullato_{ripristinati}.json")
        os.rename(log_path, backup_log)
        print(f"\nIl log è stato archiviato come: {os.path.basename(backup_log)}")
    
    print("\nFatto! La cartella 'video da analizzare' è tornata allo stato precedente.")

if __name__ == "__main__":
    annulla_classificazione()