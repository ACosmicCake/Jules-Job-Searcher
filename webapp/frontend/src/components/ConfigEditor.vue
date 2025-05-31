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

    <div class="scrape-parameters-section">
      <h3>Manual Scrape Parameters</h3>
      <div class="scrape-inputs">
        <div class="input-group">
          <label for="resultsWanted">Results Wanted:</label>
          <input type="number" id="resultsWanted" v-model.number="resultsWanted" placeholder="e.g., 20">
        </div>
        <div class="input-group">
          <label for="hoursOld">Hours Old:</label>
          <input type="number" id="hoursOld" v-model.number="hoursOld" placeholder="e.g., 72">
        </div>

        <div class="input-group">
          <label>Sites to Scrape:</label>
          <div class="checkbox-group checkbox-group-sites">
            <input type="checkbox" id="scrapeIndeed" v-model="sitesToScrape.indeed">
            <label for="scrapeIndeed">Indeed</label>
            <input type="checkbox" id="scrapeLinkedIn" v-model="sitesToScrape.linkedin">
            <label for="scrapeLinkedIn">LinkedIn</label>
            <input type="checkbox" id="scrapeZipRecruiter" v-model="sitesToScrape.ziprecruiter">
            <label for="scrapeZipRecruiter">ZipRecruiter</label>
            <input type="checkbox" id="scrapeGlassdoor" v-model="sitesToScrape.glassdoor">
            <label for="scrapeGlassdoor">Glassdoor</label>
            <input type="checkbox" id="scrapeGoogle" v-model="sitesToScrape.google">
            <label for="scrapeGoogle">Google</label>
            <input type="checkbox" id="scrapeBayt" v-model="sitesToScrape.bayt">
            <label for="scrapeBayt">Bayt</label>
          </div>
        </div>

        <div class="input-group">
          <label for="countryIndeed">Country for Indeed (e.g., USA, GBR):</label>
          <input type="text" id="countryIndeed" v-model.trim="countryIndeed" placeholder="USA">
        </div>

        <div class="input-group">
          <label for="googleSearchTerm">Google Specific Search Term:</label>
          <input type="text" id="googleSearchTerm" v-model.trim="googleSearchTerm" placeholder="e.g., software engineer intern">
        </div>

        <div class="input-group">
          <label for="distance">Search Distance (miles):</label>
          <input type="number" id="distance" v-model.number="distance" placeholder="50">
        </div>

        <div class="input-group">
          <label for="jobType">Job Type:</label>
          <select id="jobType" v-model="jobType">
            <option value="">Any</option>
            <option value="fulltime">Full-time</option>
            <option value="parttime">Part-time</option>
            <option value="internship">Internship</option>
            <option value="contract">Contract</option>
          </select>
        </div>

        <div class="input-group">
          <label>Fetch LinkedIn Descriptions:</label>
          <div class="checkbox-group">
            <input type="checkbox" id="linkedinFetchDesc" v-model="linkedinFetchDescription">
            <label for="linkedinFetchDesc">Enabled</label>
          </div>
        </div>

        <div class="input-group">
          <label>Remote Only:</label>
          <div class="checkbox-group">
            <input type="checkbox" id="isRemote" v-model="isRemote">
            <label for="isRemote">Enabled</label>
          </div>
        </div>

        <div class="input-group">
          <label>Easy Apply Only (LinkedIn):</label>
          <div class="checkbox-group">
            <input type="checkbox" id="easyApply" v-model="easyApply">
            <label for="easyApply">Enabled</label>
          </div>
        </div>

        <div class="input-group">
          <label for="descriptionFormat">Description Format:</label>
          <select id="descriptionFormat" v-model="descriptionFormat">
            <option value="markdown">Markdown</option>
            <option value="html">HTML</option>
          </select>
        </div>
      </div>
      <button @click="triggerScrapeWithParams" :disabled="isLoading" class="button-scrape">
        {{ isLoading ? 'Scraping...' : 'Scrape Jobs with Parameters' }}
      </button>
      <div v-if="scrapeStatusMessage" :class="{'success-message': isScrapeSuccess, 'error-message': !isScrapeSuccess}" class="scrape-status-message">
        {{ scrapeStatusMessage }}
      </div>
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
const successMessage = ref(''); // For config save/load
const isJsonValid = ref(true);

// Reactive variables for new scrape parameters
const resultsWanted = ref(20); 
const hoursOld = ref(72);
const sitesToScrape = ref({
  indeed: true,
  linkedin: true,
  ziprecruiter: false,
  glassdoor: false,
  google: false,
  bayt: false
});
const countryIndeed = ref('USA');
const linkedinFetchDescription = ref(true);
const googleSearchTerm = ref('');
const distance = ref(50);
const jobType = ref(''); // Default for "Any"
const isRemote = ref(false);
const easyApply = ref(false);
const descriptionFormat = ref('markdown');
const scrapeStatusMessage = ref(''); // For displaying scrape status
const isScrapeSuccess = ref(false);


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

