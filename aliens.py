import os
import sys 
import codecs 
import time
import datetime
from random import randrange
from fenix.program import Program
from fenix.process import Process 
import pygame
from pygame.locals import *
from fenix.locals import *

class Config:

	default_screen_size = (800, 600)
	fps = 30
	full_screen = False
	detect_screen_size = False
	fb_dev = "/dev/fb0"
	lives = 4
	bullets = 100

class Game(Process):

	screen_size = Config.default_screen_size
	fps = Config.fps
	full_screen = Config.full_screen
	window_title = "Aliens"

	@classmethod
	def load_fnt(self, filename, size):
		dirname, current_filename = os.path.split(os.path.abspath(__file__))
		filename = os.path.join(dirname, 'gfx', filename)
		return Program.load_fnt(filename, size)

	@classmethod
	def load_png(self, filename):
		dirname, current_filename = os.path.split(os.path.abspath(__file__))
		filename = os.path.join(dirname, 'gfx', filename)
		return Program.load_png(filename)

	@classmethod
	def load_wav(self, filename):
		dirname, current_filename = os.path.split(os.path.abspath(__file__))
		filename = os.path.join(dirname, 'sounds', filename)
		return Program.load_wav(filename)

	def begin(self):

		# Set fb device for Raspberry pi
		os.environ["SDL_FBDEV"] = Config.fb_dev

		if (Config.detect_screen_size):
			self.screen_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)

		# Set the resolution and the frames per second
		Program.set_mode(self.screen_size, self.full_screen, False)
		Program.set_fps(self.fps)
		Program.set_title(self.window_title)

		# set mouse invisible
		pygame.mouse.set_visible(False)

		self.font = Game.load_fnt("c64.ttf", 16)
		self.big_font = Game.load_fnt("c64.ttf", 50)

		# run scene
		scene = Main(self);
		scene.lives = Config.lives
		scene.bullets = Config.bullets

		while True:
			# This is the main loop

			# Simple input check
			if Program.key(K_ESCAPE):
				Program.exit()

			yield

	def millis(self):
		return int(round(time.time() * 1000))


class Bg(Process):

	def begin(self, level):

		self.graph = level.g_bg
		self.x = level.game.screen_size[0]/2
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2)

		while True:

			yield

class Sky(Process):

	star_count = 50

	def begin(self, level):

		screen_size = level.game.screen_size
		self.g_star = Game.load_png("star.png")

		for i in range(0, self.star_count):
			size = randrange(10, 100)
			x = randrange(0, screen_size[0])
			y = randrange(0, screen_size[1])
			Star(self, x, y, size)

		while True:

			yield

class Star(Process):

	def begin(self, sky, x, y, size):

		self.x = x
		self.y = y
		self.graph = sky.g_star
		self.size = size
		self.z = 500

		while True:

			yield

class Level(Process):
	game = None
	name = ""
	description = ""
	enemies_count = 0
	music = None
	next_scene = None
	txt_message_delay = 50
	next_level = None

	def load_resources(self):
		# common resources
		self.g_ship1 = Game.load_png("ship1.png")
		self.g_ship2 = Game.load_png("ship2.png")
		self.g_bullet = Game.load_png("ship_bullet1.png")
		self.s_ship = Game.load_wav("ship_motor4.wav")
		self.s_ship_explosion = Game.load_wav("ship_explosion.wav")
		self.s_ship_collision = Game.load_wav("ship_get_nyam.wav")
		self.s_bullet = Game.load_wav("ship_rocket_start2.wav")

		if (self.music is not None):
			pygame.mixer.music.load(self.music)


	def init_stat(self):
		self.txt_level = Program.write(self.game.font, 0, 0, 0, '')
		self.txt_level.colour = (255,255,255)

		self.txt_lives = Program.write(self.game.font, 200, 0, 0, '')
		self.txt_lives.colour = (127,255,127)

		self.txt_health = Program.write(self.game.font, 400, 0, 0, '')
		self.txt_health.colour = (255,127,127)

		self.txt_bullets = Program.write(self.game.font, 600, 0, 0, '')
		self.txt_bullets.colour = (127,127,255)

		self.txt_message = Program.write(self.game.big_font, self.game.screen_size[0]/2, self.game.screen_size[1]/2, 4, '')

	def update_stat(self):

		if (self.ship.health <= 0):
			self.lives -= 1
			if (self.lives >= 1):
				self.ship.health = 100

		self.txt_level.text = "Level: " + self.name
		self.txt_lives.text = "Lives: " + str(self.lives)
		self.txt_health.text = "Health: " + str(self.ship.health)
		self.txt_bullets.text = "Bullets: " + str(self.bullets)
		self.txt_message_cnt += 1
		if (self.txt_message_cnt >= self.txt_message_delay):
			self.txt_message.text = ''

		if self.lives <= 0 and self.ship.health <= 0:
			# todo: game over
			self.signal(S_KILL, True)
			self.game.scene = GameOver(self.game)
			return

		if self.enemies_count == 0:

			self.signal(S_KILL, True)
			self.game.scene = self.next_level(self.game)
			self.game.scene.lives = self.lives
			self.game.scene.bullets = self.bullets 
			return

	def start(self):
		self.txt_message_cnt = 0
		self.txt_message.text = "Level " + self.name + ": " + self.description
		if (self.music is not None):
			try:
				pygame.mixer.music.play(-1)
			except Exception as e:
				pass

	def sound(self, res):
		try:
			Program.play_wav(res);
		except Exception as e:
			pass

