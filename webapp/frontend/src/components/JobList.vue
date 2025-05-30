<template>
  <div class="job-list-container">
    <h2>Scraped Job Listings</h2>

    <div v-if="isLoading" class="loading-message">Loading jobs...</div>
    <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

    <div class="pagination-controls">
      <button @click="prevPage" :disabled="isLoading || skip === 0">Previous</button>
      <span>Page {{ currentPage }}</span>
      <button @click="nextPage" :disabled="isLoading || jobsList.length < limit">Next</button>
    </div>

    <!-- Global controls removed -->

    <ul v-if="jobsList.length > 0" class="jobs">
      <li v-for="job in jobsList" :key="job.id || job.job_url" class="job-item">
        <h3>{{ job.title || 'N/A' }}</h3>
        <p><strong>Company:</strong> {{ job.company || 'N/A' }}</p>
        <p><strong>Location:</strong> {{ job.location || 'N/A' }}</p>
        <p><strong>Date Posted:</strong> {{ formatDate(job.date_posted) }}</p>
        <p><strong>Source:</strong> {{ job.source || 'N/A' }}</p>

        <button @click="job.isExpanded = !job.isExpanded" class="button-toggle-item">
          {{ job.isExpanded ? 'Hide Details' : 'Show Details' }}
        </button>
        
        <!-- Collapsible Section for individual job -->
        <div v-if="job.isExpanded" class="job-details-collapsible">
          <p v-if="job.job_type"><strong>Job Type:</strong> {{ job.job_type }}</p>
          <p v-if="job.salary_text"><strong>Salary:</strong> {{ job.salary_text }}</p>
          <p><strong>Status:</strong> {{ job.status || 'new' }}</p>
          <p><strong>Scraped:</strong> {{ formatTimestamp(job.scraped_timestamp) }}</p>
          
          <div v-if="job.emails && job.emails.length > 0" class="job-emails">
            <strong>Contact Emails:</strong>
            <ul>
              <li v-for="email in job.emails" :key="email">{{ email }}</li>
            </ul>
          </div>
          
          <div class="job-description" v-if="job.description_text">
            <strong>Description:</strong>
            <p class="description-text">{{ job.description_text }}</p> 
          </div>
        </div>
        <!-- End Collapsible Section -->
        
        <!-- Always visible link -->
        <p v-if="job.job_url" class="job-link-paragraph">
          <a :href="job.job_url" target="_blank" rel="noopener noreferrer" class="job-link">View Job Posting</a>
        </p>
      </li>
    </ul>
    <div v-else-if="!isLoading && !errorMessage" class="no-jobs">
      No jobs found. Try scraping first.
    </div>
     <div class="pagination-controls bottom-pagination">
      <button @click="prevPage" :disabled="isLoading || skip === 0">Previous</button>
      <span>Page {{ currentPage }}</span>
      <button @click="nextPage" :disabled="isLoading || jobsList.length < limit">Next</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';

const jobsList = ref([]);
const isLoading = ref(false);
const errorMessage = ref('');
const skip = ref(0);
const limit = ref(20); // Jobs per page
// const allExpanded = ref(false); // Removed global expansion state

const currentPage = computed(() => Math.floor(skip.value / limit.value) + 1);

const fetchJobs = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    // Make sure api.getJobs returns response.data which is the array of jobs
    const response = await api.getJobs({ skip: skip.value, limit: limit.value });
    const rawJobs = response.data || []; // Ensure it's an array
    jobsList.value = rawJobs.map(job => ({ ...job, isExpanded: false })); // Add isExpanded to each job
    
    if (rawJobs.length === 0 && skip.value > 0) {
        // If on a page beyond the first and no jobs are returned,
        // it might mean we've paged too far.
        // Optionally, could auto-go to prev page or show a specific message.
        // For now, just shows "No jobs found" effectively if list is empty.
    }
  } catch (error) {
    console.error('Failed to fetch jobs:', error);
    errorMessage.value = error.response?.data?.detail || error.message || 'Failed to fetch jobs.';
    jobsList.value = []; // Clear list on error
  } finally {
    isLoading.value = false;
  }
};

