<template>
  <!-- <img alt="Vue logo" src="./assets/logo.png">
  <HelloWorld msg="Welcome to Your Vue.js App"/> -->
  <QubitLattice/>
  <div></div>
  <PlaquetteCircuit/>
</template>

<script>
// import HelloWorld from './components/HelloWorld.vue'
import QubitLattice from './components/Lattice.vue'
import PlaquetteCircuit from './components/Circuit.vue';

export default {
  name: 'App',
  components: {
    QubitLattice,
    PlaquetteCircuit
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
