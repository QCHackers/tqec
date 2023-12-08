<template>
    <div class="canvas-container">
      <div class="drawer">
        <div v-for="(rect, index) in drawerRectangles" :key="index"
          :draggable="true"
          @dragstart="handleDragStart(rect, $event)"
          class="drawer-rectangle"
          :style="{ backgroundColor: rect.color }"
        >
          {{ rect.text }}
        </div>
      </div>
      <canvas ref="canvas" :width="canvasWidth" :height="canvasHeight"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @dragover.prevent
        @drop="handleDrop"
      ></canvas>
    </div>
    <button @click="rectangles = []; drawLines()">Clear</button> 
  </template>
  
  <script>
  export default {
    data() {
      return {
        canvasWidth: 800,
        canvasHeight: 400,
        linesCount: 5,
        lineSpacing: 40,
        lineStartY: 50,
        segmentSpacing: 25,
        isMouseDown: false,
        dragItem: null,
        rectangles: [],
        drawerRectangles: [
          { color: '#3498db', text: 'M' },
          { color: '#2ecc71', text: 'G' },
          { color: '#e74c3c', text: 'C' },
          { color: '#f39c12', text: 'T' }
        ]
      };
    },
    methods: {
      drawLines() {
        const canvas = this.$refs.canvas;
        const ctx = canvas.getContext('2d');
  
        ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
  
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
  
        for (let i = 0; i < this.linesCount; i++) {
          const y = this.lineStartY + i * this.lineSpacing;
          ctx.beginPath();
          ctx.moveTo(15, y);
          ctx.lineTo(this.canvasWidth, y);
          ctx.stroke();
  
          ctx.fillText(`${i}`, 5, y + 3);
        }
      },
      drawRectangles() {
        const canvas = this.$refs.canvas;
        const ctx = canvas.getContext('2d');
  
        for (const rect of this.rectangles) {
          ctx.fillStyle = rect.color;
          ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
          ctx.fillStyle = '#000';
          ctx.font = 'bold 12px Arial';
          ctx.fillText(rect.text, rect.x + 10, rect.y + 20);
        }
      },
      handleMouseDown() {
      },
      handleMouseMove() {
      },
      handleMouseUp() {
      },
      handleDragStart(rect, event) {
        event.dataTransfer.setData('text/plain', JSON.stringify(rect));
      },
      handleDrop(event) {
        const rect = JSON.parse(event.dataTransfer.getData('text/plain'));
  
        const canvas = this.$refs.canvas;
        const rectCanvas = canvas.getBoundingClientRect();
        const x = event.clientX - rectCanvas.left;
        const y = event.clientY - rectCanvas.top;
        
        const lineStop = this.lineStartY + this.lineSpacing * this.linesCount;
        const step = this.canvasWidth / this.segmentSpacing;
        const gridX = Math.floor(x / step) * step;
        const gridY = this.lineStartY + Math.floor((y - this.lineStartY) / this.lineSpacing) * this.lineSpacing;
  
        if (gridX >= 0 && gridX <= this.canvasWidth && gridY >= this.lineStartY && gridY <= lineStop) {
            this.rectangles.push({ x: gridX, y: gridY - 15, width: 30, height: 30, color: rect.color, text: rect.text });
            this.drawLines();
            this.drawRectangles();
      }
      }
    },
    mounted() {
      this.drawLines();
      this.drawRectangles();
    },
    name: 'PlaquetteCircuit'
  };
  </script>
  
  <style>
    .canvas-container {
        text-align: center;
    }
  
  .drawer {
      display: inline-block;
      width: 100px;
      height: 100%;
      border-right: 1px solid #ccc;
      overflow-y: auto;
      margin-right: 1px;
    }
  
    .drawer-rectangle {
      width: 50px;
      height: 50px;
      margin: 5px;
      text-align: center;
      line-height: 50px;
      cursor: pointer;
      user-select: none;
    }
  
    canvas {
      display: inline-block;
      border: 1px solid #ccc;
      cursor: pointer;
    }
  </style>
