"""
CineWorld Studio's - Enhanced Cast System v2
700 Cast Members with Variable Skills, Categories, and Bonus/Malus System
"""
import random
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set
import uuid

# ==================== SKILL DEFINITIONS (50+ skill totali) ====================
# Ogni tipo di cast ha ~13 skill possibili, ogni membro ne riceve esattamente 8

ACTOR_SKILLS = {
    'drama': {'it': 'Dramma'},
    'comedy': {'it': 'Commedia'},
    'action': {'it': 'Azione'},
    'romance': {'it': 'Romantico'},
    'horror': {'it': 'Horror'},
    'sci_fi': {'it': 'Fantascienza'},
    'voice_acting': {'it': 'Doppiaggio'},
    'improvisation': {'it': 'Improvvisazione'},
    'physical_acting': {'it': 'Recitazione Fisica'},
    'emotional_depth': {'it': 'Profondità Emotiva'},
    'charisma': {'it': 'Carisma'},
    'method_acting': {'it': 'Metodo Stanislavskij'},
    'timing': {'it': 'Senso del Tempo'},
}

DIRECTOR_SKILLS = {
    'vision': {'it': 'Visione Artistica'},
    'leadership': {'it': 'Leadership'},
    'actor_direction': {'it': 'Direzione Attori'},
    'visual_style': {'it': 'Stile Visivo'},
    'storytelling': {'it': 'Narrazione'},
    'technical': {'it': 'Tecnica'},
    'innovation': {'it': 'Innovazione'},
    'pacing': {'it': 'Ritmo'},
    'atmosphere': {'it': 'Atmosfera'},
    'casting_sense': {'it': 'Senso del Casting'},
    'editing_instinct': {'it': 'Istinto di Montaggio'},
    'world_building': {'it': 'Costruzione Mondi'},
    'budget_management': {'it': 'Gestione Budget'},
}

SCREENWRITER_SKILLS = {
    'dialogue': {'it': 'Dialoghi'},
    'plot_structure': {'it': 'Struttura Trama'},
    'character_development': {'it': 'Sviluppo Personaggi'},
    'originality': {'it': 'Originalità'},
    'adaptation': {'it': 'Adattamento'},
    'pacing': {'it': 'Ritmo Narrativo'},
    'world_building': {'it': 'Creazione Mondi'},
    'emotional_impact': {'it': 'Impatto Emotivo'},
    'humor_writing': {'it': 'Scrittura Umoristica'},
    'suspense_craft': {'it': 'Costruzione Suspense'},
    'subtext': {'it': 'Sottotesto'},
    'theme_depth': {'it': 'Profondità Tematica'},
    'research': {'it': 'Ricerca'},
}

COMPOSER_SKILLS = {
    'melodic': {'it': 'Composizione Melodica'},
    'orchestration': {'it': 'Orchestrazione'},
    'emotional_scoring': {'it': 'Musica Emotiva'},
    'genre_versatility': {'it': 'Versatilità Generi'},
    'sound_design': {'it': 'Sound Design'},
    'theme_development': {'it': 'Sviluppo Temi'},
    'rhythm': {'it': 'Ritmo'},
    'harmony': {'it': 'Armonia'},
    'electronic_production': {'it': 'Produzione Elettronica'},
    'leitmotif': {'it': 'Leitmotiv'},
    'ambient_scoring': {'it': 'Musica Ambientale'},
    'mixing': {'it': 'Missaggio'},
    'vocal_arrangements': {'it': 'Arrangiamenti Vocali'},
}

# SKILLS_PER_MEMBER: ogni membro del cast ha esattamente 8 skill
SKILLS_PER_MEMBER = 8

# Film genres and their matching actor skills for bonus/malus
GENRE_SKILL_MAPPING = {
    'action': ['action', 'physical_acting'],
    'comedy': ['comedy', 'timing', 'improvisation'],
    'drama': ['drama', 'emotional_depth', 'method_acting'],
    'horror': ['horror', 'physical_acting'],
    'sci_fi': ['sci_fi', 'voice_acting'],
    'romance': ['romance', 'emotional_depth', 'charisma'],
    'thriller': ['drama', 'action', 'emotional_depth'],
    'animation': ['voice_acting', 'comedy', 'timing'],
    'documentary': ['drama', 'charisma'],
    'fantasy': ['drama', 'action', 'physical_acting'],
    'musical': ['voice_acting', 'comedy', 'timing'],
    'western': ['action', 'drama', 'physical_acting'],
    'war': ['drama', 'action', 'emotional_depth'],
    'noir': ['drama', 'emotional_depth'],
    'adventure': ['action', 'charisma', 'physical_acting'],
    'biographical': ['drama', 'method_acting', 'emotional_depth'],
}

# Categories and their star ranges
CAST_CATEGORIES = {
    'recommended': {'en': 'Recommended', 'it': 'Consigliati', 'es': 'Recomendados', 'fr': 'Recommandés', 'de': 'Empfohlen', 'stars_range': (4, 5), 'count_factor': 0.15},
    'star': {'en': 'Star', 'it': 'Star', 'es': 'Estrella', 'fr': 'Star', 'de': 'Star', 'stars_range': (4, 5), 'count_factor': 0.2},
    'known': {'en': 'Known', 'it': 'Conosciuti', 'es': 'Conocidos', 'fr': 'Connus', 'de': 'Bekannt', 'stars_range': (3, 4), 'count_factor': 0.25},
    'emerging': {'en': 'Emerging', 'it': 'Emergenti', 'es': 'Emergentes', 'fr': 'Émergents', 'de': 'Aufsteigend', 'stars_range': (2, 3), 'count_factor': 0.25},
    'unknown': {'en': 'Unknown', 'it': 'Sconosciuti', 'es': 'Desconocidos', 'fr': 'Inconnus', 'de': 'Unbekannt', 'stars_range': (1, 2), 'count_factor': 0.15},
}

# ==================== NAME GENERATION ====================

