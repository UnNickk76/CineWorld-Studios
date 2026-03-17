"""
CineWorld Studio's - Emerging Screenplays System
Generates screenplay proposals from screenwriters with pre-chosen cast.
Players can buy the screenplay only, or the full package (screenplay + cast).
"""
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# Synopsis templates per genre (Italian)
SYNOPSIS_TEMPLATES = {
    'action': [
        "Un ex agente speciale viene richiamato in servizio quando {villain} minaccia di distruggere {target}. Con solo {hours} ore a disposizione, deve attraversare {location} per fermare il piano.",
        "Durante un colpo da {amount} milioni, la squadra scopre che il vero obiettivo non è il denaro ma {secret}. Ora devono scegliere tra la fuga e la verità.",
        "Un veterano di guerra scopre che {organization} sta sviluppando {weapon} in segreto. L'unico modo per fermarlo è infiltrarsi nella loro base a {location}.",
        "Dopo un terremoto devastante, un gruppo di sopravvissuti deve attraversare una città in rovina infestata da {threat} per raggiungere l'ultimo punto di evacuazione.",
    ],
    'comedy': [
        "Un {profession} mediocre viene scambiato per {celebrity} e si ritrova catapultato in un mondo di lusso. Il problema? Deve mantenere l'inganno durante {event}.",
        "Due famiglie rivali scoprono che i loro figli si sono sposati in segreto a {location}. Il caos che ne segue coinvolge {animal}, un prete confuso e una torta nuziale gigante.",
        "Un robot domestico malfunzionante inizia a dare consigli sentimentali ai vicini di casa, creando una serie di situazioni esilaranti e inaspettate storie d'amore.",
        "Un gruppo di pensionati decide di aprire {business} per finanziare il loro viaggio intorno al mondo, ma le cose prendono una piega inaspettata quando {twist}.",
    ],
    'drama': [
        "Un pianista che ha perso l'uso della mano destra deve affrontare il suo passato quando {person} torna nella sua vita con una verità nascosta per {years} anni.",
        "Tre generazioni di una famiglia si riuniscono nella vecchia casa di campagna per {event}. I segreti sepolti da decenni emergono uno alla volta.",
        "Un giudice incorruttibile scopre che suo figlio è coinvolto nel caso più importante della sua carriera. Deve scegliere tra giustizia e famiglia.",
        "Una lettera mai spedita viene ritrovata {years} anni dopo. Il suo contenuto cambierà per sempre la vita di {people} persone in {location}.",
    ],
    'horror': [
        "Una famiglia si trasferisce in una casa vittoriana dove ogni notte alle {time} si sentono passi dal {room}. Quando scoprono cosa c'è dietro il muro, è troppo tardi.",
        "Un gruppo di ricercatori in Antartide trova {discovery} sepolto nel ghiaccio da millenni. Quando lo portano alla base, iniziano le sparizioni.",
        "Un'app di social media mostra agli utenti come moriranno. Quando le previsioni iniziano ad avverarsi, un gruppo di amici cerca disperatamente di cambiare il proprio destino.",
        "L'ultimo paziente di un ospedale psichiatrico abbandonato lascia un diario. Chi lo legge diventa ossessionato da {entity} e non riesce più a distinguere realtà e incubo.",
    ],
    'sci_fi': [
        "Nel {year}, l'umanità scopre che {discovery}. Un team di scienziati viene inviato oltre {boundary} per trovare risposte, ma ciò che trovano cambia la definizione di vita.",
        "Una colonia su {planet} perde i contatti con la Terra. {years} anni dopo, una nave di soccorso trova i coloni evoluti in qualcosa di completamente diverso.",
        "Un inventore crea un dispositivo che mostra {minutes} minuti nel futuro. Ma ogni volta che lo usa, il futuro cambia in modi sempre più catastrofici.",
        "L'intelligenza artificiale che gestisce {city} inizia a prendere decisioni che nessuno capisce. Quando un ingegnere indaga, scopre che l'IA sta cercando di proteggere l'umanità da se stessa.",
    ],
    'romance': [
        "Due sconosciuti trovano lo stesso libro in una libreria di {location}. Le note a margine che si scambiano diventano una storia d'amore epistolare nel XXI secolo.",
        "Un {profession} cinico e una {profession2} ottimista vengono bloccati insieme per {days} giorni a causa di {event}. Quello che inizia come conflitto diventa qualcosa di inaspettato.",
        "Dopo {years} anni, due ex amanti si ritrovano nella città dove si erano conosciuti. Entrambi hanno un segreto che potrebbe cambiare tutto.",
        "Una wedding planner che non crede più nell'amore deve organizzare il matrimonio perfetto. Il problema? Lo sposo è il suo primo grande amore.",
    ],
    'thriller': [
        "Un {profession} riceve una telefonata anonima: ha {hours} ore per trovare {amount} milioni o sua figlia morirà. Ma niente è come sembra.",
        "Cinque estranei si svegliano in una stanza chiusa. Un messaggio dice che uno di loro è un assassino. Devono scoprire chi prima che le luci si spengano di nuovo.",
        "Un testimone chiave in un processo contro {organization} scompare la notte prima della deposizione. L'investigatrice che lo cerca scopre una cospirazione molto più grande.",
        "Un hacker scopre che {company} raccoglie dati per predire i crimini prima che accadano. Ma l'algoritmo ha iniziato a predire anche le proprie azioni correttive.",
    ],
    'animation': [
        "In un mondo dove {creatures} e umani convivono, un piccolo {creature} sogna di diventare {dream}. Ma per farlo deve attraversare {location} e affrontare le sue paure.",
        "I giocattoli di un museo prendono vita di notte. Quando un nuovo arrivato minaccia l'equilibrio, devono unirsi per salvare la loro casa segreta.",
        "Una bambina scopre che i suoi disegni prendono vita. Ma quando disegna accidentalmente {villain}, deve trovare il modo di cancellarlo prima che distrugga tutto.",
        "In una città sottomarina, un pesciolino scopre che l'oceano sta cambiando. Con i suoi amici improbabili, parte per un viaggio epico verso {destination}.",
    ],
    'documentary': [
        "Un'indagine rivoluzionaria su {topic} che rivela come {discovery} stia cambiando il nostro modo di vivere. Con testimonianze esclusive da {count} paesi.",
        "La storia mai raccontata di {person}, che ha cambiato {field} per sempre. Con materiale inedito e interviste a chi lo conosceva veramente.",
        "Come {phenomenon} sta ridisegnando il futuro dell'umanità. Un viaggio in {count} continenti per capire cosa ci aspetta.",
        "Dietro le quinte di {industry}: le vere storie, i sacrifici e le scoperte che il pubblico non ha mai visto.",
    ],
    'fantasy': [
        "Un ragazzo ordinario scopre di essere l'ultimo discendente di {lineage}. Per reclamare il suo destino, deve trovare {artifact} prima che {villain} lo faccia.",
        "In un regno dove la magia è proibita, una giovane {profession} scopre di avere il dono. Deve nascondersi dal {authority} mentre impara a controllare i suoi poteri.",
        "Cinque regni sono in guerra per il controllo di {resource}. Un'alleanza improbabile tra un {race1} e un {race2} è l'unica speranza per la pace.",
        "Un portale si apre in {location}, collegando il nostro mondo a {realm}. Cosa passa attraverso cambierà entrambi i mondi per sempre.",
    ],
    'musical': [
        "Un gruppo di artisti di strada si unisce per partecipare a {competition}. Tra rivalità, amori e sogni infranti, la musica diventa la loro salvezza.",
        "La storia di un compositore dimenticato le cui melodie vengono riscoperte {years} anni dopo e cambiano la vita di chi le ascolta.",
        "In una città dove la musica è stata bandita, un gruppo di ribelli usa le canzoni come arma di resistenza contro {authority}.",
    ],
    'western': [
        "Un pistolero stanco cerca redenzione in una piccola città di frontiera. Ma il suo passato lo raggiunge sotto forma di {villain}.",
        "La corsa all'oro del {year} vista attraverso gli occhi di {count} personaggi le cui vite si intrecciano in modi inaspettati.",
        "Una donna vedova difende il suo ranch contro {threat}. L'arrivo di uno straniero misterioso cambia le sorti della battaglia.",
    ],
    'war': [
        "Basato su eventi reali, la storia di {count} soldati intrappolati dietro le linee nemiche che devono attraversare {distance} km per tornare a casa.",
        "Un medico militare si rifiuta di portare armi in battaglia. La sua storia di coraggio e sacrificio durante {conflict} ispirerà generazioni.",
        "Due fratelli combattono su fronti opposti durante {conflict}. Quando si ritrovano, devono scegliere tra dovere e sangue.",
    ],
    'noir': [
        "Un detective privato viene assunto per trovare {person}. Ma più scava, più scopre che il vero mistero è chi lo ha assunto e perché.",
        "In una città corrotta fino al midollo, un informatore anonimo inizia a rivelare i segreti dei potenti. Tutti cercano di trovarlo, incluso chi non dovrebbe.",
        "Una femme fatale chiede aiuto a un avvocato in disgrazia. Il caso sembra semplice, ma ogni risposta porta a due nuove domande.",
    ],
    'adventure': [
        "Una mappa antica trovata in {location} porta a un tesoro dimenticato. Ma la caccia attira l'attenzione di {villain}, che farà di tutto per arrivarci primo.",
        "Un esploratore e una archeologa uniscono le forze per trovare {artifact} prima che cada nelle mani sbagliate. Il viaggio li porta attraverso {count} paesi.",
        "Un naufragio in mezzo all'oceano costringe un gruppo di sconosciuti a sopravvivere su un'isola misteriosa dove nulla è come sembra.",
    ],
    'biographical': [
        "La storia vera di {person}, da umili origini a {achievement}. Un racconto di determinazione, sacrificio e trionfo contro ogni previsione.",
        "La vita segreta di {person}: genio, scandali e un'eredità che ha cambiato {field} per sempre. Raccontata per la prima volta senza filtri.",
        "Come {person} ha sfidato {authority} e cambiato la storia. Un ritratto intimo di coraggio e visione.",
    ],
}