class Main(Level):

	def begin(self, game):

		self.game = game
		self.lives = 0
		self.bullets = 0
		self.music = "music/_music2.xm"
		self.next_level = Level1

		self.load_resources()
	
		txt_message = Program.write(self.game.big_font, self.game.screen_size[0]/2, self.game.screen_size[1]/2, 4, 'Aliens vs Humans')
		txt_message.colour = (255, 255, 255)

		txt_help = Program.write(self.game.font, self.game.screen_size[0]/2, self.game.screen_size[1]/2 + 50, 4, 'Press "Enter" to start')
		txt_help.colour = (255,255,255)

		txt_copy1 = Program.write(self.game.font, self.game.screen_size[0]/2, self.game.screen_size[1] - 60, 4, 'Idea & Graphics: Nikita Karpov')
		txt_copy1.colour = (0, 255, 0)

		txt_copy2 = Program.write(self.game.font, self.game.screen_size[0]/2, self.game.screen_size[1] - 40, 4, 'Music & Programming: Andy Karpov')
		txt_copy2.colour = (0, 255, 0)

		txt_copy3 = Program.write(self.game.font, self.game.screen_size[0]/2, self.game.screen_size[1] - 20, 4, 'Copyright (c) 2012')
		txt_copy3.colour = (0, 255, 0)

		try:
			pygame.mixer.music.load(self.music)
			pygame.mixer.music.play(-1)
		except Exception as e:
			pass

		sky = Sky(self)
		ship = Ship(self, -200, 150)

		while True:

			ship.x += 4
			if (ship.x > self.game.screen_size[0] + 200):
				ship.x = -200

			if Program.key_released(K_RETURN):
				self.signal(S_KILL, True)
				self.game.scene = Level1(self.game)
				self.game.scene.lives = Config.lives
				self.game.scene.bullets = Config.bullets 
				return

			yield

class GameOver(Level):

	def begin(self, game):

		self.game = game
		self.lives = 0
		self.bullets = 0
		self.music = None
		self.next_level = Main
	
		txt_message = Program.write(self.game.big_font, self.game.screen_size[0]/2, self.game.screen_size[1]/2, 4, 'Game Over')
		txt_message.colour = (255, 0, 0)

		txt_help = Program.write(self.game.font, self.game.screen_size[0]/2, self.game.screen_size[1]/2 + 50, 4, 'Press "Enter" to continue')
		txt_help.colour = (255,255,255)

		while True:

			if Program.key_released(K_RETURN):
				self.signal(S_KILL, True)
				self.game.scene = Main(self.game)
				self.game.scene.lives = Config.lives
				self.game.scene.bullets = Config.bullets 
				return

			yield

class Won(Level):

	def begin(self, game):

		self.game = game
		self.lives = 0
		self.bullets = 0
		self.music = None
		self.next_level = Main
	
		txt_message = Program.write(self.game.big_font, self.game.screen_size[0]/2, self.game.screen_size[1]/2, 4, 'You Won!')
		txt_message.colour = (0, 255, 0)

		txt_help = Program.write(self.game.font, self.game.screen_size[0]/2, self.game.screen_size[1]/2 + 50, 4, 'Press "Enter" to continue')
		txt_help.colour = (255,255,255)		

		while True:

			if Program.key_released(K_RETURN):
				self.signal(S_KILL, True)
				self.game.scene = Main(self.game)
				self.game.scene.lives = Config.lives
				self.game.scene.bullets = Config.bullets 
				return

			yield

