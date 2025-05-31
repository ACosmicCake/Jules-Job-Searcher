import { createRouter, createWebHistory } from 'vue-router';
import JobList from '../components/JobList.vue';
import ConfigEditor from '../components/ConfigEditor.vue';
import CVGenerationPage from '../components/CVGenerationPage.vue'; // Import the new component

const routes = [
  {
    path: '/',
    name: 'JobList',
    component: JobList
  },
  {
    path: '/config',
    name: 'ConfigEditor',
    component: ConfigEditor
  },
  {
    path: '/generate-cv',
    name: 'GenerateCV',
    component: CVGenerationPage,
    props: route => ({ jobIds: route.query.job_ids ? route.query.job_ids.split(',') : [] })
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
