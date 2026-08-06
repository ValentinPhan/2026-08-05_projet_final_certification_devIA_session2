"""Monitoring du modele d'extraction d'allergenes (competence C11).

Rejoue le golden dataset (voir common/golden_dataset.py, C12) a travers le
pipeline hybride reel (IA + mots-cles) et journalise dans **MLflow** :

- des metriques de qualite (precision, rappel, faux positifs/negatifs) —
  permet de comparer deux executions dans le temps (avant/apres une
  modification du prompt, du dictionnaire de synonymes ou du modele) et
  donc de mesurer objectivement une amelioration ou une regression ;
- des metriques de performance (latence moyenne/mediane/max par appel) —
  pertinent pour un modele execute localement, dont la latence depend des
  ressources de la machine ;
- le detail par cas en artefact JSON, pour permettre une restitution
  accessible en complement du tableau de bord MLflow (voir
  docs/03-bloc2-ia/monitoring-modele.md).

Outil choisi : MLflow, deja present dans la stack retenue (voir
architecture.md), gratuit, sans compte, avec un stockage local par fichiers
(aucun serveur a heberger) et un tableau de bord web natif (`mlflow ui`).

Usage :
    py -m monitoring.evaluer_modele
    mlflow ui --backend-store-uri <chemin affiche par le script>
"""
from __future__ import annotations

import json
import os
import statistics
import time
from pathlib import Path

import mlflow
from openai import OpenAI

from common.golden_dataset import CAS_EVALUATION
from common.io_utils import get_data_dir, setup_logger
from api_ia.extraction import analyser_texte

logger = setup_logger("monitoring.evaluer_modele")

OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "llama3.2:3b"
EXPERIMENT_NAME = "nutriscan-extraction-allergenes"

# Le stockage de suivi par systeme de fichiers ("./mlruns") est le choix
# assume ici (gratuit, sans serveur ni compte, voir docs/03-bloc2-ia/
# monitoring-modele.md) - mais des versions recentes de MLflow le
# considerent en fin de vie et levent une exception a moins d'un opt-in
# explicite. Trouve via l'echec du premier run reel du pipeline CI/CD (S8) :
# le run local avait ete installe avec une version de MLflow anterieure a
# ce changement, ce qui masquait le probleme jusqu'a l'execution sur un
# environnement fraichement installe.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")


def run() -> Path:
    """Execute une passe de monitoring complete sur le golden dataset et journalise le resultat dans MLflow."""
    tracking_dir = get_data_dir("mlflow")
    mlflow.set_tracking_uri(tracking_dir.as_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

    vrais_positifs = faux_positifs = faux_negatifs = 0
    latences: list[float] = []
    details = []

    with mlflow.start_run():
        mlflow.log_param("modele", MODEL_NAME)
        mlflow.log_param("nb_cas_evaluation", len(CAS_EVALUATION))

        for cas in CAS_EVALUATION:
            debut = time.monotonic()
            resultat = analyser_texte(client, MODEL_NAME, cas["texte"], allergies_utilisateur=[])
            latence = time.monotonic() - debut
            latences.append(latence)

            detectes = set(resultat["allergenes_detectes"])
            attendus = set(cas["allergenes_attendus"])
            vp, fp, fn = detectes & attendus, detectes - attendus, attendus - detectes
            vrais_positifs += len(vp)
            faux_positifs += len(fp)
            faux_negatifs += len(fn)

            logger.info("%s (%.1fs) : FP=%s FN=%s", cas["id"], latence, sorted(fp), sorted(fn))
            details.append({
                "id": cas["id"],
                "latence_s": round(latence, 2),
                "allergenes_attendus": sorted(attendus),
                "allergenes_detectes": sorted(detectes),
                "detection_ia": resultat["detection_ia"],
                "detection_mots_cles": resultat["detection_mots_cles"],
                "faux_positifs": sorted(fp),
                "faux_negatifs": sorted(fn),
            })

        precision = vrais_positifs / (vrais_positifs + faux_positifs) if (vrais_positifs + faux_positifs) else 1.0
        rappel = vrais_positifs / (vrais_positifs + faux_negatifs) if (vrais_positifs + faux_negatifs) else 1.0

        mlflow.log_metric("precision", precision)
        mlflow.log_metric("rappel", rappel)
        mlflow.log_metric("vrais_positifs", vrais_positifs)
        mlflow.log_metric("faux_positifs", faux_positifs)
        mlflow.log_metric("faux_negatifs", faux_negatifs)
        mlflow.log_metric("latence_moyenne_s", statistics.mean(latences))
        mlflow.log_metric("latence_mediane_s", statistics.median(latences))
        mlflow.log_metric("latence_max_s", max(latences))

        rapport_path = get_data_dir("raw", "monitoring") / "dernier_rapport_evaluation.json"
        rapport_path.write_text(json.dumps({
            "modele": MODEL_NAME,
            "precision": precision,
            "rappel": rappel,
            "vrais_positifs": vrais_positifs,
            "faux_positifs": faux_positifs,
            "faux_negatifs": faux_negatifs,
            "latence_moyenne_s": statistics.mean(latences),
            "details": details,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        mlflow.log_artifact(str(rapport_path))

        logger.info(
            "precision=%.0f%% rappel=%.0f%% latence_moyenne=%.1fs (run MLflow : %s)",
            precision * 100, rappel * 100, statistics.mean(latences), mlflow.active_run().info.run_id,
        )

    return tracking_dir


if __name__ == "__main__":
    run()
