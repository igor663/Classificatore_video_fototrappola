# 🐾 Classificatore Video Fototrappola AI

Un sistema avanzato di visione artificiale per lo smistamento e la classificazione automatica di video provenienti da fototrappole. Il progetto utilizza il **Transfer Learning** e un approccio statistico per distinguere tra riprese di fauna selvatica e "falsi positivi" (movimento di vegetazione dovuto al vento).

## 🚀 Caratteristiche Principali

- **Visione Artificiale**: Estrazione delle caratteristiche tramite rete neurale **MobileNetV2** (PyTorch).
- **Classificazione**: Modello **Random Forest** addestrato su caratteristiche estratte per un'analisi rapida e robusta.
- **Campionamento Statistico**: Implementazione di distribuzioni **Gamma** ed **Esponenziale** per il campionamento dei frame, ottimizzata per catturare soggetti veloci (es. uccelli) che appaiono subito dopo il trigger PIR.
- **Accelerazione Hardware**: Supporto nativo per **GPU AMD Radeon (RDNA2/RX 6750 XT)** tramite piattaforma **ROCm**.
- **Analisi Contestuale**: Logica di "penalità vento" basata sulla densità temporale degli scatti giornalieri.
- **Data Management Toolkit**:
  - `Undo system`: Ripristino istantaneo dello stato precedente tramite log JSON.
  - `Duplicate cleaner`: Rimozione duplicati con gerarchia di importanza tra cartelle.
  - `Space cleaner`: Campionamento sistematico dei video vuoti per risparmiare spazio su disco.

## 🛠️ Requisiti Hardware & Software

- **Sistema Operativo**: Ubuntu 24.04 LTS (o versioni con kernel recente).
- **GPU**: AMD Radeon RX 6000 series (testato su RX 6750 XT).
- **Piattaforma**: ROCm 6.2 + PyTorch (versione ROCm).
- **Python**: 3.12+

## 📦 Installazione

1. **Clona la repository**:
   ```bash
   git clone https://github.com/igor663/Classificatore_video_fototrappola.git
   cd Classificatore_video_fototrappola

## ⚙️ Configurazione

Il sistema è interamente gestito tramite il file `config.toml`. È possibile regolare:

*   **Percorsi delle cartelle**: (`Video Con Animali`, `vuoti`, `video da analizzare`, `falsi vuoti`).
*   **Parametri di campionamento**: ($N_a$ frame da analizzare, soglia minima di voti).
*   **Distribuzioni statistiche**: (Gamma $k$ e $\theta$, Exponential $\lambda$).
*   **Soglie di sicurezza**: Parametri per la logica euristica anti-vento.

## 🖥️ Utilizzo

Il workflow tipico è gestito dall'**Orchestrator**, ma i singoli moduli possono essere richiamati indipendentemente:

### 1. Training
Analizza i video già classificati per addestrare la Random Forest.
```bash
python3 final_trainer.py
```

### 2. Simulazione
Testa l'accuratezza del modello su un campione randomico senza spostare alcun file.
```bash
python3 simulator_classifier.py
```

### 3. Classificazione
Analizza e sposta i nuovi video nelle cartelle di destinazione.
```bash
python3 classify_videos.py
```

### 4. Annullamento
In caso di errori, ripristina la posizione originale dei video analizzati nell'ultima sessione.
```bash
python3 undo_classification.py
```

## 📂 Struttura del Progetto

```text
├── final_trainer.py         # Addestramento del modello
├── classify_videos.py       # Smistamento video reale
├── simulator_classifier.py  # Test di accuratezza (no move)
├── orchestrator.py          # Coordinamento automazione
├── param_manager.py         # Gestore configurazione TOML
├── undo_classification.py   # Funzione "Annulla"
├── config.toml              # Parametri di sistema
└── utils/
    ├── elimina_duplicati.py   # Pulizia file identici (hash-based)
    ├── empty_video_cleaner.py # Rimuove video vuoti in eccesso
    └── rinomina_vbideo.py     # Rinomina i video per data e ora
```

## Nota Bene:
Alcuni video potrebbero risultare con an

