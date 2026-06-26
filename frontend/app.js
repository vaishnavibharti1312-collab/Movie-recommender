const API_URL = window.location.origin;

// State Variables
let systemMode = 'viewer'; // 'viewer' or 'business'
let activeUserProfileId = 3; // Default Viewer #3
let chartInstances = {};
let usersList = [];
let moviesList = [];
let latestSearchUrl = '';

// Initialize Page
document.addEventListener('DOMContentLoaded', async () => {
    // Start system clock in sidebar
    updateClock();
    setInterval(updateClock, 60000);
    
    // Load users list for profile selector
    await loadUserProfiles();
    
    // Switch to initial mode
    switchSystemMode('viewer');
    
    // Initialize movie list for ad selector dropdown
    await loadAdMovieOptions();
    
    // Fetch chatbot AI agent status
    checkChatbotStatus();
});

function updateClock() {
    const now = new Date();
    let hours = now.getHours().toString().padStart(2, '0');
    let minutes = now.getMinutes().toString().padStart(2, '0');
    const timeSpan = document.getElementById('system-time');
    if (timeSpan) timeSpan.innerText = `${hours}:${minutes}`;
}

async function checkChatbotStatus() {
    try {
        const response = await fetch(`${API_URL}/chat/status`);
        if (response.ok) {
            const data = await response.json();
            const viewerBadge = document.getElementById('viewer-chat-status');
            const bizBadge = document.getElementById('biz-chat-status');
            
            if (data.agent_active) {
                if (viewerBadge) {
                    viewerBadge.innerText = 'AI Agent';
                    viewerBadge.className = 'status-badge active';
                }
                if (bizBadge) {
                    bizBadge.innerText = 'AI Agent';
                    bizBadge.className = 'status-badge active';
                }
            } else {
                if (viewerBadge) {
                    viewerBadge.innerText = 'Local';
                    viewerBadge.className = 'status-badge fallback';
                }
                if (bizBadge) {
                    bizBadge.innerText = 'Local';
                    bizBadge.className = 'status-badge fallback';
                }
            }
        }
    } catch (err) {
        console.error('Error checking chatbot status:', err);
    }
}

// 1. Profile Selector Loading
async function loadUserProfiles() {
    try {
        const response = await fetch(`${API_URL}/movies`); // get users is not exposed but we know there are 48 viewers (ID 3 to 50)
        // Let's generate user selector lists based on mock database users (viewers are user_id 3 to 50)
        const select = document.getElementById('user-profile-select');
        select.innerHTML = '';
        
        for (let i = 3; i <= 50; i++) {
            const opt = document.createElement('option');
            opt.value = i;
            opt.innerText = `Viewer #${i}`;
            if (i === activeUserProfileId) opt.selected = true;
            select.appendChild(opt);
        }
    } catch (err) {
        console.error("Error loading profile lists", err);
    }
}

function onUserProfileChange() {
    const select = document.getElementById('user-profile-select');
    activeUserProfileId = parseInt(select.value);
    
    // Re-render recommendations if page active
    if (systemMode === 'viewer') {
        const activeSubPage = document.querySelector('.sub-page.active').id;
        if (activeSubPage === 'page-viewer-recs') {
            loadRecommendationsPage();
        } else if (activeSubPage === 'page-viewer-discover') {
            triggerSearch();
        }
    }
}

// 2. Navigation Actions
function switchSystemMode(mode) {
    systemMode = mode;
    
    // Toggle active link groups
    document.getElementById('nav-group-viewer').classList.toggle('active', mode === 'viewer');
    document.getElementById('nav-group-business').classList.toggle('active', mode === 'business');
    
    // Toggle Sidebar Profile Selector visibility (only make sense for user recommendations)
    document.getElementById('sidebar-profile-box').style.display = mode === 'viewer' ? 'flex' : 'none';
    
    // Toggle active buttons style
    document.getElementById('btn-mode-viewer').classList.toggle('active', mode === 'viewer');
    document.getElementById('btn-mode-business').classList.toggle('active', mode === 'business');
    
    // Set initial page
    if (mode === 'viewer') {
        showSubPage('viewer-discover');
    } else {
        showSubPage('biz-overview');
    }
}

