"""
Script per addestrare un classificatore con lo scopo di identificare la presenza di animali nei video, 
utilizzando le caratteristiche estratte da MobileNetV2 e un campionamento statistico dei frame 
basato su una distribuzione definita nel ParamManager.

Logica di Funzionamento:

1. Transfer Learning & Estrazione Caratteristiche: 
   Utilizza una rete neurale MobileNetV2 (pre-addestrata su ImageNet) come estrattore di 
   caratteristiche "frozen". Ogni fotogramma selezionato viene processato tramite 
   GPU AMD (ROCm/PyTorch) e convertito in un vettore numerico di 1280 dimensioni che 
   rappresenta le proprietà visive astratte (forme, texture, contrasti).

2. Campionamento Statistico Temporale: 
   Per superare il limite del trigger PIR (soggetti veloci o uccelli che appaiono solo 
   all'inizio), lo script non analizza il video in modo lineare. Applica una distribuzione 
   di probabilità (Gamma o Esponenziale) definita nel ParamManager per concentrare 
   il campionamento dei frame nei primi secondi della clip, massimizzando la probabilità 
   di intercettare il movimento rilevato dal sensore.

3. Addestramento Random Forest: 
   Le caratteristiche estratte dai singoli fotogrammi vengono utilizzate per addestrare 
   un classificatore Random Forest. Questo modello impara a distinguere i segnali visivi 
   tipici degli animali (anche piccoli come uccelli) dal rumore causato da rami mossi, 
   nebbia o pioggia, utilizzando le cartelle di errori corretti dall'utente (falsi vuoti) 
   come set di "hard negatives" per affinare la precisione.

4. Validazione Anti-Leakage: 
   Lo script garantisce l'affidabilità dei risultati dividendo il dataset in Training 
   e Test set esclusivamente a livello di Video intero. Questo impedisce al modello di 
   "barare" vedendo fotogrammi diversi dello stesso video in entrambe le fasi, assicurando 
   che le performance dichiarate rispecchino la reale capacità di analizzare riprese 
   totalmente nuove.

5. Ottimizzazione Hardware: 
   Il sistema è configurato per sfruttare l'accelerazione hardware della GPU AMD Radeon 
   RX 6750 XT tramite l'ambiente ROCm, permettendo l'analisi di un numero elevato di 
   frame per video (N_a) in tempi ridotti.
"""

import os
import torch
import numpy as np
import joblib
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from torchvision import models, transforms
from param_manager import ParamManager


class FinalTrainer:
    def __init__(self):

        # --- CONFIGURAZIONE GPU AMD ---
        os.environ['HSA_OVERRIDE_GFX_VERSION'] = '10.3.0'
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.pm = ParamManager()
        
        # Caricamento parametri dal TOML
        self.n_frames = self.pm.config['parameters'].get('n_frames_per_video', 15)
        
        # Caricamento Modello Visivo (MobileNetV2)
        print(f"Caricamento MobileNetV2 su {self.device}...")
        weights = models.MobileNet_V2_Weights.DEFAULT
        self.fe_model = models.mobilenet_v2(weights=weights).to(self.device)
        self.fe_model.eval()
        
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def extract_video_features(self, video_path):
        """Estrae le caratteristiche usando il campionamento statistico dal ParamManager"""
        cap = cv2.VideoCapture(video_path)
        total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_f < self.n_frames:
            cap.release()
            return None
            
        # Otteniamo gli indici dei frame tramite la distribuzione Gamma/Exp definita nel TOML
        indices = self.pm.get_frame_indices(total_f)
        
        video_feats = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                img_t = self.transform(frame).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    f = self.fe_model.features(img_t)
                    f = torch.nn.functional.adaptive_avg_pool2d(f, (1, 1))
                    video_feats.append(f.flatten().cpu().numpy())
        cap.release()
        return video_feats

    def train(self):
        # 1. RACCOLTA VIDEO
        categories = [
            ('folder_animals', 1), 
            ('folder_false_empty', 1), 
            ('folder_empty', 0)
        ]
        
        video_paths = []
        labels = []

        for key, label in categories:
            path = self.pm.get_path(key)
            if not os.path.exists(path): continue
            files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.mp4', '.avi'))]
            video_paths.extend(files)
            labels.extend([label] * len(files))

        # 2. SPLIT PER VIDEO (Evita il Data Leakage)
        vids_train, vids_test, y_train_vid, y_test_vid = train_test_split(
            video_paths, labels, test_size=0.20, stratify=labels, random_state=42
        )

        # 3. ESTRAZIONE CARATTERISTICHE
        print(f"Analisi di {len(vids_train)} video per il training...")
        X_train, y_train = [], []
        for v, l in zip(vids_train, y_train_vid):
            feats = self.extract_video_features(v)
            if feats:
                for f in feats:
                    X_train.append(f)
                    y_train.append(l)

        # 4. ADDESTRAMENTO FORESTA
        print(f"Addestramento Random Forest finale su {len(X_train)} campioni...")
        clf = RandomForestClassifier(n_estimators=300, class_weight='balanced', n_jobs=-1)
        clf.fit(X_train, y_train)

        # 5. TEST REALE
        print("Valutazione del modello sui video di test (mai visti)...")
        X_test, y_test = [], []
        for v, l in zip(vids_test, y_test_vid):
            feats = self.extract_video_features(v)
            if feats:
                for f in feats:
                    X_test.append(f)
                    y_test.append(l)
        
        preds = clf.predict(X_test)
        print("\n--- PERFORMANCE REALI ---")
        print(classification_report(y_test, preds))
        
        # 6. SALVATAGGIO
        joblib.dump(clf, self.pm.model_path)
        print(f"Modello salvato in: {self.pm.model_path}")

if __name__ == "__main__":
    FinalTrainer().train()