class Level1(Level):

	def load_resources(self):

		super(Level1, self).load_resources()

		# load gfx
		self.g_enemy1 = Game.load_png("enemy1.png")
		self.g_enemy1_1 = Game.load_png("enemy1_1.png")
		self.g_enemy2 = Game.load_png("enemy2.png")
		self.g_enemy2_2 = Game.load_png("enemy2_2.png")
		self.g_enemy2_bullet = Game.load_png("enemy2_bullet.png")
		self.g_bg = Game.load_png("bg_luna.png")

		# load sounds
		self.s_enemy2_bullet = Game.load_wav("enemy2_bullet.wav")


	def begin(self, game):

		self.name = "1"
		self.description = "Moon"
		self.game = game
		self.music = "music/_music6.xm"
		self.next_level = Level2

	
		self.load_resources()
		self.init_stat()
		self.start()

		Bg(self)
		Sky(self)
		enemies = [Enemy1(self, 300), Enemy2(self, 600), Enemy2(self, 700)]
		self.enemies_count = len(enemies)
		self.ship = Ship(self)

		while True:
			self.update_stat()
			yield


class Level2(Level):

	def load_resources(self):

		super(Level2, self).load_resources()

		# load gfx
		self.g_enemy3 = Game.load_png("enemy3.png")
		self.g_enemy3_1 = Game.load_png("enemy3_1.png")
		self.g_enemy4 = Game.load_png("enemy4.png")
		self.g_enemy4_1 = Game.load_png("enemy4_1.png")
		self.g_enemy4_bullet = Game.load_png("enemy2_bullet.png")
		self.g_bg = Game.load_png("bg_mars.png")

		# load sounds
		self.s_enemy4_bullet = Game.load_wav("enemy2_bullet.wav")

	def begin(self, game):

		self.name = "2"
		self.description = "Mars"
		self.game = game
		self.music = "music/_music7.xm"
		self.next_level = Level3
	
		self.load_resources()
		self.init_stat()
		self.start()

		Bg(self)
		Sky(self)
		enemies = [Enemy3(self, 300), Enemy4(self, 600)]
		self.enemies_count = len(enemies)
		self.ship = Ship(self)

		while True:

			self.update_stat()

			yield

class Level3(Level):

	def load_resources(self):

		super(Level3, self).load_resources()

		# load gfx
		self.g_enemy5 = Game.load_png("enemy5.png")
		self.g_enemy5_1 = Game.load_png("enemy5_1.png")
		self.g_enemy6 = Game.load_png("enemy6.png")
		self.g_enemy6_1 = Game.load_png("enemy6_1.png")
		self.g_enemy7 = Game.load_png("enemy7.png")
		self.g_enemy7_1 = Game.load_png("enemy7_1.png")
		self.g_enemy5_bullet = Game.load_png("enemy2_bullet.png")
		self.g_bg = Game.load_png("bg_neptun.png")

		# load sounds
		self.s_enemy5_bullet = Game.load_wav("enemy2_bullet.wav")

	def begin(self, game):

		self.name = "3"
		self.description = "Nepthun"
		self.game = game
		self.music = "music/music.xm"
		self.next_level = Level4
	
		self.load_resources()
		self.init_stat()
		self.start()

		Bg(self)
		Sky(self)
		enemies = [Enemy7(self, 400), Enemy6(self, randrange(500, 600)), Enemy5(self, 500, 340, 60), Enemy5(self, 500, 350, 70), Enemy5(self, 500, 360, 80), Enemy5(self, 500, 370, 90), Enemy5(self, 500, 380, 100)]
		self.enemies_count = len(enemies)
		self.ship = Ship(self)

		while True:

			self.update_stat()

			yield

class Level4(Level):

	def load_resources(self):

		super(Level4, self).load_resources()

		# load gfx
		self.g_enemy8 = Game.load_png("enemy8.png")
		self.g_enemy8_1 = Game.load_png("enemy8_1.png")
		self.g_enemy8_bullet1 = Game.load_png("enemy2_bullet.png")
		self.g_enemy8_bullet2 = Game.load_png("enemy8_bullet2.png")
		self.g_bg = Game.load_png("bg_venera.png")

		# load sounds
		self.s_enemy8_bullet1 = Game.load_wav("enemy2_bullet.wav")
		self.s_enemy8_bullet2 = Game.load_wav("enemy8_bullet2.wav")

	def begin(self, game):

		self.name = "4"
		self.description = "Venera"
		self.game = game
		self.music = "music/_music3.xm"
		self.next_level = Level5
	
		self.load_resources()
		self.init_stat()
		self.start()

		Bg(self)
		Sky(self)
		enemies = [Enemy8(self, 600)]
		self.enemies_count = len(enemies)
		self.ship = Ship(self)

		while True:

			self.update_stat()

			yield