// Function to trigger scraping with parameters
const triggerScrapeWithParams = async () => {
  isLoading.value = true;
  scrapeStatusMessage.value = '';
  isScrapeSuccess.value = false;
  try {
    const selectedSites = Object.entries(sitesToScrape.value)
      .filter(([, isActive]) => isActive)
      .map(([siteName]) => siteName);

    const params = {
      results_wanted: resultsWanted.value,
      hours_old: hoursOld.value,
      sites_to_scrape: selectedSites.length > 0 ? selectedSites : null, // Send null if no sites selected, or handle as needed by backend
      country_indeed: countryIndeed.value,
      linkedin_fetch_description: linkedinFetchDescription.value,
      google_search_term: googleSearchTerm.value || null, // Send null if empty
      distance: distance.value,
      job_type: jobType.value || null, // Send null if "Any" (empty string)
      is_remote: isRemote.value,
      easy_apply: easyApply.value,
      description_format: descriptionFormat.value,
    };
    // Assuming api.js will have a method like triggerScrapingWithParams
    const response = await api.triggerScrapingWithParams(params); 
    scrapeStatusMessage.value = `Scraping initiated with custom parameters. ${response.data?.message || ''} Jobs processed: ${response.data?.total_jobs_processed_from_fetch || 'N/A'}, New: ${response.data?.new_jobs_added || 'N/A'}`;
    isScrapeSuccess.value = true;
    // console.log('Scraping triggered:', response.data);
  } catch (error) {
    console.error('Failed to trigger scraping:', error);
    scrapeStatusMessage.value = error.response?.data?.detail || error.message || 'Failed to trigger scraping.';
    isScrapeSuccess.value = false;
  } finally {
    isLoading.value = false; // Consider a separate isLoadingScrape if needed
  }
};

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

/* Styles for new scrape parameters section */
.scrape-parameters-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.scrape-parameters-section h3 {
  color: #333;
  margin-bottom: 15px;
}

.scrape-inputs {
  display: flex;
  flex-wrap: wrap; /* Allow items to wrap to the next line */
  gap: 20px; /* Spacing between input groups */
  margin-bottom: 15px;
  /* align-items: center; */ /* Can be removed or adjusted if flex-start is better for wrapped items */
  align-items: flex-start; /* Align items to the start of the cross axis */
}

.input-group {
  display: flex;
  flex-direction: column; /* Stack label on top of input */
  margin-bottom: 10px;
  min-width: 180px; /* Ensure a minimum width for each group */
}

.input-group label,
.checkbox-group label {
  margin-bottom: 5px;
  font-size: 0.9em;
  color: #555;
}

/* Specific styling for labels within a checkbox group to reduce their right margin */
.checkbox-group label {
  margin-right: 8px;
  margin-bottom: 0; /* Align with checkbox */
}

.input-group > label { /* Styling for the main label of an input group */
  font-weight: bold;
  margin-bottom: 8px;
  display: block;
}


.input-group input[type="number"],
.input-group input[type="text"],
.input-group select { /* Added select styling */
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.95em;
  width: 100%; /* Make input elements take full width of .input-group */
  box-sizing: border-box;
}

.checkbox-group {
  display: flex;
  flex-direction: row; /* Default, but explicit */
  flex-wrap: wrap; /* Allow checkboxes to wrap within their group if needed */
  align-items: center;
}
.checkbox-group.checkbox-group-sites label {
  margin-right: 10px; /* More space for site labels */
}


.checkbox-group input[type="checkbox"] {
  margin-right: 4px;
  margin-bottom: 4px; /* Add some space if they wrap */
}

/* Remove redundant specific label styling now that .input-group > label handles boldness */
/*
.input-group > label[for^="scrape"],
.input-group > label[for="countryIndeed"],
.input-group > label:not([for^="scrapeIndeed"]):not([for^="scrapeLinkedIn"]):not([for="linkedinFetchDesc"]) {
  font-weight: bold;
  margin-bottom: 8px;
}
*/


.button-scrape {
  background-color: #ff8c00; /* Orange */
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease;
  margin-top: 10px; /* Add some space above the button */
}

.button-scrape:hover {
  background-color: #e07b00;
}

.button-scrape:disabled {
  background-color: #ffcc80;
  cursor: not-allowed;
}

.scrape-status-message {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
  text-align: center;
}
</style>
