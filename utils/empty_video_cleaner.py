""" 
Lo script raggruppa i video per data, calcola quanti eliminarne per scendere sotto i 50 e ne tiene uno ogni  K (dove K=N_videos/50).
E' disponibile anche una modalità di simulazione (dry_run=True) che mostra quanti video verrebbero eliminati senza cancellarli realmente. 
"""

import os
import math
from collections import defaultdict
from param_manager import ParamManager

def pulisci_video_vuoti(dry_run=True):
    pm = ParamManager()
    # Puntiamo alla cartella dei vuoti definita nel TOML
    cartella_vuoti = pm.get_path('folder_empty')
    
    if not os.path.exists(cartella_vuoti):
        print(f"Errore: La cartella {cartella_vuoti} non esiste.")
        return

    # 1. Raggruppa i file per data (YYYY-MM-DD)
    video_per_giorno = defaultdict(list)
    file_list = [f for f in os.listdir(cartella_vuoti) if f.lower().endswith(('.mp4', '.avi'))]
    
    for f in file_list:
        # Il nome è YYYY-MM-DD_HH-MM-SS.mp4, prendiamo i primi 10 caratteri
        data = f[:10]
        video_per_giorno[data].append(f)

    totale_da_eliminare = 0
    print(f"{'Data':<12} | {'Totali':<8} | {'Stato':<15}")
    print("-" * 45)

    percorsi_da_cancellare = []

    # 2. Analizza ogni giorno
    for data in sorted(video_per_giorno.keys()):
        files = sorted(video_per_giorno[data]) # Ordiniamoli per orario
        n = len(files)
        
        if n <= 50:
            print(f"{data:<12} | {n:<8} | OK (Sotto soglia)")
            continue
        
        # Calcoliamo il passo (k). Se n=150, k=3 (teniamo 1 ogni 3)
        passo = n / 50.0
        
        # Scegliamo quali tenere
        indici_da_tenere = [int(i * passo) for i in range(50)]
        
        to_keep = set()
        for idx in indici_da_tenere:
            if idx < n:
                to_keep.add(files[idx])
        
        # Identifichiamo quelli da cancellare
        for f in files:
            if f not in to_keep:
                percorsi_da_cancellare.append(os.path.join(cartella_vuoti, f))
        
        eliminati_oggi = n - len(to_keep)
        totale_da_eliminare += eliminati_oggi
        print(f"{data:<12} | {n:<8} | Riduzione: -{eliminati_oggi}")

    # 3. Esecuzione
    if not percorsi_da_cancellare:
        print("\nNessun video da eliminare.")
        return

    print(f"\nTotale video da eliminare: {totale_da_eliminare}")
    
    if dry_run:
        print("\n*** MODALITÀ SIMULAZIONE (DRY RUN) ***")
        print("Nessun file è stato ancora cancellato.")
        print("Per procedere davvero, imposta dry_run=False nel codice.")
    else:
        conferma = input(f"Sei SICURO di voler cancellare {totale_da_eliminare} video per sempre? (s/n): ")
        if conferma.lower() == 's':
            for p in percorsi_da_cancellare:
                try:
                    os.remove(p)
                except Exception as e:
                    print(f"Errore nella cancellazione di {p}: {e}")
            print("\nPulizia completata con successo.")
        else:
            print("\nOperazione annullata.")

if __name__ == "__main__":
    # Cambia dry_run=False per cancellare davvero i file
    pulisci_video_vuoti(dry_run=False)