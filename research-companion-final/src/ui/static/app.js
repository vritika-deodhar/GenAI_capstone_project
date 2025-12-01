// const form = document.getElementById('qryForm');
// form.addEventListener('submit', async (e) => {
//   e.preventDefault();
//   const q = document.getElementById('query').value;
//   const max = parseInt(document.getElementById('max').value || '2');
//   const resultsDiv = document.getElementById('results');
//   resultsDiv.innerHTML = '<p>Running query...</p>';
//   const resp = await fetch('/query', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query: q, max_results: max})});
//   const data = await resp.json();
//   // render
//   resultsDiv.innerHTML = '';
//   const h = document.createElement('h2');
//   h.textContent = `Results for: ${data.query}`;
//   resultsDiv.appendChild(h);
//   data.papers.forEach(p => {
//     const card = document.createElement('div');
//     card.className = 'paper';
//     const title = document.createElement('h3');
//     title.textContent = p.title || 'Untitled';
//     card.appendChild(title);
//     const authors = document.createElement('div');
//     authors.textContent = 'Authors: ' + (p.authors || []).join(', ');
//     card.appendChild(authors);
//     p.summaries.forEach((s, i) => {
//       const sub = document.createElement('div');
//       sub.className='summary';
//       const h4 = document.createElement('h4');
//       h4.textContent = `Chunk ${i+1} — Problem`;
//       sub.appendChild(h4);
//       const pprob = document.createElement('p');
//       pprob.textContent = s.problem || '';
//       sub.appendChild(pprob);
//       const meth = document.createElement('p');
//       meth.textContent = 'Methods: ' + (s.methods||[]).join(', ');
//       sub.appendChild(meth);
//       // evidence snippets
//       const ev = s.evidence || {};
//       const evDiv = document.createElement('div');
//       evDiv.className='evidence';
//       const evTitle = document.createElement('strong');
//       evTitle.textContent = 'Evidence:';
//       evDiv.appendChild(evTitle);
//       for (const [k,v] of Object.entries(ev)) {
//         const ul = document.createElement('ul');
//         v.forEach(item => {
//           const li = document.createElement('li');
//           li.textContent = `${k}: "${item.snippet}" (source: ${item.chunk_id})`;
//           ul.appendChild(li);
//         });
//         evDiv.appendChild(ul);
//       }
//       sub.appendChild(evDiv);
//       card.appendChild(sub);
//     });
//     // verifications
//     const ver = document.createElement('div');
//     ver.className='verification';
//     ver.innerHTML = `<strong>Verification issues:</strong> <pre>${JSON.stringify(p.verifications, null, 2)}</pre>`;
//     card.appendChild(ver);
//     resultsDiv.appendChild(card);
//   });
// });
const form = document.getElementById('qryForm');
const resultsDiv = document.getElementById('results');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = document.getElementById('query').value;
  const max = parseInt(document.getElementById('max').value || '2');

  resultsDiv.innerHTML = '<p>Running query...</p>';

  try {
    const resp = await fetch('/query', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({query: q, max_results: max})
    });

    const data = await resp.json();
    renderResults(data);

  } catch (err) {
    console.error(err);
    resultsDiv.innerHTML = '<p style="color:red;">Error running query. Check console.</p>';
  }
});