class Level5(Level):

	def load_resources(self):

		super(Level5, self).load_resources()

		# load gfx
		self.g_enemy6 = Game.load_png("enemy6.png")
		self.g_enemy6_1 = Game.load_png("enemy6_1.png")
		self.g_bg = Game.load_png("bg_earth.png")

	def begin(self, game):

		self.name = "5"
		self.description = "Back to Earth"
		self.game = game
		self.music = "music/_music2.xm"
		self.next_level = Won
	
		self.load_resources()
		self.init_stat()
		self.start()

		Bg(self)
		Sky(self)
		enemies = [Enemy6(self, 400, 200), Enemy6(self, 500, 900), Enemy6(self, 600, 400), Enemy6(self, 700, -100)]
		self.enemies_count = len(enemies)
		self.ship = Ship(self)

		while True:

			self.update_stat()

			yield

class Ship(Process):

	health = 100
	level = None
	speed = 10
	rocket_offset = 30
	last_enemy_collision = 0

	def begin(self, level, x = None, y = None):

		if (x != None and y != None):
			self.x = x
			self.y = y
		else:
			self.x = 200
			self.y = 200
		self.graph = level.g_ship1
		self.level = level
		animate = False

		while True:

			if (animate):
				self.graph = level.g_ship2
			else:
				self.graph = level.g_ship1

			animate = not animate

			if (x == None and y == None):

				if Program.key(K_UP):
					self.y -= self.speed
				if Program.key(K_DOWN):
					self.y += self.speed
				if Program.key(K_LEFT):
					self.x -= self.speed
				if Program.key(K_RIGHT):
					self.x += self.speed

				# bounds
				if (self.y < self.graph.get_height()/2):
					self.y = self.graph.get_height()/2
				if (self.x < self.graph.get_width()/2):
					self.x = self.graph.get_width()/2
				if (self.x > self.level.game.screen_size[0] - self.graph.get_width()/2):
					self.x = self.level.game.screen_size[0] - self.graph.get_width()/2
				if (self.y > self.level.game.screen_size[1] - self.graph.get_height()/2):
					self.y = self.level.game.screen_size[1] - self.graph.get_height()/2

			e = self.collision("Enemy1")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 10

			e = self.collision("Enemy2")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 20

			e = self.collision("Enemy3")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 30

			e = self.collision("Enemy4")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 50

			e = self.collision("Enemy5")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 10

			e = self.collision("Enemy6")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 50

			e = self.collision("Enemy7")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 20

			e = self.collision("Enemy8")
			if e and level.game.millis() - self.last_enemy_collision > 500:
				self.last_enemy_collision = level.game.millis()
				level.sound(level.s_ship_collision)
				self.health -= 20

			if Program.key_released(K_SPACE):
				self.fire()

			yield

	def fire(self):
		if self.level.bullets > 0:
			ShipBullet(self.level, self, self.rocket_offset)			
			self.rocket_offset = -self.rocket_offset
			self.level.bullets -= 1

class Enemy(Process):

	def begin(self, level, x):
		return


class Enemy1(Enemy):

	def begin(self, level, x):

		self.graph = level.g_enemy1
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 20
		self.x = x
		dir = 1
		speed = 4
		animate = 0

		while True:

			animate += 1
			if (animate > 6):
				self.graph = level.g_enemy1_1
				animate = 0
			elif (animate > 3):
				self.graph = level.g_enemy1


			self.x += dir * speed
			if (self.x > 500):
				dir = -1
			if (self.x < 100):
				dir = 1

			yield

class Enemy2(Enemy):

	level = None

	def begin(self, level, x):

		self.level = level
		self.graph = level.g_enemy2
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 30
		self.x = x

		wait_fire = self.get_wait_fire()
		wait_fire_speed = 1

		while True:

			if (wait_fire <= 0):
				self.fire()
				wait_fire = self.get_wait_fire()
				self.graph = level.g_enemy2
			elif (wait_fire < 5):
				self.graph = level.g_enemy2_2
				wait_fire -= wait_fire_speed
			else:
				wait_fire -= wait_fire_speed

			yield

	def get_wait_fire(self):
		return randrange(10, 200)

	def fire(self):
		Enemy2Bullet(self.level, self)



