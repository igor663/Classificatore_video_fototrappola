"""Simulatore per testare l'accuratezza del classificatore su un campione di video, senza spostare alcun file. 
Utile per valutare la performance reale del modello prima di applicarlo su larga scala."""

import os
import torch
import cv2
import numpy as np
import joblib
import random
from torchvision import models, transforms
from param_manager import ParamManager



class ClassifierSimulator:
    def __init__(self, sample_size=50):
        # --- CONFIGURAZIONE GPU AMD ---
        os.environ['HSA_OVERRIDE_GFX_VERSION'] = '10.3.0'
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.pm = ParamManager()
        self.sample_size = sample_size
        
        # Carica Modelli
        print(f"Caricamento IA su {self.device}...")
        self.clf = joblib.load(self.pm.model_path)
        weights = models.MobileNet_V2_Weights.DEFAULT
        self.fe_model = models.mobilenet_v2(weights=weights).to(self.device)
        self.fe_model.eval()
        
        self.transform = transforms.Compose([
            transforms.ToPILImage(), transforms.Resize((224, 224)),
            transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        # Parametri dal TOML
        self.n_frames = self.pm.config['parameters'].get('n_frames_per_video', 20)
        self.min_votes = self.pm.config['parameters'].get('min_votes_animal', 3)
        self.conf_thresh = self.pm.config['parameters'].get('conf_threshold_frame', 0.70)

    def analyze_video(self, path):
        cap = cv2.VideoCapture(path)
        total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        indices = self.pm.get_frame_indices(total_f)
        
        votes = 0
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                img_t = self.transform(frame).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    f = self.fe_model.features(img_t)
                    f = torch.nn.functional.adaptive_avg_pool2d(f, (1, 1)).flatten().cpu().numpy()
                
                prob = self.clf.predict_proba([f])[0]
                idx_animale = np.where(self.clf.classes_ == 1)[0][0]
                if prob[idx_animale] > self.conf_thresh:
                    votes += 1
        cap.release()
        return 1 if votes >= self.min_votes else 0, votes

    def run_simulation(self):
        # Cartelle da testare
        tests = [
            ('folder_animals', 1, "ANIMALI"),
            ('folder_empty', 0, "VUOTI")
        ]
        
        totale_corretti = 0
        totale_testati = 0

        print("\n" + "="*60)
        print(f"AVVIO SIMULAZIONE (Sample size: {self.sample_size} per cartella)")
        print("="*60)

        for key, ground_truth_label, label_name in tests:
            path = self.pm.get_path(key)
            files = [f for f in os.listdir(path) if f.lower().endswith(('.mp4', '.avi'))]
            
            # Prendi un campione casuale
            sample = random.sample(files, min(len(files), self.sample_size))
            
            print(f"\n--- Testando cartella: {label_name} ({len(sample)} video) ---")
            
            corretti_cartella = 0
            for vid in sample:
                prediction, votes = self.analyze_video(os.path.join(path, vid))
                
                is_correct = (prediction == ground_truth_label)
                status = "✅ OK" if is_correct else "❌ ERRORE"
                if is_correct: corretti_cartella += 1
                
                pred_label = "ANIMALE" if prediction == 1 else "VUOTO"
                print(f"{status} | Video: {vid[:30]}... | IA dice: {pred_label} ({votes} voti)")

            totale_corretti += corretti_cartella
            totale_testati += len(sample)
            print(f"Risultato {label_name}: {corretti_cartella}/{len(sample)} corretti.")

        print("\n" + "="*60)
        print(f"REPORT FINALE SIMULAZIONE")
        print(f"Accuratezza Totale: {(totale_corretti/totale_testati)*100:.2f}%")
        print(f"Video totali analizzati: {totale_testati}")
        print("Nessun file è stato spostato.")
        print("="*60)

if __name__ == "__main__":
    # Puoi cambiare 50 con il numero di video che vuoi testare per ogni cartella
    sim = ClassifierSimulator(sample_size=300)
    sim.run_simulation()