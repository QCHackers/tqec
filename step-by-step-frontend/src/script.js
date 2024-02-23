import {Stage} from '@pixi/react'
import TqecApp from './workspace'

// script.js
document.addEventListener('DOMContentLoaded', function() {
  // Get references to tabs and tab contents
  const tab1Button = document.getElementById('tab1');
  const tab2Button = document.getElementById('tab2');
  const content1 = document.getElementById('content1');
  const content2 = document.getElementById('content2');

  // Add event listeners for tab clicks
  tab1Button.addEventListener('click', () => {
    // Show content for tab 1 and hide content for tab 2
    console.log('click on tab1 button');
    content1.style.display = 'block';
    content2.style.display = 'none';
    // Clear the content of the container
    content1.innerHTML = '';
    // Render the TqecApp component inside content1
    ReactDOM.render(
    <Stage width={1400} height={900} options={{backgroundColor: 0x2980b9, antialias: true}}>
      <TqecApp />
    </Stage>
    , content1);
  });

  tab2Button.addEventListener('click', () => {
    // Show content for tab 2 and hide content for tab 1
    console.log('click on tab2 button');
    content1.style.display = 'none';
    content2.style.display = 'block';
  });
});