class Enemy3(Enemy):

	def begin(self, level, x):

		self.graph = level.g_enemy3
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 20
		self.x = x
		dir = 1
		speed = 4
		animate = 0

		while True:

			animate += 1
			if (animate > 6):
				self.graph = level.g_enemy3_1
				animate = 0
			elif (animate > 3):
				self.graph = level.g_enemy3


			self.x += dir * speed
			if (self.x > 500):
				dir = -1
			if (self.x < 100):
				dir = 1

			yield

class Enemy4(Enemy):

	level = None

	def begin(self, level, x):

		self.level = level
		self.graph = level.g_enemy4
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 220
		self.x = x

		wait_fire = self.get_wait_fire()
		wait_fire_speed = 1

		while True:

			if (wait_fire <= 0):
				self.fire()
				wait_fire = self.get_wait_fire()
				self.graph = level.g_enemy4
			elif (wait_fire < 5):
				self.graph = level.g_enemy4_1
				wait_fire -= wait_fire_speed
			else:
				wait_fire -= wait_fire_speed

			yield

	def get_wait_fire(self):
		return randrange(10, 200)

	def fire(self):
		Enemy4Bullet(self.level, self)


class Enemy5(Enemy):

	level = None

	def begin(self, level, x, y, size):

		self.level = level
		self.graph = level.g_enemy5
		self.y = y
		self.x = x
		self.size = size

		wait_fire = self.get_wait_fire()
		wait_fire_speed = 1

		while True:

			if (wait_fire <= 0):
				self.fire()
				wait_fire = self.get_wait_fire()
				self.graph = level.g_enemy5
			elif (wait_fire < 5):
				self.graph = level.g_enemy5_1
				wait_fire -= wait_fire_speed
			else:
				wait_fire -= wait_fire_speed

			yield

	def get_wait_fire(self):
		return randrange(10, 200)

	def fire(self):
		Enemy5Bullet(self.level, self)




class Enemy6(Enemy):

	def begin(self, level, x, y = None):

		self.graph = level.g_enemy6
		if (y == None):
			self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 20
		else:
			self.y = y
		self.x = x
		dir = 1
		speed = 4
		animate = 0

		while True:

			animate += 1
			if (animate > 6):
				self.graph = level.g_enemy6_1
				animate = 0
			elif (animate > 3):
				self.graph = level.g_enemy6


			self.y += dir * speed
			if (self.y > level.game.screen_size[1]):
				dir = -1
			if (self.y < 0):
				dir = 1

			yield

class Enemy7(Enemy):

	def begin(self, level, x):

		self.graph = level.g_enemy7
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 20
		self.x = x
		animate = 0

		while True:
			animate += 1
			if (animate > 3):
				self.graph = level.g_enemy7_1
				animate = 0
			elif (animate > 1):
				self.graph = level.g_enemy7

			yield

class Enemy8(Enemy):

	level = None

	def begin(self, level, x):

		self.level = level
		self.graph = level.g_enemy8
		self.y = level.game.screen_size[1] - (self.graph.get_height()/2) - 100
		self.x = x

		wait_fire1 = self.get_wait_fire()
		wait_fire2 = self.get_wait_fire()
		wait_fire_speed = 1

		while True:

			if (wait_fire1 <= 0):
				self.fire1()
				wait_fire1 = self.get_wait_fire()
				self.graph = level.g_enemy8
			elif (wait_fire1 < 5):
				self.graph = level.g_enemy8_1
				wait_fire1 -= wait_fire_speed
			else:
				wait_fire1 -= wait_fire_speed

			if (wait_fire2 <= 0):
				self.fire2()
				wait_fire2 = self.get_wait_fire()
				self.graph = level.g_enemy8
			elif (wait_fire2 < 5):
				self.graph = level.g_enemy8_1
				wait_fire2 -= wait_fire_speed
			else:
				wait_fire2 -= wait_fire_speed


			yield

	def get_wait_fire(self):
		return randrange(10, 50)

	def fire1(self):
		Enemy8Bullet1(self.level, self, 5 , 3)
		Enemy8Bullet1(self.level, self, 5 , 5)
		Enemy8Bullet1(self.level, self, 5 , -1)


	def fire2(self):
		Enemy8Bullet2(self.level, self, 5, 5)
		Enemy8Bullet2(self.level, self, 3, 5)
		Enemy8Bullet2(self.level, self, 5, -1)


