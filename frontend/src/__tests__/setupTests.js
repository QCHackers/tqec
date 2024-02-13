// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';

// dummy test to make jest not complain about no tests
test('renders learn react link', () => {
	render("<html><head></head><body><h1>TQEC Visualizer<h1/></body><html/>")
	const linkElement = screen.getByText(/TQEC Visualizer/i);
	expect(linkElement).toBeInTheDocument();
});
