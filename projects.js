(() => {
/* Données des projets, dans l’ordre de la liste. Les images sont dans
   assets/projects/<id>/ en WebP, une largeur par fichier : « <nom>-<largeur>.webp ».
   Couverture (aperçu, vignettes, projet suivant) : cover-200/400/800, en 4:5.
   Galerie : groupes { layout, head?, caption?, items } ; layout vaut full, pair,
   inset, aside, browser, browser-pair ou phones (main.js, gallery()). Une image
   animée (anim) a son image fixe (poster) : c’est elle qu’on voit d’abord, et
   la seule en mouvement réduit.
   À tenir à jour avec index.html, section Travaux : le titre (« Huit projets »),
   la note et la liste de secours du noscript ; de même pour
   brand/index.html (« Neuf projets »). only : projet réservé à une édition. */
  // image : nom de fichier sans largeur, dimensions de la plus grande, largeurs disponibles, alternative
  const im = (src, w, h, widths, alt, more) => Object.assign({ src, w, h, widths, alt }, more);
  const D = [800, 1600], M = [390, 780];

window.PROJECTS = [
  {
    id: 'wei',
    summary: 'Concevoir un parcours de demande de devis pour les voyages étudiants.',
    title: 'WEI & GO',
    tag: 'Live',
    kind: 'Site avec demande de devis',
    role: 'UI/UX · Intégration',
    year: '2026',
    tools: 'Lovable, Claude, React, WordPress',
    link: 'https://wei-go.fr',
    linkLabel: 'Voir wei-go.fr',
    cover: { w: 800, tint: '#272f22' },
    hero: { type: 'browser', ...im('hero', 2200, 1375, [800, 1400, 2200], "Page d’accueil du site WEI & GO sur ordinateur : titre « Ton WEI, inoubliable. » sur une photo d’étudiants en rouge qui font la fête, boutons « Demander un devis » et « Voir nos séjours », bandeau de destinations."),
      phone: im('06-accueil-mobile', 780, 1688, M, "Accueil du site WEI & GO sur mobile : titre « Ton WEI, inoubliable » en blanc et vert, bouton vert « Demander un devis » et bouton « Voir nos séjours ».") },
    pitch: "Le site de WEI & GO, la marque du groupe LEZGO qui organise des voyages étudiants sur mesure pour les écoles depuis 2016. Le cœur du site, c’est la demande de devis : il fallait qu’un BDE puisse la faire vite, sans se perdre.",
    facts: [['Client', 'Groupe LEZGO'], ['Rôle', 'UI/UX, intégration'], ['Outils', 'Lovable, Claude, React, WordPress'], ['Contexte', 'Alternance']],
    cols: [
      [
            "Le besoin et les utilisateurs",
            "WEI & GO organise des voyages étudiants pour les écoles. Le parcours central est la demande de devis : un BDE doit pouvoir décrire son séjour et comprendre la suite de la démarche."
      ],
      [
            "Mon rôle et les contraintes",
            "J’ai conçu le moodboard, les wireframes, les maquettes et le parcours de demande de devis, puis intégré le site dans le WordPress du groupe via un thème enfant. Le back-office existant devait être conservé. Lovable et Claude m’ont accompagné dans la réalisation."
      ],
      [
            "Les décisions d’interface",
            "Le tutoiement adapte le ton aux étudiants. Deux actions structurent l’accueil : demander un devis ou découvrir les séjours. Le parcours est présenté en quatre étapes, avec les délais annoncés par la marque. Sur mobile, les cartes et les étapes s’empilent pour garder une lecture claire."
      ],
      [
            "La réalisation et le recul",
            "La refonte a été validée et mise en ligne. Le travail couvre l’accueil, les séjours, les animations, le devis, le contact et le blog. Les écrans ci-dessous montrent le formulaire et les déclinaisons mobiles ; les délais et avis affichés sont des informations commerciales du site, pas des mesures de performance de la refonte."
      ]
],
    gallery: [
      { layout: 'browser', caption: 'La demande de devis, le cœur du site', items: [
        im('05-devis-desktop', 1600, 1156, D, "Section « Devis gratuit. » : formulaire blanc sur fond vert avec les champs nom, téléphone, e-mail, école, type de séjour, ville de départ, nombre de participants, dates et budget, et un bouton « Soumettre ».")] },
      { layout: 'browser-pair', caption: 'Les séjours, puis tout ce qui est inclus', items: [
        im('02-sejours-desktop', 1600, 1000, D, "Section « Construis le séjour qui te ressemble » : grande carte verte présentant le format WEI / WED avec une photo de piscine, et le début des cartes Animations, Séjour Ski et City Trip."),
        im('04-inclus-desktop', 1600, 1000, D, "Section « Tout est inclus. » sur fond vert foncé : six blocs avec icônes pour l’hébergement, la restauration, le transport, les animations, l’organisation et la sécurité.")] },
      { layout: 'browser', caption: '« C’est simple. » : le parcours en quatre étapes', items: [
        im('03-process-desktop', 1600, 1000, D, "Bas des cartes Animations, Séjour Ski et City Trip, puis section « C’est simple. » sur fond beige : quatre étapes numérotées avec icônes, de « Tu remplis le devis » à « Tu profites ».")] },
      { layout: 'phones', caption: 'Sur téléphone', items: [
        im('06-accueil-mobile', 780, 1688, M, "Accueil du site WEI & GO sur mobile : titre « Ton WEI, inoubliable » en blanc et vert, bouton vert « Demander un devis » et bouton « Voir nos séjours »."),
        im('07-sejours-mobile', 780, 1688, M, "Carte WEI / WED sur mobile : photo de piscine, liste hébergement, animations, soirées et transport, bouton « Voir les séjours »."),
        im('08-process-mobile', 780, 1688, M, "Section « C’est simple. » sur mobile : les quatre étapes empilées verticalement avec leurs icônes vertes.")] }
    ]
  },
  {
    id: 'quasar',
    summary: 'Apprendre le système solaire à travers une progression et des mini-jeux.',
    title: 'QUASAR',
    kind: 'Application éducative',
    role: 'UI · Interaction',
    year: '2025',
    tools: 'Figma, Illustrator, Photoshop',
    link: 'https://www.behance.net/gallery/227402211/QUASAR-Application-ducative',
    linkLabel: 'Voir sur Behance',
    cover: { w: 800, tint: '#241d47' },
    hero: { type: 'image', ...im('hero', 1600, 1042, D, "Logo Quasar, une orbite blanche traversée par une étoile, au-dessus du nom Quasar, sur un fond spatial violet.") },
    pitch: "Une application éducative pour les adolescents qui veulent découvrir le système solaire autrement. Chaque planète devient un terrain de jeu, avec ses niveaux à débloquer et ses mini-jeux.",
    facts: [['Contexte', 'Projet d’école, brief fictif'], ['Marque', 'Acadomia'], ['Cible', 'Adolescents'], ['Livrables', 'Logo, écrans mobiles, mini-jeux'], ['Outils', 'Figma, Illustrator, Photoshop']],
    cols: [
      [
            "Le brief et la cible",
            "Un projet d’école sur un brief fictif pour Acadomia : concevoir une application éducative sur le sujet de notre choix. J’ai choisi le système solaire, avec une expérience destinée aux adolescents."
      ],
      [
            "Le parcours proposé",
            "Depuis l’accueil, chaque planète donne accès à une progression par niveaux. La navigation sépare l’accueil, la progression, les cours et les paramètres. Des cadenas et des étoiles rendent visibles les niveaux à débloquer et l’avancement."
      ],
      [
            "Les interactions et leurs états",
            "Les exercices varient : répondre à un QCM, placer les lunes de Mars sur leur orbite ou trier les planètes. Les écrans prévoient la réussite et l’échec, avec une action pour continuer ou recommencer. L’univers cartoon et le fond spatial relient les activités au thème."
      ],
      [
            "Les livrables",
            "Le projet présente une identité, des écrans mobiles et plusieurs mini-jeux conçus avec Figma, Illustrator et Photoshop. Il s’agit d’une proposition d’interface pour un exercice scolaire, et non d’une application Acadomia en production."
      ]
],
    gallery: [
      { head: 'Les écrans' },
      { layout: 'inset', caption: 'L’écran de chargement', items: [
        im('02-chargement', 1600, 1954, D, "Écran de chargement de l’application Quasar sur deux maquettes d’iPhone, avec le mot « Loading... » en très grand.")] },
      { layout: 'inset', caption: 'Le menu principal et sa barre de navigation', items: [
        im('03-menu', 1600, 1175, D, "Écran « Menu » : la Terre au centre de l’écran et la barre de navigation annotée Accueil, Progression, Cours academia et Paramètre.")] },
      { layout: 'inset', caption: 'Une page d’accueil par planète', items: [
        im('04-accueil', 1600, 1208, D, "Trois écrans d’accueil montrant les planètes à débloquer, la Terre puis Mars, avec des cadenas sur les niveaux fermés.")] },
      { layout: 'inset', caption: 'La carte des niveaux à débloquer', items: [
        im('05-maps', 1600, 1525, D, "Deux écrans « Maps » : un chemin illustré au milieu d’une forêt relie les niveaux, dont « Quizz cosmique » et « Astéroïde ».")] },
      { head: 'Les mini-jeux' },
      { layout: 'inset', caption: 'Le quiz, puis le niveau terminé', items: [
        im('06-niveaux-quiz', 1600, 1225, D, "Écrans de niveau « Niveaux » : question sur la plus grosse planète du système solaire avec quatre réponses illustrées, et écran de niveau terminé avec trois étoiles.")] },
      { layout: 'inset', caption: 'Placer les lunes de Mars sur leur orbite', items: [
        im('07-niveaux-lunes', 1600, 875, D, "Mini-jeu où il faut placer les lunes de Mars, Phobos et Deimos, sur leurs orbites, en quatre états successifs.")] },
      { layout: 'inset', caption: 'Trier les planètes, rocheuses ou gazeuses', items: [
        im('08-niveaux-tri', 1600, 983, D, "Mini-jeu « Glisser les planètes dans le bon tuyau selon leur nature » : Neptune, Mercure, Saturne et Pluton à ranger dans deux tubes, planète rocheuse ou gazeuse, puis les écrans Suivant et Recommencer.")] }
    ]
  },
  {
    id: 'one-piece',
    title: 'ONE PIECE S2',
    subtitle: '<span lang="en">The Grand Line Challenge</span>',
    kind: 'Campagne digitale',
    role: 'DA · UI/UX · Campagne',
    year: '2026',
    tools: 'Figma, Photoshop, IA générative (Runway, Veo)',
    link: 'https://www.behance.net/gallery/242417537/DIGITAL-CAMPAIGN-ONE-PIECE-S2',
    linkLabel: 'Voir sur Behance',
    cover: { w: 800, tint: '#7b807e' },
    hero: { type: 'image', ...im('01-key-visual', 1600, 900, D, "Affiche One Piece : Luffy seul au milieu d’un paysage de montagnes enneigées et de tours de glace, texte « Vous entrez à présent dans le pays sans nom », logo One Piece et mention « Seulement sur Netflix, le 10 mars ».") },
    pitch: "<span lang=\"en\">The Grand Line Challenge</span>, une campagne digitale imaginée pour la sortie de la saison 2 de la série One Piece en <span lang=\"en\">live action</span>. Trois activations qui s’enchaînent, de la rue jusqu’au téléphone. C’est un exercice de mastère, pas une vraie campagne Netflix.",
    facts: [['Contexte', 'Projet de mastère (M2)'], ['Livrables', 'Vidéo, affiches DOOH, application'], ['Rôle', 'DA, affiches, UI de l’application'], ['Outils', 'Figma, Photoshop, IA générative (Runway, Veo)']],
    cols: [
      ['Le point de départ', "Un projet de deuxième année de mastère : imaginer une campagne pour la saison 2. Mon idée, c’était que chaque activation prolonge la précédente, pour faire entrer le public dans l’univers petit à petit."],
      ['Ce que j’ai fait', "D’abord une vidéo FOOH, « En route pour l’île de Drum », pensée pour des lieux très fréquentés, que j’ai produite avec Runway et Veo. Ensuite des affiches DOOH : chaque pays a son capitaine, incarné par un influenceur, et le passant détecté voit son avatar rejoindre l’équipage. Enfin, un QR code mène à un <span lang=\"en\">advergame</span> mobile."],
      ['Les écrans', "Dans l’application, chaque joueur fait avancer l’équipage de son pays sur la carte de Grand Line jusqu’à Drum Island, grâce à des mini-jeux courts : un QCM, une chasse aux coordonnées sur une carte au trésor. J’ai dessiné tout le parcours dans Figma et Photoshop, de l’accueil à l’écran de fin, avec le classement des pays toujours visible."],
      ['Ce que j’en retiens', "C’est un projet qui m’a fait progresser en UI/UX. Et il m’a confirmé qu’une activation ne vaut pas grand-chose seule : c’est l’enchaînement qui tient la campagne."]
    ],
    gallery: [
      { layout: 'full', caption: 'La bannière de la campagne', items: [
        im('02-titre-campagne', 1600, 979, D, "Bannière de la campagne : logo One Piece au-dessus de la mer, sous-titre « The Grand Line Challenge » et étiquette « Saison 2 ».")] },
      { head: 'Les affiches' },
      { layout: 'full', caption: 'L’affiche dans le métro : « Rejoins l’équipage »', items: [
        im('03-dooh-affiche-metro', 1600, 1067, D, "Affiche numérique dans une station de métro : un personnage en tenue de Luffy devant le Vogue Merry et la tour Eiffel, titre « Rejoins l’équipage », rame de métro floue à droite.")] },
      { layout: 'pair', caption: 'Le passant est scanné, puis son avatar rejoint l’équipage de France', items: [
        im('04-dooh-scan', 1600, 1067, D, "Un passant se tient devant l’écran du métro, qui affiche une silhouette humaine en hologramme bleu et le texte « Scanning en cours »."),
        im('05-dooh-equipage', 1600, 1067, D, "Le même passant devant l’écran, qui montre maintenant un personnage en tenue de Zoro, le titre « Bienvenue à bord de l’équipage de France » et un QR code « Scan pour jouer ».")] },
      { head: 'Le jeu' },
      { layout: 'inset', caption: 'La carte de Grand Line avec le classement des pays, puis le mini-jeu QCM', items: [
        im('07-advergame-accueil-qcm', 1600, 1350, D, "Écrans du jeu : carte de Grand Line avec le classement des pays, puis deux questions du mini-jeu QCM sur l’univers One Piece.")] },
      { layout: 'inset', caption: 'Le mini-jeu du trésor, puis la mission réussie', items: [
        im('08-advergame-tresor-reussi', 1600, 1367, D, "Écrans du mini-jeu trésor, avec une carte au trésor et trois coordonnées à choisir, puis écrans « Mission réussie ! +0,2 % d’avancement pour votre navire ».")] },
      { layout: 'inset', caption: 'L’écran de fin : Drum Island est atteinte', items: [
        im('09-advergame-fin', 1600, 735, D, "Écran de fin du jeu : le Vogue Merry et Chopper dans un décor enneigé, message « Drum Island atteinte ! L’équipage de France est arrivé à destination et engage Chopper ».")] }
    ]
  },
  {
    id: 'lezgo',
    summary: 'Présenter un groupe de voyages et intégrer son site vitrine en une semaine.',
    title: 'LEZGO',
    tag: 'Live',
    kind: 'Site vitrine et logo',
    role: 'Logo · UI · Intégration',
    year: '2025',
    tools: 'Illustrator, WordPress, Divi',
    link: 'https://lez-go.fr',
    linkLabel: 'Voir lez-go.fr',
    cover: { w: 780, tint: '#9a928e' },
    hero: { type: 'browser', ...im('hero', 2200, 1375, [800, 1400, 2200], "Page d’accueil du site LEZGO sur ordinateur : titre « Voyagez en groupe autrement... » sur une photo de groupe au bord d’une piscine, bouton orange « Contactez-nous » et trois phrases clés en bas de l’image."),
      phone: im('05-accueil-mobile', 780, 1688, M, "Accueil du site LEZGO sur mobile : titre « Voyagez en groupe autrement... », bouton orange « Contactez-nous » et phrases clés sur la photo de groupe.") },
    pitch: "Le logo et le site vitrine de LEZGO, le groupe qui chapeaute plusieurs marques de voyages, dont WEI & GO et Ze Trip. J’ai commencé par le logo, puis il a fallu lui donner un endroit où vivre : le site.",
    facts: [['Client', 'Groupe LEZGO'], ['Rôle', 'Logo, maquette, intégration'], ['Délai', 'Une semaine pour le site'], ['Contexte', 'Alternance']],
    cols: [
      [
            "Le besoin et le contexte",
            "LEZGO réunit plusieurs marques de voyages, dont WEI & GO et Ze Trip. La mission associe la modernisation du logo et la création du site vitrine du groupe. Le nouveau logo devait rester proche de l’identité existante."
      ],
      [
            "Mon rôle et le délai",
            "J’ai travaillé sur le logo, la maquette et l’intégration. Le site a été réalisé en une semaine, avec un template WordPress pour tenir le délai. L’identité a précédé la réalisation du site."
      ],
      [
            "La traduction dans l’interface",
            "L’accueil présente la promesse du groupe et un bouton de contact. Le savoir-faire, les partenaires, les chiffres du groupe et ses engagements structurent la suite de la page. Les captures montrent les déclinaisons sur ordinateur et téléphone."
      ],
      [
            "Le résultat et les améliorations identifiées",
            "Le site vitrine est en ligne. Quelques mois après sa réalisation, j’ai audité mon propre travail : je rendrais la page plus légère et donnerais davantage de place à l’orange de la marque. Ce recul fait partie du projet, au même titre que les écrans livrés."
      ]
],
    gallery: [
      { layout: 'browser', caption: 'Le savoir-faire du groupe', items: [
        im('03-savoir-faire-desktop', 1600, 1000, D, "Section « Notre savoir-faire » : photos arrondies de séjours et d’équipe, alternées avec trois textes courts sur la conception des séjours, la synergie entre les marques et l’humain.")] },
      { layout: 'browser-pair', caption: 'Les chiffres du groupe, puis ses engagements', items: [
        im('02-chiffres-desktop', 1600, 1000, D, "Section « Ils nous font confiance » avec des logos de partenaires, puis un bandeau dégradé bleu et orange avec quatre chiffres : 60 000 participants, 200 collaborateurs réceptifs, 420 séjours organisés, 10 années d’expérience."),
        im('04-engagements-desktop', 1600, 1000, D, "Section « Nos engagements » sur une photo assombrie : texte d’introduction, bouton « Contactez-nous » et quatre cartes Esprit d’équipe, Simplicité, Confiance et L’humain.")] },
      { layout: 'phones', caption: 'Sur téléphone', items: [
        im('05-accueil-mobile', 780, 1688, M, "Accueil du site LEZGO sur mobile : titre « Voyagez en groupe autrement... », bouton orange « Contactez-nous » et phrases clés sur la photo de groupe."),
        im('06-chiffres-mobile', 780, 1688, M, "Les quatre chiffres clés de LEZGO empilés sur mobile, dans des cartes translucides sur un fond dégradé bleu et orange."),
        im('07-engagements-mobile', 780, 1688, M, "Section « Nos engagements » sur mobile : texte d’introduction, bouton orange et première carte « Esprit d’équipe ».")] }
    ]
  },
  {
    id: 'livre-blanc',
    title: 'Du logo à la scène',
    tag: 'Live',
    kind: 'Livre blanc en ligne',
    role: 'Écriture · Design · Dev',
    year: '2026',
    tools: 'Next.js, Motion, Lenis, Vercel',
    link: 'https://du-logo-a-la-scene.vercel.app',
    linkLabel: 'Lire le livre blanc',
    cover: { w: 780, tint: '#1b1111' },
    hero: { type: 'browser', ...im('hero', 2200, 1375, [800, 1400, 2200], "Ouverture du site « Du logo à la scène » sur ordinateur : titre en blanc et rouge sur fond noir, sous-titre sur les six cas d’étude, sommaire des chapitres à gauche."),
      phone: im('07-ouverture-mobile', 780, 1688, M, "Ouverture du site « Du logo à la scène » sur mobile : titre blanc et rouge centré, sous-titre et bouton de sommaire en bas.") },
    pitch: "Un livre blanc pour décrypter et concevoir l’identité visuelle d’une équipe esport : six cas d’étude, une méthode en sept étapes, et une équipe inventée de zéro pour l’appliquer. Je l’ai écrit, mis en page et développé moi-même, sous forme de site qui se lit au scroll.",
    facts: [['Format', 'Site en <span lang="en">scrollytelling</span>'], ['Contenu', '6 cas d’étude, méthode en 7 étapes'], ['Lecture', '25 minutes, accès libre'], ['Rôle', 'Écriture, design, développement']],
    cols: [
      ['Le point de départ', "En mai 2025, pour la LCO, j’ai cherché des références sur l’identité des équipes esport. Je suis tombé sans arrêt sur les mêmes logos : loup en flammes, crâne au casque de gamer, aigle à éclairs. Et presque rien de sérieux en français. J’ai fini par écrire le livre que j’aurais voulu avoir."],
      ['Ce que j’ai fait', "J’ai analysé six équipes que je suis depuis des années : Karmine Corp, T1, G2 Esports, Fnatic, NAVI et Team Vitality. J’en ai tiré une méthode en sept étapes, du brief à la maintenance de l’identité, puis je l’ai testée sur HUNTERS, une équipe fictive : un H taillé comme des griffures, avec deux yeux de chasseur cachés dans la fente centrale, décliné sur le maillot et le <span lang=\"en\">merch</span>."],
      ['Les choix de design', "Je n’ai pas voulu d’un PDF. Le livre parle de marques qui n’existent que sur écran, alors il en est une : un site en <span lang=\"en\">scrollytelling</span>, six chapitres, un sommaire toujours accessible et environ 25 minutes de lecture. Et un site se mesure, là où un PDF téléchargé ne dit jamais s’il a été lu."],
      ['Ce que j’en retiens', "Les meilleures identités esport sont souvent celles qui ont fait des choix simples et les ont gardés dans le temps. Côté diffusion, je commencerais à partager pendant l’écriture, et pas après : j’aurais eu des retours pendant que je construisais."]
    ],
    gallery: [
      { layout: 'browser-pair', caption: 'Deux analyses : le logo de T1, puis la double palette de Karmine Corp', items: [
        im('02-logo-t1-desktop', 1600, 1000, D, "Chapitre sur le logo, approche « L’héritage codé (T1) » : le logo rouge de T1 présenté dans un cadre sombre avec une légende, suivi du texte d’analyse."),
        im('03-couleur-kc-desktop', 1600, 1000, D, "Chapitre sur la couleur : citation sur le rebrand, texte sur Fnatic, puis la double palette 2026 de Karmine Corp en quatre nuances : rouge, bleu, blanc cassé et noir.")] },
      { head: 'HUNTERS' },
      { layout: 'browser', caption: 'L’ouverture du chapitre HUNTERS, l’équipe inventée pour appliquer la méthode', items: [
        im('04-hunters-ouverture-desktop', 1600, 1000, D, "Ouverture du chapitre 6 : « HUNTERS, que la chasse commence. » en rouge et blanc sur fond noir, puis le titre HUNTERS et son introduction.")] },
      { layout: 'browser-pair', caption: 'La planche d’identité, puis le maillot', items: [
        im('05-hunters-brand-board-desktop', 1600, 1000, D, "Planche d’identité HUNTERS sur fond clair : construction géométrique du logo en forme de griffe, anatomie du logo en quatre étapes et palette Blood et Ink."),
        im('06-hunters-maillot-desktop', 1600, 1000, D, "Étape « écosystème 360 » de HUNTERS : le maillot noir et rouge présenté seul, puis porté en tenue de ville.")] },
      { layout: 'phones', caption: 'Sur téléphone', items: [
        im('07-ouverture-mobile', 780, 1688, M, "Ouverture du site « Du logo à la scène » sur mobile : titre blanc et rouge centré, sous-titre et bouton de sommaire en bas."),
        im('08-hunters-mobile', 780, 1688, M, "Ouverture du chapitre HUNTERS sur mobile : logo griffe rouge et texte « Que la chasse commence »."),
        im('09-hunters-maillot-mobile', 780, 1688, M, "Maillot HUNTERS présenté sur mobile, avec sa légende, au-dessus d’une photo du maillot porté.")] }
    ]
  },
  {
    id: 'lco',
    title: 'LCO',
    kind: 'Identité visuelle esport',
    role: 'DA · Identité · Motion',
    year: '2025',
    tools: 'Illustrator, Photoshop, After Effects, IA générative (Midjourney, Runway)',
    link: 'https://www.behance.net/gallery/226161957/LCO-League-of-Legends-Championship-Overseas',
    linkLabel: 'Voir sur Behance',
    cover: { w: 800, tint: '#257181' },
    hero: { type: 'image', ...im('01-logo-anime-poster', 960, 540, [800, 960], "Animation du logo LCO, un soleil stylisé à rayons, et du nom « League of Legends Championship Overseas » sur un fond de vagues sous-marines bleues en mouvement.", { anim: '01-logo-anime.anim.webp', label: 'le logo animé' }) },
    pitch: "L’identité visuelle d’une compétition de League of Legends imaginée pour les outre-mer, de La Réunion à la Martinique. Un projet de cours de trois semaines, et mon premier projet autour de l’esport.",
    facts: [['Contexte', 'Projet de cours, 3 semaines'], ['Date', 'Mai 2025'], ['Livrables', 'Logo, affiche, trophée, skins, scène'], ['Outils', 'Illustrator, Photoshop, After Effects, IA générative (Midjourney, Runway)']],
    cols: [
      ['Le point de départ', "Le brief : créer toute l’identité d’une compétition. J’ai imaginé la LCO, une ligue pour les territoires ultramarins, de La Réunion à la Guadeloupe en passant par Mayotte et la Martinique. Comme je viens de La Réunion, forcément, ça me parlait."],
      ['Ce que j’ai fait', "Je ne me suis pas arrêté au logo, un soleil aux rayons taillés : il y a aussi l’affiche « <span lang=\"en\">Make Them Shine</span> », le trophée, que j’ai animé, une <span lang=\"en\">skinline</span> pour Varus, Ekko et Nami, l’écran de connexion du client du jeu et la scène de la finale."],
      ['Les choix de design', "Le thème aquatique porte tout le projet, parce qu’il dit bien les îles : des bleus d’océan, un soleil, une typographie condensée et une signature, « <span lang=\"en\">The ocean is our glory.</span> »"],
      ['Ce que j’en retiens', "En cherchant des références, je n’ai presque rien trouvé de sérieux en français sur l’identité des équipes esport. C’est de là qu’est né mon livre blanc, un an plus tard."]
    ],
    gallery: [
      { layout: 'full', caption: 'L’affiche « <span lang="en">Make Them Shine</span> »', items: [
        im('02-affiches', 1600, 1131, D, "Trois affiches identiques collées sur un mur de carrelage, avec le slogan « Make Them Shine » en lettres cursives sur un visuel de vague, la date du 15/05/2025 et le logo LCO 25. Une passante floue marche devant.")] },
      { head: 'La scène' },
      { layout: 'pair', caption: 'Le logo sur les écrans de la salle', items: [
        im('03-mur-led', 1600, 1067, D, "Mur LED dans une salle sombre affichant le logo LCO et le nom complet de la ligue, avec des silhouettes de personnes devant un comptoir."),
        im('04-salle', 1600, 1067, D, "Grand écran de scène dans une salle de conférence pleine, affichant le logo et le nom de la ligue sur fond de vague.")] },
      { layout: 'full', caption: 'La scène de la finale', items: [
        im('05-scene', 1400, 881, [800, 1400], "Scène de compétition esport : écran suspendu « LCO 25 », postes de jeu blancs face à face et sol lumineux bleu.")] },
      { head: 'Le trophée' },
      { layout: 'pair', caption: 'Le trophée, puis son animation', items: [
        im('06-trophee', 1600, 1600, D, "Trophée en métal argenté en forme de vague bleue, posé sur un socle sombre sous des rayons de lumière, avec le logo LCO 25 en haut."),
        im('07-trophee-rotation-poster', 720, 720, [720], "Animation du trophée qui tourne sur lui-même sur fond gris, montrant la vague bleue enroulée dans le métal.", { anim: '07-trophee-rotation.anim.webp', label: 'le trophée qui tourne' })] },
      { head: 'La <span lang="en">skinline</span> : Varus, Ekko, Nami' },
      { layout: 'full', caption: 'Varus', items: [
        im('08-skin-varus', 1600, 935, D, "Illustration du skin LCO de Varus : le champion aux cheveux blancs et aux yeux violets tient un arc dans un décor sous-marin.")] },
      { layout: 'pair', caption: 'Ekko et Nami', items: [
        im('09-skin-ekko', 1600, 887, D, "Illustration du skin LCO d’Ekko : le champion nage parmi des coraux et des poissons colorés, une épée bleue à la main."),
        im('10-skin-nami', 1600, 887, D, "Illustration du skin LCO de Nami : la sirène à queue dorée tient un trident dans un récif.")] },
      { layout: 'full', caption: 'L’écran de connexion du client du jeu', items: [
        im('11-client-riot', 1600, 900, D, "Maquette de l’écran de connexion du client Riot Games sur un bureau Windows, avec l’illustration du skin Varus à droite.")] }
    ]
  },
  {
    id: 'pop-mart-bumi',
    title: 'POP MART X BUMI',
    subtitle: '<span lang="en">Tasty World</span>',
    kind: 'Personnage et packaging',
    role: 'DA · Branding · Packaging',
    year: '2026',
    tools: 'Photoshop, Illustrator, After Effects, IA générative',
    link: 'https://www.behance.net/gallery/246152569/POP-MART-X-BUMI-BRANDING-2026',
    linkLabel: 'Voir sur Behance',
    cover: { w: 800, tint: '#ceb5a8' },
    hero: { type: 'image', ...im('01-key-visual', 1600, 856, D, "Visuel principal : les figurines Bumi, un petit dragon crème, assises sur des nuages avec une part de pizza, un croissant, des sushis, des macarons, un taco et un bol de ramen.") },
    pitch: "BUMI est un petit dragon né avec des ailes trop petites pour voler, qui fait le tour du monde à pied pour goûter les spécialités de chaque pays. Un projet de branding mené en duo avec Vincent Aurillac, du personnage jusqu’au packaging de la collection « <span lang=\"en\">Tasty World</span> ».",
    facts: [['Contexte', 'Projet d’école'], ['Équipe', 'En duo avec Vincent Aurillac'], ['Livrables', 'Personnage, logo, packaging, campagne'], ['Outils', 'Photoshop, Illustrator, After Effects, IA générative']],
    cols: [
      ['Le point de départ', "Un projet d’école qui part d’un appel à projets de POP MART : imaginer une nouvelle licence pour une collection de figurines. Avec Vincent, mon binôme, on voulait un personnage attachant, avec une vraie histoire, et facile à décliner."],
      ['Ce que montre le projet', "L’histoire de BUMI en français et en anglais, six figurines qui mangent chacune une spécialité (tacos, croissants, pizza, sushis, macarons, ramen), une illustration à l’encre pour la boîte, un logo en tête de dragon, le packaging en boîte surprise avec son patron et son présentoir, et une campagne sur écran géant et en affiche."]
    ],
    gallery: [
      { layout: 'full', caption: 'La série <span lang="en">Tasty World</span>', items: [
        im('02-figurines-anime-poster', 1280, 640, [800, 1280], "Animation qui fait défiler les figurines de la série Tasty World, chacune dans un décor pastel lié à un plat : taco, croissant, sushi, pizza, macarons, ramen.", { anim: '02-figurines-anime.anim.webp', label: 'les figurines' })] },
      { layout: 'full', caption: 'Les logotypes de la collection', items: [
        im('03-logo-tasty-world', 1600, 516, D, "Logotype de la collection : tête de dragon rouge au trait, mention « POP MART x BUMI » et titre « Tasty World » en jaune pâle."),
        im('05-logo-bumi', 1600, 450, D, "Logotype « BUMI Tasty World » en lettres blanches contourées de rouge sur fond jaune.")] },
      { layout: 'aside', caption: 'Bumi, dessiné à l’encre pour la boîte', text: "Un petit dragon né avec des ailes trop petites pour voler. Alors il part à pied, de pays en pays, goûter les spécialités de chacun.", items: [
        im('04-dessin-bumi', 880, 713, [800, 880], "Illustration à l’encre de Bumi, petit dragon à cornes aux ailes minuscules, entouré de légumes, de champignons et de morceaux de viande.")] },
      { layout: 'pair', caption: 'La boîte surprise, puis le présentoir', items: [
        im('06-boite-figurine', 1600, 1000, D, "Boîte jaune « Bumi Tasty World » à côté de la figurine de Bumi qui mange des ramen avec un masque de renard."),
        im('07-presentoir', 1434, 896, [800, 1434], "Présentoir en carton avec plusieurs boîtes blind box « Tasty World », mention « 6 designs ».")] },
      { layout: 'full', caption: 'Le patron de la boîte', items: [
        im('08-patron-packaging', 1600, 1011, D, "Patron à plat de la boîte, sur fond de nuages : faces avec l’illustration de Bumi, les six figurines de la série, une figurine secrète, mentions légales et code-barres.")] },
      { layout: 'full', caption: 'La campagne, sur écran géant et en affiche', items: [
        im('09-campagne', 1600, 634, D, "Mur d’écrans en magasin affichant les figurines Bumi dans les nuages avec « Découvrez la collection Tasty World ! », et à droite une grande affiche illustrée de Bumi regardée par un parent et un enfant.")] }
    ]
  },
  {
    id: 'meoow',
    title: 'MEOOW!',
    kind: 'Branding et packaging',
    role: 'DA · Logo · Packaging',
    year: '2026',
    link: 'https://www.behance.net/gallery/247879525/MEOOW-CAT-FOOD-BRANDING',
    linkLabel: 'Voir sur Behance',
    tools: 'Photoshop, Illustrator, IA générative',
    cover: { w: 800, tint: '#969378' },
    hero: { type: 'image', ...im('01-logo', 1600, 900, D, "Logo « MEOOW! » en lettres bleu clair sur fond orange, au-dessus d’un chat noir aux grands yeux qui dépasse du bas de l’image.") },
    pitch: "Une marque de croquettes pour chats, pensée comme si le chat l’avait créée lui-même : de la vraie viande locale et des ingrédients qu’on comprend. Un logo, une gamme de trois recettes et ses déclinaisons.",
    facts: [['Contexte', 'Projet d’école'], ['Gamme', 'Poulet, saumon, bœuf'], ['Livrables', 'Logo, packaging, affiche, objets'], ['Outils', 'Photoshop, Illustrator, IA générative']],
    cols: [
      ['L’idée', "Tout part d’une phrase de la planche : MEOOW!, c’est la marque que le chat aurait créée « si ses petites pattounes pouvaient tenir un stylo ». Le logo le montre tel quel : un chat noir qui dépasse du bord, les yeux grands ouverts."],
      ['Ce que montre le projet', "Trois sachets aux couleurs franches, orange pour le poulet, rose pour le saumon, marron pour le bœuf, avec la même accroche : « Trop bon pour être ignoré. » Puis les déclinaisons : une affiche « Hmmmm... Meoow! », une gamelle, un <span lang=\"en\">tote bag</span> et une mise en rayon."]
    ],
    gallery: [
      { layout: 'pair', caption: 'La gamme : poulet, saumon, bœuf', items: [
        im('02-gamme-studio', 1400, 1050, [800, 1400], "Trois sachets de croquettes MEOOW! de 1 kg, au poulet en orange, au saumon en rose et au bœuf en marron, avec une fenêtre en forme de nuage et le chat noir en bas."),
        im('03-sachets-flottants', 1448, 1086, [800, 1448], "Les trois sachets MEOOW! inclinés sur fond blanc, avec les mentions « 70 % protéine naturelle » et « 100 % adoré par les chats ».")] },
      { layout: 'full', caption: 'Un sachet, trois saveurs', items: [
        im('04-saveurs-anime-poster', 1280, 720, [800, 1280], "Animation d’un sachet MEOOW! posé sur une étagère qui change de saveur, poulet, saumon puis bœuf.", { anim: '04-saveurs-anime.anim.webp', label: 'le sachet qui change de saveur' })] },
      { layout: 'pair', caption: 'En rayon, puis le format de 5 kg', items: [
        im('05-rayon-magasin', 1400, 1050, [800, 1400], "Les trois sachets sur l’étagère d’une animalerie, avec des étiquettes de prix « Gamme MEOOW! 24 € »."),
        im('06-gamme-5kg', 1400, 1050, [800, 1400], "Trois grands sacs MEOOW! de 5 kg, en orange, rose et marron, sur fond saumon.")] },
      { layout: 'full', caption: 'Sur le comptoir', items: [
        im('07-etagere', 1400, 788, [800, 1400], "Les trois sachets alignés sur un comptoir en bois devant des étagères de boutique.")] },
      { layout: 'full', caption: 'À l’heure du repas', items: [
        im('08-usage', 1448, 1086, [800, 1448], "Une personne verse des croquettes d’un sachet MEOOW! au poulet dans une gamelle, devant un chat noir assis sur le parquet.")] },
      { layout: 'pair', caption: 'Le sac en toile et la gamelle', items: [
        im('09-tote-bag', 1254, 1254, [800, 1254], "Les trois sachets MEOOW! qui dépassent d’un tote bag en toile posé sur un parquet."),
        im('10-gamelle', 1254, 1254, [800, 1254], "Gamelle en céramique blanche à l’intérieur bleu, avec le chat noir au fond et le logo MEOOW! sur le côté.")] },
      { layout: 'full', caption: 'L’affichage', items: [
        im('11-affichage', 1600, 1200, D, "Panneau d’affichage extérieur orange : « HMMMM... MEOOW! » et le chat noir qui regarde par-dessus le bord.")] }
    ]
  },
  {
    id: 'les-dieux',
    only: 'brand',
    title: 'LES DIEUX',
    kind: 'Rebranding et packaging',
    role: 'Logo · Packaging',
    year: '2025',
    tools: 'Photoshop, Illustrator, Figma',
    link: 'https://www.behance.net/gallery/216527627/REBRANDING-LES-DIEUX',
    linkLabel: 'Voir sur Behance',
    cover: { w: 800, tint: '#004f7f' },
    hero: { type: 'image', ...im('01-logo', 1600, 900, D, "Logo Les Dieux : le nom en lettres blanches hautes et étroites, avec une sardine à côté de « Les », dans une couronne de sardines bleu clair, sur un fond bleu à motif de colonnes grecques, de rameaux et d’étoiles.") },
    pitch: "Un rebranding pour Les Dieux, une marque de sardines en boîte : un nouveau logo autour d’une sardine, et des boîtes plus modernes pour ses trois recettes. Un projet d’école, en première année de mastère à l’ESD.",
    facts: [['Contexte', 'Projet d’école, 1re année de mastère à l’ESD'], ['Gamme', 'Naturel, à l’olive, au piment'], ['Livrables', 'Logo, déclinaisons, packaging'], ['Outils', 'Photoshop, Illustrator, Figma']],
    cols: [
      ['Le brief', "La marque veut se redonner une image en renouant avec ses origines grecques et son attachement à la mer. La demande : un nouveau logo centré sur une sardine, et des boîtes modernes pour ses trois recettes phares, au naturel, à l’olive et au piment."],
      ['Ce que montre le projet', "Le logo, un nom en lettres hautes et étroites dans une couronne de sardines, décliné en trois couleurs : jaune, bleu clair et rouge. Puis les trois boîtes, bleue pour la sardine au naturel, verte pour l’olive, rouge pour le piment."],
      ['Les choix de design', "Un motif bleu sur bleu de colonnes grecques, de rameaux, d’étoiles et de volutes sert de fond au logo et recouvre le couvercle des boîtes. La sardine est partout : dans le nom, et en couronne autour de lui."]
    ],
    gallery: [
      { layout: 'inset', caption: 'Le brief', items: [
        im('02-brief', 1600, 938, D, "Panneau « Le brief » sur fond bleu : « Les Dieux souhaitent se redonner une nouvelle image de marque en renouant avec leurs origines grecques et leur attachement à la mer. À travers la création d’un nouveau logo, centré sur une sardine emblématique, et des designs de boîtes modernes pour leurs trois recettes phares : “naturel”, “à l’olive” et “au piment”. La marque ambitionne de réaffirmer son authenticité, sa filière de pêche locale, et son engagement en faveur de la modernité et de la tradition. »")] },
      { layout: 'full', caption: 'Le logo en trois couleurs', items: [
        im('03-logos', 1600, 558, D, "Le logo Les Dieux en trois versions sur fond bleu nuit : le nom en blanc dans une couronne de sardines jaune, puis bleu clair, puis rouge.")] },
      { head: 'Les boîtes' },
      { layout: 'full', caption: 'La sardine au naturel', items: [
        im('04-boite-naturel', 1600, 828, D, "Boîte de sardines bleue, inclinée sur un fond bleu : couvercle au motif grec, anneau d’ouverture bleu clair, logo Les Dieux au centre, mentions « La sardine » et « Au naturel. »")] },
      { layout: 'pair', caption: 'À l’olive, puis au piment', items: [
        im('05-boite-olive', 960, 720, [800, 960], "Boîte de sardines verte sur un fond jaune, avec un anneau d’ouverture et un logo dorés, et les mentions « La sardine » et « À l’olive. »"),
        im('06-boite-piment', 960, 720, [800, 960], "Boîte de sardines rouge sur un fond rouge foncé, avec le logo Les Dieux et les mentions « La sardine » et « Au piment. »")] }
    ]
  }
];

/* Ordre par édition (data-edition sur <html>, main.js). Sans ordre, l’édition
   montre les projets sans « only » et ceux réservés à l’édition, dans
   l’ordre ci-dessus. Édition « brand » : /brand/index.html. */
window.PROJECT_ORDER = {
  ux: ['wei', 'quasar', 'lezgo', 'one-piece', 'livre-blanc', 'lco', 'pop-mart-bumi', 'meoow'],
  brand: ['lco', 'pop-mart-bumi', 'meoow', 'les-dieux', 'one-piece', 'livre-blanc', 'lezgo', 'wei', 'quasar']
};

})();
