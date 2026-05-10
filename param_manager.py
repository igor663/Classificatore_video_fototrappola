import os
import toml
import numpy as np

class ParamManager:
    def __init__(self, config_path="config.toml"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, config_path), "r") as f:
            self.config = toml.load(f)
        self.base_dir = self.config['paths']['base_dir']

    def get_frame_indices(self, total_frames):
        n = self.config['parameters']['n_frames_per_video']
        method = self.config['sampling']['method']
        
        if method == "exponential":
            # Genera campioni esponenziali, scalati sulla lunghezza del video
            lam = self.config['sampling']['exp_lambda']
            samples = np.random.exponential(1/lam, n * 2) # Generiamo più campioni per sicurezza
        elif method == "gamma":
            k = self.config['sampling']['gamma_k']
            theta = self.config['sampling']['gamma_theta']
            samples = np.random.gamma(k, theta, n * 2)
        else: # Default lineare
            return np.linspace(0, total_frames - 1, n, dtype=int).tolist()

        # Normalizziamo i campioni tra 0 e total_frames - 1
        samples = samples / np.max(samples) 
        indices = (samples * (total_frames - 1)).astype(int)
        
        # Prendiamo i primi n unici e li ordiniamo
        unique_indices = sorted(list(set(indices)))[:n]
        return unique_indices

    def get_path(self, key):
        return os.path.join(self.base_dir, self.config['paths'][key])

    @property
    def model_path(self):
        return self.config['paths']['model_output']