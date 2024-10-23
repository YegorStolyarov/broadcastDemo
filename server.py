import asyncio

clients = set()

async def main():


    async def handle_messages(client_reader, client_writer):
        client_addr = client_writer.get_extra_info('peername')
        print(f"Accepted connection from {client_addr}")
        clients.add(client_writer)
        print(f"Connected clients: {len(clients)}")

        try:
            while True:
                data = await client_reader.read(1024)
                if not data:
                    break

                message = data.decode()
                print(f"Received message from {client_addr}: {message}")

                # Broadcast the message to all connected clients
                for client in clients:
                    client.write(data)
                    await client.drain()

        finally:
            # Remove the client from the set and close the connection
            clients.remove(client_writer)
            client_writer.close()
            await client_writer.wait_closed()
            print(f"Connection closed {client_addr}")
            print(f"Connected clients: {len(clients)}")

    server = await asyncio.start_server(handle_messages, '0.0.0.0', 8888)
    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            print("Cancelled serving process.")

if __name__ == '__main__':
    asyncio.run(main())
