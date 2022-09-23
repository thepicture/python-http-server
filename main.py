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
            sock.bind((self.host, port))
            sock.listen()
            print(f'Listening on port {port}...')

            while True:
                connection, _ = sock.accept()
                headers = {'Host': f'{self.host}:{self.port}'}
                try:
                    request = connection.recv(1024).decode()
                    splittedHeader = request.split(' ')
                    method = splittedHeader[0]
                    path = self.normalize(splittedHeader[1])
                    print(f'{method} {path}')
                    body = request.split('\r\n\r\n')[1]
                    raw_headers = request.split('\r\n', 1)[1].split(
                        '\r\n\r\n')[0].split('\r\n')
                    headers = {}
                    for raw_header in raw_headers:
                        key_value_pair = raw_header.split(': ', 1)
                        headers[key_value_pair[0]] = key_value_pair[1]
                    handler = next(filter(
                        lambda x: x[0] == method and x[1] == path, self.handlers))
                    handler[2](
                        dotdict({'method': method, 'path': path,
                                'headers': headers, 'body': body}),
                        dotdict(
                            {
                                'end': lambda code, **kwargs: self.end(code, connection, headers, **kwargs),
                                'headers': headers
                            }))
                except BaseException as exception:
                    print(exception)
                    self.end(404, connection, headers)


counter = 0


def on_counter(res):
    global counter
    counter += 1
    res.headers['X-Counter-Header'] = counter
    res.end(200, body=f'This endpoint has been called {counter} times')


def main():
    server = HttpServer('127.0.0.1')
    server.get('/', lambda _, res: res.end(200))
    server.post('/', lambda req, res: res.end(201, body=f'{req.body}'))
    server.post('/counter', lambda _, res: on_counter(res))
    server.get('/animals/lemur', lambda _, res: res.end(200, body=f'Lemurs'))
    server.on('PUT', '/animals/lemur', lambda _, res: res.end(204))
    server.listen(8080)


if __name__ == '__main__':
    main()
