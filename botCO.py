import os
import json
import discord
from discord.ext import commands

import actions_directes

# Récupère le chemin courant
chemin_courant = os.getcwd()
# Définit le caractère préfixe des commandes
bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
	"""Fonction permettant de vérifier que le bot s'est bien lancé sur tous ses serveurs"""

	print("Le bot est prêt")
	for guild in bot.guilds:
		print(f'Le bot {bot.user} s\'est connecté sur les serveurs {guild.name}!')


## FONCTIONS DES COMMANDES ##

@bot.command(name = "jet")
async def jet(ctx, *commande):
	""" Fonction permettant d'effectuer et d'afficher un lancer selon une caractéristique, par la commande

	 !jet j{Joueur} d{Taille de dé(facultatif)} s{Stat} d{Difficulté(facultatif)} m{Modificateur(facultatif)} """

	infojet, color, jet, res = actions_directes.action(list(commande), ctx.guild.name)
	embed = discord.Embed(title="Jet d'Action!", color=color, description=infojet)

	if res != None:
		embed.add_field(name="Lancer", value=jet, inline=True)
		embed.add_field(name="État Final", value=res, inline=True)

	await ctx.channel.send(embed=embed)

@bot.command(name = "combat")
async def combat(ctx, *commande):
	"""Fonction permettant d'effectuer un combat d'un type donné entre deux joueurs
	
	!combat t{Type de combat} j{Joueur attaquant} c{Joueur défendant} d{Taille du dé d'attaque(facultatif)} m{Modificateur au dé de visée(facultatif)}"""

	infojet, color, jet, res, cons = actions_directes.combat(list(commande), ctx.guild.name)
	embed = discord.Embed(title="Jet de Combat!", color=color, description=infojet)

	if res != None:
		embed.add_field(name="Lancer", value=jet, inline=True)
		embed.add_field(name="État de la visée", value=res, inline=True)
		embed.add_field(name="Conséquences", value=cons, inline=False)

	await ctx.channel.send(embed=embed)

@bot.command(name = "heal")
async def heal(ctx, *commande):
	"""Permet de soigner les joueurs
	
	!heal j{Joueur(facultatif)} v{Valeur(facultatif)} d{Valeur du dé de potion(facutatif)}"""

	infojet, jet, cons, color = actions_directes.soigner(list(commande), ctx.guild.name)
	embed = discord.Embed(title="Jet de Soin!", color=color, description=infojet)

	if jet != 0:
		embed.add_field(name="Lancer Potion", value=jet, inline=False)
	
	if cons != None:
		embed.add_field(name="Conséquences", value=cons, inline=False)

	await ctx.channel.send(embed=embed)

@bot.command(name = "ajouter")
async def add(ctx, joueur : str):
	"""Fonction permettant d'ajouter un joueur ainsi que ses stats, par la commande
	
	!ajouter {Joueur}"""

	await ctx.channel.send(embed= discord.Embed(title="Ajout d'un nouveau personnage", color=0x4000FF, description=f'Ajoutons le personnage nommé {joueur}...'))
	dic = {}

	# On demande si le personnage à ajouter est un PNJ ou non
	await ctx.channel.send(embed= discord.Embed(title="Ajout d'un nouveau personnage", color=0x4000FF, description=f'Le personnage {joueur} est-il un PNJ ? (OUI ou NON)'))
	pnj = await bot.wait_for('message')
	while pnj.content != "oui" and pnj.content != "non":
		await ctx.channel.send(embed= discord.Embed(title="Ajout d'un nouveau personnage", color=0x4000FF, description=f'(RÉPONSE \'oui\' OU \'non\' !)\nLe personnage {joueur} est-il un PNJ ? (OUI ou NON)'))
		pnj = await bot.wait_for('message')
	
	dic["PNJ"] = True if (pnj.content == "oui") else False

	# On demande la valeur des stats du joueur et on les stocke dans un dictionnaire
	for stat in actions_directes.get_stat():
		await ctx.channel.send(embed= discord.Embed(title="Ajout d'un nouveau personnage", color=0x4000FF, description=f'Quelle est la valeur de {stat} de {joueur} ?'))
		msg = await bot.wait_for('message')

		while (not msg.content.isdigit()) or int(msg.content) > 20 or int(msg.content) <= 0:
			await ctx.channel.send(embed= discord.Embed(title="Ajout d'un nouveau personnage", color=0x4000FF, description=f'(VALEUR NUMÉRIQUE OBLIGATOIRE ENTRE 0 ET 20!)\nQuelle est la valeur de {stat} de {joueur} ?'))
			msg = await bot.wait_for('message')

		dic[stat] = int(msg.content)

	info, fiche = actions_directes.ajouter(joueur, dic, ctx.guild.name)

	embed = discord.Embed(title="Fiche du nouveau Personnage", color=0x4000FF, description=info)
	embed.add_field(name=joueur, value=fiche, inline=False)

	await ctx.channel.send(embed=embed)

