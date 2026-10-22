const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const projectList = document.getElementById('project-list');
const newTitleInput = document.getElementById('new-title');
const addProjectButton = document.getElementById('add-project');

function updateProjectList() {
  const cards = Array.from(document.querySelectorAll('.card'));
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

function createProjectCard(project) {
  const card = document.createElement('article');
  card.className = 'card';
  card.dataset.projectId = project.id;

  const title = document.createElement('h3');
  title.className = 'heading heading-card';
  title.textContent = project.title;

  const description = document.createElement('p');
  description.textContent = project.description;

  if (project.likes > 10) {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'Trending';
    card.append(badge);
  }

  const likes = document.createElement('p');
  likes.append('Likes: ');
  const likeCount = document.createElement('span');
  likeCount.className = 'like-count';
  likeCount.textContent = project.likes;
  likes.append(likeCount);

  const upvoteButton = document.createElement('button');
  upvoteButton.className = 'upvote-btn button';
  upvoteButton.type = 'button';
  upvoteButton.textContent = 'Upvote';

  card.append(title, description, likes, upvoteButton);
  return card;
}

if (filterInput && projectCount && projectList) {
  filterInput.addEventListener('input', updateProjectList);
  updateProjectList();
}

if (projectList) {
  projectList.addEventListener('click', async (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }

    const upvoteButton = event.target.closest('.upvote-btn');
    if (!upvoteButton) {
      return;
    }

    const card = upvoteButton.closest('.card');
    if (!card) {
      return;
    }

    const likeCount = card.querySelector('.like-count');
    upvoteButton.disabled = true;

    try {
      const response = await fetch(
        `/api/projects/${card.dataset.projectId}/upvote`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(`Upvote request failed with status ${response.status}`);
      }

      const result = await response.json();
      likeCount.textContent = result.likes;
      let badge = card.querySelector('.badge');
      if (result.likes > 10 && !badge) {
        badge = document.createElement('span');
        badge.className = 'badge';
        badge.textContent = 'Trending';
        card.insertBefore(badge, card.children[2]);
      } else if (result.likes <= 10 && badge) {
        badge.remove();
      }
    } catch (error) {
      console.error('Unable to upvote project:', error);
    } finally {
      upvoteButton.disabled = false;
    }
  });

  addProjectButton.addEventListener('click', async () => {
    addProjectButton.disabled = true;

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitleInput.value }),
      });

      if (!response.ok) {
        throw new Error(`Create project request failed with status ${response.status}`);
      }

      const project = await response.json();
      projectList.append(createProjectCard(project));
      newTitleInput.value = '';
      updateProjectList();
    } catch (error) {
      console.error('Unable to create project:', error);
    } finally {
      addProjectButton.disabled = false;
    }
  });
}
