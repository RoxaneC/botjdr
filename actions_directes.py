import os
import json
import random

import methodes_indirectes

# Récupère le chemin courant
chemin_courant = os.getcwd()

### FONCTIONS INTÉRAGISSANTS DIRECTEMENT AVEC LE BOT ###

def action(commande, guildName):
	"""Effectue un jet de dé pour une action simple"""

	# Recupère les valeurs enoncées dans la commande utiles à la méthode actuelle
	args = methodes_indirectes.lire_args(commande)
	joueur, stat, dice, diff, mod = args[0], args[2], args[4] , args[5], args[6]

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data = json.load(f)

	# Initialisation par défaut
	color = 0xFFE766
	jet = None
	res = None

	# Verifie que le joueur et la stat existent dans la partie
	if methodes_indirectes.verif_joueur(data, joueur, stat):
		# fstring expliquant le lancer de dé qui va être effectué
		infojet = f'{joueur} lance un d{dice} pour la stat {stat}, difficulté {diff} ; Modificateur supplémentaire hors stat : {mod}'

		# Effectue le lancer de dé et retourne un fstring expliquant le résultat
		jet, res, statut = methodes_indirectes.jet_action(data.get(joueur).get(stat)[1], dice, mod, diff)
		color = methodes_indirectes.switch_color_statut(statut)
	else:
		# La méthode retourne un message explicatif sinon
		infojet = f'Entrée invalide du personnage ou de la stat concernée'
	
	return infojet, color, jet, res

def combat(commande, guildName):
	"""Effectue les lancers pour représenterun échange entre deux joueurs"""

	# Recupère les valeurs enoncées dans la commande utiles à la méthode actuelle
	args = methodes_indirectes.lire_args(commande)
	attaquant, defenseur, battletype, dice, mod = args[0], args[1], args[3], args[4], args[6]

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f:
		data = json.load(f)

	# Initialisation par défaut
	color = 0xFFE766
	jet = None
	res = None
	cons = None

	if methodes_indirectes.verif_joueur(data, attaquant, "PV") and methodes_indirectes.verif_joueur(data, defenseur, "PV"):
		# Vérifie que les joueurs en combats sont tous les deux en vie
		if data.get(attaquant).get("PV") > 0 and data.get(defenseur).get("PV") > 0:
			# fstring explicative du combat à venir
			infojet = f'Le personnage {attaquant} attaque {defenseur} (DEF = {data.get(defenseur).get("Défense")}) avec une attaque {battletype} ; Modificateur supplémentaire hors stat du test de visée : {mod}'
			
			# Effectue le lancer de visée et retourne un fstring affichant le résultat
			jet, res, statut = methodes_indirectes.jet_action(data.get(attaquant).get(battletype), 20, mod, data.get(defenseur).get("Défense"))
			color = methodes_indirectes.switch_color_statut(statut)

			# Effectue le lancer d'attaque et retourne un fstring affichant le résultat
			cons, degats = methodes_indirectes.jet_attaque(dice, statut, data, attaquant, defenseur, battletype)

			# Applique les dégats dans la fiche du joueur
			data[defenseur]["PV"] = max(0, data.get(defenseur).get("PV")-degats)

			# Ajoute une conséquence si les PV du joueur tombent à 0
			if data[defenseur]["PV"] <= 0:
				cons += f'\n\n-> Le personnage {defenseur} est à terre...'

			# Met à jour le fichier base de données
			with open(chemin_joueurs, 'w') as f :
				json.dump(data, f, indent = 4)
			
		else:
			infojet = f'L\'un des deux combattant est déjà mort'
		
	else:
		infojet = f'Entrée invalide pour l\'un des deux combattants'
	
	return infojet, color, jet, res, cons

def soigner(commande, guildName):
	"""Permet de soigner un joueur en lui rendant des PV"""

	# Recupère les valeurs enoncées dans la commande utiles à la méthode actuelle
	args = methodes_indirectes.lire_args(commande)
	joueur, dice, valeur = args[0], args[4], args[7]

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f:
		data = json.load(f)

	infojet = ''
	jet = 0
	cons = ''
	color = 0xBB00FF

	# Les jets de potions ne dépassent pas 18 (à priori)
	if dice <= 18:
		infojet = f'Une potion de d{dice} va être utilisée. De plus, '
		jet, cons = methodes_indirectes.jet_soin(dice)

	infojet += f'Un soin global de {valeur} va être effectué.'

	if jet == 0:
		valeur = max(valeur,1)

	# Si aucun joueur n'est précisé, soigne tout le monde de la valeur définie
	# Sinon, soigne uniquement le joueur désigné
	if joueur == 0:
		for j in data.keys():
			data[j]["PV"] = min(data.get(j).get("PV max"), data.get(j).get("PV") + valeur+jet)
			cons += f'Le personnage {j} a récupéré {valeur+jet} PV. Il a maintenant {data.get(j).get("PV")} PV.\n'

	elif methodes_indirectes.verif_joueur(data, joueur, "PV"):
		data[joueur]["PV"] = min(data.get(joueur).get("PV max"), data.get(joueur).get("PV") + valeur+jet)
		cons += f'Le personnage {joueur} a récupéré {valeur+jet} PV. Il a maintenant {data.get(joueur).get("PV")} PV.\n'
	
	else:
		infojet = f'Le personnage nommé n\'existe pas.'
		jet = 0
		cons = None
		color = 0xFFE766

	# Met à jour le fichier base de données
	with open(chemin_joueurs, 'w') as f :
		json.dump(data, f, indent = 4)

	return infojet, jet, cons, color

