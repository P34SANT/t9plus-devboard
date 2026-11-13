import socket
import select
import threading

def handle_client(client_sock):
    try:
        req = client_sock.recv(4096)
        if not req:
            client_sock.close()
            return
        first_line = req.split(b"\r\n")[0].decode("latin1", "ignore")
        parts = first_line.split()
        if len(parts) < 2:
            client_sock.close()
            return
        method, url = parts[0], parts[1]
        if method == "CONNECT":
            host, port = url.split(":")
            remote = socket.create_connection((host, int(port)), timeout=10)
            client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            if url.startswith("http://"):
                url_no_scheme = url[7:]
                host_port = url_no_scheme.split("/")[0]
                if ":" in host_port:
                    host, port = host_port.split(":")
                    port = int(port)
                else:
                    host, port = host_port, 80
            else:
                client_sock.close()
                return
            remote = socket.create_connection((host, port), timeout=10)
            remote.sendall(req)
        
        sockets = [client_sock, remote]
        while True:
            r, _, x = select.select(sockets, [], sockets, 30)
            if x or not r:
                break
            done = False
            for s in r:
                other = remote if s is client_sock else client_sock
                try:
                    data = s.recv(16384)
                    if not data:
                        done = True
                        break
                    other.sendall(data)
                except Exception:
                    done = True
                    break
            if done:
                break
    except Exception:
        pass
    finally:
        try:
            client_sock.close()
        except Exception:
            pass
        try:
            remote.close()
        except Exception:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 8080))
    server.listen(50)
    print("HTTP Proxy listening on 0.0.0.0:8080...")
    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client,), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
