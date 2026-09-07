/* ============================================================
   musique.js — logique JS de la page Musiques (ActuWebApp)
   À placer dans : static/js/musique.js
   ============================================================ */
(function () {

    /* ── CSRF global pour htmx ──
       Au lieu de répéter {{ csrf_token }} dans hx-headers sur chaque bouton (fragile :
       ça dépend du contexte de rendu de CHAQUE vue), on lit le cookie "csrftoken" que
       Django pose automatiquement, et on l'ajoute à TOUTES les requêtes htmx ici. */
    function getCookie(name) {
        const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return match ? decodeURIComponent(match[2]) : null;
    }
    document.body.addEventListener('htmx:configRequest', (event) => {
        event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
    });

    /* ── Sidebar collapse (délégation : résiste aux ID dupliqués et aux re-swaps HTMX) ── */
    document.addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('#sbToggle');
        if (!toggleBtn) return;
        const sidebar = toggleBtn.closest('.mp-sidebar') || document.getElementById('mpSidebar');
        if (!sidebar) return;
        const collapsed = sidebar.classList.toggle('collapsed');
        const icon = toggleBtn.querySelector('#sbToggleIcon') || toggleBtn.querySelector('i');
        if (icon) icon.className = collapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
    });

    /* ── Genre pills scroll-spy ── */
    const pills    = document.querySelectorAll('.mp-genre-pill[href^="#"]');
    const sections = [];

    pills.forEach(p => {
        const id = p.getAttribute('href').slice(1);
        const el = document.getElementById(id);
        if (el) sections.push({ pill: p, el });
    });

    if (sections.length) {
        const io = new IntersectionObserver(entries => {
            entries.forEach(e => {
                if (!e.isIntersecting) return;
                pills.forEach(p => p.classList.remove('active'));
                const f = sections.find(s => s.el === e.target);
                if (f) f.pill.classList.add('active');
            });
        }, { threshold: .3 });
        sections.forEach(s => io.observe(s.el));
    }

    /* ── Smooth scroll pills ── */
    pills.forEach(p => {
        p.addEventListener('click', e => {
            const href = p.getAttribute('href');
            if (href.startsWith('#')) {
                e.preventDefault();
                document.querySelector(href)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    /* ── Like buttons ── */
    document.querySelectorAll('.mp-card__like').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault();
            const icon  = btn.querySelector('i');
            const liked = icon.classList.toggle('fas');
            icon.classList.toggle('far', !liked);
            icon.style.color     = liked ? 'var(--m-red)' : '';
            btn.style.background = liked ? 'rgba(232,39,75,.15)' : '';
        });
    });

    /* ── Gestion générique des modals injectés par HTMX (créer playlist / voir playlist) ── */
    const modalContainer = document.getElementById('modal-container');

    // Fonction globale : n'importe quel bouton/template peut appeler closePlaylistModal()
    // via onclick="closePlaylistModal()" — même les modals que je n'ai pas écrits moi-même.
    window.closePlaylistModal = function () {
        const mc = document.getElementById('modal-container');
        if (mc) mc.innerHTML = '';
    };

    // Tout ce qui suit dépend de #modal-container : on ne l'exécute que s'il existe
    // sur la page (évite une erreur si ce script est un jour partagé sur une page qui
    // n'a pas ce conteneur).
    if (modalContainer) {
        function openInjectedModal() {
            const modal = modalContainer.querySelector('.mp-modal');
            if (modal) modal.classList.add('is-open');
        }

        // Ouvre le modal dès qu'il est injecté dans #modal-container
        document.body.addEventListener('htmx:afterSwap', (e) => {
            if (e.detail.target === modalContainer) openInjectedModal();
        });

        // Ferme le modal : clic sur le fond OU sur un élément .mp-modal__x / [data-close-modal],
        // où qu'il se trouve dans la page (délégation sur document, pas seulement modalContainer,
        // au cas où le fragment injecté contiendrait sa propre structure imbriquée).
        document.addEventListener('click', (e) => {
            if (!modalContainer.contains(e.target)) return;
            const isBackdrop = e.target.classList.contains('mp-modal');
            const isCloseBtn = e.target.closest('.mp-modal__x, [data-close-modal]');
            if (isBackdrop || isCloseBtn) {
                e.preventDefault();
                modalContainer.innerHTML = '';
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') modalContainer.innerHTML = '';
        });
    }

    /* ── Lazy images fade-in ── */
    if ('IntersectionObserver' in window) {
        document.querySelectorAll('img[loading="lazy"]').forEach(img => {
            img.style.opacity    = '0';
            img.style.transition = 'opacity .3s';
            const io = new IntersectionObserver(([e]) => {
                if (!e.isIntersecting) return;
                img.addEventListener('load', () => img.style.opacity = '1');
                if (img.complete) img.style.opacity = '1';
                io.disconnect();
            }, { rootMargin: '80px' });
            io.observe(img);
        });
    }

})();
