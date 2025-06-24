from minio import Minio
from minio.error import S3Error
import json

# REMPLACEZ par votre vraie IP
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "2Tw6UR0sjgEZuzPZ99Fc"
SECRET_KEY = "DKJJ7Rs4UKUhmJlwEV6MF1tcEZ5ctjXb01i9vj0I"
BUCKET_NAME = "appstockage"

def setup_minio():
    # Connexion à MinIO
    client = Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )
    
    print("🔌 Connexion à MinIO...")
    
    # Politique pour rendre le bucket public en lecture
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"]
            }
        ]
    }
    
    # Appliquer la politique
    try:
        client.set_bucket_policy(BUCKET_NAME, json.dumps(policy))
        print(f" Politique publique appliquée au bucket '{BUCKET_NAME}'")
        print(f" Vos fichiers seront accessibles via: http://{MINIO_ENDPOINT}/{BUCKET_NAME}/")
    except S3Error as e:
        print(f" Erreur lors de l'application de la politique: {e}")

if __name__ == "__main__":
    setup_minio()