EXPANDED_NAMES = {
    'USA': {
        'first_male': ['James', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Christopher', 'Charles',
                       'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth',
                       'Kevin', 'Brian', 'George', 'Timothy', 'Ronald', 'Edward', 'Jason', 'Jeffrey', 'Ryan', 'Jacob',
                       'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin'],
        'first_female': ['Mary', 'Patricia', 'Jennifer', 'Linda', 'Barbara', 'Elizabeth', 'Susan', 'Jessica', 'Sarah', 'Karen',
                         'Lisa', 'Nancy', 'Betty', 'Margaret', 'Sandra', 'Ashley', 'Kimberly', 'Emily', 'Donna', 'Michelle',
                         'Dorothy', 'Carol', 'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Rebecca', 'Sharon', 'Laura', 'Cynthia',
                         'Kathleen', 'Amy', 'Angela', 'Shirley', 'Anna', 'Brenda', 'Pamela', 'Emma', 'Nicole', 'Helen'],
        'last': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
                 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson']
    },
    'UK': {
        'first_male': ['Oliver', 'George', 'Harry', 'Jack', 'Jacob', 'Noah', 'Charlie', 'Oscar', 'James', 'William',
                       'Henry', 'Alexander', 'Thomas', 'Edward', 'Benjamin', 'Samuel', 'Daniel', 'Joseph', 'David', 'Alfie'],
        'first_female': ['Olivia', 'Emma', 'Ava', 'Sophia', 'Isabella', 'Mia', 'Amelia', 'Charlotte', 'Emily', 'Grace',
                         'Poppy', 'Lily', 'Ella', 'Freya', 'Sophie', 'Chloe', 'Lucy', 'Hannah', 'Phoebe', 'Jessica'],
        'last': ['Smith', 'Jones', 'Williams', 'Taylor', 'Brown', 'Davies', 'Evans', 'Wilson', 'Thomas', 'Roberts',
                 'Johnson', 'Lewis', 'Walker', 'Robinson', 'Wood', 'Thompson', 'White', 'Watson', 'Jackson', 'Wright']
    },
    'Italy': {
        'first_male': ['Marco', 'Giuseppe', 'Giovanni', 'Antonio', 'Francesco', 'Mario', 'Luigi', 'Alessandro', 'Andrea', 'Luca',
                       'Roberto', 'Stefano', 'Angelo', 'Massimo', 'Pietro', 'Paolo', 'Salvatore', 'Vincenzo', 'Domenico', 'Matteo'],
        'first_female': ['Maria', 'Anna', 'Giulia', 'Francesca', 'Chiara', 'Sara', 'Laura', 'Valentina', 'Alessia', 'Elena',
                         'Federica', 'Martina', 'Silvia', 'Giorgia', 'Elisa', 'Roberta', 'Monica', 'Simona', 'Claudia', 'Paola'],
        'last': ['Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco',
                 'Bruno', 'Gallo', 'Conti', 'De Luca', 'Costa', 'Giordano', 'Mancini', 'Rizzo', 'Lombardi', 'Moretti']
    },
    'France': {
        'first_male': ['Jean', 'Pierre', 'Michel', 'André', 'Philippe', 'René', 'Louis', 'Alain', 'Jacques', 'Bernard',
                       'François', 'Marcel', 'Robert', 'Henri', 'Paul', 'Claude', 'Éric', 'Nicolas', 'Thomas', 'Alexandre'],
        'first_female': ['Marie', 'Jeanne', 'Françoise', 'Monique', 'Catherine', 'Nathalie', 'Isabelle', 'Sylvie', 'Anne', 'Martine',
                         'Camille', 'Léa', 'Emma', 'Manon', 'Chloé', 'Inès', 'Louise', 'Jade', 'Sarah', 'Élodie'],
        'last': ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau',
                 'Simon', 'Laurent', 'Lefebvre', 'Michel', 'Garcia', 'David', 'Bertrand', 'Roux', 'Vincent', 'Fournier']
    },
    'Spain': {
        'first_male': ['Antonio', 'José', 'Manuel', 'Francisco', 'David', 'Juan', 'Javier', 'Daniel', 'Carlos', 'Jesús',
                       'Alejandro', 'Miguel', 'Rafael', 'Pedro', 'Pablo', 'Ángel', 'Fernando', 'Luis', 'Alberto', 'Sergio'],
        'first_female': ['María', 'Carmen', 'Ana', 'Isabel', 'Laura', 'Cristina', 'Marta', 'Lucía', 'Elena', 'Rosa',
                         'Paula', 'Sara', 'Claudia', 'Andrea', 'Silvia', 'Raquel', 'Patricia', 'Beatriz', 'Natalia', 'Alba'],
        'last': ['García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández', 'Pérez', 'Sánchez', 'Ramírez', 'Torres',
                 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Reyes', 'Morales', 'Jiménez', 'Ruiz', 'Álvarez', 'Romero']
    },
    'Germany': {
        'first_male': ['Michael', 'Thomas', 'Andreas', 'Stefan', 'Christian', 'Markus', 'Daniel', 'Martin', 'Alexander', 'Jan',
                       'Matthias', 'Peter', 'Frank', 'Klaus', 'Jürgen', 'Wolfgang', 'Hans', 'Dieter', 'Uwe', 'Bernd'],
        'first_female': ['Maria', 'Ursula', 'Monika', 'Petra', 'Sabine', 'Andrea', 'Anna', 'Brigitte', 'Christine', 'Claudia',
                         'Julia', 'Sophie', 'Emma', 'Mia', 'Hannah', 'Lea', 'Lena', 'Sarah', 'Lisa', 'Laura'],
        'last': ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann',
                 'Schäfer', 'Koch', 'Bauer', 'Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann']
    },
    'Japan': {
        'first_male': ['Haruki', 'Yuki', 'Takeshi', 'Kenji', 'Hiroshi', 'Kazuki', 'Ryota', 'Shota', 'Daisuke', 'Yuto',
                       'Hayato', 'Kenta', 'Sho', 'Ren', 'Naoki', 'Ryu', 'Masashi', 'Taro', 'Akira', 'Koji'],
        'first_female': ['Yuki', 'Sakura', 'Aoi', 'Hana', 'Yui', 'Rin', 'Mio', 'Mei', 'Akari', 'Haruka',
                         'Nanami', 'Ayaka', 'Saki', 'Mika', 'Emi', 'Yuna', 'Riko', 'Miyu', 'Kana', 'Nana'],
        'last': ['Sato', 'Suzuki', 'Takahashi', 'Tanaka', 'Watanabe', 'Ito', 'Yamamoto', 'Nakamura', 'Kobayashi', 'Kato',
                 'Yoshida', 'Yamada', 'Sasaki', 'Yamaguchi', 'Matsumoto', 'Inoue', 'Kimura', 'Hayashi', 'Shimizu', 'Mori']
    },
    'India': {
        'first_male': ['Raj', 'Amit', 'Vikram', 'Rahul', 'Arun', 'Suresh', 'Vijay', 'Sanjay', 'Ajay', 'Manoj',
                       'Ravi', 'Krishna', 'Deepak', 'Anil', 'Rajesh', 'Mukesh', 'Sunil', 'Pradeep', 'Rakesh', 'Ashok'],
        'first_female': ['Priya', 'Anjali', 'Neha', 'Pooja', 'Divya', 'Sneha', 'Kavita', 'Sunita', 'Meena', 'Rekha',
                         'Anita', 'Deepa', 'Lakshmi', 'Radha', 'Geeta', 'Sita', 'Asha', 'Seema', 'Nisha', 'Ritu'],
        'last': ['Sharma', 'Patel', 'Singh', 'Kumar', 'Gupta', 'Shah', 'Mehta', 'Kapoor', 'Chopra', 'Malhotra',
                 'Joshi', 'Reddy', 'Rao', 'Verma', 'Agarwal', 'Mishra', 'Das', 'Nair', 'Menon', 'Pillai']
    },
    'Brazil': {
        'first_male': ['Pedro', 'Lucas', 'Gabriel', 'João', 'Matheus', 'Rafael', 'Gustavo', 'Felipe', 'Bruno', 'Leonardo',
                       'Rodrigo', 'Daniel', 'André', 'Marcos', 'Paulo', 'Thiago', 'Diego', 'Eduardo', 'Fernando', 'Carlos'],
        'first_female': ['Ana', 'Maria', 'Julia', 'Beatriz', 'Gabriela', 'Mariana', 'Amanda', 'Bruna', 'Camila', 'Fernanda',
                         'Letícia', 'Larissa', 'Juliana', 'Patricia', 'Carolina', 'Rafaela', 'Vanessa', 'Isabela', 'Natalia', 'Bianca'],
        'last': ['Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima', 'Gomes',
                 'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira', 'Barbosa']
    },
    'South Korea': {
        'first_male': ['Min-jun', 'Seo-jun', 'Do-yun', 'Ye-jun', 'Si-u', 'Ha-jun', 'Jun-seo', 'Ji-ho', 'Jun-woo', 'Hyun-woo',
                       'Ji-hoon', 'Seung-min', 'Jun-young', 'Tae-hyung', 'Min-ho', 'Jae-won', 'Sung-min', 'Woo-jin', 'Dong-hyun', 'Kyung-min'],
        'first_female': ['Seo-yeon', 'Ha-yoon', 'Ji-woo', 'Seo-yun', 'Ji-yoo', 'Ye-eun', 'Chae-won', 'Min-seo', 'So-yeon', 'Yu-na',
                         'Ji-min', 'Ye-ji', 'Hye-jin', 'Soo-jin', 'Eun-ji', 'Yoon-ah', 'Ha-na', 'Mi-young', 'Sun-hee', 'Jin-ah'],
        'last': ['Kim', 'Lee', 'Park', 'Choi', 'Jeong', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim',
                 'Han', 'Oh', 'Seo', 'Shin', 'Kwon', 'Hwang', 'Ahn', 'Song', 'Yu', 'Hong']
    },
    'China': {
        'first_male': ['Wei', 'Fang', 'Lei', 'Yang', 'Jun', 'Jie', 'Chao', 'Ming', 'Tao', 'Long',
                       'Hao', 'Bo', 'Peng', 'Feng', 'Kai', 'Qiang', 'Gang', 'Xin', 'Yu', 'Chen'],
        'first_female': ['Li', 'Na', 'Yan', 'Juan', 'Xiu', 'Jing', 'Mei', 'Ying', 'Hong', 'Fang',
                         'Min', 'Hua', 'Lan', 'Qing', 'Xia', 'Ling', 'Ping', 'Xue', 'Hui', 'Dan'],
        'last': ['Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou',
                 'Xu', 'Sun', 'Ma', 'Hu', 'Guo', 'Lin', 'He', 'Luo', 'Gao', 'Zheng']
    },
    'Mexico': {
        'first_male': ['José', 'Juan', 'Miguel', 'Carlos', 'Luis', 'Francisco', 'Pedro', 'Antonio', 'Jesús', 'Jorge',
                       'Manuel', 'Ricardo', 'Alejandro', 'Fernando', 'Rafael', 'Roberto', 'Eduardo', 'Diego', 'Sergio', 'Daniel'],
        'first_female': ['María', 'Guadalupe', 'Rosa', 'Ana', 'Carmen', 'Patricia', 'Margarita', 'Elena', 'Teresa', 'Josefina',
                         'Sofía', 'Valentina', 'Camila', 'Ximena', 'Fernanda', 'Daniela', 'Regina', 'Lucía', 'Natalia', 'Isabella'],
        'last': ['García', 'Hernández', 'López', 'Martínez', 'González', 'Rodríguez', 'Pérez', 'Sánchez', 'Ramírez', 'Cruz',
                 'Flores', 'Gómez', 'Morales', 'Vázquez', 'Jiménez', 'Reyes', 'Díaz', 'Torres', 'Gutiérrez', 'Ruiz']
    },
    'Russia': {
        'first_male': ['Alexander', 'Dmitri', 'Sergei', 'Andrei', 'Nikolai', 'Ivan', 'Mikhail', 'Vladimir', 'Pavel', 'Maxim',
                       'Aleksei', 'Yuri', 'Viktor', 'Oleg', 'Boris', 'Igor', 'Konstantin', 'Anatoli', 'Grigori', 'Roman'],
        'first_female': ['Anastasia', 'Elena', 'Natalia', 'Olga', 'Tatiana', 'Irina', 'Svetlana', 'Maria', 'Ekaterina', 'Anna',
                         'Oksana', 'Yulia', 'Valentina', 'Galina', 'Ludmila', 'Daria', 'Polina', 'Vera', 'Nadezhda', 'Larisa'],
        'last': ['Ivanov', 'Smirnov', 'Kuznetsov', 'Popov', 'Sokolov', 'Lebedev', 'Kozlov', 'Novikov', 'Morozov', 'Petrov',
                 'Volkov', 'Solovyov', 'Vasiliev', 'Zaytsev', 'Pavlov', 'Fedorov', 'Orlov', 'Andreev', 'Makarov', 'Nikolaev']
    },
    'Australia': {
        'first_male': ['Liam', 'Noah', 'Oliver', 'Jack', 'William', 'Leo', 'Lucas', 'Henry', 'Ethan', 'James',
                       'Mason', 'Archer', 'Hudson', 'Hunter', 'Cooper', 'Finn', 'Harrison', 'Lachlan', 'Riley', 'Kai'],
        'first_female': ['Charlotte', 'Amelia', 'Olivia', 'Isla', 'Mia', 'Ava', 'Grace', 'Willow', 'Harper', 'Ella',
                         'Zoe', 'Chloe', 'Ruby', 'Lily', 'Ivy', 'Sienna', 'Matilda', 'Evie', 'Frankie', 'Billie'],
        'last': ['Smith', 'Jones', 'Williams', 'Brown', 'Wilson', 'Taylor', 'Johnson', 'White', 'Martin', 'Anderson',
                 'Thompson', 'Nguyen', 'Thomas', 'Walker', 'Harris', 'Lee', 'Ryan', 'Robinson', 'Kelly', 'King']
    },
    'Nigeria': {
        'first_male': ['Chukwuemeka', 'Oluwaseun', 'Adebayo', 'Chibueze', 'Emeka', 'Oluwatobi', 'Ifeanyi', 'Nnamdi', 'Obinna', 'Tunde',
                       'Babajide', 'Olumide', 'Chinedu', 'Segun', 'Ikenna', 'Damilola', 'Femi', 'Kelechi', 'Ayodeji', 'Uche'],
        'first_female': ['Ngozi', 'Chiamaka', 'Aisha', 'Oluwadamilola', 'Chioma', 'Funmilayo', 'Adaeze', 'Ifeoma', 'Temitope', 'Blessing',
                         'Nneka', 'Amara', 'Folake', 'Yetunde', 'Adeola', 'Zainab', 'Obioma', 'Titilayo', 'Chinyere', 'Omolara'],
        'last': ['Okafor', 'Adeyemi', 'Okonkwo', 'Ibrahim', 'Abubakar', 'Ogundimu', 'Olawale', 'Nwachukwu', 'Balogun', 'Adeniyi',
                 'Eze', 'Udoh', 'Amadi', 'Chukwu', 'Okoro', 'Adekunle', 'Onyeka', 'Idris', 'Obiora', 'Nnaji']
    },
    'Turkey': {
        'first_male': ['Mehmet', 'Ali', 'Mustafa', 'Ahmet', 'Hakan', 'Emre', 'Burak', 'Can', 'Kaan', 'Yusuf',
                       'Omer', 'Murat', 'Kemal', 'Serkan', 'Tolga', 'Deniz', 'Baran', 'Eren', 'Furkan', 'Onur'],
        'first_female': ['Fatma', 'Ayse', 'Zeynep', 'Elif', 'Merve', 'Ebru', 'Selin', 'Defne', 'Esra', 'Dilara',
                         'Naz', 'Ceren', 'Buse', 'Ece', 'Gamze', 'Tugba', 'Sibel', 'Hande', 'Melis', 'Pinar'],
        'last': ['Yilmaz', 'Kaya', 'Demir', 'Celik', 'Sahin', 'Yildiz', 'Yildirim', 'Ozturk', 'Aydin', 'Ozdemir',
                 'Arslan', 'Dogan', 'Kilic', 'Aslan', 'Cetin', 'Koc', 'Kurt', 'Ozkan', 'Simsek', 'Polat']
    },
    'Sweden': {
        'first_male': ['Erik', 'Lars', 'Anders', 'Johan', 'Karl', 'Per', 'Nils', 'Lennart', 'Sven', 'Olof',
                       'Gustaf', 'Axel', 'Oscar', 'Hugo', 'Elias', 'Liam', 'Lucas', 'William', 'Viktor', 'Felix'],
        'first_female': ['Anna', 'Eva', 'Maria', 'Karin', 'Sara', 'Lena', 'Kristina', 'Birgitta', 'Marie', 'Ingrid',
                         'Maja', 'Ebba', 'Ella', 'Astrid', 'Wilma', 'Saga', 'Freja', 'Alva', 'Alma', 'Elsa'],
        'last': ['Andersson', 'Johansson', 'Karlsson', 'Nilsson', 'Eriksson', 'Larsson', 'Olsson', 'Persson', 'Svensson', 'Gustafsson',
                 'Pettersson', 'Jonsson', 'Hansson', 'Bengtsson', 'Jönsson', 'Lindberg', 'Jakobsson', 'Magnusson', 'Lindström', 'Olofsson']
    },
    'Argentina': {
        'first_male': ['Santiago', 'Mateo', 'Nicolás', 'Valentín', 'Joaquín', 'Lautaro', 'Benjamín', 'Tomás', 'Facundo', 'Thiago',
                       'Martín', 'Agustín', 'Felipe', 'Ignacio', 'Gonzalo', 'Maximiliano', 'Ramiro', 'Federico', 'Emiliano', 'Luciano'],
        'first_female': ['Sofía', 'Valentina', 'Isabella', 'Mía', 'Catalina', 'Emilia', 'Martina', 'Lucía', 'Julieta', 'Renata',
                         'Florencia', 'Camila', 'Pilar', 'Agustina', 'Delfina', 'Sol', 'Rocío', 'Celeste', 'Bianca', 'Victoria'],
        'last': ['González', 'Rodríguez', 'Gómez', 'Fernández', 'López', 'Díaz', 'Martínez', 'Pérez', 'García', 'Sánchez',
                 'Romero', 'Sosa', 'Álvarez', 'Torres', 'Ruiz', 'Ramírez', 'Flores', 'Acosta', 'Medina', 'Benítez']
    },
    'Canada': {
        'first_male': ['Liam', 'Noah', 'Jack', 'Benjamin', 'Lucas', 'Henry', 'Ethan', 'Oliver', 'Owen', 'James',
                       'Logan', 'Alexander', 'William', 'Theodore', 'Nathan', 'Gabriel', 'Samuel', 'Dylan', 'Jacob', 'Ryan'],
        'first_female': ['Emma', 'Olivia', 'Charlotte', 'Amelia', 'Sophia', 'Ava', 'Mia', 'Isla', 'Chloe', 'Ella',
                         'Zoey', 'Riley', 'Nora', 'Lily', 'Eleanor', 'Hannah', 'Abigail', 'Harper', 'Aria', 'Scarlett'],
        'last': ['Smith', 'Brown', 'Tremblay', 'Martin', 'Roy', 'Wilson', 'Macdonald', 'Taylor', 'Campbell', 'Anderson',
                 'Jones', 'Gagnon', 'Thompson', 'Leblanc', 'White', 'Williams', 'Côté', 'Johnson', 'Lee', 'Walker']
    },
    'Poland': {
        'first_male': ['Jan', 'Andrzej', 'Piotr', 'Krzysztof', 'Stanislaw', 'Tomasz', 'Pawel', 'Marcin', 'Marek', 'Michal',
                       'Grzegorz', 'Jerzy', 'Tadeusz', 'Adam', 'Lukasz', 'Zbigniew', 'Ryszard', 'Dariusz', 'Wojciech', 'Rafal'],
        'first_female': ['Anna', 'Maria', 'Katarzyna', 'Malgorzata', 'Agnieszka', 'Barbara', 'Ewa', 'Krystyna', 'Elzbieta', 'Joanna',
                         'Monika', 'Dorota', 'Aleksandra', 'Zofia', 'Magdalena', 'Beata', 'Renata', 'Iwona', 'Teresa', 'Danuta'],
        'last': ['Nowak', 'Kowalski', 'Wisniewski', 'Wojciechowski', 'Kaminski', 'Lewandowski', 'Zielinski', 'Szymanski', 'Wozniak', 'Dabrowski',
                 'Kozlowski', 'Jankowski', 'Mazur', 'Kwiatkowski', 'Krawczyk', 'Piotrowski', 'Grabowski', 'Pawlak', 'Michalski', 'Zajac']
    },
    'Thailand': {
        'first_male': ['Somchai', 'Somsak', 'Somporn', 'Surachai', 'Wichai', 'Chai', 'Nattapong', 'Pongsakorn', 'Thanakorn', 'Kittisak',
                       'Supachai', 'Wattana', 'Prawit', 'Anon', 'Panya', 'Boonsri', 'Niran', 'Krit', 'Thana', 'Anek'],
        'first_female': ['Suda', 'Malee', 'Supatra', 'Nong', 'Ploy', 'Fah', 'Kanya', 'Nattaya', 'Siriporn', 'Naree',
                         'Wannee', 'Lalita', 'Pornthip', 'Ratana', 'Siriwan', 'Araya', 'Anchan', 'Buppha', 'Duangjai', 'Kaewta'],
        'last': ['Saetang', 'Srisai', 'Kaewprasert', 'Chaiyaphum', 'Phanomwan', 'Thongchai', 'Rattanakorn', 'Phoonsiri', 'Wongsakorn', 'Narongrit',
                 'Limsakul', 'Thaweesak', 'Phongphaew', 'Somkid', 'Prasoet', 'Bunnak', 'Jantarakul', 'Wongsawat', 'Suwannarat', 'Chaiprasit']
    },
    'Egypt': {
        'first_male': ['Mohamed', 'Ahmed', 'Mahmoud', 'Ali', 'Hassan', 'Omar', 'Ibrahim', 'Mostafa', 'Youssef', 'Khaled',
                       'Amr', 'Tarek', 'Karim', 'Sami', 'Hossam', 'Adel', 'Nabil', 'Sherif', 'Walid', 'Ashraf'],
        'first_female': ['Fatma', 'Mona', 'Heba', 'Nour', 'Dina', 'Rania', 'Yasmine', 'Sara', 'Laila', 'Amira',
                         'Mariam', 'Aya', 'Hana', 'Salma', 'Ghada', 'Nesma', 'Eman', 'Amal', 'Nagwa', 'Sahar'],
        'last': ['El-Sayed', 'Hassan', 'Mohamed', 'Ahmed', 'Ali', 'Ibrahim', 'Mansour', 'Abdel-Fattah', 'Farouk', 'Khalil',
                 'Naguib', 'Shafik', 'Rizk', 'Mourad', 'Samir', 'Osman', 'Youssef', 'Abdallah', 'Kamal', 'Selim']
    },
    'Iran': {
        'first_male': ['Ali', 'Mohammad', 'Hossein', 'Amir', 'Reza', 'Mehdi', 'Hamid', 'Saeed', 'Majid', 'Javad',
                       'Farhad', 'Babak', 'Dariush', 'Behnam', 'Kourosh', 'Arash', 'Shahram', 'Omid', 'Parviz', 'Nader'],
        'first_female': ['Fatemeh', 'Zahra', 'Maryam', 'Sara', 'Parisa', 'Leila', 'Nasrin', 'Shirin', 'Azadeh', 'Mina',
                         'Sahar', 'Niloufar', 'Bahar', 'Golnaz', 'Sepideh', 'Mahsa', 'Nazanin', 'Atefeh', 'Elham', 'Neda'],
        'last': ['Ahmadi', 'Hosseini', 'Mohammadi', 'Rezaei', 'Karimi', 'Hashemi', 'Mousavi', 'Moradi', 'Jafari', 'Ebrahimi',
                 'Rahimi', 'Ghorbani', 'Noori', 'Safari', 'Bagheri', 'Khanizadeh', 'Shirazi', 'Tehrani', 'Esfahani', 'Tabatabai']
    },
    'South Africa': {
        'first_male': ['Thabo', 'Sipho', 'Mandla', 'Bongani', 'Sifiso', 'Nkosinathi', 'Lwazi', 'Sandile', 'Themba', 'Kagiso',
                       'Pieter', 'Johan', 'Jan', 'Andries', 'Willem', 'Hennie', 'Francois', 'Charl', 'Riaan', 'Deon'],
        'first_female': ['Nomzamo', 'Thandiwe', 'Zanele', 'Lerato', 'Palesa', 'Nomvula', 'Sibongile', 'Nandi', 'Ayanda', 'Thuli',
                         'Charlize', 'Anette', 'Elise', 'Marié', 'Sarie', 'Lindiwe', 'Mpho', 'Khanyi', 'Pearl', 'Minnie'],
        'last': ['Nkosi', 'Dlamini', 'Ndlovu', 'Zulu', 'Mthembu', 'Van der Merwe', 'Botha', 'Pretorius', 'Du Plessis', 'Naidoo',
                 'Pillay', 'Govender', 'Mokoena', 'Molefe', 'Khumalo', 'Mkhize', 'Ngcobo', 'Joubert', 'Venter', 'Jansen']
    }
}

