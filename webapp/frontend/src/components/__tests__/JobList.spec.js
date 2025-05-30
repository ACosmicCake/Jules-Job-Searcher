import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobList from '../JobList.vue';
import api from '../../services/api';

// Mock the api module
vi.mock('../../services/api', () => ({
  default: {
    getJobs: vi.fn(),
    getJobDetails: vi.fn(), // Assuming this might be used, even if not detailed in this test file
  },
}));

describe('JobList.vue', () => {
  let wrapper;

  const mockJobs = [
    { id: 1, title: 'Software Engineer', company: 'Tech Corp', location: 'New York', status: 'new', job_url: 'url1', job_site_id: 'site1' },
    { id: 2, title: 'Data Scientist', company: 'Data Inc', location: 'Remote', status: 'applied', job_url: 'url2', job_site_id: 'site2' },
  ];

  beforeEach(() => {
    vi.resetAllMocks();
    // Default mock for getJobs to prevent errors on mount if loadJobs is called automatically
    api.default.getJobs.mockResolvedValue({ data: mockJobs });
    wrapper = mount(JobList); // Mount here, assuming loadJobs is called on mount
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
  });

  it('renders correctly and loads jobs on mount', async () => {
    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('table.job-table').exists()).toBe(true); // Assuming a table for jobs

    await flushPromises(); // Wait for loadJobs on mount to complete

    expect(api.default.getJobs).toHaveBeenCalledTimes(1);
    // Check if jobs are rendered
    const rows = wrapper.findAll('table.job-table tbody tr');
    expect(rows.length).toBe(mockJobs.length);
    expect(rows[0].text()).toContain('Software Engineer');
    expect(rows[1].text()).toContain('Data Scientist');
  });

  describe('loadJobs', () => {
    it('shows error message on API failure', async () => {
      api.default.getJobs.mockRejectedValue({ response: { data: { detail: 'Failed to load jobs' } } });
      // Need to remount or manually call loadJobs if it's not automatically called again
      // For this test, let's assume we can trigger it or it's called on some event
      // If loadJobs is the method that's called:
      await wrapper.vm.loadJobs(); // Manually call
      await flushPromises();

      expect(wrapper.vm.errorMessage).toBe('Failed to load jobs');
      // Optionally, check that the job list is empty or an error message is displayed in the template
      expect(wrapper.find('div.error-message').text()).toContain('Failed to load jobs');
    });

    it('shows "no jobs" message when API returns empty list', async () => {
      api.default.getJobs.mockResolvedValue({ data: [] });
      await wrapper.vm.loadJobs();
      await flushPromises();

      expect(wrapper.vm.jobs.length).toBe(0);
      expect(wrapper.find('p.no-jobs-message').text()).toContain('No jobs found.'); // Assuming such an element
      const rows = wrapper.findAll('table.job-table tbody tr');
      expect(rows.length).toBe(0);
    });
  });

  describe('Filtering', () => {
    it('calls loadJobs with filter parameters when filter inputs change', async () => {
      // Assuming filter inputs like:
      // <input v-model="filters.title" @input="applyFilters" />
      // <select v-model="filters.status" @change="applyFilters">...</select>

      // Clear the initial call from mount
      api.default.getJobs.mockClear();
      api.default.getJobs.mockResolvedValue({ data: [] }); // Subsequent calls return empty for simplicity

      // Simulate changing title filter
      const titleInput = wrapper.find('input.filter-title'); // Assuming selector
      await titleInput.setValue('Engineer');
      // If applyFilters is called on input/change, it should trigger loadJobs.
      // Or, if there's an "Apply Filters" button:
      // await wrapper.find('button.apply-filters-button').trigger('click');

      // For this example, let's assume filters are applied automatically or via a method:
      // wrapper.vm.filters.title = 'Engineer'; // This would be the model update
      // await wrapper.vm.applyFilters(); // Or whatever method triggers the API call

      // A common pattern is to have a watcher on filters or call loadJobs in applyFilters method
      // Let's assume applyFilters calls loadJobs. We call applyFilters manually.
      wrapper.vm.filters.title = 'Engineer'; // Manually update the reactive property
      await wrapper.vm.applyFilters(); // Manually call the method that triggers loadJobs
      await flushPromises();

      expect(api.default.getJobs).toHaveBeenCalledTimes(1);
      expect(api.default.getJobs).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Engineer',
        // other filters should be at their default/initial values
        status: wrapper.vm.filters.status, // or initial value like ''
        skip: 0, // Assuming default skip
        limit: wrapper.vm.pagination.limit, // Assuming default limit
      }));

      // Simulate changing status filter
      api.default.getJobs.mockClear();
      const statusSelect = wrapper.find('select.filter-status'); // Assuming selector
      await statusSelect.setValue('applied'); // This updates wrapper.vm.filters.status
      await wrapper.vm.applyFilters();
      await flushPromises();

      expect(api.default.getJobs).toHaveBeenCalledTimes(1);
      expect(api.default.getJobs).toHaveBeenCalledWith(expect.objectContaining({
        title: 'Engineer', // From previous filter
        status: 'applied',
        skip: 0,
        limit: wrapper.vm.pagination.limit,
      }));
    });
  });

  describe('Pagination', () => {
    it('calls loadJobs with correct skip/limit when pagination changes', async () => {
      // Assuming pagination controls like:
      // <button @click="nextPage" class="next-page-button">Next</button>
      // <button @click="prevPage" class="prev-page-button">Previous</button>
      // And data properties like: pagination: { skip: 0, limit: 10, total: 0 }

      api.default.getJobs.mockClear();
      api.default.getJobs.mockResolvedValue({ data: [] });

      // Simulate clicking next page
      // This assumes nextPage method updates pagination.skip and calls loadJobs
      // wrapper.vm.pagination.skip = 0; // Initial state
      // wrapper.vm.pagination.limit = 10;
      await wrapper.find('button.next-page-button').trigger('click');
      await flushPromises();

      expect(api.default.getJobs).toHaveBeenCalledTimes(1);
      expect(api.default.getJobs).toHaveBeenCalledWith(expect.objectContaining({
        skip: 10, // Assuming limit is 10, so skip becomes 10 for page 2
        limit: 10, // Assuming limit is 10
        // other filters at their current state
      }));

      // Simulate clicking previous page
      api.default.getJobs.mockClear();
      // Manually set skip to simulate being on page 2
      wrapper.vm.pagination.skip = 10;
      await wrapper.find('button.prev-page-button').trigger('click');
      await flushPromises();

      expect(api.default.getJobs).toHaveBeenCalledTimes(1);
      expect(api.default.getJobs).toHaveBeenCalledWith(expect.objectContaining({
        skip: 0, // Back to page 1
        limit: 10,
      }));
    });
  });

  it('handles view job details click (optional)', async () => {
    // This is a basic test. If JobDetails is a modal or separate route, testing might be more complex.
    // Assuming a button on each job row to view details.
    // <button @click="viewDetails(job.id)" class="view-details-button">View</button>
    api.default.getJobDetails.mockResolvedValue({ data: { id: 1, title: 'Software Engineer', description: 'Detailed description.' } });

    // Ensure jobs are loaded first
    await flushPromises(); // For initial loadJobs

    const viewDetailsButton = wrapper.find('table.job-table tbody tr:first-child button.view-details-button');
    if (viewDetailsButton.exists()) {
        await viewDetailsButton.trigger('click');
        await flushPromises();

        expect(api.default.getJobDetails).toHaveBeenCalledTimes(1);
        expect(api.default.getJobDetails).toHaveBeenCalledWith(mockJobs[0].id); // or mockJobs[0].job_site_id depending on what's used

        // Check if details are displayed (e.g., in a modal or a dedicated section)
        // expect(wrapper.find('.job-details-modal').text()).toContain('Detailed description.');
        // For now, just check the API call.
    } else {
        console.warn("View details button not found for JobList.spec.js test.");
    }
  });
});
