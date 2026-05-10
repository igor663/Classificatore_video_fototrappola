"""Script per coordinare il training, la classificazione e la simulazione della classificazione.
Ideale per gestire sessioni di lavoro prolungate, assicurando che ogni fase venga avviata immediatamente al termine della precedente senza supervisione manuale"""

from classify_videos import VideoClassifier
from train_classifier import FinalTrainer
from simulator_classifier import ClassifierSimulator


if __name__ == "__main__":
    # 1. Addestramento del modello (se necessario)
    trainer = FinalTrainer()
    trainer.train()

    # 2. Classificazione dei video, con sposptamento fisico
    # classifier = VideoClassifier()
    # classifier.run()

    #3. Classificazione simulata per testare la logica decisionale senza spostare file
    sim = ClassifierSimulator(sample_size=300)
    sim.run_simulation()
    