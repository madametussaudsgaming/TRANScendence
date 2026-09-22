# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    moneyManipulation.py                               :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: rpadasia <ryanpadasian@gmail.com>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/22 21:47:33 by rpadasia          #+#    #+#              #
#    Updated: 2026/09/22 22:02:10 by rpadasia         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

from engine import Game

class moneyManipulate:
	def gainMoney(ID, amount):
		player = Game.getPlayer(ID)
		player.money += amount

	#(as in the pain of losing money)
	def painMoney(ID, amount):
		player = Game.getPlayer(ID)
		player.money -= amount
