// static/js/create_shapes.js

export const environmentObjects = [];

/**
 * Create a single shape element and append it to the document.
 * @param {'triangle'|'square'|'circle'} shape
 * @param {string} color
 * @param {number} x
 * @param {number} y
 * @returns {{ el: HTMLElement, label: HTMLElement }}
 */
export function createShape(shape, color, x, y) {
  const el = document.createElement('div');
  el.classList.add('shape', shape);

  if (shape === 'triangle') {
    const colorMap = { green: 'green', red: 'red', blue: 'blue', yellow: 'yellow' };
    el.style.borderBottomColor = colorMap[color] || 'purple';
  } else {
    const colorMap = {
      green: '#28a745',
      red: '#dc3545',
      blue: '#007bff',
      yellow: '#ffc107'
    };
    el.style.backgroundColor = colorMap[color] || 'steelblue';
  }

  el.style.left = `${x}px`;
  el.style.top  = `${y}px`;

  // Position label
  const label = document.createElement('div');
  label.classList.add('pos-label');
  label.textContent = `(${Math.round(x)}, ${Math.round(y)})`;
  el.appendChild(label);

  document.body.appendChild(el);
  return { el, label };
}

/** @returns {{ x: number, y: number }} a random position within the window margins */
export function randomPos() {
  const margin = 80;
  return {
    x: Math.random() * (window.innerWidth  - margin * 2) + margin,
    y: Math.random() * (window.innerHeight - margin * 2) + margin
  };
}

/** Clear and rebuild the environmentObjects array with preset shapes */
export function createEnvironment() {
  environmentObjects.length = 0;

  let pos, shapeData;
  pos = randomPos();
  shapeData = createShape('triangle', 'green', pos.x, pos.y);
  environmentObjects.push({ shape: 'triangle', color: 'green', ...shapeData, x: pos.x, y: pos.y });

  pos = randomPos();
  shapeData = createShape('square', 'red', pos.x, pos.y);
  environmentObjects.push({ shape: 'square', color: 'red', ...shapeData, x: pos.x, y: pos.y });

  pos = randomPos();
  shapeData = createShape('circle', 'blue', pos.x, pos.y);
  environmentObjects.push({ shape: 'circle', color: 'blue', ...shapeData, x: pos.x, y: pos.y });

  pos = randomPos();
  shapeData = createShape('square', 'yellow', pos.x, pos.y);
  environmentObjects.push({ shape: 'square', color: 'yellow', ...shapeData, x: pos.x, y: pos.y });
}
