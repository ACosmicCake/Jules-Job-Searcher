import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import ScraperControls from '../ScraperControls.vue';
import api from '../../services/api';

// Mock the api module
vi.mock('../../services/api', () => ({
  default: {
    scrapeJobs: vi.fn(), // For background scrape
    triggerScrapingWithParams: vi.fn(), // For synchronous scrape with params
  },
}));

describe('ScraperControls.vue', () => {
  let wrapper;

  beforeEach(() => {
    vi.resetAllMocks();
    wrapper = mount(ScraperControls);
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
  });

  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true);
    expect(wrapper.find('button.trigger-background-scrape-button').exists()).toBe(true);
    expect(wrapper.find('button.trigger-synchronous-scrape-button').exists()).toBe(true);
    expect(wrapper.find('input[type="number"].results-wanted-input').exists()).toBe(true);
    expect(wrapper.find('input[type="number"].hours-old-input').exists()).toBe(true);
    // Add checks for other potential inputs like sites, roles, locations if they are part of this component
  });

  describe('triggerBackgroundScrape', () => {
    it('calls api.scrapeJobs and shows success message', async () => {
      api.default.scrapeJobs.mockResolvedValue({ data: { message: 'Background scraping initiated' } });

      await wrapper.find('button.trigger-background-scrape-button').trigger('click');
      await flushPromises();

      expect(api.default.scrapeJobs).toHaveBeenCalledTimes(1);
      expect(wrapper.vm.scrapeMessage).toBe('Background scraping initiated');
      expect(wrapper.vm.scrapeError).toBe('');
    });

    it('shows error message on api.scrapeJobs failure', async () => {
      api.default.scrapeJobs.mockRejectedValue({ response: { data: { detail: 'Background scrape failed' } } });

      await wrapper.find('button.trigger-background-scrape-button').trigger('click');
      await flushPromises();

      expect(api.default.scrapeJobs).toHaveBeenCalledTimes(1);
      expect(wrapper.vm.scrapeError).toBe('Background scrape failed');
      expect(wrapper.vm.scrapeMessage).toBe('');
    });
  });

  describe('triggerSynchronousScrape', () => {
    it('calls api.triggerScrapingWithParams with parameters and shows success', async () => {
      api.default.triggerScrapingWithParams.mockResolvedValue({ data: { message: 'Synchronous scraping completed', new_jobs_added: 5 } });

      // Set input values
      await wrapper.find('input[type="number"].results-wanted-input').setValue(50);
      await wrapper.find('input[type="number"].hours-old-input').setValue(24);
      // Set other params like sites, roles, locations if they exist in the component
      // wrapper.vm.syncParams.sites = ['indeed_sync']; // Example if data property exists

      await wrapper.find('button.trigger-synchronous-scrape-button').trigger('click');
      await flushPromises();

      expect(api.default.triggerScrapingWithParams).toHaveBeenCalledTimes(1);
      expect(api.default.triggerScrapingWithParams).toHaveBeenCalledWith(expect.objectContaining({
        results_wanted: 50,
        hours_old: 24,
        // sites: ['indeed_sync'] // if this param is collected
      }));
      expect(wrapper.vm.scrapeMessage).toContain('Synchronous scraping completed');
      expect(wrapper.vm.scrapeMessage).toContain('New jobs added: 5');
      expect(wrapper.vm.scrapeError).toBe('');
    });

    it('shows error message on api.triggerScrapingWithParams failure', async () => {
      api.default.triggerScrapingWithParams.mockRejectedValue({ response: { data: { detail: 'Sync scrape failed' } } });

      await wrapper.find('input[type="number"].results-wanted-input').setValue(10); // Set some valid values
      await wrapper.find('input[type="number"].hours-old-input').setValue(12);

      await wrapper.find('button.trigger-synchronous-scrape-button').trigger('click');
      await flushPromises();

      expect(api.default.triggerScrapingWithParams).toHaveBeenCalledTimes(1);
      expect(wrapper.vm.scrapeError).toBe('Sync scrape failed');
      expect(wrapper.vm.scrapeMessage).toBe('');
    });

    it('performs basic validation if inputs are invalid (e.g., results_wanted < 0)', async () => {
      // Assuming the component or HTML5 input type="number" min="0" handles this
      // Or the component has explicit validation logic.

      // Example: results_wanted is negative
      await wrapper.find('input[type="number"].results-wanted-input').setValue(-5);
      await wrapper.find('input[type="number"].hours-old-input').setValue(24);

      await wrapper.find('button.trigger-synchronous-scrape-button').trigger('click');
      await flushPromises();

      // Check if API was NOT called due to validation
      expect(api.default.triggerScrapingWithParams).not.toHaveBeenCalled();
      // Check if an error message related to validation is shown
      expect(wrapper.vm.scrapeError).toContain('Invalid input'); // Or similar message
      // Or check for HTML5 validation message if that's the mechanism
      // const input = wrapper.find('input[type="number"].results-wanted-input').element;
      // expect(input.validity.valid).toBe(false); // If using HTML5 validation
    });
  });
});
