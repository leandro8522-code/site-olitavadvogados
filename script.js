document.addEventListener('DOMContentLoaded', () => {
    // ─── Carregar Notícias do noticias.json ───────────────────────────────────
    function criarCardNoticia(noticia, isArticle = false) {
        const tag = isArticle ? 'article' : 'div';
        const delay = noticia.delay ? ` ${noticia.delay}` : '';
        const animClass = isArticle ? '' : ` slide-up${delay}`;
        const fonteHtml = noticia.fonte
            ? `<span class="news-fonte">Fonte: <a href="${noticia.fonte_url || '#'}" target="_blank" rel="noopener noreferrer">${noticia.fonte}</a></span>`
            : '';
        const destinoUrl = `noticia.html?id=${encodeURIComponent(noticia.id)}`;
        return `
            <${tag} class="card news-card${animClass}"
                style="background-image: url('${noticia.image}');">
                <div class="news-overlay"></div>
                <div class="news-content">
                    <h3>${noticia.title}</h3>
                    <p>${noticia.summary}</p>
                    ${fonteHtml}
                    <a href="${destinoUrl}" class="news-link">
                        Ler Notícia Completa <i class="fa-solid fa-arrow-right"></i>
                    </a>
                </div>
            </${tag}>`;
    }

    // Grade da página inicial (mostra apenas as 3 primeiras)
    const homeGrid = document.getElementById('news-grid-home');
    if (homeGrid) {
        fetch('noticias.json')
            .then(r => r.json())
            .then(noticias => {
                homeGrid.innerHTML = noticias.slice(0, 3).map(n => criarCardNoticia(n, false)).join('');
                // Re-observa animações nos cards recém-criados
                document.querySelectorAll('#news-grid-home .slide-up').forEach(el => {
                    const obs = new IntersectionObserver((entries, o) => {
                        entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); o.unobserve(entry.target); } });
                    }, { threshold: 0.15 });
                    obs.observe(el);
                });
            })
            .catch(() => { homeGrid.innerHTML = '<p>Não foi possível carregar as notícias.</p>'; });
    }

    // Grade da página todas-noticias.html (mostra todas)
    const allGrid = document.getElementById('news-grid-all');
    if (allGrid) {
        fetch('noticias.json')
            .then(r => r.json())
            .then(noticias => {
                allGrid.innerHTML = noticias.map(n => criarCardNoticia(n, true)).join('');
            })
            .catch(() => { allGrid.innerHTML = '<p>Não foi possível carregar as notícias.</p>'; });
    }

    // ─── Navbar Scroll Effect ─────────────────────────────────────────────────
    const navbar = document.getElementById('navbar');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Mobile Menu Toggle
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    const links = document.querySelectorAll('.nav-links li a');

    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        const icon = hamburger.querySelector('i');
        if (navLinks.classList.contains('active')) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-xmark');
        } else {
            icon.classList.remove('fa-xmark');
            icon.classList.add('fa-bars');
        }
    });

    // Close mobile menu when clicking a link
    links.forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            hamburger.querySelector('i').classList.remove('fa-xmark');
            hamburger.querySelector('i').classList.add('fa-bars');
        });
    });

    // Intersection Observer for Scroll Animations
    const animationElements = document.querySelectorAll('.fade-up, .fade-in, .slide-up');

    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Stop observing once visible
            }
        });
    }, observerOptions);

    animationElements.forEach(el => {
        observer.observe(el);
    });

    // Form Submission — Envia por EmailJS
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const originalText = btn.innerHTML;

            // Feedback visual: carregando
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...';
            btn.disabled = true;

            // Coleta os dados do formulário
            const assunto = document.getElementById('subject');
            const area = assunto.options[assunto.selectedIndex].text;

            const templateParams = {
                from_name: document.getElementById('name').value.trim(),
                from_email: document.getElementById('email').value.trim(),
                phone: document.getElementById('phone').value.trim(),
                subject: area,
                message: document.getElementById('message').value.trim(),
                to_email: 'leandro_aoliveira@hotmail.com'
            };

            emailjs.send('service_bxfft9g', 'template_p0jomx9', templateParams)
                .then(() => {
                    // Sucesso
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Mensagem Enviada!';
                    btn.style.backgroundColor = '#10B981';
                    btn.style.color = '#fff';
                    btn.style.borderColor = '#10B981';
                    contactForm.reset();

                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                        btn.style = '';
                    }, 4000);
                })
                .catch((error) => {
                    // Erro
                    console.error('Erro ao enviar:', error);
                    btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Erro ao enviar. Tente novamente.';
                    btn.style.backgroundColor = '#EF4444';
                    btn.style.color = '#fff';
                    btn.style.borderColor = '#EF4444';

                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                        btn.style = '';
                    }, 4000);
                });
        });
    }

});
