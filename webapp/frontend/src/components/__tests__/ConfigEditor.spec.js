import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import ConfigEditor from '../ConfigEditor.vue'; // Adjust path: ../ConfigEditor.vue
import api from '../../services/api';

// Mock the api service
vi.mock('../../services/api', () => ({
  default: {
    getConfig: vi.fn(),
    updateConfig: vi.fn(),
    // Mock other functions if ConfigEditor starts using them
  }
}));

describe('ConfigEditor.vue', () => {
  let wrapper;

  const mockConfigData = {
    personal_info: { full_name: 'Test User', email: 'test@example.com' },
    job_preferences: { desired_roles: ['Developer'] },
  };

  beforeEach(() => {
    // Reset mocks before each test
    api.getConfig.mockReset();
    api.updateConfig.mockReset();
    
    // Default mock implementation
    api.getConfig.mockResolvedValue({ data: JSON.parse(JSON.stringify(mockConfigData)) }); // Deep copy
    api.updateConfig.mockResolvedValue({ data: { message: 'Configuration updated successfully.' } });
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
  });

  it('renders and fetches config on mount', async () => {
    wrapper = mount(ConfigEditor);
    
    expect(api.getConfig).toHaveBeenCalledTimes(1);
    
    // Wait for promises to resolve and component to update
    await flushPromises();
    
    const textarea = wrapper.find('textarea');
    expect(textarea.exists()).toBe(true);
    expect(textarea.element.value).toBe(JSON.stringify(mockConfigData, null, 2));
    expect(wrapper.vm.isJsonValid).toBe(true); // Should be valid initially
  });

  it('calls updateConfig when save button is clicked with valid JSON', async () => {
    wrapper = mount(ConfigEditor);
    await flushPromises(); // Initial load

    const newConfig = { newKey: 'newValue' };
    const newConfigString = JSON.stringify(newConfig, null, 2);

    // Simulate user editing the textarea
    const textarea = wrapper.find('textarea');
    await textarea.setValue(newConfigString);
    expect(wrapper.vm.editableJsonString).toBe(newConfigString); // Check v-model binding
    expect(wrapper.vm.isJsonValid).toBe(true);


    const saveButton = wrapper.find('button.button-save');
    await saveButton.trigger('click');
    
    expect(api.updateConfig).toHaveBeenCalledTimes(1);
    expect(api.updateConfig).toHaveBeenCalledWith(newConfig); // Check if called with parsed object

    await flushPromises(); // Wait for potential success message
    expect(wrapper.find('.success-message').exists()).toBe(true);
    expect(wrapper.find('.success-message').text()).toContain('Configuration updated successfully!');
  });

  it('displays error message when getConfig fails', async () => {
    api.getConfig.mockRejectedValueOnce(new Error('Network Error fetching config'));
    wrapper = mount(ConfigEditor);
    
    expect(api.getConfig).toHaveBeenCalledTimes(1);
    await flushPromises();
    
    const errorMessageDiv = wrapper.find('.error-message');
    expect(errorMessageDiv.exists()).toBe(true);
    expect(errorMessageDiv.text()).toContain('Network Error fetching config');
  });

  it('displays error message when updateConfig fails', async () => {
    wrapper = mount(ConfigEditor);
    await flushPromises(); // Initial load

    api.updateConfig.mockRejectedValueOnce(new Error('Network Error saving config'));
    
    const validJsonString = JSON.stringify({ key: "value" }, null, 2);
    const textarea = wrapper.find('textarea');
    await textarea.setValue(validJsonString); // Set some valid JSON to enable save

    const saveButton = wrapper.find('button.button-save');
    await saveButton.trigger('click');
    
    expect(api.updateConfig).toHaveBeenCalledTimes(1);
    await flushPromises();

    const errorMessageDiv = wrapper.find('.error-message');
    expect(errorMessageDiv.exists()).toBe(true);
    expect(errorMessageDiv.text()).toContain('Network Error saving config');
  });


  it('disables save button if JSON in textarea is invalid', async () => {
    wrapper = mount(ConfigEditor);
    await flushPromises(); // Initial load

    const textarea = wrapper.find('textarea');
    await textarea.setValue('{"key": "value", invalid}'); // Invalid JSON

    // isJsonValid should be updated by the watcher
    expect(wrapper.vm.isJsonValid).toBe(false);

    const saveButton = wrapper.find('button.button-save');
    // In Vue Test Utils, `element.disabled` reflects the disabled attribute
    expect(saveButton.element.disabled).toBe(true);
    
    // Also check if hint is shown
    expect(wrapper.find('.json-error-hint').exists()).toBe(true);
  });
  
  it('enables save button if JSON becomes valid', async () => {
    wrapper = mount(ConfigEditor);
    await flushPromises(); // Initial load

    const textarea = wrapper.find('textarea');
    // Start with invalid JSON
    await textarea.setValue('{"key": "value", invalid}');
    expect(wrapper.vm.isJsonValid).toBe(false);
    const saveButton = wrapper.find('button.button-save');
    expect(saveButton.element.disabled).toBe(true);

    // Correct the JSON
    await textarea.setValue('{"key": "value"}');
    expect(wrapper.vm.isJsonValid).toBe(true);
    expect(saveButton.element.disabled).toBe(false);
    expect(wrapper.find('.json-error-hint').exists()).toBe(false); // Hint should disappear
  });

  it('reloads configuration when reload button is clicked', async () => {
    wrapper = mount(ConfigEditor);
    await flushPromises(); // Initial load
    
    // Clear current config string to simulate a change or ensure reload works
    wrapper.vm.editableJsonString = '';
    api.getConfig.mockClear(); // Clear previous calls from onMounted
    
    // Second getConfig call will use the default mock
    api.getConfig.mockResolvedValueOnce({ data: { reloadedKey: 'reloadedValue' } });

    const reloadButton = wrapper.find('button.button-reload');
    await reloadButton.trigger('click');

    expect(api.getConfig).toHaveBeenCalledTimes(1); // Called again
    await flushPromises();

    const textarea = wrapper.find('textarea');
    expect(textarea.element.value).toBe(JSON.stringify({ reloadedKey: 'reloadedValue' }, null, 2));
  });

});