def ajouter(joueur, dic, guildName):
	"""Ajoute un nouveau joueur à la base de données"""

	# On récupère le dictionnaire contenant les joueurs déjà existants et leurs stats
	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data =  json.load(f)

	# On définit les modificateurs de base des stats du nouveau joueur
	for stat in ["Force","Dextérité","Constitution","Intelligence","Sagesse","Charisme"]:
		dic[stat] = [dic.get(stat)]
		dic[stat].append(methodes_indirectes.switch_mod_stat(dic.get(stat)[0]))

	# On calcule les valeurs non entrées par l'utilisateur
	dic["Contact"] = max(dic.get("Niveau") + dic.get("Force")[1],0)
	dic["Distance"] = max(dic.get("Niveau") + dic.get("Dextérité")[1], 0)
	dic["Initiative"] = dic.get("Dextérité")[0]
	dic["Défense"] = 10 + dic.get("Dextérité")[1]

	# On ajoute l'entrée correspondant au joueur à ajouter, contenant ses valeurs de stat
	data[joueur] = dic

	# On réécrit dans le fichier de sauvegarde le dictionnaire contenant le nouveau joueur
	with open(chemin_joueurs, 'w') as f :
		json.dump(data, f, indent = 4)

	info = f'Le personnage {joueur} a été ajouté avec les statistiques suivantes :'
	fiche = methodes_indirectes.affiche_stats(dic)

	# On retourne une phrase résumant l'action
	return info, fiche

def supprimer(joueur, guildName):
	"""Supprime un joueur de la base de données"""
	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data =  json.load(f)

	# On supprime les entrées correspondant au joueur paramètre, renvoyant None si le joueur est introuvable
	j = data.pop(joueur, None)

	# Si le joueur était dans le dictionnaire, on sauvegarde le dictionnaire modifié
	# Sinon on ne fait rien
	# On renvoie chaque fois une phrase résumant ce qu'il s'est passé
	if j != None:
		with open(chemin_joueurs, 'w') as f :
			json.dump(data, f, indent = 4)
		return f'Le personnage {joueur} a bien été supprimé de la liste'
	else:
		return f'Personnage {joueur} introuvable.'

def level_up(joueur, guildName):
	"""Fait level up le joueur concerné"""

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data =  json.load(f)

	# Verifie que le joueur et la stat existent dans la partie
	# La méthode retourne un message explicatif sinon
	if methodes_indirectes.verif_joueur(data, joueur, "Niveau"):
		# Récupère sa valeure et lance le dé de vie du joueur
		dice = data.get(joueur).get("Dé de vie")
		pv = random.randint(1, dice)

		info = f'Le joueur {joueur} a augmenté de niveau et gagne {pv} PV (dé de vie : d{dice})'

		# Augmente les valeurs concernées par la montée de niveau
		data[joueur]["Niveau"] += 1
		data[joueur]["PV max"] += pv
		data[joueur]["PV"] += pv
		data[joueur]["Contact"] += 1
		data[joueur]["Distance"] += 1
		data[joueur]["Magique"] += 1

		stat = methodes_indirectes.affiche_stats(data.get(joueur))
		color = 0x4000FF

		# On réécrit dans le fichier de sauvegarde le dictionnaire contenant le joueur
		with open(chemin_joueurs, 'w') as f :
			json.dump(data, f, indent = 4)

	else:
		info = f'Entrée invalide du joueur'
		stat = None
		color = 0xFFE766

	return info, stat, color

