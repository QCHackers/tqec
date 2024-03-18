import logo from './tqec_logo.svg';
import './App.css';
import {Stage} from '@pixi/react'
import TqecApp from './workspace'
import formattedInfoTabContent from './formattedInfoTab';

/* The logo has been created as the SVG rendering of the ASCII:
 *
 *    /---/  //---/    //---/   //---/
 *     //   //   /    //-/     //
 *    //   //---/==  //---/   //---/
 *
 *  with the web app: https://ivanceras.github.io/svgbob-editor/
 */

const handleTabClick = (tabId) => {
   // Hide all tab contents
  const tabContents = document.querySelectorAll('.Tab-content');
  tabContents.forEach(content => {
      content.style.display = 'none';
  });

  // Show the clicked tab content
  const clickedTabContent = document.getElementById(`content${tabId}`);
  if (clickedTabContent) {
      clickedTabContent.style.display = 'block';
  }

  // Optionally, you can perform additional actions when a tab is clicked
  console.log(`Tab ${tabId} clicked`);
};

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <a
          className="App-link"
          href="https://github.com/QCHackers/tqec"
          target="_blank"
          rel="noopener noreferrer"
        >
          TQEC repo
        </a>
      </header>

      <div className="Tabs">
        <button className="Tab-button" id="tab1" onClick={() => handleTabClick(1)}>Info</button>
        <button className="Tab-button" id="tab2" onClick={() => handleTabClick(2)}>Compose library</button>
        <button className="Tab-button" id="tab3" onClick={() => handleTabClick(3)}>Create code</button>
        {/* -- Add more tabs as needed -- */}
      </div>

      <div id="Tab-content">
        <div id="content1" className="Tab-content active">
          {/*-- Content for Tab 1 -- */}
          {formattedInfoTabContent}
        </div>

        <div id="content2" className="Tab-content">
          {/*-- Content for Tab 2 -- */}

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
            <p className="Comment-paragraph">Enter file name:</p>
            <input className="Cell-size"
              type="number"
              id="dxCell"
              placeholder="2"
            />
            <p className="Comment-paragraph">x</p>
            <input className="Cell-size"
              type="number"
              id="dyCell"
              placeholder="2"
            />
          </div>

          <Stage width={1400} height={900} options={{backgroundColor: 0x2980b9, antialias: true}}>
            <TqecApp />
          </Stage>

          <p className="Comment-paragraph">Circuit-editing area:</p>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <textarea
              className="Text-area"
              type="text"
              id="editableText"
              placeholder="Edit the circuit here..."
            />
        </div>

        </div>

        <div id="content3" className="Tab-content">
          {/*-- Content for Tab 3 -- */}
          Content of tab 3
        </div>
        {/*-- Add more content areas as needed -- */}
      </div>
    </div>
  );
}

export default App;