# ==================== FILMING LOCATIONS ====================

FILMING_LOCATIONS = {
    'studios': [
        {'id': 'hollywood_studios', 'name': 'Hollywood Studios', 'city': 'Los Angeles', 'country': 'USA', 'cost': 500000, 'quality_bonus': 15, 'type': 'studio'},
        {'id': 'pinewood', 'name': 'Pinewood Studios', 'city': 'London', 'country': 'UK', 'cost': 450000, 'quality_bonus': 14, 'type': 'studio'},
        {'id': 'cinecitta', 'name': 'Cinecittà Studios', 'city': 'Rome', 'country': 'Italy', 'cost': 380000, 'quality_bonus': 13, 'type': 'studio'},
        {'id': 'babelsberg', 'name': 'Studio Babelsberg', 'city': 'Berlin', 'country': 'Germany', 'cost': 400000, 'quality_bonus': 13, 'type': 'studio'},
        {'id': 'toho', 'name': 'Toho Studios', 'city': 'Tokyo', 'country': 'Japan', 'cost': 420000, 'quality_bonus': 14, 'type': 'studio'},
    ],
    'urban': [
        {'id': 'nyc_manhattan', 'name': 'Manhattan, New York', 'city': 'New York', 'country': 'USA', 'cost': 450000, 'quality_bonus': 12, 'type': 'urban'},
        {'id': 'london_west_end', 'name': 'West End, London', 'city': 'London', 'country': 'UK', 'cost': 420000, 'quality_bonus': 11, 'type': 'urban'},
        {'id': 'paris_montmartre', 'name': 'Montmartre, Paris', 'city': 'Paris', 'country': 'France', 'cost': 380000, 'quality_bonus': 12, 'type': 'urban'},
        {'id': 'tokyo_shibuya', 'name': 'Shibuya, Tokyo', 'city': 'Tokyo', 'country': 'Japan', 'cost': 400000, 'quality_bonus': 11, 'type': 'urban'},
    ],
    'nature': [
        {'id': 'grand_canyon', 'name': 'Grand Canyon', 'city': 'Arizona', 'country': 'USA', 'cost': 200000, 'quality_bonus': 14, 'type': 'nature'},
        {'id': 'swiss_alps', 'name': 'Swiss Alps', 'city': 'Zermatt', 'country': 'Switzerland', 'cost': 350000, 'quality_bonus': 15, 'type': 'nature'},
        {'id': 'new_zealand', 'name': 'New Zealand Landscapes', 'city': 'Wellington', 'country': 'New Zealand', 'cost': 400000, 'quality_bonus': 16, 'type': 'nature'},
    ],
    'historical': [
        {'id': 'colosseum', 'name': 'Colosseum', 'city': 'Rome', 'country': 'Italy', 'cost': 600000, 'quality_bonus': 16, 'type': 'historical'},
        {'id': 'versailles', 'name': 'Palace of Versailles', 'city': 'Versailles', 'country': 'France', 'cost': 700000, 'quality_bonus': 17, 'type': 'historical'},
    ],
    'beach': [
        {'id': 'maldives', 'name': 'Maldives Islands', 'city': 'Malé', 'country': 'Maldives', 'cost': 600000, 'quality_bonus': 15, 'type': 'beach'},
        {'id': 'hawaii', 'name': 'Hawaiian Islands', 'city': 'Honolulu', 'country': 'USA', 'cost': 450000, 'quality_bonus': 14, 'type': 'beach'},
    ],
}