const nextPage = () => {
  if (jobsList.value.length < limit.value) {
    // Don't go to next page if current page wasn't full (implies no more jobs)
    // This is a client-side heuristic as backend doesn't send totalJobs
    return; 
  }
};

const nextPage = () => {
  if (jobsList.value.length < limit.value) {
    // Don't go to next page if current page wasn't full (implies no more jobs)
    // This is a client-side heuristic as backend doesn't send totalJobs
    return; 
  }
  skip.value += limit.value;
  fetchJobs();
};

const prevPage = () => {
  if (skip.value > 0) {
    skip.value = Math.max(0, skip.value - limit.value);
    fetchJobs();
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  // Assuming dateStr is YYYY-MM-DD or a full ISO timestamp that Date can parse
  const options = { year: 'numeric', month: 'long', day: 'numeric' };
  try {
    return new Date(dateStr).toLocaleDateString(undefined, options);
  } catch (e) {
    return dateStr; // Fallback to original string if parsing fails
  }
};

const formatTimestamp = (timestampStr) => {
  if (!timestampStr) return 'N/A';
  try {
    return new Date(timestampStr).toLocaleString();
  } catch (e) {
    return timestampStr;
  }
};

const truncateDescription = (text, maxLength) => {
  if (!text) return 'N/A';
  // No longer truncating here as full description is shown when expanded
  // If a preview is needed when collapsed, that would be handled differently.
  // For now, description is only shown when job.isExpanded is true.
  return text; 
};

onMounted(() => {
  fetchJobs();
});

// toggleAllDetails method removed

</script>

<style scoped>
/* Global controls styles removed */

.button-toggle-item {
  padding: 6px 12px;
  background-color: #007bff; /* Blue */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
  margin-top: 5px;
  margin-bottom: 10px;
  transition: background-color 0.2s;
}
.button-toggle-item:hover {
  background-color: #0056b3;
}

.job-details-collapsible {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #eee; /* Visual separator for collapsible content */
}

.job-link-paragraph { /* Ensure consistent spacing for the link */
  margin-top: 10px;
}

.job-list-container {
  padding: 20px;
  max-width: 900px;
  margin: 20px auto;
  font-family: Arial, sans-serif;
}

h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 25px;
}

.loading-message, .error-message, .no-jobs {
  text-align: center;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 5px;
}

.loading-message { background-color: #eef; color: #335; }
.error-message { background-color: #fdd; color: #c33; border: 1px solid #c55; }
.no-jobs { background-color: #f0f0f0; color: #555; }

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.pagination-controls.bottom-pagination {
  margin-top: 20px;
}

.pagination-controls button {
  padding: 8px 15px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.pagination-controls button:hover:not(:disabled) {
  background-color: #2980b9;
}

.pagination-controls button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.pagination-controls span {
  font-size: 0.9em;
  color: #555;
}

.jobs {
  list-style-type: none;
  padding: 0;
}

.job-item {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.job-item h3 {
  margin-top: 0;
  color: #2980b9;
  font-size: 1.4em;
}

.job-item p {
  margin: 8px 0;
  font-size: 0.95em;
  line-height: 1.5;
  color: #333;
}

.job-item strong {
  color: #555;
}

.job-emails {
  margin-top: 10px;
  font-size: 0.9em;
}
.job-emails ul {
  padding-left: 20px;
  margin-top: 5px;
}

.job-description {
  margin-top: 10px;
}

.description-text {
  font-size: 0.9em;
  color: #444;
  white-space: pre-wrap; /* Preserve line breaks from description */
  background-color: #f9f9f9;
  padding: 8px;
  border-radius: 3px;
  border: 1px solid #eee;
  max-height: 200px; /* Max height for description in normal view */
  overflow-y: auto;  /* Scroll for long descriptions */
}

/* When allExpanded is true, description might show full text, remove max-height or adjust */
.job-details-collapsible .description-text {
  /* Potentially remove max-height if allExpanded should mean truly all details */
   max-height: none; /* Show full description when expanded */
}


.job-link {
  display: inline-block;
  /* margin-top: 10px; */ /* Moved to .job-link-paragraph for consistent spacing */
  padding: 8px 12px;
  background-color: #27ae60;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 0.9em;
  transition: background-color 0.2s;
}

.job-link:hover {
  background-color: #229954;
}
</style>
