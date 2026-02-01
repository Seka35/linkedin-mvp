// Recherche de prospects
document.getElementById('search-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = document.getElementById('search-query').value;
    const maxResults = document.getElementById('max-results').value;

    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div style="padding:1rem;color:var(--text-muted);">🔄 Recherche en cours sur Google/SearchAPI... Veuillez patienter.</div>';

    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, max_results: parseInt(maxResults) })
        });

        const data = await response.json();

        if (data.success) {
            resultsDiv.innerHTML = `
                <div style="padding:1rem; background:#e8f5e9; border-radius:4px; color:#2e7d32; margin-top:10px;">
                    ✅ <strong>Succès !</strong> ${data.found} profils trouvés pour "${query}".<br>
                    <a href="/prospects" style="color:#2e7d32; text-decoration:underline;">Voir la liste des prospects →</a>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `<div style="padding:1rem; color:red;">❌ ${data.error || 'Erreur inconnue'}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = '<div style="padding:1rem; color:red;">❌ Erreur réseau ou serveur. Vérifiez la console.</div>';
    }
});

// Envoyer demande de connexion
async function sendConnection(prospectId) {
    const message = prompt('Message personnalisé pour l\'invitation (Laisser vide pour envoyer sans note) :');

    if (message === null) return; // Annulé par l'utilisateur

    // Feedback visuel immédiat
    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = "⏳ Envoi...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prospect_id: prospectId, message: message || '' })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Demande de connexion envoyée avec succès !');
            location.reload();
        } else {
            alert('❌ Erreur : ' + (data.error || 'Impossible d\'envoyer la demande. Vérifiez les logs.'));
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (error) {
        alert('❌ Erreur technique : ' + error.message);
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Envoyer message
async function sendMessage(prospectId) {
    const message = prompt('Message à envoyer :');

    if (!message) return;

    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = "⏳ Envoi...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prospect_id: prospectId, message })
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ Message envoyé !');
            location.reload();
        } else {
            alert('❌ Erreur : ' + (data.error || 'Echec envoi message'));
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (error) {
        alert('❌ Erreur : ' + error.message);
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Afficher formulaire création campagne
function showCreateCampaign() {
    document.getElementById('create-campaign-form').style.display = 'block';
}

// Créer campagne
document.getElementById('campaign-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch('/api/campaign/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Campagne créée avec succès !');
            location.reload();
        }
    } catch (error) {
        alert('❌ Erreur : ' + error.message);
    }
});

// Lancer une campagne
async function runCampaign(campaignId) {
    if (!confirm('Lancer cette campagne maintenant ?')) return;

    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = "⏳ Lancement...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/campaign/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ campaign_id: campaignId })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Campagne lancée ! ' + result.message);
            location.reload();
        } else {
            alert('❌ Erreur : ' + (result.error || 'Échec'));
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (error) {
        alert('❌ Erreur : ' + error.message);
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Mettre en pause une campagne
async function pauseCampaign(campaignId) {
    if (!confirm('Mettre cette campagne en pause ?')) return;

    try {
        const response = await fetch('/api/campaign/pause', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ campaign_id: campaignId })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Campagne mise en pause');
            location.reload();
        }
    } catch (error) {
        alert('❌ Erreur : ' + error.message);
    }
}

// Reprendre une campagne
// Reprendre une campagne
async function resumeCampaign(campaignId) {
    if (!confirm('Reprendre cette campagne ?')) return;

    try {
        const response = await fetch('/api/campaign/resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ campaign_id: campaignId })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Campagne reprise');
            location.reload();
        }
    } catch (error) {
        alert('❌ Erreur : ' + error.message);
    }
}

// Gestion des logs
let logIntervals = {};

function toggleLogs(campaignId) {
    const container = document.getElementById(`logs-container-${campaignId}`);
    if (container.style.display === 'none') {
        container.style.display = 'block';
        startLogPolling(campaignId);
    } else {
        container.style.display = 'none';
        stopLogPolling(campaignId);
    }
}

function startLogPolling(campaignId) {
    // Poll immédiatement
    fetchLogs(campaignId);

    // Puis toutes les 2 secondes
    if (logIntervals[campaignId]) clearInterval(logIntervals[campaignId]);

    logIntervals[campaignId] = setInterval(() => {
        fetchLogs(campaignId);
    }, 2000);
}

function stopLogPolling(campaignId) {
    if (logIntervals[campaignId]) {
        clearInterval(logIntervals[campaignId]);
        delete logIntervals[campaignId];
    }
}

async function fetchLogs(campaignId) {
    try {
        const response = await fetch(`/api/campaign/logs/${campaignId}`);
        const data = await response.json();

        const logsContent = document.getElementById(`logs-content-${campaignId}`);
        if (data.logs) {
            logsContent.innerText = data.logs;
            // Scroll to bottom
            const container = document.getElementById(`logs-container-${campaignId}`);
            container.scrollTop = container.scrollHeight;
        }
    } catch (error) {
        console.error('Erreur logs:', error);
    }
}

// Auto-open logs when running
const originalRunCampaign = runCampaign;
runCampaign = async function (campaignId) {
    // Lancer la campagne (logique existante)
    if (!confirm('Lancer cette campagne maintenant ?')) return;

    const btn = event.target;
    const originalText = btn.innerText;
    btn.innerText = "⏳ Lancement...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/campaign/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ campaign_id: campaignId })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ Campagne lancée en arrière-plan ! Les logs vont s\'afficher.');
            // Ne pas recharger la page pour voir les logs
            btn.innerText = "🚀 En cours...";

            // Ouvrir les logs
            const container = document.getElementById(`logs-container-${campaignId}`);
            container.style.display = 'block';
            startLogPolling(campaignId);

        } else {
            alert('❌ Erreur : ' + (result.error || 'Échec'));
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (error) {
        alert('❌ Erreur : ' + error.message);
        btn.innerText = originalText;
        btn.disabled = false;
    }
};