def get_all_locations_flat() -> List[dict]:
    """Get all locations as a flat list."""
    all_locations = []
    for category, locations in FILMING_LOCATIONS.items():
        for loc in locations:
            loc_copy = loc.copy()
            loc_copy['category'] = category
            loc_copy['cost'] = int(loc_copy['cost'] * 1.2)
            loc_copy['cost_per_day'] = loc_copy['cost'] // 7
            all_locations.append(loc_copy)
    return all_locations

# ==================== SKILL UTILITIES ====================

def calculate_stars(skills: dict) -> int:
    """Calculate star rating (1-5) based on average skills (0-100 scale)."""
    if not skills:
        return 1
    avg = sum(skills.values()) / len(skills)
    if avg >= 85:
        return 5
    elif avg >= 65:
        return 4
    elif avg >= 45:
        return 3
    elif avg >= 25:
        return 2
    else:
        return 1


def calculate_imdb_rating(skills: dict, fame_score: float, films_count: int) -> float:
    """Calculate IMDb-style rating (0.0 to 100.0 with 1 decimal).
    Based on: average skills (60%), fame (25%), experience (15%).
    """
    if not skills:
        return 0.0
    avg_skill = sum(skills.values()) / len(skills)
    fame_factor = min(100, fame_score)
    experience_factor = min(100, films_count * 3)
    
    rating = (avg_skill * 0.60) + (fame_factor * 0.25) + (experience_factor * 0.15)
    return round(max(0.0, min(100.0, rating)), 1)


