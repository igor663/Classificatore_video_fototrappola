"""
Lo script scansiona la cartella dei video, identifica i duplicati basandosi su dimensione e contenuto (hash), e li elimina mantenendo solo una copia per gruppo di duplicati. 
La scelta di quale file mantenere si basa su una gerarchia di cartelle:
"""

import os
import hashlib

# Definizione della gerarchia (Punteggio minore = Maggiore importanza)
GERARCHIA_CARTELLE = {
    "Video Con Animali": 1,
    "falsi vuoti": 2,
    "video con altro": 3,
    "vuoti": 4,
    "video da analizzare": 5
}

def get_punteggio_priorita(percorso_file):
    """Restituisce il punteggio di importanza basato sulla cartella contenitrice."""
    for nome_cartella, punteggio in GERARCHIA_CARTELLE.items():
        if nome_cartella in percorso_file:
            return punteggio
    return 999  # Se non è in nessuna delle cartelle indicate, è meno importante di tutte

def calcola_hash(percorso_file, chunk_size=8192):
    """Calcola l'MD5 del file a pezzi."""
    hash_md5 = hashlib.md5()
    try:
        with open(percorso_file, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def pulisci_duplicati(cartella_base, dry_run=True):
    estensioni_video = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.3gp', '.asf'}
    mappa_dimensione = {}
    
    print(f"--- Fase 1: Scansione dimensioni in {cartella_base} ---")
    for root, _, files in os.walk(cartella_base):
        for f in files:
            if os.path.splitext(f)[1].lower() in estensioni_video:
                path = os.path.join(root, f)
                size = os.path.getsize(path)
                if size not in mappa_dimensione:
                    mappa_dimensione[size] = []
                mappa_dimensione[size].append(path)

    # Dizionario per raggruppare i file per contenuto reale (hash)
    # { 'hash_binario': [lista_percorsi_file_identici] }
    mappa_hash = {}

    print("--- Fase 2: Analisi hash per file sospetti ---")
    for size, percorsi in mappa_dimensione.items():
        if len(percorsi) < 2:
            continue
        
        for p in percorsi:
            h = calcola_hash(p)
            if h:
                if h not in mappa_hash:
                    mappa_hash[h] = []
                mappa_hash[h].append(p)

    print("--- Fase 3: Risoluzione duplicati in base alla priorità ---")
    eliminati_totali = 0

    for h, percorsi in mappa_hash.items():
        if len(percorsi) < 2:
            continue

        # Ordina i percorsi in base al punteggio di priorità (dal più importante al meno)
        percorsi_ordinati = sorted(percorsi, key=get_punteggio_priorita)
        
        # Il primo della lista è quello da TENERE
        da_tenere = percorsi_ordinati[0]
        da_eliminare = percorsi_ordinati[1:]

        print(f"\nGruppo duplicati trovato (Hash: {h[:8]}...):")
        print(f"  [TENGO] {da_tenere} (Priorità: {get_punteggio_priorita(da_tenere)})")

        for file_pessimo in da_eliminare:
            eliminati_totali += 1
            print(f"  [CANCELLO] {file_pessimo} (Priorità: {get_punteggio_priorita(file_pessimo)})")
            
            if not dry_run:
                try:
                    os.remove(file_pessimo)
                except Exception as e:
                    print(f"    ERRORE CANCELLAZIONE: {e}")

    print("\n" + "="*50)
    if dry_run:
        print(f"SIMULAZIONE COMPLETATA. Avrei eliminato {eliminati_totali} file duplicati.")
        print("Per procedere davvero, imposta dry_run=False nello script.")
    else:
        print(f"PULIZIA COMPLETATA. Eliminati {eliminati_totali} file duplicati.")

# --- AVVIO ---
cartella_madre = "/home/igor/Videos/Video Fototrappola"

# Imposta dry_run=False per cancellare davvero
# Imposta dry_run=True per una simulazione senza cancellazione
pulisci_duplicati(cartella_madre, dry_run=False)