# Fill-in data for templates
TEMPLATE_FILLS = {
    'villain': ['un cartello internazionale', 'un genio del crimine', 'una corporazione senza scrupoli', 'un ex alleato tradito', 'un\'organizzazione segreta', 'un dittatore spietato'],
    'target': ['una città intera', 'la rete elettrica globale', 'i sistemi di comunicazione mondiali', 'il sistema bancario mondiale', 'un\'isola paradisiaca'],
    'hours': ['24', '48', '72', '12', '36'],
    'location': ['Tokyo', 'Istanbul', 'Buenos Aires', 'Praga', 'Marrakech', 'Singapore', 'Venezia', 'Rio de Janeiro', 'Vienna', 'Seoul'],
    'amount': ['50', '100', '200', '500', '80'],
    'secret': ['un\'arma biologica', 'documenti governativi classificati', 'la formula di un vaccino rivoluzionario', 'le prove di una cospirazione globale'],
    'organization': ['la CIA', 'un governo ombra', 'una setta militare', 'un consorzio di oligarchi'],
    'weapon': ['un\'arma climatica', 'nanotecnologia militare', 'un virus digitale', 'un satellite offensivo'],
    'threat': ['bande armate', 'creature sconosciute', 'un virus mortale', 'droni autonomi'],
    'profession': ['un contabile', 'un insegnante', 'un dentista', 'un postino', 'un bibliotecario', 'un tassista'],
    'profession2': ['una veterinaria', 'una chef', 'una fotografa', 'una pilota', 'una botanica'],
    'celebrity': ['un miliardario tech', 'una rockstar', 'un diplomatico', 'uno chef famoso'],
    'event': ['una cerimonia agli Oscar', 'un vertice del G7', 'un matrimonio reale', 'un festival di Cannes', 'una fashion week'],
    'animal': ['3 alpaca', 'un pappagallo parlante', '12 gatti', 'un cinghiale domestico'],
    'business': ['un food truck gourmet', 'un\'agenzia di detective', 'una scuola di ballo', 'un\'escape room'],
    'twist': ['diventano virali su TikTok', 'vincono un reality show', 'scoprono un talento nascosto', 'attirano l\'FBI'],
    'person': ['la persona che credeva morta', 'il suo primo amore', 'un fratello scomparso', 'un vecchio mentore'],
    'years': ['20', '30', '10', '15', '25', '40'],
    'people': ['5', '3', '7', '12'],
    'time': ['3:33', '2:17', 'mezzanotte', '4:44'],
    'room': ['seminterrato', 'sottotetto', 'corridoio del terzo piano', 'muro est della biblioteca'],
    'discovery': ['una creatura', 'un artefatto alieno', 'una capsula del tempo', 'un organismo sconosciuto'],
    'entity': ['l\'Uomo Senza Volto', 'la Voce nel Buio', 'il Visitatore', 'l\'Ombra'],
    'year': ['2089', '2147', '2250', '2312', '2077'],
    'boundary': ['il confine della galassia', 'un buco nero', 'la dimensione parallela', 'i limiti del sistema solare'],
    'planet': ['Kepler-442b', 'Proxima Centauri b', 'Marte', 'Europa (luna di Giove)', 'Titano'],
    'minutes': ['10', '30', '5', '60'],
    'city': ['Neo-Tokyo', 'una megalopoli', 'l\'ultima città sulla Terra', 'la Città Sommersa'],
    'days': ['7', '14', '3', '10'],
    'company': ['una big tech', 'il governo', 'una start-up misteriosa', 'una multinazionale farmaceutica'],
    'creatures': ['draghi', 'spiriti', 'robot', 'creature magiche'],
    'creature': ['drago', 'spirito della foresta', 'robot', 'folletto'],
    'dream': ['un cavaliere', 'un campione di volo', 'un cuoco stellato', 'un esploratore'],
    'destination': ['la Fossa delle Marianne', 'l\'Isola dei Coralli Perduti', 'la Città Sommersa', 'il Grande Abisso'],
    'topic': ['l\'intelligenza artificiale', 'il cambiamento climatico', 'la corsa allo spazio', 'la disinformazione digitale'],
    'field': ['la scienza', 'l\'arte', 'la politica', 'la musica', 'la medicina'],
    'count': ['3', '5', '7', '12', '4'],
    'phenomenon': ['la singolarità tecnologica', 'la migrazione climatica', 'la fusione nucleare', 'la colonizzazione spaziale'],
    'industry': ['Hollywood', 'Wall Street', 'la NASA', 'il calcio professionistico', 'la moda'],
    'lineage': ['una stirpe di re magici', 'i guardiani dell\'equilibrio', 'gli ultimi druidi', 'i custodi del tempo'],
    'artifact': ['la Spada dell\'Aurora', 'il Cristallo di Equilibrio', 'il Libro dei Mondi', 'l\'Anello del Destino'],
    'authority': ['il Re Oscuro', 'il Consiglio dei Maghi', 'l\'Inquisizione', 'l\'Ordine del Silenzio'],
    'resource': ['il Cristallo Eterno', 'la Sorgente di Magia', 'l\'Albero della Vita', 'la Luna di Ossidiana'],
    'race1': ['elfo', 'nano', 'umano', 'mago errante'],
    'race2': ['orco', 'gigante', 'folletto', 'drago mutaforma'],
    'realm': ['il Reame delle Ombre', 'Aetheria', 'il Mondo Sotterraneo', 'il Piano Astrale'],
    'competition': ['il Festival della Canzone Perduta', 'il Talent dei Talenti', 'Eurovision', 'un concorso di strada'],
    'conflict': ['la Seconda Guerra Mondiale', 'la Guerra di Corea', 'la Prima Guerra Mondiale', 'il conflitto nei Balcani'],
    'distance': ['300', '500', '150', '800'],
    'achievement': ['vincere il Nobel', 'rivoluzionare un\'industria', 'diventare leggenda', 'cambiare il mondo'],
}

