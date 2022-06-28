import json
import os
import random

# Récupère le chemin courant
chemin_courant = os.getcwd()


### FONCTIONS UTILISÉES UNIQUEMENT DANS LE MODULE ACTIONS_DIRECTES.PY ###

def lire_args(commande):
	"""Permet de lire les différents arguments des commandes
	
	Renvoi l'ensemble des variables possibles, on ne gardera à l'appel que les valeurs qui nous intéressent"""

	# Initialisation des variables pour éviter les erreurs
	# Et initialisation des valeurs par défaut
	joueur1, joueur2, stat, battletype, dice, diff, mod, valeur, pnj = 0,0,0,0,20,10,0,0,False

	# On stocke les valeurs des arguments dans les variables correspondant à leurs "caractère-clé"
	for arg in commande:
		if arg.startswith("j"):
			joueur1 = arg[1:]
		elif arg.startswith("vs"):
			joueur2 = arg[2:]
		elif arg.startswith("s"):
			stat = arg[1:]
		elif arg.startswith("t"):
			battletype = arg[1:]

		# arguments souvent facultatifs
		elif arg.startswith("diff"):
			diff = int(arg[4:])
		elif arg.startswith("d"):
			dice = int(arg[1:])
		elif arg.startswith("m"):
			mod = int(arg[1:])
		elif arg.startswith("v"):
			valeur = int(arg[1:])
		elif arg == "pnj":
			pnj = True

	# On retourne l'ensemble des valeurs possibles
	return [joueur1, joueur2, stat, battletype, dice, diff, mod, valeur, pnj]

### FONCTIONS DE JET

def jet_action(mod_stat, dice, mod, diff):
	""" Lance le dé et renvoie une string présentant le résultat pour une action """

	# Jette le dé et calcul le résultat du lancer
	de = random.randint(1, dice)
	res_total = de + mod_stat + mod
	jet = f'{de} + {mod_stat} (mod stat/combat) + {mod} = {res_total}'

	# Récuperation de statut du lancer (réussi ou raté)
	res, statut = statut_lancer(res_total, diff, de, dice)

	return jet, res, statut

def jet_attaque(dice, statut, data, attaquant, defenseur, battletype):
	"""Lance le dé et renvoie une string présentant le résultat pour une attaque"""

	cons = ''
	degats_totaux = 0

	# Effectue les lancers et affiche les résultats des attaques selon le statut du lancer
	if statut == 'Réussite Critique':
		# En cas de réussite critique, le joueur effectue deux lancers et applique deux fois le modificateur
		attaque1 = random.randint(1, dice)
		attaque2 = random.randint(1, dice)
		mod = data.get(attaquant).get(switch_battle_mod(battletype))[1]
		degats_totaux = max(attaque1 + attaque2 + 2*mod, 1)

		# Forme la fstring présentant les résultats de l'attaque
		cons += f'L\'attaque inflige {attaque1} + {attaque2} + 2 * {mod} = {degats_totaux} ! (minimum 1)\n'
		cons += f'Le personnage {defenseur} prend {degats_totaux} dégats! Il lui reste {data[defenseur]["PV"] - degats_totaux} PV'

	elif statut == 'Réussite':
		# En cas de réussite, le joueur effectue un lancer et applique les modificateurs
		attaque = random.randint(1, dice)
		mod = data.get(attaquant).get(switch_battle_mod(battletype))[1]
		degats_totaux = max(attaque + mod, 1)

		# Forme la fstring présentant les résultats de l'attaque
		cons += f'L\'attaque inflige {attaque} + {mod} = {degats_totaux} (minimum 1)\n'
		cons += f'Le personnage {defenseur} prend {degats_totaux} dégats! Il lui reste {data[defenseur]["PV"] - degats_totaux} PV'

	else:
		cons += 'L\'attaque rate...'

	return cons, degats_totaux

def jet_soin(dice):
	"""Effectue un jet de soin"""

	jet = random.randint(1, dice)
	cons = f'La potion va rendre {jet} PV.\n'

	return jet, cons

### FONCTIONS DE SWITCHER

def switch_mod_stat(val):
	"""Permet de définir la valeur du modificateur selon celle de la stat concernée à la création d'un joueur"""

	# Permet d'effectuer le switch/case voulu
	switcher = {
		0: 0,
		1: -5,
		2: -4,
		3: -4,
		4: -3,
		5: -3,
		6: -2,
		7: -2,
		8: -1,
		9: -1,
		10: 0,
		11: 0,
		12: 1,
		13: 1,
		14: 2,
		15: 2,
		16: 3,
		17: 3,
		18: 4,
		19: 4,
		20: 5
	}

	return switcher.get(val)

def switch_color_statut(val):
	"""Permet de définir la couleur associée à un évenement"""

	# Permet d'effectuer le switch/case voulu
	switcher = {
		'Réussite Critique': 0xf3f6f4,
		'Échec Critique': 0x444444,
		'Réussite': 0x8fce00,
		'Échec': 0xf44336
	}

	return switcher.get(val)

def switch_battle_mod(val):
	"""Permet de définir la statistique associée à un type de combat"""

	# Permet d'effectuer le switch/case voulu
	switcher = {
        "Magique": "Intelligence",
        "Contact": "Force",
        "Distance": "Dextérité"
	}

	return switcher.get(val)

### FONCTIONS DE FORMATION DE STRING

def statut_lancer(valeur, difficulte, de, dice):
	"""Vérifie si le lancer est raté ou réussi en fonction de la difficulté annoncée
	Vérifie également si le résultat est critique"""

	res = f''
	statut = ''

	if de == dice:
		res = f'-> BRAVO, c\'est une réussite critique! ~'
		statut = 'Réussite Critique'
	elif de == 1:
		res = f'-> MAIS C\'ÉTAIT SUR EN FAIT ! C\'est un échec critique...'
		statut = 'Échec Critique'
	elif valeur >= difficulte:
		res = f'-> L\'action est réussie!'
		statut = 'Réussite'
	elif valeur < difficulte:
		res = f'-> L\'action est ratée...'
		statut = 'Échec'

	return res, statut

def affiche_stats(dic):
	"""Met proprement dans un string les valeurs d'un dictionnaire pour le rendre lisible"""

	res = ''
	for stat, value in dic.items():
		res += f'- {stat} : {value}\n'

	return res

### FONCTIONS DE VÉRIFICATION

def verif_liste(guildName):
	"""Permet de vérifier si le serveur à une base de données de joueurs
	Si la base n'existe pas, une nouvelle est crée"""

	chemin_joueurs = chemin_courant + f'/listes_info/liste_joueurs_{guildName}.json'

	if not os.path.exists(chemin_joueurs) :
		with open(chemin_joueurs, 'w') as f :
			json.dump({"Init":{"valeur":10}}, f, indent=4)

	return chemin_joueurs

def verif_joueur(data, joueur, stat):
	"""Verifie si la stat ou le joueur font bien parti du jeu"""

	if joueur not in data.keys():
		return False
	elif stat not in data.get(joueur).keys():
		return False
	else:
		return True
