from fastapi import FastAPI
from pydantic import BaseModel
import pika  # import RabbitMQ library
import json
from fastapi import FastAPI
from typing import List
import json
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
import time
import datetime


# Request body Schema
class PatientInfo(BaseModel):
    id_paciente: str
    data_nascimento: str
    sexo: str
    texto_prontuario: str
    Id_atendimento: str
    data_atendimento: str


# Load the pre-trained model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("pucpr/clinicalnerpt-disorder")
model = AutoModelForTokenClassification.from_pretrained("pucpr/clinicalnerpt-disorder")

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
channel = connection.channel()

# Declare a queue to hold the patient information
channel.queue_declare(queue='patient_queue', durable=True)


app = FastAPI()

@app.post("/patients")
async def save_patient(patient_info: PatientInfo):
    """Proccess patient information with clinicalnerpt-disorder and save into RabbitMQ"""

    # Tokenize the patient's medical record text
    inputs = tokenizer(patient_info.texto_prontuario, max_length=512, truncation=True, return_tensors="pt")
    tokens = inputs.tokens()

    # Get the model's predictions
    outputs = model(**inputs).logits
    predictions = torch.argmax(outputs, dim=2)

    # Convert the predictions to labels
    labels = [model.config.id2label[prediction] for prediction in predictions[0].numpy()]

    # Add a label called "cancer_detected" to messages that contain the words "cancer" or "CA" in "texto_prontuario"
    if "cancer" in patient_info.texto_prontuario.lower() or "ca" in patient_info.texto_prontuario.lower():
        labels.append("cancer_detected")
        labels.append(datetime.date.today().strftime("%d/%m/%Y"))

    # Package the patient information and predictions into a dictionary
    data = {
        'id_paciente': patient_info.id_paciente,
        'data_nascimento': patient_info.data_nascimento,
        'sexo': patient_info.sexo,
        'texto_prontuario': patient_info.texto_prontuario,
        'Id_atendimento': patient_info.Id_atendimento,
        'data_atendimento': patient_info.data_atendimento,
        'predictions': labels
    }

    # Convert the dictionary to a JSON string and send it to the patient queue in RabbitMQ
    channel.basic_publish(exchange='',
                          routing_key='patient_queue',
                          body=json.dumps(data),
                          properties=pika.BasicProperties(
                              delivery_mode=2  # make message persistent
                          ))

    return {"message": "Patient information saved to RabbitMQ."}



@app.get("/patients/{patient_id}")
async def get_patient_medical_records(patient_id: str):
    """Gel all the medical records for a given patient (using the patient ID)"""

    medical_records = []

    # Consume messages from the patient queue until there are none left or timeout
    start_time = time.time()
    while True:
        method_frame, properties, body = channel.basic_get(queue='patient_queue', auto_ack=True)
        if body is None:
            break
        else:
            data = json.loads(body)
            # If you want to see the messages being consumed, just uncomment the line below
            # print(data)

            # If the patient ID matches the requested ID, add the medical record to the list
            if data['id_paciente'] == patient_id:
                medical_records.append(data['texto_prontuario'])              

        # For non-production environments: Avoiding straining my computer
        if time.time() - start_time > 30:
            break

    return {"patient_id": patient_id, "medical_records": medical_records}

