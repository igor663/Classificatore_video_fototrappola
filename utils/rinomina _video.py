"""Codice che standartizza i nomi dei video in base alla data di ultima modifica (cioè quella che teoricaente è la data di creazione), garantendo unicità a livello globale su tutto il disco."""

import os
from datetime import datetime

def rinomina_video_sul_posto(cartella_base):
    # Estensioni video da considerare
    estensioni_video = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.3gp', '.asf'}
    
    # Insieme per tenere traccia dei nomi già assegnati in TUTTO il disco
    # così garantiamo che ogni nome sia unico a prescindere dalla cartella
    nomi_globali_usati = set()

    print(f"Inizio rinomina in corso nella cartella: {cartella_base}")
    print("-" * 50)

    # Scansione ricorsiva (entra in tutte le sottocartelle)
    for root, dirs, files in os.walk(cartella_base):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in estensioni_video:
                percorso_vecchio = os.path.join(root, filename)
                
                try:
                    # Ottieni la data di ultima modifica
                    timestamp = os.path.getmtime(percorso_vecchio)
                    data_ora = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S')
                    
                    # Nome desiderato
                    nuovo_nome_base = f"{data_ora}"
                    nuovo_nome = f"{nuovo_nome_base}{ext}"
                    
                    # Controllo unicità globale (per evitare duplicati tra cartelle diverse)
                    counter = 1
                    while nuovo_nome in nomi_globali_usati:
                        nuovo_nome = f"{nuovo_nome_base}_{counter}{ext}"
                        counter += 1
                    
                    nomi_globali_usati.add(nuovo_nome)
                    
                    percorso_nuovo = os.path.join(root, nuovo_nome)
                    
                    # Rinominazione effettiva
                    if percorso_vecchio != percorso_nuovo:
                        os.rename(percorso_vecchio, percorso_nuovo)
                        print(f"Rinominato: {filename} -> {nuovo_nome}")
                    
                except Exception as e:
                    print(f"Errore su {filename}: {e}")

    print("-" * 50)
    print("Operazione completata!")

# --- CONFIGURAZIONE ---
# Inserisci il percorso della cartella madre
percorso_target = '/home/igor/Videos/Video Fototrappola'

# Avvio
rinomina_video_sul_posto(percorso_target)