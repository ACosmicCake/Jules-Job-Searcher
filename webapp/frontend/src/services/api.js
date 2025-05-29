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

  // Job Management (placeholders)
  scrapeJobs() {
    return apiClient.post('/jobs/scrape');
  },
  getJobs(params) { // params = { title, location, source, status, page, limit }
    return apiClient.get('/jobs', { params });
  },
  getJobDetails(jobId) {
    return apiClient.get(`/jobs/${jobId}`);
  },

  // Logs (placeholder)
  getLogs(lines = 100) {
    return apiClient.get('/logs', { params: { lines } });
  }
};
