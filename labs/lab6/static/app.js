const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const cards = Array.from(document.querySelectorAll('.card'));

function updateProjectList() {
  const query = filterInput.value.trim().toLowerCase();
  const visibleTitles = [];
  let visibleCount = 0;

  cards.forEach((card) => {
    const text = card.textContent.toLowerCase();
    const matches = query === '' || text.includes(query);

    card.classList.toggle('hidden', !matches);

    if (matches) {
      visibleCount += 1;
      visibleTitles.push(card.querySelector('h3').textContent.trim());
    }
  });

  projectCount.textContent = `Showing ${visibleCount} of ${cards.length} projects`;
  console.log(visibleTitles);
}

if (filterInput && projectCount && cards.length > 0) {
  filterInput.addEventListener('input', updateProjectList);
  updateProjectList();
}
