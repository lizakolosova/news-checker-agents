import { API_CONFIG } from '../config/constants';


export const factCheckService = {
  async checkArticle(articleData) {
    const response = await fetch(
      `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.FACT_CHECK}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(articleData),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
        `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return response.json();
  },
};
