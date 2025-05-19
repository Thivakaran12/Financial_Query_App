/**
 * financialApi.js
 *
 * Fetches the merged quarterly P&L JSON for a given company.
 * Reads from the `public/data/<slug>/all.json` path in the CRA build.
 */

const DATA_BASE = process.env.REACT_APP_DATA_URL || '';

/**
 * Load all financial records for the given company slug.
 *
 * @param {string} slug – URL‐friendly company identifier (e.g. "dipped-products").
 * @returns {Promise<Array<Object>>} – Array of P&L record objects.
 * @throws {Error} – If the network request fails or the response is not OK.
 */
export async function fetchCompanyData(slug) {
  const url = `${DATA_BASE}/data/${slug}/all.json`;
  const resp = await fetch(url);

  if (!resp.ok) {
    throw new Error(
      `fetchCompanyData error: HTTP ${resp.status} – ${resp.statusText}`
    );
  }

  return resp.json();
}
