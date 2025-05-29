<template>
  <div class="config-editor">
    <h2>Configuration Editor</h2>
    
    <div v-if="isLoading" class="loading-message">
      Loading configuration...
    </div>

    <div v-if="errorMessage" class="error-message">
      <p><strong>Error:</strong> {{ errorMessage }}</p>
    </div>

    <div v-if="successMessage" class="success-message">
      <p><strong>Success:</strong> {{ successMessage }}</p>
    </div>

    <div v-if="configData && !isLoading" class="config-form">
      <p>
        Edit the configuration JSON below. Be careful with the structure.
        Refer to <code>config.json.example</code> or documentation for the expected format.
      </p>
      <textarea 
        v-model="editableJsonString" 
        rows="30" 
        cols="100" 
        placeholder="Loading configuration..."
        aria-label="Configuration JSON"
      ></textarea>
      <div class="actions">
        <button @click="saveConfig" :disabled="isLoading || !isJsonValid" class="button-save">
          {{ isLoading ? 'Saving...' : 'Save Configuration' }}
        </button>
        <button @click="fetchConfig" :disabled="isLoading" class="button-reload">
          Reload Configuration
        </button>
        <p v-if="!isJsonValid" class="json-error-hint">
          JSON is not valid. Please correct before saving.
        </p>
      </div>
    </div>
    <div v-else-if="!isLoading && !configData && !errorMessage">
        <p>No configuration data loaded, or an error occurred preventing display.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import api from '../services/api'; // Adjust path if api.js is elsewhere

const configData = ref(null); // Stores the object representation
const editableJsonString = ref(''); // Stores the string representation for textarea
const isLoading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const isJsonValid = ref(true);

// Fetch initial configuration
const fetchConfig = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  isJsonValid.value = true; // Assume valid until proven otherwise by edits
  try {
    const response = await api.getConfig();
    configData.value = response.data;
    // Initialize textarea with fetched data, pretty-printed
    editableJsonString.value = JSON.stringify(response.data, null, 2);
    // console.log('Configuration loaded:', configData.value);
  } catch (error) {
    console.error('Failed to fetch config:', error);
    errorMessage.value = error.response?.data?.detail || error.message || 'Failed to fetch configuration.';
    configData.value = null; // Clear data on error
    editableJsonString.value = ''; // Clear textarea on error
  } finally {
    isLoading.value = false;
  }
};

// Save configuration
const saveConfig = async () => {
  if (!isJsonValid.value) {
    errorMessage.value = 'Cannot save: JSON is not valid.';
    return;
  }
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';
  try {
    // Parse the string from textarea back into an object
    const newConfigData = JSON.parse(editableJsonString.value);
    await api.updateConfig(newConfigData);
    successMessage.value = 'Configuration updated successfully!';
    // Update local configData to reflect saved changes (or re-fetch)
    configData.value = newConfigData; 
    // console.log('Configuration saved.');
  } catch (error) {
    // Handle JSON parsing error from textarea or API error
    console.error('Failed to save config:', error);
    if (error instanceof SyntaxError) { // JSON parsing error from textarea content
        errorMessage.value = 'Failed to save: Invalid JSON format in textarea. ' + error.message;
        isJsonValid.value = false; // Mark as invalid
    } else { // API error
        errorMessage.value = error.response?.data?.detail || error.message || 'Failed to save configuration.';
    }
  } finally {
    isLoading.value = false;
  }
};

// Watch for changes in the textarea to validate JSON in real-time
watch(editableJsonString, (newValue) => {
  try {
    JSON.parse(newValue);
    isJsonValid.value = true;
    // Clear previous JSON error message if it becomes valid
    if (errorMessage.value.startsWith('Failed to save: Invalid JSON format')) {
        errorMessage.value = '';
    }
  } catch (e) {
    isJsonValid.value = false;
    // Optionally, provide immediate feedback about JSON validity here,
    // or wait until save is attempted. The current setup disables save button.
  }
});

// Lifecycle hook
onMounted(() => {
  fetchConfig();
});
</script>

<style scoped>
.config-editor {
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: #f9f9f9;
  max-width: 800px;
  margin: 20px auto;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}

.loading-message, .error-message, .success-message {
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 4px;
  text-align: center;
}

.loading-message {
  background-color: #e0e0e0;
  color: #555;
}

.error-message {
  background-color: #ffdddd;
  color: #d8000c;
  border: 1px solid #d8000c;
}

.success-message {
  background-color: #ddffdd;
  color: #006400;
  border: 1px solid #006400;
}

.config-form p {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 10px;
}

textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
  box-sizing: border-box; /* Ensures padding doesn't expand width */
  margin-bottom: 15px;
  background-color: #fff;
  color: #333;
}

.actions {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 10px; /* Spacing between buttons */
}

.button-save, .button-reload {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease;
}

.button-save {
  background-color: #4CAF50; /* Green */
  color: white;
}

.button-save:hover {
  background-color: #45a049;
}

.button-save:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.button-reload {
  background-color: #007bff; /* Blue */
  color: white;
}

.button-reload:hover {
  background-color: #0056b3;
}

.button-reload:disabled {
  background-color: #7aa5d2;
  cursor: not-allowed;
}

.json-error-hint {
    color: #d8000c;
    font-size: 0.8em;
    margin-left: 10px;
}
</style>