def is_cast_star(fame_category: str, stars: int, avg_film_quality: float) -> bool:
    """Determine if a cast member is a Star."""
    return fame_category == 'star' or (stars >= 4 and avg_film_quality >= 70)


def get_fame_badge(role_type: str, is_star: bool, fame_category: str) -> dict:
    """Get fame badge/indicator for cast member."""
    if not is_star and fame_category != 'star':
        return None
    
    badges = {
        'actor': {'icon': 'star', 'label': 'Star del Cinema', 'color': 'gold'},
        'director': {'icon': 'crown', 'label': 'Regista Celebre', 'color': 'purple'},
        'screenwriter': {'icon': 'award', 'label': 'Sceneggiatore Premiato', 'color': 'blue'},
        'composer': {'icon': 'music', 'label': 'Maestro Compositore', 'color': 'emerald'},
    }
    return badges.get(role_type, {'icon': 'star', 'label': 'Famoso', 'color': 'gold'})

def get_category_from_stars(stars: int) -> str:
    """Get category name from star rating."""
    if stars >= 5:
        return 'star'
    elif stars >= 4:
        return 'known'
    elif stars >= 3:
        return 'emerging'
    else:
        return 'unknown'

def calculate_fame_from_career(years_active: int, films_count: int, avg_film_quality: float) -> float:
    """Calculate fame (0-100) based on career achievements."""
    years_score = min(years_active * 2, 30)
    films_score = min(films_count * 2, 40)
    quality_score = (avg_film_quality / 100) * 30
    return min(100, years_score + films_score + quality_score)

