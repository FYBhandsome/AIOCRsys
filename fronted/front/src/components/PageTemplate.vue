<template>
  <div class="page-container">
    <div class="header">
      <h1>{{ pageTitle }}</h1>
    </div>
    
    <div class="content-section">
      <p>{{ pageDescription }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  pageTitle: {
    type: String,
    required: true
  },
  pageDescription: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.header {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  text-align: center;
}

.header h1 {
  font-size: 28px;
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
}

.content-section {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>