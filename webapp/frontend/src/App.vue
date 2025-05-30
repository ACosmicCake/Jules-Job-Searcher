<template>
  <div id="app-container">
    <header>
      <h1>AI Job Agent Dashboard</h1>
    </header>
    <main>
      <ConfigEditor />
      <JobList /> 
      <!-- Other components will be added here later, e.g., for CV management -->
    </main>
    <footer>
      <p>&copy; 2024 AI Job Agent</p>
    </footer>
  </div>
</template>

<script setup>
import ConfigEditor from './components/ConfigEditor.vue';
import JobList from './components/JobList.vue'; // Import the JobList component
// HelloWorld component is no longer used by default, so no need to import unless specifically needed.
// import HelloWorld from './components/HelloWorld.vue' 
</script>

<style>
/* Global styles or App-specific styles */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f4f6f8;
  color: #333;
}

#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

header h1 {
  margin: 0;
  font-size: 1.8em;
}

main {
  flex-grow: 1;
  padding: 20px;
  max-width: 1200px; /* Max width for main content area */
  margin: 0 auto; /* Center content */
  width: 100%;
  box-sizing: border-box;
}

footer {
  text-align: center;
  padding: 1rem;
  background-color: #34495e;
  color: #ecf0f1;
  font-size: 0.9em;
}

/* Basic styling for components - can be moved to a global CSS or scoped */
h2 {
  color: #2c3e50;
}
</style>
