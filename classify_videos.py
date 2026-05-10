"""Script principale per classificare i video in base alla presenza di animali, con logica avanzata che tiene conto della densità giornaliera (per identificare giorni ventosi) e di una soglia di confidenza dinamica.
 I video vengono spostati FISICAMENTE nelle cartelle appropriate e viene creato un log dettagliato degli spostamenti per poter annullare gli spostamenti in caso di errore o risultato insoddisfacente."""

import os
import cv2
import torch
import numpy as np
import joblib
import shutil
import json
from collections import Counter
from torchvision import models, transforms
from param_manager import ParamManager

class VideoClassifier:
    def __init__(self):
        # --- CONFIGURAZIONE GPU AMD ---
        os.environ['HSA_OVERRIDE_GFX_VERSION'] = '10.3.0'
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.pm = ParamManager()
        self.log_filename = "spostamenti_log.json"
        self.history = []
        
        # Carica Random Forest
        self.clf = joblib.load(self.pm.model_path)
        
        # Carica MobileNetV2 PyTorch
        print(f"Modelli pronti su {self.device}.")
        weights = models.MobileNet_V2_Weights.DEFAULT
        self.fe_model = models.mobilenet_v2(weights=weights).to(self.device)
        self.fe_model.eval()
        
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # Parametri dal TOML
        self.soglia_vento = self.pm.config['parameters'].get('soglia_video_giornalieri', 50)
        self.min_votes = self.pm.config['parameters'].get('min_votes_animal', 3)
        self.conf_thresh = self.pm.config['parameters'].get('conf_threshold_frame', 0.75)
        self.sicurezza_vento = self.pm.config['parameters'].get('sicurezza_minima_vento', 0.85)

    def run(self):
        sorgente = self.pm.get_path('folder_to_analyze')
        dest_animals = self.pm.get_path('folder_animals')
        dest_empty = self.pm.get_path('folder_empty')
        
        video_files = [f for f in os.listdir(sorgente) if f.lower().endswith(('.mp4', '.avi'))]
        if not video_files:
            print("Nessun video da analizzare.")
            return

        # 1. Calcolo densità giornaliera
        date_counts = Counter([f[:10] for f in video_files])
        
        print(f"Analisi di {len(video_files)} video...")

        for vid_name in video_files:
            path = os.path.join(sorgente, vid_name)
            cap = cv2.VideoCapture(path)
            total_f = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            indices = self.pm.get_frame_indices(total_f)
            
            animal_votes = 0
            max_prob = 0
            
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
                    prob_animale = prob[idx_animale]
                    
                    if prob_animale > self.conf_thresh:
                        animal_votes += 1
                    max_prob = max(max_prob, prob_animale)
            cap.release()

            # 2. Logica decisionale con penalità vento
            num_video_oggi = date_counts[vid_name[:10]]
            giorno_ventoso = num_video_oggi > self.soglia_vento
            
            if giorno_ventoso:
                # In caso di vento, servono più voti O una sicurezza estrema su almeno un frame
                decisione = 1 if (animal_votes >= self.min_votes + 2 or max_prob > self.sicurezza_vento) else 0
                motivo = f"Vento ({num_video_oggi} vid/gg)"
            else:
                decisione = 1 if animal_votes >= self.min_votes else 0
                motivo = "Calmo"

            # 3. Spostamento
            target_dir = dest_animals if decisione == 1 else dest_empty
            dest_full = os.path.join(target_dir, vid_name)
            
            # Gestione nomi duplicati
            c = 1
            while os.path.exists(dest_full):
                base, ext = os.path.splitext(vid_name)
                dest_full = os.path.join(target_dir, f"{base}_{c}{ext}")
                c += 1

            shutil.move(path, dest_full)
            self.history.append({"originale": path, "attuale": dest_full})
            
            status = "ANIMALE" if decisione == 1 else "ALTRO"
            print(f"[{status}] {vid_name} | Voti: {animal_votes} | Max Prob: {max_prob:.2f} | {motivo}")

        # 4. Salvataggio Log
        with open(self.log_filename, "w") as f:
            json.dump(self.history, f, indent=4)
        print("Analisi completata.")

if __name__ == "__main__":
    VideoClassifier().run()