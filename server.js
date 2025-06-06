const http = require('http');
const crypto = require('crypto');

const PORT = 8765;
const clients = new Map();
let nextId = 1;
const world = { players: {}, bullets: [], zombies: [] };

function parseFrame(buffer) {
  const second = buffer[1];
  let length = second & 0x7f;
  let offset = 2;
  if (length === 126) {
    length = buffer.readUInt16BE(offset);
    offset += 2;
  } else if (length === 127) {
    length = Number(buffer.readBigUInt64BE(offset));
    offset += 8;
  }
  const mask = buffer.slice(offset, offset + 4);
  offset += 4;
  const payload = Buffer.alloc(length);
  for (let i = 0; i < length; i++) {
    payload[i] = buffer[offset + i] ^ mask[i % 4];
  }
  return payload.toString();
}

function frameData(data) {
  const payload = Buffer.from(JSON.stringify(data));
  const length = payload.length;
  let header;
  if (length < 126) {
    header = Buffer.from([0x81, length]);
  } else if (length < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x81;
    header[1] = 126;
    header.writeUInt16BE(length, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x81;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(length), 2);
  }
  return Buffer.concat([header, payload]);
}

const server = http.createServer();

server.on('upgrade', (req, socket) => {
  if (req.headers.upgrade !== 'websocket') {
    socket.end('HTTP/1.1 400 Bad Request');
    return;
  }
  const key = req.headers['sec-websocket-key'];
  const accept = crypto
    .createHash('sha1')
    .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
    .digest('base64');
  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    `Sec-WebSocket-Accept: ${accept}\r\n` +
    '\r\n'
  );

  const id = nextId++;
  clients.set(socket, id);
  world.players[id] = { x: 0, y: 0, angle: 0, hp: 100 };

  socket.on('data', (buf) => {
    try {
      const msg = JSON.parse(parseFrame(buf));
      if (msg.type === 'state') {
        world.players[id] = msg.player;
        world.bullets = msg.bullets || world.bullets;
        world.zombies = msg.zombies || world.zombies;
      }
    } catch (err) {
      console.error('Bad frame', err);
    }
  });

  socket.on('close', () => {
    clients.delete(socket);
    delete world.players[id];
  });
socket.on("error", () => {});
});

function broadcast() {
  for (const [socket, id] of clients.entries()) {
    try {
      socket.write(frameData({ type: 'world', id, world }));
    } catch (_) {}
  }
}

setInterval(broadcast, 50);

function start(port = PORT) {
  server.listen(port, () => {
    console.log(`Server listening on ${port}`);
  });
  return server;
}

if (require.main === module) {
  start(PORT);
}

module.exports = { start };
