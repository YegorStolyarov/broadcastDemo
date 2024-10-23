import socket
import threading
import uuid
import json
import datetime
import asyncio

client_id = str(uuid.uuid4())
stop_event = threading.Event()
pause_event = threading.Event()


async def handle_received_messages(sock, loop):
    while not stop_event.is_set():
        try:
            data = await loop.sock_recv(sock, 1024)
            if not data:
                break
            message = data.decode()

            try:
                data = json.loads(message)
                sender_id = data['id']
                timestamp = data['timestamp_ms']
                increment = data['increment']

                if sender_id != client_id:
                    current_time = int(
                        datetime.datetime.now().timestamp() * 1000)
                    time_diff = current_time - timestamp

                    if time_diff:
                        print(
                            f"Received message from {sender_id} - Time difference: {time_diff} ms, "
                            f"Message index: {increment}")
            except json.JSONDecodeError:
                print("Failed to decode message")
        except ConnectionResetError:
            print("Connection closed by the server")
            break

def receive_messages(sock):
    # inject some async code to make reading potentially huge amount of messages from socket non-blocking
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_received_messages(sock, loop))


def send_messages(sock):
    increment = 0
    try:
        while not stop_event.is_set():
            timestamp_ms = int(datetime.datetime.now().timestamp() * 1000)
            message = json.dumps({
                "id": client_id,
                "timestamp_ms": timestamp_ms,
                "increment": increment
            })

            sock.sendall(message.encode())

            increment += 1

            pause_event.wait(1)
    except BrokenPipeError:
        print("Connection lost")


def main():
    server_ip = '127.0.0.1'
    server_port = 8888

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    receive_thread = threading.Thread(target=receive_messages,
                                      args=(sock,))
    send_thread = threading.Thread(target=send_messages, args=(sock,))

    receive_thread.start()
    send_thread.start()

    try:
        receive_thread.join()
        send_thread.join()
    except KeyboardInterrupt:
        print("\nClient is shutting down...")
        stop_event.set()
        receive_thread.join()
        send_thread.join()
    finally:
        sock.close()
        print("Connection closed")


if __name__ == '__main__':
    main()
