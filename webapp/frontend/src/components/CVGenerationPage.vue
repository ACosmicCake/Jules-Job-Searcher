<template>
  <div class="cv-generation-page">
    <h2>CV Generation</h2>

    <div v-if="isLoadingJobs" class="loading-message">
      Loading job details...
    </div>

    <div v-if="errorMessage" class="error-message">
      <p><strong>Error:</strong> {{ errorMessage }}</p>
    </div>

    <div v-if="!isLoadingJobs && jobs.length > 0" class="selected-jobs-section">
      <h3>Selected Jobs:</h3>
      <ul>
        <li v-for="job in jobs" :key="job.id" class="job-detail-item">
          <strong>{{ job.title || 'N/A' }}</strong> - <span>{{ job.company || 'N/A' }}</span>
          <p v-if="job.location"><em>Location: {{ job.location }}</em></p>
        </li>
      </ul>
      <!-- Further CV generation controls will go here -->
    </div>

    <div v-if="!isLoadingJobs && jobs.length > 0" class="cv-upload-section">
      <h3>Upload Your CV</h3>
      <div class="upload-area">
        <input type="file" @change="handleCvUpload" accept=".pdf,.doc,.docx" class="file-input"/>
        <p v-if="isUploadingCv" class="status-message loading-message">Uploading CV...</p>
        <p v-if="cvUploadStatus" :class="{'success-message': cvUploadStatus.startsWith('CV uploaded successfully'), 'error-message': cvUploadStatus.startsWith('CV upload failed')}" class="status-message">
          {{ cvUploadStatus }}
        </p>
      </div>
    </div>

    <div class="generation-controls" v-if="!isLoadingJobs && jobs.length > 0">
      <button
        @click="triggerCvGeneration"
        :disabled="!cvSuccessfullyUploaded || jobs.length === 0 || isGeneratingCvs"
        class="button-generate"
      >
        Generate Tailored CVs
      </button>
    </div>

    <div v-if="isGeneratingCvs" class="status-message loading-message">
      Generating CVs, please wait...
    </div>

    <div v-if="generationResults.length > 0" class="generation-results-section">
      <h3>Generation Results:</h3>
      <ul>
        <li v-for="(result, index) in generationResults" :key="index"
            :class="{'result-item-success': result.status === 'success', 'result-item-error': result.status === 'error'}">
          <p><strong>Job:</strong> {{ findJobTitle(result.job_id) }}</p>
          <div v-if="result.status === 'success'">
            <p>Status: {{ result.message }}</p>
            <p>Generated File: {{ result.generated_cv_filename }}</p>
            <!-- Download link placeholder -->
            <!-- <a :href="result.download_url" target="_blank">Download CV</a> -->
          </div>
          <div v-if="result.status === 'error'">
            <p class="error-text">Error: {{ result.message }}</p>
          </div>
        </li>
      </ul>
    </div>

    <div v-if="generationError" class="status-message error-message">
      Error: {{ generationError }}
    </div>

    <div v-if="!isLoadingJobs && jobs.length === 0 && !errorMessage" class="no-jobs-message">
      <p>No jobs selected or details could not be loaded. Please go back and select jobs from the list.</p>
    </div>
     <router-link to="/" class="back-link">Back to Job List</router-link>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, computed } from 'vue'; // Import computed
import api from '@/services/api'; // Assuming api.js is in src/services

const props = defineProps({
  jobIds: {
    type: Array,
    default: () => []
  }
});

const jobs = ref([]);
const isLoadingJobs = ref(false);
const errorMessage = ref('');

// CV Upload state
const isUploadingCv = ref(false);
const cvUploadStatus = ref('');
const uploadedCvFile = ref(null); // Optional: store the File object

// CV Generation state
const isGeneratingCvs = ref(false);
const generationResults = ref([]);
const generationError = ref('');

const cvSuccessfullyUploaded = computed(() => {
  return cvUploadStatus.value.startsWith('CV uploaded successfully');
});

onMounted(async () => {
  isLoadingJobs.value = true;
  errorMessage.value = '';
  jobs.value = [];

  if (!props.jobIds || props.jobIds.length === 0) {
    errorMessage.value = 'No job IDs provided.';
    isLoadingJobs.value = false;
    return;
  }

  try {
    const fetchedJobsDetails = await Promise.all(
      props.jobIds.map(id => api.getJobDetails(id).then(response => response.data))
    );
    jobs.value = fetchedJobsDetails.filter(job => job); // Filter out any null responses if a job wasn't found
    if (jobs.value.length !== props.jobIds.length) {
        // This means some jobs were not found or failed to load
        console.warn("CVGenerationPage: Some job details could not be fetched.");
        // Optionally set a non-critical error message or notification
    }
  } catch (error) {
    console.error('Failed to fetch job details:', error);
    errorMessage.value = `Failed to load job details. ${error.message || ''}`;
  } finally {
    isLoadingJobs.value = false;
  }
});