@bot.command(name = "supprimer")
async def supp(ctx, joueur : str):
	"""Fonction permettant de supprimer un joueur, par la commande
	
	!supprimer {Joueur}"""

	roles = [r.name for r in ctx.message.author.roles]

	if "MJ" in roles:
		info = actions_directes.supprimer(joueur, ctx.guild.name)
		embed = discord.Embed(title="Suppression d'un Personnage", color=0x4000FF, description=info)

	else:
		embed = discord.Embed(title="Suppression d'un Personnage", color=0xFFE766, description="Vous n'avez pas les authorisations nécessaires pour cette commande.")
		
	await ctx.channel.send(embed=embed)

@bot.command(name="lvlup")
async def levelup(ctx, joueur):
	"""Permet de faire level up un joueur et d'augmenter ses stats en consequence par la commande
	
	!lvlup {Joueur}"""

	roles = [r.name for r in ctx.message.author.roles]

	if "MJ" in roles:
		info, stat, color = actions_directes.level_up(joueur, ctx.guild.name)
		embed = discord.Embed(title="Niveau Supplémentaire", color=color, description=info)

		if stat != None:
			embed.add_field(name=joueur, value=stat, inline=False)

	else:
		embed = discord.Embed(title="Niveau Supplémentaire", color=0xFFE766, description="Vous n'avez pas les authorisations nécessaires pour cette commande.")

	await ctx.channel.send(embed=embed)

@bot.command(name = "modifstat")
async def modifier(ctx, *commande):
	"""Fonction permettant de modifier la valeur d'une stat d'un joueur, par la commande
	
	!modifstat j{Joueur} s{Stat} v{Nouvelle valeur}"""

	roles = [r.name for r in ctx.message.author.roles]

	if "MJ" in roles:
		info = actions_directes.modifier_stat(commande, ctx.guild.name)
		embed = discord.Embed(title="Modification de Statistique", color=0x4000FF, description=info)

	else:
		embed = discord.Embed(title="Modification de Statistique", color=0xFFE766, description="Vous n'avez pas les authorisations nécessaires pour cette commande.")

	await ctx.channel.send(embed=embed)

@bot.command(name = "modifmod")
async def modifier(ctx, *commande):
	"""### Fonction permettant de modifier la valeur du modificateur d'une stat d'un joueur, par la commande
	
	!modifmod j{Joueur} s{Stat} v{Nouvelle valeur}"""

	roles = [r.name for r in ctx.message.author.roles]

	if "MJ" in roles:
		info = actions_directes.modifier_mod(commande, ctx.guild.name)
		embed = discord.Embed(title="Modification d'un Modificateur", color=0x4000FF, description=info)

	else:
		embed = discord.Embed(title="Modification d'un Modificateur", color=0xFFE766, description="Vous n'avez pas les authorisations nécessaires pour cette commande.")

	await ctx.channel.send(embed=embed)

@bot.command(name = "afficher")
async def affiche_joueurs(ctx, *commande):
	"""Affiche les joueurs ou une valeur de stat précise, par la commande
	
	!afficher j{Joueur(facultatif)} s{Stat(facultatif)} pnj(facultatif)}"""

	roles = [r.name for r in ctx.message.author.roles]

	if "MJ" in roles:
		j,s = actions_directes.get_joueurs(list(commande), ctx.guild.name)
		embed = discord.Embed(title="Affichage des Personnages", color=0x4000FF, description="")

		for i in range(0,len(j)):
			embed.add_field(name=j[i], value=s[i], inline=True)

	else:
		embed = discord.Embed(title="Affichage des Personnages", color=0xFFE766, description="Vous n'avez pas les authorisations nécessaires pour cette commande.")
	
	await ctx.channel.send(embed=embed)

@bot.command(name = "aide")
async def aide(ctx):
	"""Fonction qui affiche l'aide, par la commande
	
	!aide"""

	embed = discord.Embed(title = "Aide", description="Voici la liste des commandes disponibles",color=0xFFFFFF)

	with open(chemin_courant + "/liste_commandes.json", 'r') as f:
		data = json.load(f)
	
	for key in data:
		embed.add_field(name=key, value="\n".join(data.get(key)), inline=False)
	
	await ctx.channel.send(embed = embed)


###


with open(chemin_courant + "/private_info/Token.txt", 'r') as f :
	token = f.read()

bot.run(token)
