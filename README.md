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