def get_fame_category_from_score(fame: float) -> str:
    """Get fame category name from score."""
    if fame >= 90:
        return 'superstar'
    elif fame >= 70:
        return 'famous'
    elif fame >= 50:
        return 'rising'
    elif fame >= 30:
        return 'known'
    else:
        return 'unknown'

def calculate_cast_cost(stars: int, fame: float, role_type: str, years_active: int) -> int:
    """Calculate hiring cost based on stars, fame, role and experience."""
    base_costs = {
        'actor': 50000,
        'director': 100000,
        'screenwriter': 40000,
        'composer': 60000
    }
    base = base_costs.get(role_type, 50000)
    
    star_multipliers = {1: 0.5, 2: 1.0, 3: 2.0, 4: 4.0, 5: 8.0}
    star_mult = star_multipliers.get(stars, 1.0)
    
    fame_mult = 0.5 + (fame / 100) * 2.5
    exp_bonus = min(years_active * 5000, 100000)
    
    cost = int((base * star_mult * fame_mult) + exp_bonus)
    return int(cost * 1.2)

# ==================== CAST GENERATION ====================

def generate_actor_age() -> int:
    """Generate realistic age distribution for actors.
    45% 18-36, 33% 37-50, 12% 51-70, 5% 70-90, 3% 14-17, 2% 6-13
    """
    roll = random.random()
    if roll < 0.02:      # 2% baby actors
        return random.randint(6, 13)
    elif roll < 0.05:    # 3% teen actors
        return random.randint(14, 17)
    elif roll < 0.50:    # 45% young adults (biggest pool)
        return random.randint(18, 36)
    elif roll < 0.83:    # 33% experienced adults
        return random.randint(37, 50)
    elif roll < 0.95:    # 12% senior actors
        return random.randint(51, 70)
    else:                # 5% veteran/elderly actors
        return random.randint(70, 90)


def generate_other_cast_age(role_type: str) -> int:
    """Generate realistic age for directors, screenwriters, composers."""
    if role_type == 'director':
        return random.choices(
            [random.randint(25, 35), random.randint(36, 50), random.randint(51, 70), random.randint(71, 85)],
            weights=[25, 40, 25, 10]
        )[0]
    elif role_type == 'screenwriter':
        return random.choices(
            [random.randint(22, 35), random.randint(36, 50), random.randint(51, 65), random.randint(66, 80)],
            weights=[30, 35, 25, 10]
        )[0]
    else:  # composer
        return random.choices(
            [random.randint(20, 35), random.randint(36, 50), random.randint(51, 70), random.randint(71, 85)],
            weights=[25, 35, 30, 10]
        )[0]


def generate_variable_skills(all_skills: Dict, min_skills: int = 8, max_skills: int = 8) -> Dict[str, int]:
    """
    Generate exactly 8 skills for a cast member from the pool.
    Skills are integer values from 0 to 100. 0 is extremely rare.
    """
    skill_keys = list(all_skills.keys())
    num_skills = min(SKILLS_PER_MEMBER, len(skill_keys))
    selected_skill_keys = random.sample(skill_keys, num_skills)
    
    skills = {}
    for key in selected_skill_keys:
        roll = random.random()
        if roll < 0.005:      # 0.5% chance for near-zero (1-5) — extremely rare
            value = random.randint(1, 5)
        elif roll < 0.05:     # 4.5% chance for very low (6-20)
            value = random.randint(6, 20)
        elif roll < 0.15:     # 10% low (21-35)
            value = random.randint(21, 35)
        elif roll < 0.40:     # 25% below average (36-50)
            value = random.randint(36, 50)
        elif roll < 0.70:     # 30% average (51-65)
            value = random.randint(51, 65)
        elif roll < 0.88:     # 18% good (66-80)
            value = random.randint(66, 80)
        elif roll < 0.96:     # 8% very good (81-90)
            value = random.randint(81, 90)
        else:                 # 4% excellent (91-100)
            value = random.randint(91, 100)
        skills[key] = value
    
    return skills