function renderResults(data) {
  resultsDiv.innerHTML = '';

  const h = document.createElement('h2');
  h.textContent = `Results for: ${data.query}`;
  resultsDiv.appendChild(h);

  // runtime
  if (data.runtime_seconds !== undefined) {
    const rt = document.createElement('p');
    rt.textContent = `Runtime: ${data.runtime_seconds}s`;
    resultsDiv.appendChild(rt);
  }

  // Ranking
  if (data.ranking && data.ranking.length) {
    const rh = document.createElement('h3');
    rh.textContent = 'Paper ranking';
    resultsDiv.appendChild(rh);

    const ul = document.createElement('ul');
    data.ranking.forEach(r => {
      const li = document.createElement('li');
      li.textContent = `${r.title} (score: ${r.score}, published: ${r.published || 'N/A'})`;
      ul.appendChild(li);
    });
    resultsDiv.appendChild(ul);
  }

  // Research gaps
  if (data.research_gaps && data.research_gaps.text) {
    const gh = document.createElement('h3');
    gh.textContent = 'Research Gaps';
    resultsDiv.appendChild(gh);

    const gp = document.createElement('div');
    gp.innerHTML = marked.parse(data.research_gaps.text || '');
    resultsDiv.appendChild(gp);
  }

  // Method comparison table
  if (data.comparison && data.comparison.rows && data.comparison.rows.length) {
    const mh = document.createElement('h3');
    mh.textContent = 'Method comparison';
    resultsDiv.appendChild(mh);

    const table = document.createElement('table');
    table.className = 'method-table';

    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>Paper</th><th>Published</th><th>Method</th><th>Datasets</th><th>Results</th></tr>';
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    data.comparison.rows.forEach(row => {
      const tr = document.createElement('tr');
      const resStr = row.results ? JSON.stringify(row.results) : '';

      tr.innerHTML = `
        <td>${row.title}</td>
        <td>${row.published || ''}</td>
        <td>${row.method || ''}</td>
        <td>${(row.datasets || []).join(', ')}</td>
        <td>${resStr}</td>
      `;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    resultsDiv.appendChild(table);
  }

  // Per-paper details
  data.papers.forEach(p => {
    const card = document.createElement('div');
    card.className = 'paper';

    const title = document.createElement('h3');
    title.textContent = p.title || 'Untitled';
    card.appendChild(title);

    const authors = document.createElement('div');
    authors.textContent = 'Authors: ' + (p.authors || []).join(', ');
    card.appendChild(authors);

    const pub = document.createElement('div');
    pub.textContent = 'Published: ' + (p.published || 'N/A');
    card.appendChild(pub);

    if (p.paper_summary) {
      const ps = p.paper_summary;
      const oh = document.createElement('h4');
      oh.textContent = 'Paper Summary';
      card.appendChild(oh);

      const op = document.createElement('p');
      op.textContent = ps.overall_problem || '';
      card.appendChild(op);

      const om = document.createElement('p');
      om.textContent = 'Methods: ' + (ps.overall_methods || []).join(', ');
      card.appendChild(om);

      const od = document.createElement('p');
      od.textContent = 'Datasets: ' + (ps.overall_datasets || []).join(', ');
      card.appendChild(od);

      // const orDiv = document.createElement('pre');
      // orDiv.textContent = 'Results: ' + JSON.stringify(ps.overall_results || {});
      // card.appendChild(orDiv);
      const res = document.createElement('div');
      res.innerHTML = "<b>Results:</b><br/>";

      if (ps.overall_results && Object.keys(ps.overall_results).length > 0) {
        Object.entries(ps.overall_results).forEach(([k, v]) => {
          const line = document.createElement("div");
          line.textContent = `• ${k.toUpperCase()}: ${v}`;
          res.appendChild(line);
        });
      } else {
        res.textContent = "Results: Not explicitly reported";
      }

      card.appendChild(res);

    }

    resultsDiv.appendChild(card);
  });

  // References
  if (data.references && data.references.length) {
    const rh = document.createElement('h3');
    rh.textContent = 'References';
    resultsDiv.appendChild(rh);

    const ul = document.createElement('ul');
    data.references.forEach(r => {
      const li = document.createElement('li');
      const authors = (r.authors || []).join(', ');
      const year = r.published ? String(r.published).slice(0, 4) : 'n.d.';
      li.textContent = `${authors} (${year}). ${r.title}. [${r.url}]`;
      ul.appendChild(li);
    });
    resultsDiv.appendChild(ul);
  }
}

