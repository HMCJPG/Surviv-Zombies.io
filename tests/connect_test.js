const { start } = require('../server');
const net = require('net');
const crypto = require('crypto');

const server = start(8765);

const socket = net.createConnection(8765, 'localhost', () => {
  const key = crypto.randomBytes(16).toString('base64');
  const req =
    'GET / HTTP/1.1\r\n' +
    'Host: localhost\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    `Sec-WebSocket-Key: ${key}\r\n` +
    'Sec-WebSocket-Version: 13\r\n' +
    '\r\n';
  socket.write(req);
});

socket.once('data', data => {
  console.log(data.toString().split('\r\n')[0]);
  socket.destroy();
  server.close();
});
