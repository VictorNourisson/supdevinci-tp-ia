import os
import time
import cv2
import urllib.request
import json
from dotenv import load_dotenv

def load_env_credentials():
    """
    Tente de charger les identifiants AWS à partir d'un fichier .env, s'il existe.
    Retourne un tuple (access_key, secret_key, region) ou (None, None, None).
    """
    if os.path.exists(".env"):
        load_dotenv()
        return (
            os.getenv("ACCESS_KEY"),
            os.getenv("SECRET_KEY"),
            os.getenv("AWS_REGION")
        )
    return None, None, None

def determine_file_type(filepath):
    """
    Examine l'extension d'un fichier pour en déduire s'il s'agit d'une image ou d'une vidéo.
    """
    base = os.path.basename(filepath)
    extension = base.split(".")[-1].lower()

    if extension in ["jpg", "png", "tiff", "svg", "jpeg"]:
        return "image"
    elif extension in ["mp4", "avi", "mkv", "mov"]:
        return "vidéo"
    return None

def grab_video_frame(video_path, frame_idx=0):
    """
    Ouvre un fichier vidéo et en extrait une frame donnée (par défaut la 1ère).
    Retourne l'image ou None si la lecture échoue.
    """
    vid = cv2.VideoCapture(video_path)
    vid.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    success, frame = vid.read()
    return frame if success else None

def detect_moderation_from_bytes(image_content, rekognition_client):
    """
    Détecte tout contenu sensible via Rekognition à partir d'un flux binaire.
    Retourne une liste de labels de modération.
    """
    response = rekognition_client.detect_moderation_labels(Image={'Bytes': image_content})
    return [label["Name"] for label in response["ModerationLabels"]]

def transcribe_via_aws(local_path, transcribe_client, s3_client, job_tag, s3_bucket):
    """
    1) Envoie un fichier local (vidéo) dans un bucket S3.
    2) Lance la transcription via Amazon Transcribe en passant une URI s3://.
    3) Patiente le temps que le job soit fini, et renvoie le texte transcrit.

    Retourne None si le job échoue.
    """
    # Emplacement (key) où stocker le fichier dans le bucket
    key_path = f"temp/transcriptions/{job_tag}.mp4"

    # Envoi dans le bucket
    s3_client.upload_file(local_path, s3_bucket, key_path)

    # URI pour Transcribe
    media_uri = f"s3://{s3_bucket}/{key_path}"

    # Lancement du job
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_tag,
        Media={'MediaFileUri': media_uri},
        MediaFormat='mp4',
        LanguageCode='fr-FR'
    )

    # Boucle d'attente
    while True:
        current = transcribe_client.get_transcription_job(TranscriptionJobName=job_tag)
        status = current["TranscriptionJob"]["TranscriptionJobStatus"]
        if status in ["COMPLETED", "FAILED"]:
            break
        time.sleep(5)

    if status == "COMPLETED":
        transcript_url = current["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        with urllib.request.urlopen(transcript_url) as resp:
            data = json.loads(resp.read())
        return data["results"]["transcripts"][0]["transcript"]
    return None

def analyze_media(file_path, rekognition, transcribe, comprehend, s3, bucket_name):
    """
    Analyse un fichier image ou vidéo.
    1) Vérifie d'abord s'il y a un contenu sensible (modération).
    2) Si tout va bien, détermine des hashtags à partir de labels.
    3) Pour une vidéo, effectue également la transcription (Transcribe) et en extrait des mots-clés via Comprehend.

    Retourne:
      - {"moderation_labels": [...]} si contenu sensible détecté
      - {"subtitles": ..., "hashtags": [...]} si tout est conforme
      - None en cas de problème (lecture, transcription, etc.)
    """
    filepath_lower = file_path.lower()

    # Cas image
    if filepath_lower.endswith(('png', 'jpg', 'jpeg')):
        with open(file_path, 'rb') as img_file:
            content = img_file.read()
        if not content:
            return None

        # Vérifier la modération
        mod_result = rekognition.detect_moderation_labels(Image={'Bytes': content})
        if mod_result['ModerationLabels']:
            return {
                "moderation_labels": [item["Name"] for item in mod_result['ModerationLabels']]
            }

        # Extraire labels / visages / célébrités
        detection_labels = rekognition.detect_labels(Image={'Bytes': content}, MaxLabels=10)
        detection_faces = rekognition.detect_faces(Image={'Bytes': content}, Attributes=['ALL'])
        detection_celeb = rekognition.recognize_celebrities(Image={'Bytes': content})

        tags_set = set("#" + label['Name'] for label in detection_labels['Labels'])
        for face in detection_faces.get('FaceDetails', []):
            if face.get('Emotions'):
                tags_set.add("#" + face['Emotions'][0]['Type'])
        tags_set.update("#" + celeb['Name'] for celeb in detection_celeb.get('CelebrityFaces', []))

        return {
            "subtitles": None,
            "hashtags": list(tags_set)
        }

    # Cas vidéo
    elif filepath_lower.endswith(('mp4', 'avi', 'mov', 'mkv')):
        frame = grab_video_frame(file_path, 0)
        if frame is None:
            return None

        ok, encoded_jpg = cv2.imencode('.jpg', frame)
        if not ok:
            return None
        jpg_bytes = encoded_jpg.tobytes()

        # Vérifier la modération
        mod_result = rekognition.detect_moderation_labels(Image={'Bytes': jpg_bytes})
        if mod_result['ModerationLabels']:
            return {
                "moderation_labels": [item["Name"] for item in mod_result['ModerationLabels']]
            }

        # Détection de labels / visages / célébrités
        detection_labels = rekognition.detect_labels(Image={'Bytes': jpg_bytes}, MaxLabels=10)
        detection_faces = rekognition.detect_faces(Image={'Bytes': jpg_bytes}, Attributes=['ALL'])
        detection_celeb = rekognition.recognize_celebrities(Image={'Bytes': jpg_bytes})

        tags_set = set("#" + label['Name'] for label in detection_labels['Labels'])
        for face in detection_faces.get('FaceDetails', []):
            if face.get('Emotions'):
                tags_set.add("#" + face['Emotions'][0]['Type'])
        tags_set.update("#" + celeb['Name'] for celeb in detection_celeb.get('CelebrityFaces', []))

        # Transcription audio via Transcribe
        job_id = f"transcription-job-{int(time.time())}"
        transcript = transcribe_via_aws(
            local_path=file_path,
            transcribe_client=transcribe,
            s3_client=s3,
            job_tag=job_id,
            s3_bucket=bucket_name
        )
        if not transcript:
            return None

        # Extraction de mots-clés via Comprehend => hashtags
        kw_response = comprehend.detect_key_phrases(Text=transcript, LanguageCode='fr')
        keywords = ["#" + k['Text'] for k in kw_response.get('KeyPhrases', [])]

        return {
            "subtitles": transcript,
            "hashtags": keywords
        }

    # Fichier non pris en charge
    return None