def generate_cast_member_v2(
    role_type: str, 
    category: str = 'random',
    nationality: str = None,
    ensure_skills: List[str] = None
) -> dict:
    """
    Generate a cast member with VARIABLE skills.
    
    role_type: 'actor', 'director', 'screenwriter', 'composer'
    category: 'recommended', 'star', 'known', 'emerging', 'unknown', 'random'
    ensure_skills: List of skill keys that MUST be present (optional)
    """
    
    # Pick nationality
    if not nationality:
        nationality = random.choice(list(EXPANDED_NAMES.keys()))
    
    names = EXPANDED_NAMES.get(nationality, EXPANDED_NAMES['USA'])
    gender = random.choice(['male', 'female'])
    
    if gender == 'male':
        first_name = random.choice(names['first_male'])
    else:
        first_name = random.choice(names['first_female'])
    last_name = random.choice(names['last'])
    
    # Get skill definitions based on role — all types get exactly 8 skills from 13
    if role_type == 'actor':
        all_skills = ACTOR_SKILLS
    elif role_type == 'director':
        all_skills = DIRECTOR_SKILLS
    elif role_type == 'composer':
        all_skills = COMPOSER_SKILLS
    else:  # screenwriter
        all_skills = SCREENWRITER_SKILLS
    
    # Generate exactly 8 skills
    skills = generate_variable_skills(all_skills)
    
    # If ensure_skills specified, make sure they're present
    if ensure_skills:
        for skill_key in ensure_skills:
            if skill_key in all_skills and skill_key not in skills:
                # Replace the lowest skill
                lowest = min(skills, key=skills.get)
                del skills[lowest]
                skills[skill_key] = random.randint(10, 80)
    
    # Adjust skills based on category (target star range)
    if category != 'random' and category in CAST_CATEGORIES:
        min_stars, max_stars = CAST_CATEGORIES[category]['stars_range']
        target_avg = (min_stars + max_stars) / 2 * 20  # Convert stars to avg skill (0-100 scale)
        
        current_avg = sum(skills.values()) / len(skills) if skills else 50
        adjustment = (target_avg - current_avg) * 0.5
        
        for key in skills:
            new_val = skills[key] + adjustment + random.uniform(-5, 5)
            skills[key] = max(1, min(100, int(new_val)))
    
    # Calculate derived stats
    stars = calculate_stars(skills)
    
    avg_skill = sum(skills.values()) / len(skills) if skills else 50
    base_years = max(1, int(avg_skill / 7) + random.randint(-2, 5))
    years_active = min(40, max(1, base_years))
    films_count = max(0, int(years_active * random.uniform(0.5, 2)))
    avg_film_quality = min(100, max(20, avg_skill * 0.8 + random.randint(-10, 20)))
    
    fame = calculate_fame_from_career(years_active, films_count, avg_film_quality)
    fame_category = get_fame_category_from_score(fame)
    
    # Star system
    cast_is_star = is_cast_star(fame_category, stars, avg_film_quality)
    fame_badge = get_fame_badge(role_type, cast_is_star, fame_category)
    
    # IMDb-style rating
    imdb_rating = calculate_imdb_rating(skills, fame, films_count)
    
    # Star cost bonus (+40% for stars)
    base_cost = calculate_cast_cost(stars, fame, role_type, years_active)
    cost = int(base_cost * 1.4) if cast_is_star else base_cost
    
    # Generate avatar
    seed = f"{first_name}{last_name}{role_type}".replace(' ', '')
    if gender == 'female':
        hair_styles = ['longHairStraight', 'longHairCurly', 'longHairBob', 'longHairStraight2']
        avatar_url = f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor=ffd5dc,c0aede&top={random.choice(hair_styles)}"
    else:
        hair_styles = ['shortHairShortFlat', 'shortHairShortWaved', 'shortHairTheCaesar']
        facial_hair = ['', '&facialHair=beardLight', '&facialHair=beardMedium']
        avatar_url = f"https://api.dicebear.com/9.x/avataaars/svg?seed={seed}&backgroundColor=b6e3f4,ffdfbf&top={random.choice(hair_styles)}{random.choice(facial_hair)}"
    
    # Determine primary and secondary skills
    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
    primary_skills = [s[0] for s in sorted_skills[:2]] if len(sorted_skills) >= 2 else [s[0] for s in sorted_skills]
    secondary_skill = sorted_skills[2][0] if len(sorted_skills) >= 3 else None
    
    return {
        'id': str(uuid.uuid4()),
        'name': f"{first_name} {last_name}",
        'gender': gender,
        'nationality': nationality,
        'age': generate_actor_age() if role_type == 'actor' else generate_other_cast_age(role_type),
        'role_type': role_type,
        'skills': skills,
        'primary_skills': primary_skills,
        'secondary_skill': secondary_skill,
        'stars': stars,
        'imdb_rating': imdb_rating,
        'is_star': cast_is_star,
        'fame_badge': fame_badge,
        'years_active': years_active,
        'films_count': films_count,
        'avg_film_quality': round(avg_film_quality, 1),
        'fame': round(fame, 1),
        'fame_category': fame_category,
        'category': category if category != 'random' else get_category_from_stars(stars),
        'cost': cost,
        'cost_per_film': cost,
        'avatar_url': avatar_url,
        'films_worked': [],
        'created_at': datetime.now(timezone.utc).isoformat()
    }

def generate_full_cast_pool(
    role_type: str,
    total_count: int = 100
) -> List[dict]:
    """
    Generate a full pool of cast members distributed across categories.
    """
    cast_pool = []
    
    # Calculate counts per category
    category_counts = {}
    for cat_id, cat_info in CAST_CATEGORIES.items():
        category_counts[cat_id] = int(total_count * cat_info['count_factor'])
    
    # Adjust to match total
    current_total = sum(category_counts.values())
    if current_total < total_count:
        category_counts['known'] += (total_count - current_total)
    
    # Generate cast for each category
    for category, count in category_counts.items():
        for _ in range(count):
            member = generate_cast_member_v2(role_type, category)
            cast_pool.append(member)
    
    return cast_pool

# ==================== BONUS/MALUS CALCULATION ====================

def calculate_cast_film_bonus(actor_skills: dict, film_genre: str) -> dict:
    """
    Calculate bonus/malus for an actor based on film genre match.
    Returns a dict with bonus percentage and explanation.
    """
    matching_skills = GENRE_SKILL_MAPPING.get(film_genre, [])
    
    if not matching_skills:
        return {'bonus_percent': 0, 'type': 'neutral', 'reason': 'No specific skill match'}
    
    # Check if actor has any matching skills
    matched = []
    total_skill_value = 0
    
    for skill in matching_skills:
        if skill in actor_skills:
            matched.append(skill)
            total_skill_value += actor_skills[skill]
    
    if not matched:
        # Actor doesn't have any matching skills - MALUS
        return {
            'bonus_percent': -15,
            'type': 'malus',
            'reason': f'No {film_genre} skills'
        }
    
    # Calculate bonus based on skill values (0-100 scale)
    avg_matched = total_skill_value / len(matched)
    
    if avg_matched >= 80:
        return {'bonus_percent': 20, 'type': 'major_bonus', 'reason': f'Esperto in {film_genre}'}
    elif avg_matched >= 60:
        return {'bonus_percent': 10, 'type': 'bonus', 'reason': f'Abile in {film_genre}'}
    elif avg_matched >= 40:
        return {'bonus_percent': 5, 'type': 'minor_bonus', 'reason': f'Competente in {film_genre}'}
    else:
        return {'bonus_percent': -5, 'type': 'minor_malus', 'reason': f'Debole in {film_genre}'}