function showSubPage(pageKey, event = null) {
    // Hide all sub-pages
    document.querySelectorAll('.sub-page').forEach(el => el.classList.remove('active'));
    
    // Activate target
    const targetId = `page-${pageKey}`;
    const targetPage = document.getElementById(targetId);
    if (targetPage) targetPage.classList.add('active');
    
    // Update navigation active styles
    if (event) {
        document.querySelectorAll('.sidebar-nav .nav-link').forEach(el => el.classList.remove('active'));
        event.currentTarget.classList.add('active');
    } else {
        // Find link matching pageKey manually
        document.querySelectorAll('.sidebar-nav .nav-link').forEach(el => {
            const clickAttr = el.getAttribute('onclick');
            if (clickAttr && clickAttr.includes(pageKey)) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    }
    
    // Update top bar title & description
    updateTopBarText(pageKey);
    
    // Route page loading operations
    routePageLoading(pageKey);
}

function updateTopBarText(pageKey) {
    const title = document.getElementById('page-title');
    const subtitle = document.getElementById('page-subtitle');
    
    switch(pageKey) {
        case 'viewer-discover':
            title.innerText = "Discover Content Library";
            subtitle.innerText = "Filter and explore our complete cross-platform movie catalog";
            break;
        case 'viewer-recs':
            title.innerText = "Personalized Matching Suite";
            subtitle.innerText = "AI-powered content matching based on your watch profile and rating history";
            break;
        case 'viewer-chatbot':
            title.innerText = "Conversational Assistant";
            subtitle.innerText = "Ask details, recommend genres, or query movie streaming links in natural language";
            break;
        case 'biz-overview':
            title.innerText = "Executive BI Summary";
            subtitle.innerText = "High-level platform KPI analytics and core subscriber churn risks";
            break;
        case 'biz-content':
            title.innerText = "Content Performance Hub";
            subtitle.innerText = "Genre analysis, ratings averages, and platform licensing distributions";
            break;
        case 'biz-churn':
            title.innerText = "Subscriber Churn Analytics";
            subtitle.innerText = "Machine learning risk assessments, engagement factors, and customer retention recommendations";
            break;
        case 'biz-trends':
            title.innerText = "Google Trends & Forecasting";
            subtitle.innerText = "Linear regression models predicting next-quarter genre popularity and acquisition advice";
            break;
        case 'biz-ads':
            title.innerText = "Ad Placement Target Optimizer";
            subtitle.innerText = "Model-based ad campaign target matching and suitability score simulator";
            break;
        case 'biz-chatbot':
            title.innerText = "Enterprise AI Analyst";
            subtitle.innerText = "Ask operational questions, summarize churn, or fetch data breakdowns";
            break;
    }
}

function routePageLoading(pageKey) {
    // Clear old charts to prevent duplicate canvases
    destroyAllCharts();
    
    switch(pageKey) {
        case 'viewer-discover':
            triggerSearch();
            break;
        case 'viewer-recs':
            loadRecommendationsPage();
            break;
        case 'biz-overview':
            loadBIOverviewPage();
            break;
        case 'biz-content':
            loadBIContentPage();
            break;
        case 'biz-churn':
            loadBIChurnPage();
            break;
        case 'biz-trends':
            loadBITrendsPage();
            break;
        case 'biz-ads':
            initializeAdSimulation();
            break;
    }
}

// 3. Destroy ChartJS instances to prevent canvas hover rendering crashes
function destroyAllCharts() {
    Object.keys(chartInstances).forEach(key => {
        if (chartInstances[key]) {
            chartInstances[key].destroy();
            chartInstances[key] = null;
        }
    });
}

// 4. VIEWER DISCOVER PAGES
async function triggerSearch() {
    const titleVal = document.getElementById('filter-title').value.trim();
    const genreVal = document.getElementById('filter-genre').value;
    const platformVal = document.getElementById('filter-platform').value;
    const langVal = document.getElementById('filter-lang').value;
    
    let url = `${API_URL}/movies/search?`;
    if (titleVal) url += `title=${encodeURIComponent(titleVal)}&`;
    if (genreVal) url += `genre=${encodeURIComponent(genreVal)}&`;
    if (platformVal) url += `platform=${encodeURIComponent(platformVal)}&`;
    if (langVal) url += `language=${encodeURIComponent(langVal)}&`;
    
    latestSearchUrl = url;
    const currentUrl = url;
    
    try {
        const response = await fetch(url);
        const movies = await response.json();
        
        // Ignore response if a newer search has been initiated
        if (latestSearchUrl !== currentUrl) {
            return;
        }
        
        const grid = document.getElementById('movies-discover-grid');
        grid.innerHTML = '';
        
        if (movies.length === 0) {
            grid.innerHTML = '<p class="text-secondary" style="grid-column: 1/-1; text-align: center; padding: 3rem;">No movies matched your filters. Try widening your search.</p>';
            return;
        }
        
        movies.forEach(movie => {
            const card = renderMovieCard(movie);
            grid.appendChild(card);
        });
    } catch (err) {
        if (latestSearchUrl === currentUrl) {
            console.error("Error searching movies", err);
        }
    }
}

// 5. Render Movie Card Helper
function renderMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    card.setAttribute('onclick', `openMovieModal(${movie.movie_id})`);
    
    const platformsBadges = movie.platforms.map(p => `<span class="badge platform">${p}</span>`).join('');
    
    const reasonText = movie.reason ? `<div class="movie-card-reason">${movie.reason}</div>` : '';
    const scoreBadge = movie.score ? `<span class="badge success" style="margin-top: 4px;">Match: ${(movie.score*100).toFixed(0)}%</span>` : '';
    
    card.innerHTML = `
        <div class="movie-poster-box">
            <img src="${movie.poster_url}" alt="${movie.title}" class="movie-poster" onerror="this.src='https://via.placeholder.com/300x450/1e293b/f8fafc?text=${encodeURIComponent(movie.title)}'">
            <div class="movie-card-overlay">
                <span class="badge primary">⭐ ${movie.vote_average.toFixed(1)}</span>
                ${scoreBadge}
            </div>
        </div>
        <div class="movie-card-info">
            <h4 class="movie-card-title">${movie.title}</h4>
            <div class="movie-card-meta">
                <span>${movie.release_year}</span>
                <span>${movie.language}</span>
            </div>
            <div class="badge-list mt-2">
                ${movie.genres.split(',').slice(0,2).map(g => `<span class="badge">${g.strip ? g.strip() : g}</span>`).join('')}
            </div>
            <div class="badge-list mt-2">
                ${platformsBadges}
            </div>
            ${reasonText}
        </div>
    `;
    return card;
}

// 6. VIEWER RECOMMENDATIONS PAGE
async function loadRecommendationsPage() {
    try {
        // A. Fetch personalized recommendations
        const pRecsResponse = await fetch(`${API_URL}/recommendations/user/${activeUserProfileId}`);
        const pRecs = await pRecsResponse.json();
        
        const pGrid = document.getElementById('movies-personalized-grid');
        pGrid.innerHTML = '';
        if (pRecs.length === 0) {
            pGrid.innerHTML = '<p class="text-secondary">No recommendations calculated yet. Create watch history by leaving ratings.</p>';
        } else {
            pRecs.forEach(movie => {
                pGrid.appendChild(renderMovieCard(movie));
            });
        }
        
        // B. Fetch general trending
        const trendingResponse = await fetch(`${API_URL}/movies/trending?limit=4`);
        const trending = await trendingResponse.json();
        
        const tGrid = document.getElementById('movies-trending-grid');
        tGrid.innerHTML = '';
        trending.forEach(movie => {
            tGrid.appendChild(renderMovieCard(movie));
        });
    } catch(err) {
        console.error("Error loading recommendations", err);
    }
}

// 7. VIEWER CHATBOT PAGE
async function sendViewerChat() {
    const input = document.getElementById('viewer-chat-input');
    const query = input.value.trim();
    if (!query) return;
    
    appendMessage('viewer-chat-display', 'user', query);
    input.value = '';
    
    try {
        const response = await fetch(`${API_URL}/chat/user?query=${encodeURIComponent(query)}&user_id=${activeUserProfileId}`, {
            method: 'POST'
        });
        const data = await response.json();
        appendMessage('viewer-chat-display', 'bot', data.response);
    } catch(err) {
        appendMessage('viewer-chat-display', 'bot', 'Sorry, my movie database system is currently experiencing issues. Please try again.');
    }
}

function handleViewerChatKey(e) {
    if (e.key === 'Enter') sendViewerChat();
}

function sendQuickQuery(text) {
    const input = document.getElementById('viewer-chat-input');
    input.value = text;
    sendViewerChat();
}

function appendMessage(containerId, sender, text) {
    const display = document.getElementById(containerId);
    const bubble = document.createElement('div');
    bubble.className = `message ${sender}`;
    bubble.innerHTML = text;
    display.appendChild(bubble);
    display.scrollTop = display.scrollHeight;
}

// 8. MOVIE DETAIL MODAL
async function openMovieModal(movieId) {
    try {
        const response = await fetch(`${API_URL}/movies/${movieId}`);
        const movie = await response.json();
        
        const modal = document.getElementById('movie-modal');
        const modalContent = document.getElementById('modal-body-content');
        
        const platBadges = movie.platforms.map(p => `<span class="badge platform">${p}</span>`).join('');
        
        // Sentiment Ratio markup
        const sent = movie.sentiment_summary;
        let sentimentRatioMarkup = '<p class="text-muted">No audience reviews available yet.</p>';
        if (sent.total_reviews > 0) {
            sentimentRatioMarkup = `
                <div class="sentiment-meter-box mt-2">
                    <span style="font-size: 0.8rem; font-weight: bold;">Audience Sentiment:</span>
                    <div class="progress-bar-container mt-1" style="height: 10px;">
                        <div class="progress-bar success" style="width: ${sent.positive_ratio}%" title="Positive: ${sent.positive_ratio}%"></div>
                        <div class="progress-bar warning" style="width: ${sent.neutral_ratio}%" title="Neutral: ${sent.neutral_ratio}%"></div>
                        <div class="progress-bar danger" style="width: ${sent.negative_ratio}%" title="Negative: ${sent.negative_ratio}%"></div>
                    </div>
                    <div class="meta-row mt-1" style="font-size: 0.75rem; justify-content: space-between;">
                        <span class="text-success">Positive: ${sent.positive_ratio}%</span>
                        <span class="text-warning">Neutral: ${sent.neutral_ratio}%</span>
                        <span class="text-danger">Negative: ${sent.negative_ratio}%</span>
                    </div>
                </div>
            `;
        }
        
        // Render reviews list
        const reviewsMarkup = movie.reviews.map(r => `
            <div class="modal-review-item">
                <span class="badge ${r.sentiment === 'positive' ? 'success' : r.sentiment === 'negative' ? 'danger' : 'warning'}" style="float: right;">
                    ${r.sentiment}
                </span>
                <p><em>"${r.text}"</em></p>
            </div>
        `).join('');
        
        // Fetch content similar recommendations
        const simResponse = await fetch(`${API_URL}/recommendations/similar/${movie.movie_id}`);
        const sims = await simResponse.json();
        const simCards = sims.map(sm => `
            <div class="top-movie-item" style="cursor: pointer;" onclick="openMovieModal(${sm.movie_id})">
                <span class="title">${sm.title}</span>
                <span class="badge platform">⭐ ${sm.vote_average.toFixed(1)}</span>
            </div>
        `).join('');

        modalContent.innerHTML = `
            <div class="modal-poster-col">
                <img src="${movie.poster_url}" alt="${movie.title}" onerror="this.src='https://via.placeholder.com/300x450/1e293b/f8fafc?text=${encodeURIComponent(movie.title)}'">
                ${sentimentRatioMarkup}
            </div>
            <div class="modal-info-col">
                <h2>${movie.title}</h2>
                <div class="meta-row">
                    <span class="badge primary">⭐ ${movie.vote_average.toFixed(1)} Rating</span>
                    <span class="badge">Popularity: ${movie.popularity.toFixed(0)}</span>
                    <span class="badge">${movie.release_year}</span>
                    <span class="badge">${movie.runtime} Min</span>
                    <span class="badge">${movie.language}</span>
                </div>
                <div class="meta-row" style="font-size: 0.85rem; color: var(--text-secondary); margin-top: -0.5rem; margin-bottom: 0.25rem;">
                    <span><strong>Director:</strong> ${movie.crew || 'N/A'}</span>
                    <span style="margin-left: 1.5rem;"><strong>Starring:</strong> ${movie.cast || 'N/A'}</span>
                </div>
                <div class="badge-list">
                    ${movie.genres.split(',').map(g => `<span class="badge">${g.strip ? g.strip() : g}</span>`).join('')}
                </div>
                
                <div>
                    <h4 class="mb-1" style="font-size: 0.9rem;">Overview</h4>
                    <p class="modal-overview">${movie.overview}</p>
                </div>
                
                <div>
                    <h4 class="mb-1" style="font-size: 0.9rem;">Available to Stream On:</h4>
                    <div class="badge-list mt-1">
                        ${platBadges ? platBadges : '<span class="text-secondary">Not available on standard platforms</span>'}
                    </div>
                </div>

                <div class="modal-reviews-box">
                    <h4>Audience Reviews (${sent.total_reviews})</h4>
                    <div style="max-height: 180px; overflow-y: auto;">
                        ${reviewsMarkup ? reviewsMarkup : '<p class="text-secondary" style="font-size: 0.8rem;">No reviews left yet.</p>'}
                    </div>
                </div>

                <div class="modal-similar-box mt-2">
                    <h4 class="mb-1" style="font-size: 0.9rem;">Similar Content Discoveries</h4>
                    <div class="top-movies-list mt-1">
                        ${simCards ? simCards : '<p class="text-secondary" style="font-size: 0.8rem;">No similar recommendations found.</p>'}
                    </div>
                </div>
            </div>
        `;
        
        modal.classList.add('open');
    } catch(err) {
        console.error("Error opening movie detail", err);
    }
}

function closeMovieModal(e) {
    if (e === null || e.target === document.getElementById('movie-modal')) {
        document.getElementById('movie-modal').classList.remove('open');
    }
}

// 9. BUSINESS OVERVIEW PAGE
async function loadBIOverviewPage() {
    try {
        const response = await fetch(`${API_URL}/analytics/dashboard`);
        const stats = await response.json();
        
        document.getElementById('kpi-movies').innerText = stats.total_movies;
        document.getElementById('kpi-users').innerText = stats.total_users;
        document.getElementById('kpi-rating').innerText = stats.average_rating.toFixed(1);
        document.getElementById('kpi-sentiment').innerText = `${stats.sentiment_ratios.positive.toFixed(0)}%`;
        
        // Churn widgets
        const cs = stats.churn_risk_summary;
        const totalChurn = cs.High + cs.Medium + cs.Low;
        document.getElementById('widget-churn-high').innerText = cs.High;
        document.getElementById('widget-churn-med').innerText = cs.Medium;
        document.getElementById('widget-churn-low').innerText = cs.Low;
        
        if (totalChurn > 0) {
            document.getElementById('churn-progress-high').style.width = `${(cs.High / totalChurn * 100)}%`;
            document.getElementById('churn-progress-med').style.width = `${(cs.Medium / totalChurn * 100)}%`;
            document.getElementById('churn-progress-low').style.width = `${(cs.Low / totalChurn * 100)}%`;
        }
        
        // Fetch trending content widget
        const trendResponse = await fetch(`${API_URL}/movies/trending?limit=3`);
        const trendMovies = await trendResponse.json();
        
        const listDiv = document.getElementById('widget-top-movies');
        listDiv.innerHTML = '';
        
        trendMovies.forEach(m => {
            const item = document.createElement('div');
            item.className = 'top-movie-item';
            item.innerHTML = `
                <span class="title">${m.title}</span>
                <span class="badge platform">Popularity: ${m.popularity.toFixed(0)}</span>
            `;
            listDiv.appendChild(item);
        });
    } catch(err) {
        console.error("Error loading BI Overview", err);
    }
}

// 10. BUSINESS CONTENT PERFORMANCE (ChartsJS)
async function loadBIContentPage() {
    try {
        const response = await fetch(`${API_URL}/analytics/dashboard`);
        const stats = await response.json();
        
        // A. Genre Distribution Chart (Bar)
        const genreLabels = stats.genre_distribution.map(d => d.genre);
        const genreCounts = stats.genre_distribution.map(d => d.count);
        const genreRatings = stats.genre_distribution.map(d => d.avg_rating);
        
        const ctxGenre = document.getElementById('chart-genre-distribution').getContext('2d');
        chartInstances['genre-dist'] = new Chart(ctxGenre, {
            type: 'bar',
            data: {
                labels: genreLabels,
                datasets: [{
                    label: 'Movie Count',
                    data: genreCounts,
                    backgroundColor: 'rgba(59, 130, 246, 0.65)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
        
        // B. Average Ratings Chart (Horizontal Bar)
        const ctxRatings = document.getElementById('chart-genre-ratings').getContext('2d');
        chartInstances['genre-ratings'] = new Chart(ctxRatings, {
            type: 'bar',
            data: {
                labels: genreLabels,
                datasets: [{
                    label: 'Average Rating (Out of 10)',
                    data: genreRatings,
                    backgroundColor: 'rgba(139, 92, 246, 0.65)',
                    borderColor: '#8b5cf6',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { min: 5, max: 10, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    y: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
        
        // C. Platform counts chart (Bar)
        const platLabels = stats.platform_distribution.map(d => d.platform_name);
        const platCounts = stats.platform_distribution.map(d => d.movie_count);
        
        const ctxPlat = document.getElementById('chart-platform-distribution').getContext('2d');
        chartInstances['plat-dist'] = new Chart(ctxPlat, {
            type: 'bar',
            data: {
                labels: platLabels,
                datasets: [{
                    label: 'Movie Library Count',
                    data: platCounts,
                    backgroundColor: 'rgba(16, 185, 129, 0.65)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
        
        // D. Review Sentiment (Pie)
        const sent = stats.sentiment_ratios;
        const ctxSent = document.getElementById('chart-sentiment-distribution').getContext('2d');
        chartInstances['sent-dist'] = new Chart(ctxSent, {
            type: 'pie',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: [sent.positive, sent.neutral, sent.negative],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.75)',
                        'rgba(245, 158, 11, 0.75)',
                        'rgba(239, 68, 68, 0.75)'
                    ],
                    borderColor: '#0d1426',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { color: '#94a3b8', boxWidth: 15 } }
                }
            }
        });
    } catch(err) {
        console.error("Error loading BI charts", err);
    }
}

// 11. BUSINESS SUBSCRIBER CHURN HUB
async function loadBIChurnPage() {
    try {
        const response = await fetch(`${API_URL}/churn/high-risk`);
        const list = await response.json();
        
        document.getElementById('churn-high-risk-badge').innerText = `${list.length} Users Flagged`;
        
        const tbody = document.getElementById('churn-subscribers-table');
        tbody.innerHTML = '';
        
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 2rem; color:var(--text-secondary);">No high-risk subscribers found. Churn models healthy.</td></tr>';
            return;
        }
        
        list.forEach(c => {
            const tr = document.createElement('tr');
            const features = c.features;
            
            tr.innerHTML = `
                <td><strong>#${c.user_id}</strong></td>
                <td>${c.name}</td>
                <td><span class="badge danger" style="font-weight:bold;">${(c.churn_probability*100).toFixed(0)}%</span></td>
                <td>${features.watch_time} hrs</td>
                <td>${features.logins}</td>
                <td>$${features.monthly_charges}</td>
                <td><span style="color: ${features.support_complaints >= 3 ? 'var(--danger)' : 'white'}">${features.support_complaints}</span></td>
                <td>
                    <button class="action-btn" onclick="triggerRetentionCampaign(${c.user_id})">Trigger Campaign</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(err) {
        console.error("Error loading BI Churn page", err);
    }
}

// Click Trigger Retention Campaign: Fetch custom ML response and display as premium toast!
async function triggerRetentionCampaign(userId) {
    try {
        const response = await fetch(`${API_URL}/churn/predict?customer_id=${userId}`, { method: 'POST' });
        const res = await response.json();
        
        showToastNotification(
            `Retention Campaign Triggered (User #${userId})`,
            `<strong>Identified Factors:</strong> ${res.important_features.join(', ')}<br><strong>Retention Strategy:</strong> ${res.retention_action}`
        );
    } catch(err) {
        console.error("Error launching campaign", err);
    }
}

function showToastNotification(title, message) {
    // Remove existing toast if present
    const old = document.getElementById('toast-notification');
    if (old) old.remove();
    
    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = 'toast-notice';
    toast.innerHTML = `
        <button class="toast-close" onclick="this.parentElement.remove()">✕ Close</button>
        <div class="toast-title">✨ ${title}</div>
        <div class="toast-msg">${message}</div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 8 seconds
    setTimeout(() => {
        if (toast) toast.remove();
    }, 8000);
}

// 12. BUSINESS MARKET TRENDS FORECASTING PAGE (ChartJS line forecasting)
async function loadBITrendsPage() {
    try {
        const response = await fetch(`${API_URL}/analytics/trends`);
        const data = await response.json();
        
        // Update Growing/Declining badges in HTML
        const growBox = document.getElementById('trends-growing-genres');
        growBox.innerHTML = data.top_growing.map(g => `<span class="badge success" style="font-size:0.75rem; padding: 4px 10px;">${g}</span>`).join('');
        
        const declineBox = document.getElementById('trends-declining-genres');
        declineBox.innerHTML = data.top_declining.map(g => `<span class="badge danger" style="font-size:0.75rem; padding: 4px 10px;">${g}</span>`).join('');
        
        document.getElementById('trends-strategy-text').innerText = data.investment_recommendation;
        
        // Generate Line Forecasting Chart
        const datasets = [];
        const colors = {
            "Sci-Fi": "#3b82f6",
            "Action": "#8b5cf6",
            "Drama": "#f59e0b",
            "Comedy": "#ec4899",
            "Thriller": "#10b981",
            "Romance": "#ef4444",
            "Horror": "#06b6d4"
        };
        
        let allDates = [];
        const forecasts = data.forecasts;
        
        Object.keys(forecasts).forEach(genre => {
            const history = forecasts[genre].history;
            const forecast = forecasts[genre].forecast;
            
            // Collect all dates
            const dates = history.map(h => h.date).concat(forecast.map(f => f.date));
            if (dates.length > allDates.length) allDates = dates;
            
            // Map scores
            const scores = history.map(h => h.score).concat(forecast.map(f => f.score));
            
            datasets.push({
                label: genre,
                data: scores,
                borderColor: colors[genre] || '#ffffff',
                borderWidth: 2,
                pointRadius: history.map(h => 2).concat(forecast.map(f => 4)), // Make forecast points look slightly different
                pointBackgroundColor: history.map(h => colors[genre]).concat(forecast.map(f => "#ffffff")),
                fill: false,
                tension: 0.15
            });
        });
        
        // Keep only every 2nd date label on X axis to prevent crowding
        const formattedLabels = allDates.map(d => {
            const dateObj = new Date(d);
            return dateObj.toLocaleDateString('en-US', { month: 'short', year: '25' === d.slice(2,4) ? undefined : '2-digit' });
        });

        const ctxForecast = document.getElementById('chart-genre-forecasting').getContext('2d');
        chartInstances['genre-forecasting'] = new Chart(ctxForecast, {
            type: 'line',
            data: {
                labels: formattedLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: '#94a3b8', boxWidth: 12 } }
                },
                scales: {
                    y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });
        
    } catch(err) {
        console.error("Error loading BI trends forecasting", err);
    }
}

// 13. AD PLACEMENT SIMULATOR
async function loadAdMovieOptions() {
    try {
        const response = await fetch(`${API_URL}/movies?limit=100`);
        moviesList = await response.json();
        
        const select = document.getElementById('ad-movie-select');
        select.innerHTML = '<option value="">-- Choose content --</option>';
        moviesList.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.movie_id;
            opt.innerText = m.title;
            select.appendChild(opt);
        });
    } catch(err) {
        console.error("Error loading ad selector list", err);
    }
}

function initializeAdSimulation() {
    const select = document.getElementById('ad-movie-select');
    if (select.value === '') {
        // default select first movie
        if (select.options.length > 1) {
            select.selectedIndex = 1;
            runAdSimulation();
        }
    }
}

async function runAdSimulation() {
    const movieId = document.getElementById('ad-movie-select').value;
    const detailsDiv = document.getElementById('ad-movie-details');
    const resultsDiv = document.getElementById('ad-campaigns-list');
    
    if (!movieId) {
        detailsDiv.style.display = 'none';
        resultsDiv.innerHTML = '<p class="text-secondary">Please select a movie from the dropdown.</p>';
        return;
    }
    
    try {
        // A. Load movie overview
        const movie = moviesList.find(m => m.movie_id == movieId);
        if (movie) {
            document.getElementById('ad-movie-title').innerText = movie.title;
            document.getElementById('ad-movie-genre').innerText = movie.genres.split(',')[0];
            document.getElementById('ad-movie-rating').innerText = `⭐ ${movie.vote_average.toFixed(1)}`;
            document.getElementById('ad-movie-runtime').innerText = `${movie.runtime} Min`;
            document.getElementById('ad-movie-desc').innerText = movie.overview;
            detailsDiv.style.display = 'block';
        }
        
        // B. Fetch ad optimization strategy
        const response = await fetch(`${API_URL}/analytics/ad-placement/${movieId}`);
        const campaigns = await response.json();
        
        resultsDiv.innerHTML = '';
        campaigns.forEach(c => {
            const card = document.createElement('div');
            card.className = 'campaign-card';
            
            // Set score color based on value
            const scoreColor = c.suitability_score >= 70 ? 'var(--success)' : c.suitability_score >= 45 ? 'var(--warning)' : 'var(--text-muted)';
            
            card.innerHTML = `
                <div class="campaign-top">
                    <span class="campaign-title">${c.category} Campaign</span>
                    <span class="suitability-score" style="color: ${scoreColor}">${c.suitability_score.toFixed(0)}% Suitability</span>
                </div>
                <div class="campaign-meta">
                    <strong>Target Segment:</strong> ${c.target_audience}
                </div>
                <div class="campaign-reason">
                    <strong>Placement Alignment:</strong> ${c.reason}
                </div>
            `;
            resultsDiv.appendChild(card);
        });
    } catch(err) {
        console.error("Error executing ad simulator", err);
    }
}

// 14. BUSINESS AI CHATBOT PAGE
async function sendBizChat() {
    const input = document.getElementById('biz-chat-input');
    const query = input.value.trim();
    if (!query) return;
    
    appendMessage('biz-chat-display', 'user', query);
    input.value = '';
    
    try {
        const response = await fetch(`${API_URL}/chat/company?query=${encodeURIComponent(query)}`, {
            method: 'POST'
        });
        const data = await response.json();
        appendMessage('biz-chat-display', 'bot', data.response);
    } catch(err) {
        appendMessage('biz-chat-display', 'bot', 'Failed to retrieve analyst insights. Database query timed out.');
    }
}

function handleBizChatKey(e) {
    if (e.key === 'Enter') sendBizChat();
}

function sendBizQuickQuery(text) {
    const input = document.getElementById('biz-chat-input');
    input.value = text;
    sendBizChat();
}
