# CineWorld Studio's - Minigame Data & Questions
# Contains game definitions, trivia questions, and challenge definitions

import random
import logging
import os

MINI_GAMES = [
    {'id': 'trivia', 'name': 'Film Trivia', 'description': 'Answer movie questions', 'reward_min': 5000, 'reward_max': 50000, 'cooldown_minutes': 30, 'questions_count': 5},
    {'id': 'guess_genre', 'name': 'Guess the Genre', 'description': 'Match films to their genres', 'reward_min': 3000, 'reward_max': 30000, 'cooldown_minutes': 20, 'questions_count': 5},
    {'id': 'director_match', 'name': 'Director Match', 'description': 'Match directors to their famous films', 'reward_min': 4000, 'reward_max': 40000, 'cooldown_minutes': 25, 'questions_count': 5},
    {'id': 'box_office_bet', 'name': 'Box Office Bet', 'description': 'Guess which film earned more', 'reward_min': 10000, 'reward_max': 100000, 'cooldown_minutes': 60, 'questions_count': 3},
    {'id': 'year_guess', 'name': 'Release Year', 'description': 'Guess when films were released', 'reward_min': 6000, 'reward_max': 60000, 'cooldown_minutes': 45, 'questions_count': 5}
]

# Trivia Questions Database - Multilingual
TRIVIA_QUESTIONS = {
    'en': [
        {'question': 'Which film won Best Picture at the 2020 Oscars?', 'options': ['1917', 'Parasite', 'Joker', 'Once Upon a Time in Hollywood'], 'answer': 'Parasite'},
        {'question': 'Who directed "Inception"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'What year was "The Godfather" released?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Which actor played Jack in "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'What is the highest-grossing film of all time?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: The Force Awakens'], 'answer': 'Avatar'},
        {'question': 'Who directed "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'In which film does Tom Hanks say "Life is like a box of chocolates"?', 'options': ['Cast Away', 'Forrest Gump', 'The Green Mile', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'What is the name of the fictional African country in "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Who played the Joker in "The Dark Knight"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'Which film features a character named Andy Dufresne?', 'options': ['The Green Mile', 'The Shawshank Redemption', 'Stand By Me', 'Misery'], 'answer': 'The Shawshank Redemption'},
    ],
    'it': [
        {'question': 'Quale film ha vinto il miglior film agli Oscar 2020?', 'options': ['1917', 'Parasite', 'Joker', 'C\'era una volta a Hollywood'], 'answer': 'Parasite'},
        {'question': 'Chi ha diretto "Inception"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'In che anno è uscito "Il Padrino"?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Quale attore ha interpretato Jack in "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'Qual è il film con il maggior incasso di tutti i tempi?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: Il risveglio della Forza'], 'answer': 'Avatar'},
        {'question': 'Chi ha diretto "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'In quale film Tom Hanks dice "La vita è come una scatola di cioccolatini"?', 'options': ['Cast Away', 'Forrest Gump', 'Il miglio verde', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'Come si chiama il paese africano immaginario in "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Chi ha interpretato il Joker in "Il cavaliere oscuro"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'In quale film appare il personaggio Andy Dufresne?', 'options': ['Il miglio verde', 'Le ali della libertà', 'Stand By Me', 'Misery'], 'answer': 'Le ali della libertà'},
    ],
    'es': [
        {'question': '¿Qué película ganó el Oscar a la Mejor Película en 2020?', 'options': ['1917', 'Parásitos', 'Joker', 'Érase una vez en Hollywood'], 'answer': 'Parásitos'},
        {'question': '¿Quién dirigió "Origen"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': '¿En qué año se estrenó "El Padrino"?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': '¿Qué actor interpretó a Jack en "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': '¿Cuál es la película más taquillera de todos los tiempos?', 'options': ['Avatar', 'Vengadores: Endgame', 'Titanic', 'Star Wars: El despertar de la Fuerza'], 'answer': 'Avatar'},
        {'question': '¿Quién dirigió "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': '¿En qué película Tom Hanks dice "La vida es como una caja de bombones"?', 'options': ['Náufrago', 'Forrest Gump', 'La milla verde', 'Big'], 'answer': 'Forrest Gump'},
        {'question': '¿Cómo se llama el país africano ficticio en "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': '¿Quién interpretó al Joker en "El caballero oscuro"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': '¿En qué película aparece el personaje Andy Dufresne?', 'options': ['La milla verde', 'Cadena perpetua', 'Cuenta conmigo', 'Misery'], 'answer': 'Cadena perpetua'},
    ],
    'fr': [
        {'question': 'Quel film a remporté l\'Oscar du meilleur film en 2020?', 'options': ['1917', 'Parasite', 'Joker', 'Once Upon a Time in Hollywood'], 'answer': 'Parasite'},
        {'question': 'Qui a réalisé "Inception"?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'En quelle année "Le Parrain" est-il sorti?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Quel acteur a joué Jack dans "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'Quel est le film le plus rentable de tous les temps?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: Le Réveil de la Force'], 'answer': 'Avatar'},
        {'question': 'Qui a réalisé "Pulp Fiction"?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'Dans quel film Tom Hanks dit "La vie c\'est comme une boîte de chocolats"?', 'options': ['Seul au monde', 'Forrest Gump', 'La Ligne verte', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'Comment s\'appelle le pays africain fictif dans "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Qui a joué le Joker dans "The Dark Knight"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'Dans quel film apparaît le personnage Andy Dufresne?', 'options': ['La Ligne verte', 'Les Évadés', 'Stand By Me', 'Misery'], 'answer': 'Les Évadés'},
    ],
    'de': [
        {'question': 'Welcher Film gewann 2020 den Oscar für den besten Film?', 'options': ['1917', 'Parasite', 'Joker', 'Once Upon a Time in Hollywood'], 'answer': 'Parasite'},
        {'question': 'Wer führte bei "Inception" Regie?', 'options': ['Steven Spielberg', 'Christopher Nolan', 'Martin Scorsese', 'James Cameron'], 'answer': 'Christopher Nolan'},
        {'question': 'In welchem Jahr wurde "Der Pate" veröffentlicht?', 'options': ['1970', '1972', '1974', '1976'], 'answer': '1972'},
        {'question': 'Welcher Schauspieler spielte Jack in "Titanic"?', 'options': ['Brad Pitt', 'Tom Hanks', 'Leonardo DiCaprio', 'Johnny Depp'], 'answer': 'Leonardo DiCaprio'},
        {'question': 'Was ist der erfolgreichste Film aller Zeiten?', 'options': ['Avatar', 'Avengers: Endgame', 'Titanic', 'Star Wars: Das Erwachen der Macht'], 'answer': 'Avatar'},
        {'question': 'Wer führte bei "Pulp Fiction" Regie?', 'options': ['Quentin Tarantino', 'Martin Scorsese', 'Ridley Scott', 'David Fincher'], 'answer': 'Quentin Tarantino'},
        {'question': 'In welchem Film sagt Tom Hanks "Das Leben ist wie eine Schachtel Pralinen"?', 'options': ['Cast Away', 'Forrest Gump', 'The Green Mile', 'Big'], 'answer': 'Forrest Gump'},
        {'question': 'Wie heißt das fiktive afrikanische Land in "Black Panther"?', 'options': ['Zamunda', 'Wakanda', 'Genovia', 'Latveria'], 'answer': 'Wakanda'},
        {'question': 'Wer spielte den Joker in "The Dark Knight"?', 'options': ['Jared Leto', 'Joaquin Phoenix', 'Heath Ledger', 'Jack Nicholson'], 'answer': 'Heath Ledger'},
        {'question': 'In welchem Film kommt die Figur Andy Dufresne vor?', 'options': ['The Green Mile', 'Die Verurteilten', 'Stand By Me', 'Misery'], 'answer': 'Die Verurteilten'},
    ]
}

GENRE_QUESTIONS = {
    'en': [
        {'question': '"The Exorcist" (1973)', 'options': ['Action', 'Comedy', 'Horror', 'Drama'], 'answer': 'Horror'},
        {'question': '"The Hangover" (2009)', 'options': ['Horror', 'Comedy', 'Drama', 'Thriller'], 'answer': 'Comedy'},
        {'question': '"Schindler\'s List" (1993)', 'options': ['Comedy', 'Action', 'Drama', 'Sci-Fi'], 'answer': 'Drama'},
        {'question': '"Die Hard" (1988)', 'options': ['Comedy', 'Romance', 'Action', 'Horror'], 'answer': 'Action'},
        {'question': '"The Notebook" (2004)', 'options': ['Action', 'Horror', 'Comedy', 'Romance'], 'answer': 'Romance'},
        {'question': '"Alien" (1979)', 'options': ['Comedy', 'Sci-Fi', 'Drama', 'Romance'], 'answer': 'Sci-Fi'},
        {'question': '"The Silence of the Lambs" (1991)', 'options': ['Comedy', 'Romance', 'Action', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Finding Nemo" (2003)', 'options': ['Horror', 'Animation', 'Drama', 'Action'], 'answer': 'Animation'},
    ],
    'it': [
        {'question': '"L\'Esorcista" (1973)', 'options': ['Azione', 'Commedia', 'Horror', 'Drammatico'], 'answer': 'Horror'},
        {'question': '"Una notte da leoni" (2009)', 'options': ['Horror', 'Commedia', 'Drammatico', 'Thriller'], 'answer': 'Commedia'},
        {'question': '"Schindler\'s List" (1993)', 'options': ['Commedia', 'Azione', 'Drammatico', 'Fantascienza'], 'answer': 'Drammatico'},
        {'question': '"Die Hard" (1988)', 'options': ['Commedia', 'Romantico', 'Azione', 'Horror'], 'answer': 'Azione'},
        {'question': '"Le pagine della nostra vita" (2004)', 'options': ['Azione', 'Horror', 'Commedia', 'Romantico'], 'answer': 'Romantico'},
        {'question': '"Alien" (1979)', 'options': ['Commedia', 'Fantascienza', 'Drammatico', 'Romantico'], 'answer': 'Fantascienza'},
        {'question': '"Il silenzio degli innocenti" (1991)', 'options': ['Commedia', 'Romantico', 'Azione', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Alla ricerca di Nemo" (2003)', 'options': ['Horror', 'Animazione', 'Drammatico', 'Azione'], 'answer': 'Animazione'},
    ],
    'es': [
        {'question': '"El Exorcista" (1973)', 'options': ['Acción', 'Comedia', 'Terror', 'Drama'], 'answer': 'Terror'},
        {'question': '"Resacón en Las Vegas" (2009)', 'options': ['Terror', 'Comedia', 'Drama', 'Suspense'], 'answer': 'Comedia'},
        {'question': '"La lista de Schindler" (1993)', 'options': ['Comedia', 'Acción', 'Drama', 'Ciencia Ficción'], 'answer': 'Drama'},
        {'question': '"Jungla de cristal" (1988)', 'options': ['Comedia', 'Romance', 'Acción', 'Terror'], 'answer': 'Acción'},
        {'question': '"Diario de una pasión" (2004)', 'options': ['Acción', 'Terror', 'Comedia', 'Romance'], 'answer': 'Romance'},
        {'question': '"Alien" (1979)', 'options': ['Comedia', 'Ciencia Ficción', 'Drama', 'Romance'], 'answer': 'Ciencia Ficción'},
        {'question': '"El silencio de los corderos" (1991)', 'options': ['Comedia', 'Romance', 'Acción', 'Suspense'], 'answer': 'Suspense'},
        {'question': '"Buscando a Nemo" (2003)', 'options': ['Terror', 'Animación', 'Drama', 'Acción'], 'answer': 'Animación'},
    ],
    'fr': [
        {'question': '"L\'Exorciste" (1973)', 'options': ['Action', 'Comédie', 'Horreur', 'Drame'], 'answer': 'Horreur'},
        {'question': '"Very Bad Trip" (2009)', 'options': ['Horreur', 'Comédie', 'Drame', 'Thriller'], 'answer': 'Comédie'},
        {'question': '"La Liste de Schindler" (1993)', 'options': ['Comédie', 'Action', 'Drame', 'Science-Fiction'], 'answer': 'Drame'},
        {'question': '"Piège de cristal" (1988)', 'options': ['Comédie', 'Romance', 'Action', 'Horreur'], 'answer': 'Action'},
        {'question': '"N\'oublie jamais" (2004)', 'options': ['Action', 'Horreur', 'Comédie', 'Romance'], 'answer': 'Romance'},
        {'question': '"Alien" (1979)', 'options': ['Comédie', 'Science-Fiction', 'Drame', 'Romance'], 'answer': 'Science-Fiction'},
        {'question': '"Le Silence des agneaux" (1991)', 'options': ['Comédie', 'Romance', 'Action', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Le Monde de Nemo" (2003)', 'options': ['Horreur', 'Animation', 'Drame', 'Action'], 'answer': 'Animation'},
    ],
    'de': [
        {'question': '"Der Exorzist" (1973)', 'options': ['Action', 'Komödie', 'Horror', 'Drama'], 'answer': 'Horror'},
        {'question': '"Hangover" (2009)', 'options': ['Horror', 'Komödie', 'Drama', 'Thriller'], 'answer': 'Komödie'},
        {'question': '"Schindlers Liste" (1993)', 'options': ['Komödie', 'Action', 'Drama', 'Science-Fiction'], 'answer': 'Drama'},
        {'question': '"Stirb langsam" (1988)', 'options': ['Komödie', 'Romanze', 'Action', 'Horror'], 'answer': 'Action'},
        {'question': '"Wie ein einziger Tag" (2004)', 'options': ['Action', 'Horror', 'Komödie', 'Romanze'], 'answer': 'Romanze'},
        {'question': '"Alien" (1979)', 'options': ['Komödie', 'Science-Fiction', 'Drama', 'Romanze'], 'answer': 'Science-Fiction'},
        {'question': '"Das Schweigen der Lämmer" (1991)', 'options': ['Komödie', 'Romanze', 'Action', 'Thriller'], 'answer': 'Thriller'},
        {'question': '"Findet Nemo" (2003)', 'options': ['Horror', 'Animation', 'Drama', 'Action'], 'answer': 'Animation'},
    ]
}

DIRECTOR_QUESTIONS = {
    'en': [
        {'question': 'Who directed "E.T. the Extra-Terrestrial"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Who directed "The Shining"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Who directed "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Who directed "Fight Club"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Who directed "The Lord of the Rings" trilogy?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'it': [
        {'question': 'Chi ha diretto "E.T. l\'extra-terrestre"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Chi ha diretto "Shining"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Chi ha diretto "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Chi ha diretto "Fight Club"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Chi ha diretto la trilogia "Il Signore degli Anelli"?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'es': [
        {'question': '¿Quién dirigió "E.T. el extraterrestre"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': '¿Quién dirigió "El resplandor"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': '¿Quién dirigió "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': '¿Quién dirigió "El club de la lucha"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': '¿Quién dirigió la trilogía "El Señor de los Anillos"?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'fr': [
        {'question': 'Qui a réalisé "E.T. l\'extra-terrestre"?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Qui a réalisé "Shining"?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Qui a réalisé "Avatar"?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Qui a réalisé "Fight Club"?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Qui a réalisé la trilogie "Le Seigneur des Anneaux"?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ],
    'de': [
        {'question': 'Wer führte bei "E.T. - Der Außerirdische" Regie?', 'options': ['George Lucas', 'Steven Spielberg', 'James Cameron', 'Ridley Scott'], 'answer': 'Steven Spielberg'},
        {'question': 'Wer führte bei "Shining" Regie?', 'options': ['Stanley Kubrick', 'Alfred Hitchcock', 'John Carpenter', 'Wes Craven'], 'answer': 'Stanley Kubrick'},
        {'question': 'Wer führte bei "Avatar" Regie?', 'options': ['Steven Spielberg', 'Peter Jackson', 'James Cameron', 'Christopher Nolan'], 'answer': 'James Cameron'},
        {'question': 'Wer führte bei "Fight Club" Regie?', 'options': ['David Fincher', 'Quentin Tarantino', 'Martin Scorsese', 'Darren Aronofsky'], 'answer': 'David Fincher'},
        {'question': 'Wer führte bei "Der Herr der Ringe"-Trilogie Regie?', 'options': ['Peter Jackson', 'Guillermo del Toro', 'Sam Raimi', 'Terry Gilliam'], 'answer': 'Peter Jackson'},
    ]
}

BOX_OFFICE_QUESTIONS = {
    'en': [
        {'question': 'Which film earned more worldwide?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Which film earned more worldwide?', 'options': ['The Lion King 2019 ($1.6B)', 'Frozen II ($1.4B)'], 'answer': 'The Lion King 2019 ($1.6B)'},
        {'question': 'Which film earned more worldwide?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'it': [
        {'question': 'Quale film ha incassato di più nel mondo?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Quale film ha incassato di più nel mondo?', 'options': ['Il Re Leone 2019 ($1.6B)', 'Frozen II ($1.4B)'], 'answer': 'Il Re Leone 2019 ($1.6B)'},
        {'question': 'Quale film ha incassato di più nel mondo?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'es': [
        {'question': '¿Qué película recaudó más en todo el mundo?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': '¿Qué película recaudó más en todo el mundo?', 'options': ['El Rey León 2019 ($1.6B)', 'Frozen II ($1.4B)'], 'answer': 'El Rey León 2019 ($1.6B)'},
        {'question': '¿Qué película recaudó más en todo el mundo?', 'options': ['Vengadores: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'fr': [
        {'question': 'Quel film a rapporté le plus dans le monde?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Quel film a rapporté le plus dans le monde?', 'options': ['Le Roi Lion 2019 ($1.6B)', 'La Reine des neiges II ($1.4B)'], 'answer': 'Le Roi Lion 2019 ($1.6B)'},
        {'question': 'Quel film a rapporté le plus dans le monde?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ],
    'de': [
        {'question': 'Welcher Film hat weltweit mehr eingespielt?', 'options': ['Titanic ($2.2B)', 'Jurassic World ($1.6B)'], 'answer': 'Titanic ($2.2B)'},
        {'question': 'Welcher Film hat weltweit mehr eingespielt?', 'options': ['Der König der Löwen 2019 ($1.6B)', 'Die Eiskönigin II ($1.4B)'], 'answer': 'Der König der Löwen 2019 ($1.6B)'},
        {'question': 'Welcher Film hat weltweit mehr eingespielt?', 'options': ['Avengers: Endgame ($2.8B)', 'Avatar ($2.9B)'], 'answer': 'Avatar ($2.9B)'},
    ]
}

YEAR_QUESTIONS = {
    'en': [
        {'question': 'When was "Star Wars: A New Hope" released?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'When was "The Matrix" released?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'When was "Jaws" released?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'When was "Back to the Future" released?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'When was "Jurassic Park" released?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'it': [
        {'question': 'Quando è uscito "Star Wars: Una nuova speranza"?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'Quando è uscito "Matrix"?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'Quando è uscito "Lo squalo"?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'Quando è uscito "Ritorno al futuro"?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'Quando è uscito "Jurassic Park"?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'es': [
        {'question': '¿Cuándo se estrenó "Star Wars: Una nueva esperanza"?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': '¿Cuándo se estrenó "Matrix"?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': '¿Cuándo se estrenó "Tiburón"?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': '¿Cuándo se estrenó "Regreso al futuro"?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': '¿Cuándo se estrenó "Parque Jurásico"?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'fr': [
        {'question': 'Quand est sorti "Star Wars: Un nouvel espoir"?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'Quand est sorti "Matrix"?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'Quand est sorti "Les Dents de la mer"?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'Quand est sorti "Retour vers le futur"?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'Quand est sorti "Jurassic Park"?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ],
    'de': [
        {'question': 'Wann wurde "Star Wars: Eine neue Hoffnung" veröffentlicht?', 'options': ['1975', '1977', '1979', '1981'], 'answer': '1977'},
        {'question': 'Wann wurde "Matrix" veröffentlicht?', 'options': ['1997', '1998', '1999', '2000'], 'answer': '1999'},
        {'question': 'Wann wurde "Der weiße Hai" veröffentlicht?', 'options': ['1973', '1975', '1977', '1979'], 'answer': '1975'},
        {'question': 'Wann wurde "Zurück in die Zukunft" veröffentlicht?', 'options': ['1983', '1985', '1987', '1989'], 'answer': '1985'},
        {'question': 'Wann wurde "Jurassic Park" veröffentlicht?', 'options': ['1991', '1993', '1995', '1997'], 'answer': '1993'},
    ]
}

def get_questions_for_language(game_id: str, language: str):
    """Get questions in the specified language"""
    questions_map = {
        'trivia': TRIVIA_QUESTIONS,
        'guess_genre': GENRE_QUESTIONS,
        'director_match': DIRECTOR_QUESTIONS,
        'box_office_bet': BOX_OFFICE_QUESTIONS,
        'year_guess': YEAR_QUESTIONS
    }
    questions = questions_map.get(game_id, TRIVIA_QUESTIONS)
    return questions.get(language, questions.get('en', []))


async def generate_ai_questions(game_id: str, language: str, count: int, seen_questions: list = None):
    """Generate fresh AI-powered questions for mini-games. Falls back to static pool on failure."""
    import json as json_lib
    
    lang_map = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
    lang_name = lang_map.get(language, 'English')
    
    game_prompts = {
        'trivia': f"""Generate {count} unique film trivia multiple-choice questions in {lang_name}.
Each question should be about real movies, actors, directors, or cinema history.
Mix different decades (from 1920s to 2020s) and genres. Make them fun and varied in difficulty.
Format: JSON array of objects with "question", "options" (array of 4 choices), "answer" (the correct option, must be one of the options).""",
        
        'guess_genre': f"""Generate {count} unique "Guess the Genre" questions in {lang_name}.
Each question shows a real movie title with its year, and the player must pick the correct genre.
Use well-known films from different decades. Genres should be localized in {lang_name}.
Format: JSON array of objects with "question" (just the movie title and year, e.g. '"Inception" (2010)'), "options" (4 genre choices in {lang_name}), "answer" (correct genre in {lang_name}).""",
        
        'director_match': f"""Generate {count} unique "Who directed this film?" questions in {lang_name}.
Each question asks who directed a specific well-known film. Use famous directors and iconic movies.
Format: JSON array of objects with "question" (the question text), "options" (4 director names), "answer" (correct director name).""",
        
        'box_office_bet': f"""Generate {count} unique "Which film earned more at the box office?" questions in {lang_name}.
Each question compares two real films with their actual worldwide gross. Include the amounts in the options.
Format: JSON array of objects with "question" (the comparison question), "options" (2 choices with amounts like "Titanic ($2.2B)"), "answer" (the correct higher-earning film with amount).""",
        
        'year_guess': f"""Generate {count} unique "When was this film released?" questions in {lang_name}.
Each question asks about the release year of a well-known film. Offer 4 year options close together.
Format: JSON array of objects with "question" (the question text), "options" (4 year choices as strings), "answer" (correct year as string)."""
    }
    
    prompt = game_prompts.get(game_id)
    if not prompt:
        return get_questions_for_language(game_id, language)
    
    if seen_questions:
        seen_titles = seen_questions[:20]
        prompt += f"\n\nIMPORTANT: Do NOT use any of these films/questions that the player has already seen: {', '.join(seen_titles)}"
    
    prompt += "\n\nRespond ONLY with the JSON array, no other text."
    
    try:
        if not EMERGENT_LLM_KEY:
            return get_questions_for_language(game_id, language)
        
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"minigame-{game_id}-{uuid.uuid4()}",
            system_message="You are a cinema quiz master. Generate accurate, fun movie trivia questions. Always respond with valid JSON only."
        ).with_model("openai", "gpt-4o-mini")
        
        response = await chat.send_message(UserMessage(prompt))
        
        # Parse JSON from response (it's a string)
        text = response.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
            text = text.rsplit('```', 1)[0]
        text = text.strip()
        
        questions = json_lib.loads(text)
        
        if not isinstance(questions, list) or len(questions) < count:
            logging.warning(f"[MINIGAME AI] Invalid response format for {game_id}, falling back")
            return get_questions_for_language(game_id, language)
        
        # Validate structure
        for q in questions[:count]:
            if not all(k in q for k in ('question', 'options', 'answer')):
                return get_questions_for_language(game_id, language)
            if q['answer'] not in q['options']:
                # Fix: ensure answer is in options
                q['options'][-1] = q['answer']
        
        logging.info(f"[MINIGAME AI] Generated {len(questions)} fresh questions for {game_id}/{language}")
        return questions[:count]
    except Exception as e:
        logging.error(f"[MINIGAME AI] Error generating questions for {game_id}: {e}")
        return get_questions_for_language(game_id, language)

# Challenges
DAILY_CHALLENGES = [
    {'id': 'like_5_films', 'name': 'Social Butterfly', 'description': 'Like 5 films from other players', 'reward': 25000, 'target': 5},
    {'id': 'send_10_messages', 'name': 'Chatterbox', 'description': 'Send 10 messages in chat', 'reward': 15000, 'target': 10},
    {'id': 'play_3_minigames', 'name': 'Gamer', 'description': 'Play 3 mini games', 'reward': 30000, 'target': 3},
    {'id': 'visit_5_profiles', 'name': 'Explorer', 'description': 'Visit 5 player profiles', 'reward': 10000, 'target': 5}
]

WEEKLY_CHALLENGES = [
    {'id': 'create_film', 'name': 'Producer', 'description': 'Create and release a film', 'reward': 500000, 'target': 1},
    {'id': 'earn_1m', 'name': 'Mogul', 'description': 'Earn $1,000,000 from box office', 'reward': 250000, 'target': 1000000},
    {'id': 'get_50_likes', 'name': 'Fan Favorite', 'description': 'Get 50 likes on your films', 'reward': 200000, 'target': 50},
    {'id': 'win_3_pvp', 'name': 'Champion', 'description': 'Win 3 PvP challenges', 'reward': 300000, 'target': 3}
]