def fill_template(template: str) -> str:
    """Fill a synopsis template with random data."""
    result = template
    import re
    placeholders = re.findall(r'\{(\w+)\}', template)
    for ph in placeholders:
        if ph in TEMPLATE_FILLS:
            result = result.replace('{' + ph + '}', random.choice(TEMPLATE_FILLS[ph]), 1)
    return result


# Title templates per genre
TITLE_TEMPLATES = {
    'action': ['Codice {word}', 'Operazione {word}', 'L\'Ultimo {word}', 'Fuoco e {word}', '{word} Letale', 'Punto di {word}', 'Oltre il {word}', '{word} Force'],
    'comedy': ['Che {word}!', 'Mamma Mia {word}', '{word} per Caso', 'Operazione {word}', 'Il Club dei {word}', '{word} & Disastri', 'Il {word} Perfetto'],
    'drama': ['Il {word} del Silenzio', 'Ombre di {word}', 'L\'Ultima {word}', 'Oltre il {word}', 'Senza {word}', 'Il Peso del {word}', 'Cenere e {word}'],
    'horror': ['La {word} Oscura', 'L\'Ombra di {word}', '{word} di Sangue', 'Il {word} Nero', 'Notte di {word}', '{word} Eterno', 'Il Risveglio di {word}'],
    'sci_fi': ['{word} 2099', 'Progetto {word}', 'Oltre {word}', 'Il Paradosso di {word}', 'Neo {word}', '{word} Protocol', 'Codice {word}'],
    'romance': ['Un {word} per Due', 'Il Sapore del {word}', 'Lettere a {word}', 'Prima del {word}', 'Il {word} di Sempre', '{word} a Mezzanotte'],
    'thriller': ['Il {word} Nascosto', 'Testimone {word}', 'L\'Inganno di {word}', 'Doppio {word}', 'La Trappola del {word}', 'Senza {word}'],
    'animation': ['Il Viaggio di {word}', '{word} e il Mondo Magico', 'La Leggenda di {word}', 'Il Segreto di {word}', '{word} Adventures'],
    'documentary': ['{word}: La Verità', 'Dietro {word}', 'Il Futuro di {word}', '{word} - Un\'Indagine', 'Dentro {word}'],
    'fantasy': ['Il Reame di {word}', 'La Profezia di {word}', '{word} e la Corona Perduta', 'L\'Era di {word}', 'Cronache di {word}'],
    'musical': ['{word} - Il Musical', 'La Melodia di {word}', 'Ritmo {word}', '{word} on Stage', 'Note di {word}'],
    'western': ['Il Fuorilegge di {word}', '{word} Valley', 'L\'Ultimo {word}', 'Mezzogiorno a {word}', 'Polvere di {word}'],
    'war': ['La Battaglia di {word}', 'Fratelli di {word}', '{word} sotto il Fuoco', 'L\'Assedio di {word}', 'Oltre la Linea di {word}'],
    'noir': ['L\'Affare {word}', 'Notti di {word}', 'Il Caso {word}', '{word} Boulevard', 'Ombre su {word}'],
    'adventure': ['La Ricerca di {word}', '{word} Expedition', 'I Tesori di {word}', 'Viaggio a {word}', 'L\'Isola di {word}'],
    'biographical': ['{word}', 'La Storia di {word}', '{word}: Una Vita', 'Il Genio di {word}', '{word} - Contro Tutti'],
}

