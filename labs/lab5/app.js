const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const cards = Array.from(document.querySelectorAll('.card'));

function updateProjectList() {
  const query = filterInput.value.trim().toLowerCase(); // hand-edited by JM
  let visibleCount = 0;

  cards.forEach((card) => {
    const text = card.textContent.toLowerCase(); //hand-edited by JM    
    const matches = query === '' || text.includes(query);

    card.classList.toggle('is-hidden', !matches);

    if (matches) {
      visibleCount += 1;
    }
  });

  projectCount.textContent = `Showing ${visibleCount} of ${cards.length} projects`;
}

if (filterInput && projectCount && cards.length > 0) {
  filterInput.addEventListener('input', updateProjectList);
  updateProjectList();
}
