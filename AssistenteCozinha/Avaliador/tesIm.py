# import websockets
# import ssl
# import asyncio

# event_loop = None  # Loop principal será definido no main

# event_loop = asyncio.get_event_loop()
# async def send_scxml_event(event_name):
#     try:
#         uri = "wss://localhost:8005/IM/USER1/APP"
#         ssl_context = ssl._create_unverified_context()

#         event_command = event_name.replace("mmi:", "")  # e.g. "feedbackStart"
#         message = f"""
#         <mmi:mmi xmlns:mmi="http://www.w3.org/2008/04/mmi-arch">
#             <mmi:extensionNotification mmi:context="ctx-1" mmi:requestId="req-1" mmi:source="ASSESSMENT" mmi:target="IM">
#                 <mmi:data>
#                     <event>{event_command}</event>
#                 </mmi:data>
#             </mmi:extensionNotification>
#         </mmi:mmi>
#         """

#         async with websockets.connect(uri, ssl=ssl_context) as websocket:
#             await websocket.send(message)
#             print(f"[SCXML] Enviado mmi:extensionNotification com evento: {event_name}")
#     except Exception as e:
#         print(f"[SCXML] Erro ao enviar evento {event_name}: {e}")

# def trigger_scxml_event(event_name):
#     if event_loop:
#         asyncio.run_coroutine_threadsafe(send_scxml_event(event_name), event_loop)
#     else:
#         print("[SCXML] event_loop não definido.")


# trigger_scxml_event("mmi:feedbackStop")
# event_loop.run_forever()

import asyncio
import websockets
import ssl

async def enviar_mensagem_teste(mensagem):
    try:
        uri = "wss://localhost:8000/IM/USER1/APP"
        ssl_context = ssl._create_unverified_context()
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            mensagem_xml = f"""
            <emma:emma version="1.0" xmlns:emma="http://www.w3.org/2003/04/emma">
                <emma:interpretation id="command1">
                    <emma:function>{mensagem}</emma:function>
                </emma:interpretation>
            </emma:emma>
            """
            await websocket.send(mensagem_xml)
            print(f"Mensagem de teste enviada: {mensagem_xml}")
    except Exception as e:
        print(f"Erro ao enviar mensagem de teste: {e}")

asyncio.run(enviar_mensagem_teste("Teste 1"))