class ShipBullet(Process):

	def begin(self, level, player, rocket_offset):
		self.x = player.x + 60
		self.y = player.y + rocket_offset

		self.graph = level.g_bullet
		level.sound(level.s_bullet)

		while True:

			e = self.collision("Enemy1")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy2")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy2Bullet")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				return

			e = self.collision("Enemy3")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy4")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy4Bullet")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				return

			e = self.collision("Enemy5")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy5Bullet")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				return

			e = self.collision("Enemy6")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy7")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy8")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				level.enemies_count -= 1
				return

			e = self.collision("Enemy8Bullet")
			if e:
				level.sound(level.s_ship_explosion)
				e.signal(S_KILL)
				return

			#self.y += 10
			self.x += 15
			if (self.y < 0):
				return
			if (self.x < 0):
				return

			if (self.x > level.game.screen_size[0]):
				return
			if (self.y > level.game.screen_size[1]):
				return

			yield

class Enemy2Bullet(Process):

	def begin(self, level, enemy):
		self.x = enemy.x - enemy.graph.get_width()/2
		self.y = enemy.y - 70

		self.graph = level.g_enemy2_bullet
		level.sound(level.s_enemy2_bullet)

		while True:

			e = self.collision("Ship")
			if e:
				level.sound(level.s_ship_explosion)
				level.ship.health -= 100
				#if (level.ship.health <= 0):
				#	e.signal(S_KILL)
				return

			self.y -= 2
			self.x -= 5
			if (self.y < 0 or self.y > level.game.screen_size[1]):
				return
			if (self.x < 0 or self.y > level.game.screen_size[0]):
				return

			yield

class Enemy4Bullet(Process):

	def begin(self, level, enemy):
		self.x = enemy.x - enemy.graph.get_width()/2
		self.y = enemy.y - 40

		self.graph = level.g_enemy4_bullet
		level.sound(level.s_enemy4_bullet)

		while True:

			e = self.collision("Ship")
			if e:
				level.sound(level.s_ship_explosion)
				level.ship.health -= 100
				#if (level.ship.health <= 0):
				#	e.signal(S_KILL)
				return

			#self.y -= 2
			self.x -= 5
			if (self.y < 0 or self.y > level.game.screen_size[1]):
				return
			if (self.x < 0 or self.y > level.game.screen_size[0]):
				return

			yield

class Enemy5Bullet(Process):

	def begin(self, level, enemy):

		self.graph = level.g_enemy5_bullet

		self.x = enemy.x - enemy.graph.get_width()/2
		self.y = enemy.y - enemy.graph.get_height()/2 + self.graph.get_height()/2

		level.sound(level.s_enemy5_bullet)

		while True:

			e = self.collision("Ship")
			if e:
				level.sound(level.s_ship_explosion)
				level.ship.health -= 100
				return

			#self.y -= 2
			self.x -= 5
			if (self.y < 0 or self.y > level.game.screen_size[1]):
				return
			if (self.x < 0 or self.y > level.game.screen_size[0]):
				return

			yield


class Enemy8Bullet1(Process):

	def begin(self, level, enemy, offset_x = 5, offset_y = 3):

		self.graph = level.g_enemy8_bullet1

		self.x = enemy.x - enemy.graph.get_width()/2 
		self.y = enemy.y - enemy.graph.get_height()/2 + self.graph.get_height()/2  + 20

		level.sound(level.s_enemy8_bullet1)

		while True:

			e = self.collision("Ship")
			if e:
				level.sound(level.s_ship_explosion)
				level.ship.health -= 100
				return

			self.y -= offset_y
			self.x -= offset_x
			if (self.y < 0 or self.y > level.game.screen_size[1]):
				return
			if (self.x < 0 or self.y > level.game.screen_size[0]):
				return

			yield

class Enemy8Bullet2(Process):

	def begin(self, level, enemy, offset_x = 5, offset_y = 5):

		self.graph = level.g_enemy8_bullet2

		self.x = enemy.x - enemy.graph.get_width()/2 + 40
		self.y = enemy.y - enemy.graph.get_height()/2 + self.graph.get_height()/2

		level.sound(level.s_enemy8_bullet2)

		while True:

			e = self.collision("Ship")
			if e:
				level.sound(level.s_ship_explosion)
				level.ship.health -= 100
				return

			self.y -= offset_y
			self.x -= offset_x
			if (self.y < 0 or self.y > level.game.screen_size[1]):
				return
			if (self.x < 0 or self.y > level.game.screen_size[0]):
				return

			yield


if __name__ == '__main__':
	Game()
