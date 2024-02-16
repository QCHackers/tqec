import logo from './tqec_logo.svg';
import './App.css';
import {Stage} from '@pixi/react'
import TqecApp from './workspace'

/* The logo has been created as the SVG rendering of the ASCII:
 *
 *    /---/  //---/    //---/   //---/
 *     //   //   /    //-/     //
 *    //   //---/==  //---/   //---/
 *
 *  with the web app: https://ivanceras.github.io/svgbob-editor/
 */

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
        <Stage width={1400} height={900} options={{backgroundColor: 0x2980b9, antialias: true}}>
          <TqecApp />
        </Stage>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          <p style={{ marginTop: '200px', marginRight: '20px', fontsize: '18px' }}>Circuit-editing area:</p>
          <textarea
            type="text"
            id="editableText"
            placeholder="Edit the circuit here..."
            style={{ fontSize: '18px', width: '700px', height: '250px' }}
          />
        </div>

      </header>
    </div>
  );
}

export default App;
