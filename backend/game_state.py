# CineWorld Studio's - Shared Game State
# Global state shared across route modules

# Online users tracking: {user_id: {'nickname': ..., 'avatar_url': ..., 'last_seen': ...}}
online_users = {}

CHAT_BOTS = [
    {
        'id': 'bot-cinemaster',
        'nickname': 'CineMaster',
        'avatar_url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=CineMaster&backgroundColor=feca57',
        'is_bot': True, 'is_moderator': True, 'role': 'moderator',
        'bio': 'Official CineWorld Moderator. Here to help and keep the community safe!',
        'welcome_messages': {
            'en': 'Welcome to CineWorld Studios! Feel free to ask questions. Be respectful to others!',
            'it': 'Benvenuto a CineWorld Studios! Sentiti libero di fare domande. Sii rispettoso con gli altri!',
            'es': '¡Bienvenido a CineWorld Studios! Siéntete libre de hacer preguntas. ¡Sé respetuoso con los demás!',
            'fr': 'Bienvenue à CineWorld Studios! N\'hésitez pas à poser des questions. Soyez respectueux envers les autres!',
            'de': 'Willkommen bei CineWorld Studios! Fühlen Sie sich frei, Fragen zu stellen. Seien Sie respektvoll!'
        }
    },
    {
        'id': 'bot-filmguide',
        'nickname': 'FilmGuide',
        'avatar_url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=FilmGuide&backgroundColor=48dbfb',
        'is_bot': True, 'is_moderator': True, 'role': 'helper',
        'bio': 'Your friendly film production assistant. Tips & tricks for new producers!',
        'tips': {
            'en': ['Tip: Choose sponsors carefully - they take a cut of your revenue!', 'Tip: Higher quality equipment = better film scores!', 'Tip: Star actors cost more but attract bigger audiences!'],
            'it': ['Consiglio: Scegli gli sponsor con attenzione!', 'Consiglio: Attrezzature di qualita superiore = punteggi film migliori!', 'Consiglio: Gli attori famosi costano di piu ma attirano piu pubblico!'],
        }
    },
    {
        'id': 'bot-newsbot',
        'nickname': 'CineNews',
        'avatar_url': 'https://api.dicebear.com/9.x/bottts-neutral/svg?seed=NewsBot&backgroundColor=ff6b6b',
        'is_bot': True, 'is_moderator': False, 'role': 'announcer',
        'bio': 'Breaking news and announcements from CineWorld HQ!'
    }
]
