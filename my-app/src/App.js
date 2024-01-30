import logo from './logo.svg';
import './App.css';
import {Stage} from '@pixi/react'
import TqecApp from './workspace'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://github.com/QCHackers/tqec"
          target="_blank"
          rel="noopener noreferrer"
        >
          TQEC repo
        </a>
        <Stage width={1000} height={800} options={{backgroundColor: 0x012b30, antialias: true}}>
          <TqecApp />
        </Stage>
      </header>
    </div>
  );
}

export default App;
