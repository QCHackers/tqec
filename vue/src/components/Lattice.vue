<template>
    <div class="lattice" @mousedown="handleMouseDown" @mousemove="handleMouseMove" @mouseup="handleMouseUp">
        <canvas ref="canvas" :width="canvasWidth" :height="canvasHeight"></canvas>
    </div>
        <button @click="fillPoints">Fill</button>
        <button @click="selectedPoints.clear(); drawGrid()">Clear</button>
</template>
  
<script>
class Qubit {
    constructor(x, y, c) {
        this.x = x;
        this.y = y;
        this.counter = c;
    }
}

export default {
    data() {
        return {
            gridSize: 20,
            canvasWidth: 400,
            canvasHeight: 400,
            isMouseDown: false,
            selectedPoints: new Set(),
            counter: 0
        };
    },
    methods: {
        fillPoints() {
            const canvas = this.$refs.canvas;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#3498db';
            let sortedPoints = Array.from(this.selectedPoints).sort((a, b) => a.counter - b.counter);
            ctx.beginPath();
            sortedPoints.forEach((p, i) => {
                if (i == 0) {
                    ctx.moveTo(p.x, p.y);
                } else {
                    ctx.lineTo(p.x, p.y);
                }
            });
            ctx.closePath();
            ctx.fill();
        },
        drawGrid() {
            const canvas = this.$refs.canvas;
            const ctx = canvas.getContext('2d');

            const step = this.canvasWidth / this.gridSize;

            ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
            ctx.strokeStyle = '#ccc';
            ctx.lineWidth = 1;

            for (let x = 0; x <= this.canvasWidth; x += step) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, this.canvasHeight);
                ctx.stroke();
            }

            for (let y = 0; y <= this.canvasHeight; y += step) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(this.canvasWidth, y);
                ctx.stroke();
            }

            for (let x = 0; x <= this.canvasWidth; x += step) {
                for (let y = 0; y <= this.canvasHeight; y += step) {
                    let c = -1;
                    this.selectedPoints.forEach(p => {
                        if (p.x == x && p.y == y) {
                            c = p.counter;
                        }
                    });
                    ctx.fillStyle = c >= 0 ? '#3498db' : '#fff';
                    ctx.fillRect(x - 5, y - 5, 10, 10);
                    if (c >= 0) {
                        ctx.font = '10px Arial';
                        ctx.fillStyle = "red";
                        ctx.fillText(c,x-2.5,y+3);

                    }
                }
            }
        },
        handleMouseDown(event) {
            this.isMouseDown = true;
            this.selectPoint(event);
        },
        handleMouseMove() {
            return
        },
        handleMouseUp() {
            this.isMouseDown = false;
        },
        selectPoint(event) {
            const canvas = this.$refs.canvas;
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            const step = this.canvasWidth / this.gridSize;
            const gridX = Math.floor(x / step) * step;
            const gridY = Math.floor(y / step) * step;

            // const count = this.counter++
            const point = new Qubit(gridX, gridY, this.counter++);
            let haspoint = false;
            this.selectedPoints.forEach(p => {
                if (p.x == gridX && p.y == gridY) {
                    haspoint = true;
                    point.counter = p.counter;
                }
            })
            if (!haspoint) {
                this.selectedPoints.add(point);
            } else {
                console.log("delete");
                this.selectedPoints.delete(point);
                // TODO reset counter
            }

            this.drawGrid();
        }
    },
    mounted() {
        this.drawGrid();
    },
    name: 'QubitLattice'
};
</script>
  
<style>
.lattice {
    border: 1px solid #ccc;
}

canvas {
    cursor: pointer;
}
</style>
