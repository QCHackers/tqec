// eslint.config.js
import stylisticJs from '@stylistic/eslint-plugin-js';

module.exports = {
	env: {
		browser: true,
		es2021: true,
	},
	extends: 'airbnb',
	overrides: [
		{
			env: {
				node: true,
			},
			files: ['.eslintrc.{js,cjs}'],
			parserOptions: {
				sourceType: 'script',
			},
		},
	],
	parserOptions: {
		ecmaVersion: 'latest',
		sourceType: 'module',
	},
	rules: {},
};
