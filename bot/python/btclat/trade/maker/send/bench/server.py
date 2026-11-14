"""A stand-in venue on 127.0.0.1 in its own process: POST /order answers live with an order id
(the body's hash), DELETE /order cancels it, GET /time answers the clock. `ms` adds a fixed
server delay. Plain HTTP/1.1 (httpx falls back from HTTP/2 without TLS): this measures our
process, not the network."""
from __future__ import annotations

import hashlib
import json
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def handler(ms: float):
    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def setup(self):
            super().setup()
            self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)   # no Nagle + delayed-ACK 40 ms

        def _send(self, body) -> None:
            time.sleep(ms / 1e3)
            raw = json.dumps(body).encode()
            head = (f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(raw)}\r\n"
                    "Connection: keep-alive\r\n\r\n").encode()
            self.wfile.write(head + raw)                                              # one segment

        def _body(self) -> bytes:
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))

        def do_GET(self):
            self._send(int(time.time()))

        def do_POST(self):
            oid = "0x" + hashlib.sha256(self._body()).hexdigest()
            self._send({"success": True, "orderID": oid, "status": "live", "makingAmount": "", "takingAmount": ""})

        def do_DELETE(self):
            oid = json.loads(self._body() or b"{}").get("orderID")
            self._send({"canceled": [oid], "not_canceled": {}})
    return H


def serve(port_q, ms: float) -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler(ms))
    srv.daemon_threads = True
    port_q.put(srv.server_address[1])
    srv.serve_forever()