def modifier_stat(commande, guildName):
	"""Modifie la valeur d'une stat, en mettant aussi à jour son modificateur"""

	# Recupère les valeurs enoncées dans la commande utiles à la méthode actuelle
	args = methodes_indirectes.lire_args(commande)
	joueur, stat, valeur = args[0], args[2], args[7]

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data =  json.load(f)

	# Verifie que le joueur et la stat existent dans la partie
	# Retourne un message explicatif sinon
	if methodes_indirectes.verif_joueur(data, joueur, stat):
		# Récupère l'ensemble des stats du joueur
		dic_stat = data.get(joueur)

		# Met à jour la stat avec la nouvelle valeur, ainsi que son modificateur
		# Et éventuellement les stats dépendantes de celle modifiée
		if stat in ["Force","Dextérité","Constitution","Intelligence","Sagesse","Charisme"]:
			dic_stat[stat][0] = valeur
			dic_stat[stat][1] = methodes_indirectes.switch_mod_stat(valeur)
			
			if stat == "Force":
				dic_stat["Contact"] = max(dic_stat.get("Niveau") + dic_stat.get(stat)[1], 0)
			
			if stat == "Dextérité":
				dic_stat["Distance"] = max(dic_stat.get("Niveau") + dic_stat.get(stat)[1], 0)
				dic_stat["Initiative"] = dic_stat.get(stat)[0]
				dic_stat["Défense"] = 10 + dic_stat.get(stat)[1]

		else:
			if stat == "Niveau":
				dic_stat["Contact"] = max(valeur + dic_stat.get("Force")[1], 0)
				dic_stat["Distance"] = max(valeur + dic_stat.get("Dextérité")[1], 0)
				dic_stat["Magique"] = max(dic_stat.get("Magique") + valeur - dic_stat.get(stat), 0)

			dic_stat[stat] = valeur

		# On met dans la clé du joueur le dictionnaire de stats modifié
		data[joueur] = dic_stat

		# On met à jour le fichier contenant les joueurs
		with open(chemin_joueurs, 'w') as f :
			json.dump(data, f, indent = 4)
		
		info = f'La statistique {stat} du joueur {joueur} a été mise à jour avec la valeur : {valeur}.\n'
		info += methodes_indirectes.affiche_stats(dic_stat)

	else:
		info = f'Entrée invalide du joueur ou de la stat concernée'

	return info

def modifier_mod(commande, guildName):
	"""Modifie le modificateur d'une stat"""

	# Recupère les valeurs enoncées dans la commande utiles à la méthode actuelle
	args = methodes_indirectes.lire_args(commande)
	joueur, stat, valeur = args[0], args[2], args[7]

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data =  json.load(f)

	# Verifie que le joueur et la stat existent dans la partie
	# Retourne un message explicatif sinon
	if methodes_indirectes.verif_joueur(data, joueur, stat):
		if stat in ["Force","Dextérité","Constitution","Intelligence","Sagesse","Charisme"]:
			# Récupère l'ensemble des stats du joueur
			dic_stat = data.get(joueur)

			# Met à jour la stat avec la nouvelle valeur, ainsi que son modificateur
			# Et éventuellement les stats dépendantes de celle modifiée
			dic_stat[stat][1] = valeur

			if stat == "Force":
				dic_stat["Contact"] = max(dic_stat.get("Niveau") + dic_stat.get(stat)[1], 0)
			
			if stat == "Dextérité":
				dic_stat["Distance"] = max(dic_stat.get("Niveau") + dic_stat.get(stat)[1], 0)
				dic_stat["Défense"] = 10 + dic_stat.get(stat)[1]

			# On met dans la clé du joueur le dictionnaire de stats modifié
			data[joueur] = dic_stat

			# On met à jour le fichier contenant les joueurs
			with open(chemin_joueurs, 'w') as f :
				json.dump(data, f, indent = 4)

			info = f'Le modificateur de {stat} du joueur {joueur} a été mis à jour avec la valeur : {valeur}.\n'
			info += methodes_indirectes.affiche_stats(dic_stat)
	
		else:
			info = f'La statistique n\'as pas de modificateur'

	else:
		info = f'Entrée invalide du joueur ou de la stat concernée'
	
	return info

def get_stat():
	"""Renvoie la liste des statistiques utilisée dans la création de personnage"""

	with open(chemin_courant + "/liste_stat.json", 'r') as f :
		data = json.load(f)

	return data

def get_joueurs(commande, guildName):
	"""Renvoie la fiche du joueur demandé, ou l'ensemble de joueur si aucun argument"""

	# Recupère les valeurs enoncées dans la commande utiles à la méthode actuelle
	args = methodes_indirectes.lire_args(commande)
	joueur, stat, pnj = args[0], args[2], args[8]

	# Charge le fichier contenant les joueurs du serveur d'où vient la commande
	chemin_joueurs = methodes_indirectes.verif_liste(guildName)
	with open(chemin_joueurs, 'r') as f :
		data = json.load(f)

	j = []
	s = []

	# Modifie la fstring selon les informations demandées par la commande
	if joueur!=0 and stat!=0:
		j.append(joueur)
		s.append(f'- {stat} : ' + str(data.get(joueur).get(stat)))

	elif joueur!=0:
		j.append(joueur)
		s.append(methodes_indirectes.affiche_stats(data.get(joueur)))

	elif stat!=0:
		for k in data.keys():
			if pnj:
				aux1 = k
				aux2 = f'- {stat} : ' + str(data.get(k).get(stat))
				j.append(aux1)
				s.append(aux2)
			elif not data.get(k).get("PNJ"):
				aux1 = k
				aux2 = f'- {stat} : ' + str(data.get(k).get(stat))
				j.append(aux1)
				s.append(aux2)

	else:
		for k in data.keys():
			if pnj:
				aux1 = k
				aux2 = methodes_indirectes.affiche_stats(data.get(k))
				j.append(aux1)
				s.append(aux2)
			elif not data.get(k).get("PNJ"):
				aux1 = k
				aux2 = methodes_indirectes.affiche_stats(data.get(k))
				j.append(aux1)
				s.append(aux2)

	return j,s
