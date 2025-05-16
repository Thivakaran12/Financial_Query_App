export async function askLLM(companySlug, question) {
  const res = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company: companySlug, question })
  });
  const data = await res.json();
  return data.answer;
}
