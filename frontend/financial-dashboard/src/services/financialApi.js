// financialApi.js
export async function fetchCompanyData(slug) {
  const res = await fetch(`/data/${slug}/all.json`);
  if (!res.ok) throw new Error(`Failed to load ${slug}`);
  return res.json();
}
