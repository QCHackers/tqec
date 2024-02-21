import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';

test('renders learn react link', () => {
	render("<html><head></head><body><h1>TQEC Visualizer<h1/></body><html/>")
	const linkElement = screen.getByText(/TQEC Visualizer/i);
	expect(linkElement).toBeInTheDocument();
});
