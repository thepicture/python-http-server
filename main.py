from httpserver import HttpServer

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
