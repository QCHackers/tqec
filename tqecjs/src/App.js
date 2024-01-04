import './App.css';
import { Stage } from '@pixi/react';
import PixiApp from './workspace';

const tqecBlue = 0x1099bb;

function App() {
	return (
		<div>
			<div className='App'>
				<header className='App-header'>TQEC Visualizer</header>
			</div>
			<Stage
				width={window.innerWidth}
				height={window.innerHeight}
				options={{ backgroundColor: tqecBlue }}>
				<PixiApp />
			</Stage>
		</div>
	);
}

export default App;
