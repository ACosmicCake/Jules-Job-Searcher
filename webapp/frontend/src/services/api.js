import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api', // Adjust if your backend runs elsewhere
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  // Config Management
  getConfig() {
    return apiClient.get('/config');
  },
  updateConfig(configData) {
    return apiClient.post('/config', configData);
  },

  // CV Management (placeholders, can be filled later)
  uploadCv(formData) {
    return apiClient.post('/cv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  parseCv() {
    return apiClient.post('/cv/parse');
  },
  getCvData() {
    return apiClient.get('/cv/data');
  },

  // Job Management
  // This is the background scraping task
  scrapeJobs() { 
    return apiClient.post('/jobs/scrape'); 
  },
  // New synchronous scraping with parameters
  triggerScrapingWithParams(params) { 
    // params = { results_wanted, hours_old }
    // This endpoint is not under /api, so call it directly.
    return axios.post('http://localhost:8000/scrape-jobs/', params, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },
  getJobs(params) { // params = { title, location, source, status, skip, limit }
    // This endpoint is /jobs/, not /api/jobs/. Call it directly.
    // Ensure params are correctly passed for axios.get with direct URL
    return axios.get('http://localhost:8000/jobs/', { 
      params: params, // Pass params object for query string generation
      headers: { // Optional: if any specific headers needed, though typically not for GET
        'Content-Type': 'application/json', 
      }
    });
  },
  getJobDetails(jobId) {
    return apiClient.get(`/jobs/${jobId}`);
  },

  // CV Generation
  generateTailoredCvs(payload) { // payload = { job_ids: [...] }
    return apiClient.post('/cv/generate-tailored', payload);
  },

  // Logs (placeholder)
  getLogs(lines = 100) {
    return apiClient.get('/logs', { params: { lines } });
  }
};
