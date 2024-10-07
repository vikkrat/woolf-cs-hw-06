import socket
import json
import logging
import os
from datetime import datetime
from message_operations import message_ops, db_connection

# Налаштування логування
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def save_to_local_storage(message):
    storage_path = os.path.join('client', 'storage', 'data.json')
    try:
        # Читаємо існуючі дані
        if os.path.exists(storage_path):
            with open(storage_path, 'r') as file:
                try:
                    data = json.load(file)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
        else:
            data = []
        
        # Додаємо нове повідомлення
        data.append(message)
        
        # Записуємо оновлені дані
        with open(storage_path, 'w') as file:
            json.dump(data, file, indent=2)
        
    except Exception as e:
        logging.error(f"Помилка при збереженні локально: {str(e)}")

def run_socket_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('0.0.0.0', 5000)
    server_socket.bind(server_address)
    try:
        while True:
            data, address = server_socket.recvfrom(1024)

            try:
                message = json.loads(data.decode('utf-8'))
                username = message.get('username', 'Anonymous')
                message_text = message.get('message', '')

                full_message = {
                    "date": datetime.now().isoformat(),
                    "username": username,
                    "message": message_text
                }

                try:
                    message_id = message_ops.save_message(username, message_text)
                    response = json.dumps({"status": "success", "message_id": str(message_id)})
                except Exception as db_error:
                    logging.error(f"Помилка при збереженні в MongoDB: {db_error}")
                    save_to_local_storage(full_message)
                    response = json.dumps({"status": "success", "storage": "local"})

                server_socket.sendto(response.encode('utf-8'), address)

            except json.JSONDecodeError as json_error:
                response = json.dumps({"status": "error", "message": "Invalid JSON data"})
                server_socket.sendto(response.encode('utf-8'), address)

            except Exception as e:
                logging.error(f"Загальна помилка при обробці повідомлення: {e}")
                response = json.dumps({"status": "error", "message": str(e)})
                server_socket.sendto(response.encode('utf-8'), address)

    except KeyboardInterrupt:
        logging.info("Сервер зупинено користувачем")
    finally:
        server_socket.close()
        db_connection.close_connection()
        logging.info("З'єднання закрито")

if __name__ == "__main__":
    try:
        run_socket_server()
    except Exception as e:
        logging.error(f"Критична помилка: {e}")