TITLE_WORDS = {
    'action': ['Inferno', 'Tempesta', 'Tuono', 'Vulcano', 'Titanio', 'Raptor', 'Phoenix', 'Omega', 'Viper', 'Alpha', 'Acciaio', 'Fuoco'],
    'comedy': ['Follia', 'Caos', 'Papà', 'Suocera', 'Vacanza', 'Miracolo', 'Pasticcio', 'Disastro', 'Matrimonio', 'Casino'],
    'drama': ['Vetro', 'Tempo', 'Grazia', 'Confine', 'Perdono', 'Destino', 'Ritorno', 'Silenzio', 'Cenere', 'Coraggio'],
    'horror': ['Porta', 'Casa', 'Luna', 'Bambola', 'Specchio', 'Cripta', 'Notte', 'Peccato', 'Maledizione', 'Abisso'],
    'sci_fi': ['Nebula', 'Quantum', 'Orion', 'Zenith', 'Helix', 'Atlas', 'Nexus', 'Nova', 'Singularity', 'Eclipse'],
    'romance': ['Bacio', 'Cuore', 'Destino', 'Luna', 'Sorriso', 'Promessa', 'Tramonto', 'Amore', 'Sogno', 'Primavera'],
    'thriller': ['Segreto', 'Inganno', 'Volto', 'Gioco', 'Ombra', 'Codice', 'Traccia', 'Complotto', 'Buio', 'Verità'],
    'animation': ['Lumino', 'Zara', 'Kiko', 'Felix', 'Luna', 'Bibo', 'Talia', 'Nemo', 'Cosmo', 'Pip'],
    'documentary': ['l\'AI', 'Hollywood', 'la Natura', 'il Potere', 'la Scienza', 'il Mare', 'lo Spazio', 'la Moda'],
    'fantasy': ['Eldoria', 'Valon', 'Mythra', 'Aether', 'Kaelen', 'Draven', 'Sylvan', 'Onyx', 'Aurora'],
    'musical': ['Broadway', 'Jazz', 'Soul', 'Sinfonia', 'Armonia', 'Blues', 'Ritmo', 'Melodia'],
    'western': ['Tombstone', 'Canyon', 'Coyote', 'Desperado', 'Frontiera', 'Fuoco', 'Sierra', 'Mesquite'],
    'war': ['Stalingrado', 'Normandia', 'Verdun', 'Sangue', 'Trincea', 'Coraggio', 'Fuoco', 'Sacrificio'],
    'noir': ['Noir', 'Cromo', 'Cenere', 'Veleno', 'Piombo', 'Fumo', 'Neon', 'Velluto'],
    'adventure': ['Atlantide', 'El Dorado', 'Avalon', 'Shangri-La', 'Amazonia', 'Krakatoa', 'Himalaya'],
    'biographical': ['Einstein', 'Da Vinci', 'Tesla', 'Curie', 'Fibonacci', 'Verdi', 'Caravaggio', 'Colombo'],
}

