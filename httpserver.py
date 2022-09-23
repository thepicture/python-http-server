import socket


class dotdict(dict):
    __getattr__ = dict.get


class HttpServer:
    def __init__(self, host) -> None:
        self.host = host
        self.handlers = []

    def normalize(self, path):
        return path if path.endswith('/') else path + '/'

    def on(self, method, path, handler):
        self.handlers.append((method, self.normalize(path), handler))

    def get(self, path, handler):
        self.on('GET', path, handler)

    def post(self, path, handler):
        self.on('POST', path, handler)

    def end(self, code, connection, headers, **kwargs):
        response = f"HTTP/1.1 {code} " \
            f"{kwargs.get('message_code', '')}\r\n"
        for header, value in headers.items():
            response += f"{header}: {value}\r\n"
        response += f"\r\n{kwargs.get('body', '')}"
        connection.sendall(response.encode())
        connection.close()

    def listen(self, port):
        if len(self.handlers) == 0:
            raise RuntimeError('no any handlers provided')
        self.port = port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self._listen(port, sock)

    def _listen(self, port, sock):
        sock.bind((self.host, port))
        sock.listen()
        print(f'Listening on port {port}...')

        while True:
            self._handle_request(sock)

    def _handle_request(self, sock):
        connection, _ = sock.accept()
        headers = {'Host': f'{self.host}:{self.port}'}
        try:
            headers = self._invoke_handler(connection)
        except BaseException as exception:
            self._on_exception(connection, headers, exception)

    def _on_exception(self, connection, headers, exception):
        print(exception)
        self.end(404, connection, headers)

    def _invoke_handler(self, connection):
        request = connection.recv(1024).decode()
        splittedHeader = request.split(' ')
        method = splittedHeader[0]
        path = self.normalize(splittedHeader[1])
        print(f'{method} {path}')
        body = self._get_body(request)
        raw_headers = self._parse_raw_headers(request)
        headers = {}
        for raw_header in raw_headers:
            self._parse_headers(headers, raw_header)
        handler = self._find_handler(method, path)
        req = dotdict({'method': method, 'path': path,
                       'headers': headers, 'body': body})

        end = lambda code, **kwargs: self.end(code,
                                              connection, headers, **kwargs)
        res = dotdict({'end': end, 'headers': headers})

        handler[2](req, res)

        return headers

    def _get_body(self, request):
        return request.split('\r\n\r\n')[1]

    def _parse_raw_headers(self, request):
        return request.split('\r\n', 1)[1].split(
            '\r\n\r\n')[0].split('\r\n')

    def _find_handler(self, method, path):
        return next(filter(
            lambda x: x[0] == method and x[1] == path, self.handlers))

    def _parse_headers(self, headers, raw_header):
        key_value_pair = raw_header.split(': ', 1)
        headers[key_value_pair[0]] = key_value_pair[1]
