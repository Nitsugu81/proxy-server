import socket
import threading
import time

class Proxy:
    def __init__(self):
        self.blocked_urls = []
        self.cache = {}
        self.cache_expiry = {}  # Store timestamp for cache expiry
        self.cache_lock = threading.Lock()
        self.lock = threading.Lock()
    
    def handle_client(self, client_socket):
        # Receive data from the client
        request = client_socket.recv(1024)
        start_time = time.time()  # Start timer
        if request.startswith(b'CONNECT'):    
            self.handle_https(client_socket, request)
        else:
            # If not a CONNECT request, handle as HTTP request
            self.handle_http(client_socket, request)
        end_time = time.time()  # End timer
        duration = end_time - start_time
        print("[*] Request duration: {:.6f} seconds".format(duration))

    
    def handle_http(self, client_socket, request):
        # Extract domain from the HTTP request
        lines = request.split(b'\r\n')
        host_header = next((line for line in lines if line.startswith(b'Host:')), None)
        if host_header:
            domain = host_header.split(b' ')[1].decode()
        else:
            return
        if domain in self.blocked_urls:
            print("[*] URL Blocked: {}".format(domain))
            client_socket.close()
            return
        # Check if the response is in cache and not expired
        with self.cache_lock:
            if domain in self.cache and time.time() < self.cache_expiry[domain]:
                print("[*] Serving from cache: {}".format(domain))
                response = self.cache[domain]
            else:
                # Connect to the remote server specified in the HTTP request
                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_socket.connect((domain, 80))

                # Send the HTTP request to the remote server
                remote_socket.send(request)

                # Receive the response from the remote server
                start_time = time.time()  # Start timer for response time
                response = remote_socket.recv(4096)
                end_time = time.time()  # End timer for response time
                duration = end_time - start_time
                print("[*] Response received in {:.6f} seconds".format(duration))

                # Cache the response
                self.cache[domain] = response
                # Set expiry time to 60 seconds
                self.cache_expiry[domain] = time.time() + 60

                # Close the remote socket
                remote_socket.close()

                # Calculate bandwidth used
                bandwidth = len(response) / duration  # Bytes per second
                print("[*] Bandwidth used: {:.2f} bytes/second".format(bandwidth))
        # Send the response back to the client
        client_socket.send(response)
        # Close client socket
        client_socket.close()

    def handle_https(self, client_socket, request):
        # Extracting the host and port from the CONNECT request
        host_port = request.split(b' ')[1].decode().split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 443

        if host in self.blocked_urls:
            print("[*] URL Blocked: {}".format(host))
            client_socket.close()
            return

        try:
            # Connect to the requested host and port
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            # Send 200 code response
            reply = "HTTP/1.0 200 Connection established\r\n"
            reply += "Proxy-agent: Pyx\r\n"
            reply += "\r\n"
            client_socket.sendall(reply.encode())
        except socket.error as err:
            # Proper error handling needed here
            print(err)
            return

        # Forward bytes between client and server
        client_socket.setblocking(0)
        client.setblocking(0)
        while True:
            # Receive data from client
            try:
                client_data = client_socket.recv(1024)
                if client_data:
                    client.sendall(client_data)
            except socket.error:
                pass

            # Receive data from server
            try:
                server_data = client.recv(1024)
                if server_data:
                    client_socket.sendall(server_data)
            except socket.error:
                pass



    def proxy_server(self, bind_ip, bind_port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((bind_ip, bind_port))
        server.listen(5)
        print("[*] Listening on {}:{}".format(bind_ip, bind_port))
        print("[*] List of commands :")
        print("  -b 'URLadresse' => block URL")
        print("  -u 'URLadresse' => unblock URL")

        while True:
            client, addr = server.accept()
            print("[*] Accepted connection from: {}:{}".format(addr[0], addr[1]))

            # Create a thread to handle the client
            client_handler = threading.Thread(target=self.handle_client, args=(client,))
            client_handler.start()

    def user_input_thread(self):
        while True:
            user_input = input()
            user_input_split = user_input.split(" ")
            if user_input_split and '-b' == user_input_split[0]:
                with self.lock:
                    if len(user_input_split) > 1:
                        self.blocked_urls.append(user_input_split[1])
                        print("* Adresse ajoutée à la liste des URL bloquées.")
                    else:
                        print("* Veuillez spécifier une URL à bloquer.")
            elif user_input_split and '-u' == user_input_split[0]:
                with self.lock:
                    if len(user_input_split) > 1:
                        if user_input_split[1] in self.blocked_urls:
                            self.blocked_urls.remove(user_input_split[1])
                            print("* Adresse retirée de la liste des URL bloquées.")
                        else:
                            print("* L'adresse spécifiée n'est pas dans la liste des URL bloquées.")
                    else:
                        print("* Veuillez spécifier une URL à débloquer.")
            else:
                print("* Commande inconnue")

    def run(self):
        bind_ip = '0.0.0.0'  # Listen on all network interfaces
        bind_port = 3333 # Listening port
        self.proxy_server(bind_ip, bind_port)

if __name__ == "__main__":
    proxy = Proxy()
    threading.Thread(target=proxy.user_input_thread).start()  # Start the user input thread
    proxy.run()
