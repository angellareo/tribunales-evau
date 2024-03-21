<script setup>
defineProps({
  msg: {
    type: String,
    required: true
  }
})
</script>

<template>
<div class="container">
  <div id="app">
    <h1>Bienvenidos al reparto...</h1>
    <p>Se puede incluir una breve descripción de instruccciones y teléfonos de contacto</p>
    <h5>Como se utiliza por personal interno, las opciones que habitualmente aparecen en una APP no se están desarrollando en este momento&nbsp;&nbsp;</h5>
    <br />
  </div>
</div>
</template>

<style scoped>
h1 {
  text-transform: uppercase !important;
  position: relative;
  padding: 0 0 12px 0;
  margin-bottom: 20px;
}

h1::after {
  /* display: inline-block; */
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 80px;
  background-color: #008000;
  /* size: 2px; */
  /* color: #008000; */
  padding: 0 0 4px 0;
}

a {
  color: #008000;
}

h3 {
  font-size: 1.2rem;
}

.greetings h1,
.greetings h3 {
  text-align: center;
}

@media (min-width: 1024px) {
  .greetings h1,
  .greetings h3 {
    text-align: center;
  }
}


</style>
