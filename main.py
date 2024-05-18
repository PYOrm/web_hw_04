import datetime
import json
import mimetypes
import pathlib
import socket
import urllib.parse
from time import sleep
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = urllib.parse.urlparse(self.path)
        match url_path.path:
            case "/":
                self.send_html_file(str(pathlib.Path(".").absolute().joinpath("front_init").joinpath("index.html")))
            case "/massage":
                self.send_html_file(str(pathlib.Path(".").absolute().joinpath("front_init").joinpath("massage.html")))
            case _:
                file = pathlib.Path(".").absolute().joinpath("front_init").joinpath(url_path.path[1::])
                if file.exists():
                    self.send_static_content(str(file))
                else:
                    self.send_html_file(str(pathlib.Path(".").absolute().joinpath("front_init").joinpath("error.html")))

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"])).decode()
        data = urllib.parse.unquote_plus(data)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect(("127.0.0.1", 5000))
                client_socket.send(data.encode())
            except ConnectionRefusedError:
                sleep(0.5)
            finally:
                client_socket.close()
                self.send_response(303)
                self.send_header("Location", "/message.html")
                self.end_headers()

    def send_html_file(self, filename: str, status=200):
        self.send_response(status)
        self.send_header('Content-type', "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static_content(self, filename: str, status=200):
        self.send_response(status)
        mt = mimetypes.guess_type(self.path)
        if mt[0]:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "plain/text")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())


class SocketServer:

    def __init__(self, server: str, port: int):
        self.run_server(server, port)

    def run_server(self, host: str, port: int):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen(1)
            while True:
                conn, address = s.accept()
                with conn as con:
                    if con:
                        self.accept_new_connection(con, address)

    def accept_new_connection(self, conn, address):
        new_thread = Thread(name=f"th_{conn}", daemon=True, target=self.new_thread_connection,
                            args=(conn, "./front_init/storage/data.json"))
        new_thread.start()
        new_thread.join()

    def new_thread_connection(self, conn, file: str):
        while True:
            data = conn.recv(1024).decode()
            if data:
                with open("./front_init/storage/data.json", "r", encoding="utf-8") as f:
                    data_load = dict(json.load(f))
                data_load.update(self.prepare_data_for_store(data))
                with open("./front_init/storage/data.json", "w", encoding="utf-8") as f:
                    json.dump(data_load, f, ensure_ascii=False)
            else:
                break
        conn.close()

    def prepare_data_for_store(self, raw_data: str) -> dict:
        msg = {key: val for key, val in [row.split("=") for row in raw_data.split("&")]}
        dt_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        return {dt_str: msg}


def run(server=HTTPServer, handler=HttpHandler):
    server_address = ("", 3000)
    http = server(server_address, handler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    server_thread = Thread(target=run, daemon=True)
    socket_thread = Thread(target=SocketServer, args=("127.0.0.1", 5000), daemon=True)
    socket_thread.start()
    server_thread.start()
    server_thread.join()
    socket_thread.join()
