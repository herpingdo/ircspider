from socket import socket, AF_INET, SOCK_STREAM
from urllib import urlopen
from time import sleep
import sys
import threading
import traceback
#sock = socket(AF_INET, SOCK_STREAM)

netlist = urlopen("http://irc.netsplit.de/networks/").read()
netlist = netlist.split("\n")

#Netsplit.de IRC network crawler by AppleDash (I'm ashamed.)
#The most horrible thing I've ever written.
#It is only half working, and horribly inefficient.
#I claim I can code, but I don't claim I can code well.
#It is littered with random "pass"es because if I don't put
#something there, and I switch away from my editor, it messes
#up the indentation.

class CrawlThread(threading.Thread):

	def notinit(self, host):
		self.host = host

	def run(self):
		w = open("./log.txt", 'a')
		sock = socket(AF_INET, SOCK_STREAM)
		sock.connect((self.host, 6667))
		running = 1
		chanlist = list()
		sock.send("NICK Spider1337\r\nUSER Spider * * :Spider\r\n")
		cur = ""
		curdata = ""
		factor = 50
		while running:
			data = sock.recv(2048)
			if not data or data == "":
				continue
			for line in data.split("\n"):
				if not line or line == "":
					continue
				s = line.split(" ")
				try:
					if s[1] == "372": #MOTD
						continue
					if s[1] == "376" or s[1] == "422": #End of MOTD (or missing MOTD)
						sock.send("LIST\r\n")
						continue
					if s[0] == "PING":
						sock.send(line.replace("PING", "PONG")  + '\r\n')
						continue
					if s[1] == "322": #/list channel
						#:anti-malware.247fixes.com 322 Spider1337 #domainops 3 :[+ntr] Topic: Open Chat 4<<14][4>> DragonHeart is headed home from
						chan = s[3]
						chanlist.append(chan)
						continue							
					if s[1] == "323": #End of /list
						chan = chanlist.pop()
						cur = chan
						sock.send("JOIN " + chan + "\r\n")
						continue
					if s[1] == "332": #Channel topic
						line2 = line[1:]
						topic = line2[line2.index(":"):]
						curdata = curdata + "\n\tTOPIC: " + topic + " "
						sock.send("MODE " + cur + "\r\n")
					if s[1] == "474" or s[1] == "KICK": #Banned or got kicked
						curdata = "\n\tNetwork: " + self.host + curdata
						curdata = curdata + "\n\t" + "Trolling Factor: " + str(factor) + " "
						print "Channel: " + cur ,
						print curdata
						w.write("Channel: " + cur)
						w.write(curdata + "\n")
						cur = ""
						curdata = ""
						chan = chanlist.pop()
						cur = chan
						if not chan:
							sock.send("QUIT :Bye bye\r\n")
							running = 0
						sock.send("JOIN " + chan + "\r\n")
						pass
						continue
					if s[1] == "324": #Mode reply
						mode = s[4]
						curdata = curdata + "\n\tMODES: " + mode + " "
						moderated = self.modes(mode, "m")
						noexternal = self.modes(mode, "n")
						opssett = self.modes(mode, "t")
						if moderated:
							factor = factor - 10
						if noexternal == 0:
							factor = factor + 10
						if opssett == 0:
							factor = factor + 25
						#TODO: Implement more factor modifiers.
						sock.send("PART " + cur + "\r\n")
						curdata = "\n\tNetwork: " + self.host + curdata
						curdata = curdata + "\n\t" + "Trolling Factor: " + str(factor) + " "
						print "Channel: " + cur ,
						print curdata
						w.write("Channel: " + cur)
						w.write(curdata + "\n")
						cur = ""
						curdata = ""
						chan = None
						try:
							chan = chanlist.pop()
							cur = chan
						except:
							pass
						if not chan or chan is None:
							sock.send("QUIT :Bye bye\r\n")
							running = 0
							break
						sock.send("JOIN " + chan + "\r\n")
						continue
					if s[1] == "353": #Users list
						line2 = line[1:]
						usersraw = line2[line2.index(":"):]
						users = line2[1:].split(" ")
						curdata += "\n\tUSERS: " + usersraw + " "
						for u in users:
							c = ord(u[0])
							if c == ord('@') or c == ord('&') or c == ord('~') or c == ord('%'):
								factor = factor - 5
						continue
					if "You cannot list within the first" in line:
						sleep(60100)
						sock.send("LIST\r\n")
				except IndexError as ie:
					pass
				except (Exception) as e:
					print '-'*60
					traceback.print_exc(file=sys.stdout)
					print '-'*60
 				except:
 					print("Exception")
 					print sys.exc_info()[0]
				continue #Comment this out for debug printing
				for c in line:
					if (ord(c) < 0 or ord(c) > 298):
						continue
				print "[" + self.host + "] " + line

	def modes(self, s, s2):
		ret = 0
		try:
			ret = s.index(s2)
		except:
			ret = 0
		if ret > 0:
			return 1
		return 0

def crawlIrc(host):
	th = CrawlThread()
	th.notinit(host)
	th.start()


def processNetwork(path):
	nethtml = urlopen(path).read()
	split = nethtml.split("\n")
	count = 0;
	doing = 0
	for line in split:
		if count == 4:
			parsed = line.split("<td nowrap=\"nowrap\">")[1].split("&nbsp")[0]
			print parsed
			crawlIrc(parsed)
			break
		if "hostname&nbsp;&nbsp;" in line: 
			doing = 1
		if doing:
			count = count + 1
#       <td nowrap="nowrap">irc.chaosirc.com&nbsp;&nbsp;</td>

doing = 0

for line in netlist:
	if doing:
		spl = line.split("href=\"/networks/")
		for l in spl:
			if "<td colspan=" in l:
				continue
			name = l.split("\"")[0]
			processNetwork("http://irc.netsplit.de/networks/" + name)
		doing = 0
		#break
	else:
		if ("<th valign=\"top\">" in line):
			doing = 1