async function handleCvUpload(event) {
  cvUploadStatus.value = '';
  isUploadingCv.value = true;
  const file = event.target.files[0];

  if (!file) {
    isUploadingCv.value = false;
    return;
  }

  // Optional: Store the file object if needed for other purposes
  uploadedCvFile.value = file;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.uploadCv(formData);
    cvUploadStatus.value = `CV uploaded successfully: ${response.data.filename || 'Unknown filename'}. Path: ${response.data.saved_path_in_config || ''}`;
    // Consider if you need to clear the file input: event.target.value = null;
  } catch (error) {
    console.error('CV upload failed:', error);
    cvUploadStatus.value = `CV upload failed: ${error.response?.data?.detail || error.message || 'Unknown error'}`;
  } finally {
    isUploadingCv.value = false;
  }
}

function findJobTitle(jobId) {
  const job = jobs.value.find(j => j.id.toString() === jobId.toString()); // Ensure type consistency for comparison
  return job ? `${job.title} at ${job.company}` : 'Unknown Job';
}

async function triggerCvGeneration() {
  if (!cvSuccessfullyUploaded.value || props.jobIds.length === 0) {
    generationError.value = "Please upload a CV and ensure jobs are selected.";
    return;
  }

  isGeneratingCvs.value = true;
  generationResults.value = [];
  generationError.value = '';

  const payload = {
    job_ids: props.jobIds
  };

  try {
    const response = await api.generateTailoredCvs(payload);
    generationResults.value = response.data;
  } catch (error) {
    console.error('Failed to generate CVs:', error);
    generationError.value = `Failed to generate CVs: ${error.response?.data?.detail || error.message || 'Unknown error'}`;
  } finally {
    isGeneratingCvs.value = false;
  }
}
</script>

<style scoped>
.cv-generation-page {
  padding: 20px;
  max-width: 800px;
  margin: 20px auto;
  font-family: Arial, sans-serif;
  background-color: #f9f9f9;
  border: 1px solid #ccc;
  border-radius: 8px;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 25px;
}

.loading-message, .error-message, .no-jobs-message {
  text-align: center;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 5px;
}

.loading-message { background-color: #eef; color: #335; }
.error-message { background-color: #fdd; color: #c33; border: 1px solid #c55; }
.no-jobs-message { background-color: #f0f0f0; color: #555; }

.selected-jobs-section {
  margin-top: 20px;
}

.selected-jobs-section h3 {
  color: #333;
  margin-bottom: 15px;
}

.selected-jobs-section ul {
  list-style-type: none;
  padding: 0;
}

.job-detail-item {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px 15px;
  margin-bottom: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.job-detail-item strong {
  color: #2980b9;
}
.job-detail-item span {
  color: #555;
}
.job-detail-item p {
  font-size: 0.9em;
  color: #777;
  margin-top: 5px;
}

.cv-upload-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.cv-upload-section h3 {
  color: #333;
  margin-bottom: 15px;
}

.upload-area .file-input {
  display: block;
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: white;
}

.upload-area .status-message { /* General styling for status messages */
  padding: 10px;
  margin-top: 10px;
  border-radius: 4px;
  text-align: center;
  font-size: 0.9em;
}
/* Specific success/error styling for status messages is already handled by existing classes */
/* .loading-message, .success-message, .error-message */

.generation-controls {
  text-align: center;
  margin-top: 20px;
  margin-bottom: 20px;
}

.button-generate {
  padding: 12px 25px;
  background-color: #28a745; /* Green for generate */
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1.1em;
  transition: background-color 0.2s;
}

.button-generate:hover:not(:disabled) {
  background-color: #218838;
}

.button-generate:disabled {
  background-color: #a3d9b1;
  cursor: not-allowed;
}

.generation-results-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.generation-results-section h3 {
  color: #333;
  margin-bottom: 15px;
}

.generation-results-section ul {
  list-style-type: none;
  padding: 0;
}

.generation-results-section li { /* General item styling */
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.result-item-success {
  background-color: #e6ffed; /* Light green background for success */
  border-left: 5px solid #28a745;
}

.result-item-error {
  background-color: #ffeeee; /* Light red background for error */
  border-left: 5px solid #dc3545;
}
.result-item-error .error-text {
  color: #dc3545; /* Darker red for error text */
  font-weight: bold;
}


.back-link {
  display: block;
  text-align: center;
  margin-top: 25px;
  padding: 10px 15px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s;
}
.back-link:hover {
  background-color: #0056b3;
}
</style>
