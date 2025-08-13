""" from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import time

import requests

def send_message():
    url = "http://localhost:5005/webhooks/rest/webhook" 
    payload = {
        "sender": "USER1",  
        "message": "Viva"
    }
    
    try:
        response = requests.post(url, json=payload)
        print("Mensagem enviada! Resposta:", response.json())
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

if __name__ == "__main__":
    while True:
        send_message()
        time.sleep(60)
 """

import asyncio
import websockets

connected_clients = set()

# Array de mensagens
messages = ["Mensagem 1", "Mensagem 2", "Mensagem 3"]

async def notify_clients():
    while True:
        if connected_clients and messages:
            # Envia apenas a primeira mensagem do array
            message = messages[0]
            await asyncio.gather(*(client.send(message) for client in connected_clients))
            print(message)
        await asyncio.sleep(5)  # Envia mensagem a cada 5 segundos

async def server(websocket, path):
    connected_clients.add(websocket)
    try:
        print("Novo cliente conectado.")
        await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosed:
        print("Cliente desconectado")
    finally:
        connected_clients.remove(websocket)

async def main():
    start_server = websockets.serve(server, "localhost", 8765)
    await asyncio.gather(start_server, notify_clients())  # Inicia servidor e notificador juntos

asyncio.run(main())