const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const projectList = document.getElementById('project-list');
const newTitleInput = document.getElementById('new-title');
const addProjectButton = document.getElementById('add-project');
const smartNotesInput = document.getElementById('smart-notes');
const smartCreateButton = document.getElementById('smart-create');
const githubImportForm = document.getElementById('github-import-form');
const githubDraftPanel = document.getElementById('github-draft');
const githubStatus = document.getElementById('github-status');
const githubFeedbackInput = document.getElementById('github-feedback');
const sendGithubFeedbackButton = document.getElementById('send-github-feedback');
const sendGithubFeedbackBlindButton = document.getElementById('send-github-feedback-blind');
const approveGithubDraftButton = document.getElementById('approve-github-draft');
let githubSessionId = null;

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
  description.textContent = project.summary || project.description;

  const author = document.createElement('p');
  author.textContent = `Author: ${project.author}`;

  card.append(title, description, author);

  if (project.technologies) {
    const technologies = document.createElement('p');
    technologies.textContent = `Technologies: ${project.technologies}`;
    card.insertBefore(technologies, author);
  }

  if (project.difficulty) {
    const difficulty = document.createElement('p');
    difficulty.textContent = `Difficulty: ${project.difficulty}`;
    card.insertBefore(difficulty, author);
  }

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

  card.append(likes, upvoteButton);
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
        card.insertBefore(badge, card.querySelector('.like-count').closest('p'));
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

  smartCreateButton.addEventListener('click', async () => {
    smartCreateButton.disabled = true;

    try {
      const response = await fetch('/api/projects/smart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: smartNotesInput.value }),
      });

      if (!response.ok) {
        throw new Error(`Smart create request failed with status ${response.status}`);
      }

      const project = await response.json();
      projectList.append(createProjectCard(project));
      smartNotesInput.value = '';
      updateProjectList();
    } catch (error) {
      console.error('Unable to smart-create project:', error);
    } finally {
      smartCreateButton.disabled = false;
    }
  });
}

function showGithubDraft(draft) {
  document.getElementById('github-draft-title').textContent = draft.title;
  document.getElementById('github-draft-summary').textContent = draft.summary;
  document.getElementById('github-draft-technologies').textContent =
    draft.technologies.join(', ');
  document.getElementById('github-draft-difficulty').textContent = draft.difficulty;
  githubDraftPanel.classList.remove('hidden');
}

if (githubImportForm && githubDraftPanel && githubStatus) {
  githubImportForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const fetchButton = document.getElementById('fetch-github-draft');
    fetchButton.disabled = true;
    githubStatus.textContent = '';

    try {
      const response = await fetch('/api/projects/git-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner: document.getElementById('repo-owner').value,
          repo: document.getElementById('repo-name').value,
        }),
      });

      if (!response.ok) {
        throw new Error(`GitHub import failed with status ${response.status}`);
      }

      const result = await response.json();
      githubSessionId = result.session_id;
      showGithubDraft(result.draft);
      approveGithubDraftButton.disabled = false;
      githubStatus.textContent = '';
    } catch (error) {
      githubStatus.textContent = 'Unable to fetch a project draft. Check the repository and try again.';
      console.error('Unable to fetch GitHub project draft:', error);
    } finally {
      fetchButton.disabled = false;
    }
  });
}

if (
  githubDraftPanel &&
  githubStatus &&
  githubFeedbackInput &&
  sendGithubFeedbackButton &&
  sendGithubFeedbackBlindButton &&
  approveGithubDraftButton
) {
  sendGithubFeedbackButton.addEventListener('click', async () => {
    if (!githubSessionId) {
      return;
    }

    sendGithubFeedbackButton.disabled = true;
    githubStatus.textContent = '';
    try {
      const response = await fetch('/api/projects/git-refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: githubSessionId,
          feedback: githubFeedbackInput.value,
        }),
      });

      if (!response.ok) {
        throw new Error(`Draft refinement failed with status ${response.status}`);
      }

      const draft = await response.json();
      showGithubDraft(draft);
      githubFeedbackInput.value = '';
      approveGithubDraftButton.disabled = false;
    } catch (error) {
      githubStatus.textContent = 'Unable to update the draft. Please try again.';
      console.error('Unable to refine GitHub project draft:', error);
    } finally {
      sendGithubFeedbackButton.disabled = false;
    }
  });

  approveGithubDraftButton.addEventListener('click', async () => {
    if (!githubSessionId) {
      return;
    }

    approveGithubDraftButton.disabled = true;
    githubStatus.textContent = '';
    try {
      const response = await fetch('/api/projects/git-commit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: githubSessionId }),
      });

      if (!response.ok) {
        throw new Error(`Saving the project failed with status ${response.status}`);
      }

      const project = await response.json();
      projectList.append(createProjectCard(project));
      updateProjectList();
      githubDraftPanel.classList.add('hidden');
      githubSessionId = null;
      githubStatus.textContent = 'Project approved and saved.';
    } catch (error) {
      githubStatus.textContent = 'Unable to save the project. Please try again.';
      console.error('Unable to approve GitHub project draft:', error);
    } finally {
      approveGithubDraftButton.disabled = false;
    }
  });

  sendGithubFeedbackBlindButton.addEventListener('click', async () => {
    if (!githubSessionId) {
      return;
    }

    sendGithubFeedbackBlindButton.disabled = true;
    githubStatus.textContent = '';
    try {
      const response = await fetch('/api/projects/git-refine-blind', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: githubSessionId,
          feedback: githubFeedbackInput.value,
        }),
      });

      if (!response.ok) {
        throw new Error(`Blind draft refinement failed with status ${response.status}`);
      }

      const draft = await response.json();
      showGithubDraft(draft);
      githubFeedbackInput.value = '';
      approveGithubDraftButton.disabled = true;
      githubStatus.textContent = 'This preview was refined without history and is display-only.';
    } catch (error) {
      githubStatus.textContent = 'Unable to refine the draft without history. Please try again.';
      console.error('Unable to refine GitHub project draft without history:', error);
    } finally {
      sendGithubFeedbackBlindButton.disabled = false;
    }
  });
}
