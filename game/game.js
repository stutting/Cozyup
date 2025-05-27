(() => {
  const startScreen = document.getElementById('start-screen');
  const gameScreen = document.getElementById('game-screen');
  const messageScreen = document.getElementById('message-screen');
  const startBtn = document.getElementById('start-btn');
  const nextBtn = document.getElementById('next-btn');
  const messageEl = document.getElementById('message');

  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  const keys = { left: false, right: false, up: false };
  document.addEventListener('keydown', e => {
    if (e.code === 'ArrowLeft') keys.left = true;
    if (e.code === 'ArrowRight') keys.right = true;
    if (e.code === 'Space') keys.up = true;
  });
  document.addEventListener('keyup', e => {
    if (e.code === 'ArrowLeft') keys.left = false;
    if (e.code === 'ArrowRight') keys.right = false;
    if (e.code === 'Space') keys.up = false;
  });

  class Rect {
    constructor(x, y, w, h) {
      this.x = x;
      this.y = y;
      this.w = w;
      this.h = h;
    }
    draw(color) {
      ctx.fillStyle = color;
      ctx.fillRect(this.x, this.y, this.w, this.h);
    }
    intersects(r) {
      return !(this.x + this.w < r.x || this.x > r.x + r.w ||
               this.y + this.h < r.y || this.y > r.y + r.h);
    }
  }

  class Player extends Rect {
    constructor(x, y) {
      super(x, y, 30, 40);
      this.vx = 0;
      this.vy = 0;
      this.onGround = false;
    }
    update(platforms) {
      const SPEED = 2;
      const JUMP = 6;
      const GRAVITY = 0.3;

      if (keys.left) this.vx = -SPEED;
      else if (keys.right) this.vx = SPEED;
      else this.vx = 0;

      if (keys.up && this.onGround) {
        this.vy = -JUMP;
        this.onGround = false;
      }

      this.vy += GRAVITY;
      this.x += this.vx;
      this.y += this.vy;

      // collisions
      this.onGround = false;
      for (let p of platforms) {
        if (this.intersects(p)) {
          if (this.vy > 0 && this.y + this.h - this.vy <= p.y) {
            this.y = p.y - this.h;
            this.vy = 0;
            this.onGround = true;
          } else if (this.vy < 0 && this.y >= p.y + p.h - 1) {
            this.y = p.y + p.h;
            this.vy = 0;
          } else if (this.vx > 0 && this.x + this.w - this.vx <= p.x) {
            this.x = p.x - this.w;
          } else if (this.vx < 0 && this.x >= p.x + p.w - 1) {
            this.x = p.x + p.w;
          }
        }
      }
    }
    draw() { super.draw('#00ff00'); }
  }

  class Coin extends Rect {
    constructor(x, y) { super(x, y, 20, 20); this.collected = false; }
    draw() { if (!this.collected) super.draw('#ffd700'); }
  }

  const levels = [
    {
      platforms: [ new Rect(0, 360, 800, 40), new Rect(200, 280, 200, 20) ],
      coins: [ new Coin(100, 320), new Coin(250, 240), new Coin(500, 320) ]
    },
    {
      platforms: [
        new Rect(0, 360, 800, 40),
        new Rect(150, 300, 150, 20),
        new Rect(350, 250, 150, 20),
        new Rect(550, 200, 150, 20)
      ],
      coins: [ new Coin(170, 260), new Coin(370, 210), new Coin(570, 160) ]
    }
  ];

  let currentLevel = 0;
  let player;
  let platforms;
  let coins;
  let gameRunning = false;

  function startLevel(index) {
    const lvl = levels[index];
    platforms = lvl.platforms;
    coins = lvl.coins;
    player = new Player(20, 300);
    gameRunning = true;
    window.requestAnimationFrame(loop);
  }

  function loop() {
    if (!gameRunning) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    player.update(platforms);
    player.draw();

    for (let coin of coins) {
      if (!coin.collected && player.intersects(coin)) coin.collected = true;
      coin.draw();
    }

    for (let p of platforms) p.draw('#654321');

    if (coins.every(c => c.collected)) {
      gameRunning = false;
      messageEl.textContent = currentLevel < levels.length - 1 ?
        'Level Complete!' : 'You Win!';
      nextBtn.textContent = currentLevel < levels.length - 1 ? 'Next Level' : 'Restart';
      messageScreen.classList.remove('hidden');
    } else {
      window.requestAnimationFrame(loop);
    }
  }

  startBtn.onclick = () => {
    startScreen.classList.add('hidden');
    gameScreen.classList.remove('hidden');
    startLevel(0);
  };

  nextBtn.onclick = () => {
    messageScreen.classList.add('hidden');
    if (currentLevel < levels.length - 1) {
      currentLevel++;
    } else {
      currentLevel = 0;
    }
    startLevel(currentLevel);
  };
})();