def get_skill_translation(skill_key: str, role_type: str, language: str = 'en') -> str:
    """Get translated skill name."""
    skill_dicts = {
        'actor': ACTOR_SKILLS,
        'director': DIRECTOR_SKILLS,
        'screenwriter': SCREENWRITER_SKILLS,
        'composer': COMPOSER_SKILLS
    }
    
    skill_dict = skill_dicts.get(role_type, {})
    skill_info = skill_dict.get(skill_key, {})
    
    return skill_info.get(language, skill_info.get('en', skill_key))

def get_category_translation(category: str, language: str = 'en') -> str:
    """Get translated category name."""
    cat_info = CAST_CATEGORIES.get(category, {})
    return cat_info.get(language, cat_info.get('en', category))

# ==================== CAST AFFINITY SYSTEM ====================

def calculate_cast_affinity(cast_collaboration_history: Dict[str, Dict[str, int]]) -> Dict:
    """
    Calculate affinity bonus based on how many times cast members have worked together.
    
    cast_collaboration_history: {
        'actor1_id': {'actor2_id': 3, 'director_id': 2, ...},
        'director_id': {'actor1_id': 2, ...}
    }
    
    Returns: {
        'total_bonus_percent': float,
        'affinity_pairs': [{'pair': [id1, id2], 'films_together': int, 'bonus': float}, ...]
    }
    """
    affinity_pairs = []
    processed_pairs = set()
    total_bonus = 0.0
    
    AFFINITY_BONUS_PER_FILM = 2.0  # +2% per ogni film fatto insieme
    MAX_AFFINITY_BONUS_PER_PAIR = 10.0  # Max +10% per coppia
    
    for person1_id, collaborators in cast_collaboration_history.items():
        for person2_id, films_together in collaborators.items():
            # Create a sorted tuple to avoid counting pairs twice
            pair_key = tuple(sorted([person1_id, person2_id]))
            
            if pair_key not in processed_pairs and films_together > 0:
                processed_pairs.add(pair_key)
                
                # Calculate bonus for this pair
                pair_bonus = min(films_together * AFFINITY_BONUS_PER_FILM, MAX_AFFINITY_BONUS_PER_PAIR)
                total_bonus += pair_bonus
                
                affinity_pairs.append({
                    'pair': list(pair_key),
                    'films_together': films_together,
                    'bonus_percent': pair_bonus
                })
    
    # Cap total affinity bonus at 30%
    MAX_TOTAL_AFFINITY_BONUS = 30.0
    capped_total = min(total_bonus, MAX_TOTAL_AFFINITY_BONUS)
    
    return {
        'total_bonus_percent': capped_total,
        'affinity_pairs': affinity_pairs,
        'uncapped_bonus': total_bonus,
        'was_capped': total_bonus > MAX_TOTAL_AFFINITY_BONUS
    }

def get_affinity_description(films_together: int, language: str = 'en') -> str:
    """Get a description for the affinity level."""
    descriptions = {
        'en': {
            1: 'Acquaintances',
            2: 'Colleagues',
            3: 'Regular Partners',
            5: 'Close Collaborators',
            8: 'Dream Team'
        },
        'it': {
            1: 'Conoscenti',
            2: 'Colleghi',
            3: 'Partner Abituali',
            5: 'Collaboratori Affiatati',
            8: 'Dream Team'
        }
    }
    
    lang_desc = descriptions.get(language, descriptions['en'])
    
    for threshold in sorted(lang_desc.keys(), reverse=True):
        if films_together >= threshold:
            return lang_desc[threshold]
    
    return lang_desc.get(1, 'Unknown')

# ==================== INFRASTRUCTURE TRADING ====================

def calculate_infrastructure_value(infrastructure: dict, market_conditions: float = 1.0) -> dict:
    """Calculate the value of an infrastructure for trading."""
    from game_systems import INFRASTRUCTURE_TYPES
    
    infra_type_info = INFRASTRUCTURE_TYPES.get(infrastructure.get('type', 'cinema'), {})
    base_value = infrastructure.get('purchase_cost', infra_type_info.get('base_cost', 1000000))
    
    infra_level = infrastructure.get('infra_level', 1)
    level_multiplier = 1 + (infra_level - 1) * 0.15
    
    infra_fame = infrastructure.get('average_review', 3.0) * 20
    fame_multiplier = 0.8 + (infra_fame / 100) * 0.4
    
    city = infrastructure.get('city', {})
    location_multiplier = city.get('wealth', 1.0)
    
    total_revenue = infrastructure.get('total_revenue', 0)
    revenue_bonus = min(total_revenue * 0.01, base_value * 0.3)
    
    purchase_date = infrastructure.get('purchase_date')
    if purchase_date:
        try:
            from datetime import datetime, timezone
            purchased = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
            days_owned = (datetime.now(timezone.utc) - purchased).days
            if days_owned <= 30:
                time_multiplier = 0.9 + (days_owned / 30) * 0.1
            else:
                time_multiplier = 1.0 + min((days_owned - 30) / 365, 0.2)
        except:
            time_multiplier = 1.0
    else:
        time_multiplier = 1.0
    
    calculated_value = base_value * level_multiplier * fame_multiplier * location_multiplier * time_multiplier
    calculated_value += revenue_bonus
    calculated_value *= market_conditions
    
    calculated_value = round(calculated_value / 10000) * 10000
    
    min_value = int(base_value * 0.5)
    max_value = int(base_value * 3.0)
    
    final_value = max(min_value, min(max_value, int(calculated_value)))
    
    return {
        'calculated_value': final_value,
        'min_price': int(final_value * 0.8),
        'max_price': int(final_value * 1.2),
        'suggested_price': final_value,
        'factors': {
            'base_value': base_value,
            'level_multiplier': round(level_multiplier, 2),
            'fame_multiplier': round(fame_multiplier, 2),
            'location_multiplier': round(location_multiplier, 2),
            'time_multiplier': round(time_multiplier, 2),
            'revenue_bonus': int(revenue_bonus)
        },
        'infra_level': infra_level,
        'infra_fame': round(infra_fame, 1)
    }

def check_can_trade_infrastructure(user_level: int) -> bool:
    """Check if user has reached the level required for infrastructure trading."""
    TRADE_REQUIRED_LEVEL = 15
    return user_level >= TRADE_REQUIRED_LEVEL

TRADE_REQUIRED_LEVEL = 15

# Legacy function for compatibility
def generate_cast_member(role_type: str, skill_tier: str = 'random', nationality: str = None) -> dict:
    """Legacy function - redirects to new system."""
    category_map = {
        'beginner': 'unknown',
        'intermediate': 'emerging',
        'advanced': 'known',
        'expert': 'star',
        'random': 'random'
    }
    category = category_map.get(skill_tier, 'random')
    return generate_cast_member_v2(role_type, category, nationality)

def generate_cast_pool(role_type: str, count_per_tier: int = 10) -> dict:
    """Legacy function - generates pool organized by old tier names."""
    pool = {
        'beginner': [],
        'intermediate': [],
        'advanced': [],
        'expert': []
    }
    
    tier_to_category = {
        'beginner': 'unknown',
        'intermediate': 'emerging', 
        'advanced': 'known',
        'expert': 'star'
    }
    
    for tier, category in tier_to_category.items():
        for _ in range(count_per_tier):
            member = generate_cast_member_v2(role_type, category)
            pool[tier].append(member)
    
    return pool