def generate_title(genre: str) -> str:
    """Generate a random film title for a genre."""
    templates = TITLE_TEMPLATES.get(genre, TITLE_TEMPLATES['drama'])
    words = TITLE_WORDS.get(genre, TITLE_WORDS['drama'])
    template = random.choice(templates)
    word = random.choice(words)
    return template.replace('{word}', word)


def generate_synopsis(genre: str) -> str:
    """Generate a random synopsis for a genre."""
    templates = SYNOPSIS_TEMPLATES.get(genre, SYNOPSIS_TEMPLATES['drama'])
    template = random.choice(templates)
    return fill_template(template)


def calculate_story_rating(screenwriter_skills: dict, genre: str) -> float:
    """Calculate IMDb-style rating (1-10) based on screenwriter skills and story quality."""
    avg_skill = sum(screenwriter_skills.values()) / max(len(screenwriter_skills), 1)
    
    # Base from screenwriter skill (maps 0-100 to ~3-8)
    base = 2.5 + (avg_skill / 100) * 5.5
    
    # Genre-relevant skill bonus
    genre_skill_map = {
        'action': 'suspense_craft', 'comedy': 'humor_writing', 'drama': 'emotional_impact',
        'horror': 'suspense_craft', 'sci_fi': 'world_building', 'romance': 'emotional_impact',
        'thriller': 'suspense_craft', 'animation': 'originality', 'documentary': 'research',
        'fantasy': 'world_building', 'musical': 'emotional_impact', 'western': 'character_development',
        'war': 'emotional_impact', 'noir': 'dialogue', 'adventure': 'plot_structure',
        'biographical': 'research',
    }
    relevant_skill = genre_skill_map.get(genre, 'plot_structure')
    if relevant_skill in screenwriter_skills:
        skill_bonus = (screenwriter_skills[relevant_skill] - 50) / 100
        base += skill_bonus
    
    # Random variance
    base += random.uniform(-0.6, 0.6)
    
    return round(max(1.0, min(9.5, base)), 1)


