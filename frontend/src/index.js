import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import App from './App';

const initialState = {
  todos: [],
};

const reducer = (action, state = initialState) => {
  switch (action) {
  case 'ADD_TODO':
    return {
      ...state,
      todos: [...state.todos, action.payload],
    };
  case 'REMOVE_TODO':
    return {
      ...state,
      todos: state.todos.filter((todo) => todo.id !== action.payload),
    };
  default:
    return state;
  }
};

const store = configureStore({ reducer });

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);

export default store;
