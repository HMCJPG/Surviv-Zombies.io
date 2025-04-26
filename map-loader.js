const mapLoader = document.getElementById('mapLoader');

mapLoader.addEventListener('change', e => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(evt) {
    try {
      const data = JSON.parse(evt.target.result);
      if (data.rocks) {
        rocks.length = 0;
        data.rocks.forEach(r => rocks.push({ x: r.x, y: r.y, hp: r.hp ?? 8 }));
      }
      if (data.walls) {
        walls.length = 0;
        data.walls.forEach(w => walls.push(w));
      }
      if (data.playerStart) {
        player.x = data.playerStart.x;
        player.y = data.playerStart.y;
      }
      console.log("Map loaded successfully.");
    } catch (err) {
      alert("Invalid map file");
    }
  };
  reader.readAsText(file);
});