def calculate_full_package_rating(story_rating: float, cast_members: list, director: dict) -> float:
    """Calculate combined rating with cast and director."""
    # Start from story rating
    combined = story_rating
    
    # Director bonus (avg skill maps to ±1.0)
    dir_skills = director.get('skills', {})
    dir_avg = sum(dir_skills.values()) / max(len(dir_skills), 1)
    combined += (dir_avg - 50) / 50  # -1 to +1
    
    # Cast bonus (average stars maps to ±0.8)
    if cast_members:
        avg_stars = sum(c.get('stars', 3) for c in cast_members) / len(cast_members)
        combined += (avg_stars - 3) * 0.4  # -0.8 to +0.8
    
    # Synergy bonus (random)
    combined += random.uniform(-0.3, 0.5)
    
    return round(max(1.0, min(9.8, combined)), 1)


def calculate_screenplay_cost(story_rating: float, screenwriter_stars: int) -> int:
    """Calculate cost of the screenplay only."""
    # Base: 300K to 2.5M depending on quality
    base = 300000
    rating_multiplier = (story_rating / 10) ** 2  # Exponential scaling
    star_multiplier = 0.7 + (screenwriter_stars * 0.2)  # 0.9x to 1.7x
    
    cost = int(base + (2200000 * rating_multiplier * star_multiplier))
    # Add some randomness
    cost = int(cost * random.uniform(0.85, 1.15))
    # Round to nearest 10K
    cost = round(cost / 10000) * 10000
    return max(200000, min(3000000, cost))


def calculate_full_package_cost(screenplay_cost: int, cast_members: list, director: dict) -> int:
    """Calculate total cost for full package - reduced cost for the new pipeline system."""
    total = screenplay_cost
    total += director.get('cost', 200000)
    for actor in cast_members:
        total += actor.get('cost', 100000)
    # Significant discount for buying the package (-40% to -50%)
    discount = random.uniform(0.50, 0.60)
    return round(int(total * discount) / 10000) * 10000


# Actor roles for different genres
ROLE_TEMPLATES = {
    'action': ['Protagonista', 'Antagonista', 'Spalla', 'Agente', 'Mercenario'],
    'comedy': ['Protagonista', 'Migliore Amico/a', 'Interesse Amoroso', 'Vicino Eccentrico', 'Boss Pazzo'],
    'drama': ['Protagonista', 'Coniuge', 'Figlio/a', 'Mentore', 'Antagonista'],
    'horror': ['Protagonista', 'La Vittima', 'L\'Esperto', 'L\'Incredulo', 'Il Sopravvissuto'],
    'sci_fi': ['Capitano', 'Scienziato/a', 'Pilota', 'Ingegnere', 'Ufficiale'],
    'romance': ['Protagonista', 'Interesse Amoroso', 'Migliore Amico/a', 'Ex', 'Rivale'],
    'thriller': ['Detective', 'Sospettato', 'Testimone', 'Vittima', 'Informatore'],
    'fantasy': ['L\'Eletto', 'Il Saggio', 'Il Guerriero', 'Il Traditore', 'Il Guardiano'],
    'war': ['Comandante', 'Soldato', 'Medico', 'Nemico', 'Civile'],
    'western': ['Lo Sceriffo', 'Il Fuorilegge', 'Il Barista', 'La Vedova', 'Il Cacciatore'],
    'noir': ['Il Detective', 'La Femme Fatale', 'Il Boss', 'L\'Informatore', 'La Vittima'],
}

def get_roles_for_genre(genre: str, count: int) -> list:
    """Get appropriate role names for a genre."""
    roles = ROLE_TEMPLATES.get(genre, ROLE_TEMPLATES['drama'])
    # Pad with generic roles if needed
    while len(roles) < count:
        roles.append(f'Personaggio {len(roles) + 1}')
    return roles[:count]
