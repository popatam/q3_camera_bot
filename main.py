import os
import re
import subprocess
from datetime import datetime as dt
import time


class q3_cam():
  def __init__(self):
    self.q3_log = '/home/q3/.q3a/osp/qconsole.log'
    self.regex_entered = re.compile(r'(broadcast: print ")(.*)(\^7 entered the game\\n")')
    self.regex_conn = re.compile(r'(broadcast: print ")(.*)( \^7connected\\n")')
    self.regex_disc = re.compile(r'(broadcast: print ")(.*)(\^7 disconnected\\n")')
    self.regex_timed = re.compile(r'(broadcast: print ")(.*)(\^7 timed out\\n")')
    self.regex_dropped = re.compile(r'(broadcast: print ")(.*)(\^7 Dropped due to inactivity\\n")')
    self.regex_ready = re.compile(r'All players ready.  Countdown started!')
    self.regex_warmup = re.compile(r'Warmup:')
    # self.regex_shutd = re.compile(r'==== ShutdownGame ====')  # unused
    # Rcon from 192.168.0.216: map pro-q3dm6
    # Loading viewcam positions from "cfg-viewcam/viewcam-pro-q3dm6.cfg"
    # Current map: "pro-q3dm6"
    # Next map: SAME MAP
    # (InitGame: .*\\mapname\\)(pro-q3dm6(\\.*)
    self.bots_dict = dict()
    self.bot_counter = 0
    host = ''  # FIXME
    port = '27960'
    self.q3_server = ':'.join([host, port])

  def log_it(self, text):
    print(text)  # FIXME

  def bash(self, *args):
    #  "выполняет команду на баше"
    cmd_string = ' '.join(str(e) for e in args)
    cmd = bytes(cmd_string, encoding='utf-8')
    proc = subprocess.Popen([cmd], shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
      outs, errs = proc.communicate(input=None, timeout=20)
      if errs:
        return errs.decode('utf-8')
      else:
        return outs.decode('utf-8')
    except Exception as e:
      proc.kill()

  def connected(self, line):
    screen_name = ''.join(['camera_', str(self.bot_counter)])
    bot_name = ''.join(['camera_', str(self.bot_counter)])
    result = self.regex_conn.match(line)
    if result is not None:
      if result.groups()[1].startswith('camera_'):
        self.log_it('its a bot')
#        print('it is a bot')  # pass  FIXME
      else:
        player = result.groups()[1]
        self.bash('screen -d -m -S', screen_name)
        self.bash('screen -S', screen_name, '-X stuff', '"su q3 \n"')
        self.bash('screen -S', screen_name, '-X stuff', '"Xvfb ', ''.join([':', str(self.bot_counter)]),
             ' -shmem -screen 0 32x24x16 & \n"')
        self.bash('screen -S', screen_name,
             '-X stuff',
             ''.join(['"DISPLAY=0:', str(self.bot_counter)]),
             ' /usr/lib/ioquake3/ioquake3 +set fs_game osp +set com_protocol 68 +set r_mode -1 +set r_fullscreen 0 +set r_customwidth 32 +set r_customheight 24',
             '+set cl_autoRecordDemo 0',
             '+set g_syncronousClients 1',
             '+connect', self.q3_server,
             '+set name', bot_name,
             ' \n"')
        self.bots_dict.update({screen_name: player})
        self.bot_counter += 1
    else:
      pass

  def entered(self, line):
    result = self.regex_entered.match(line)
    if result is not None:
      entered_player = result.groups()[1]
      for bot_name, player in self.bots_dict.items():
        if entered_player == bot_name:
          print('going spec')  # delme later
          time.sleep(1.5)
          player_escaped = re.sub(r'\^\d', '', player)
          self.bash('screen -S', bot_name, '-X stuff', '"\\TEAM s \n"')  # go to spectators
          self.bash('screen -S', bot_name, '-X stuff', '"\\FOLLOW', player_escaped,
               ' \n"')  # go to spectators & follow player
          self.bash('screen -S', bot_name, '-X stuff', '"/team s \n"')  # go to spectators
          self.bash('screen -S', bot_name, '-X stuff', '"/follow', player_escaped, ' \n"')  # go to spectators & follow player
    else:
      pass

  def disconnected(self, line):
   result = self.regex_disc.match(line)
   if result is not None:
     clear_list = list()
     for k, v in self.bots_dict.items():
       if v == result.groups()[1]:
         screen_name = k
         display_number = screen_name[7:]
         self.bash('screen -S', screen_name, '-X stuff', ' "\\Quit \n"')  # exit from game
         self.bash('screen -S', screen_name, '-X stuff', ' " exit \n"')  # exit to root
         self.bash("kill", "`ps aux|grep  'Xvfb", ''.join([':', str(display_number)]),
              "-shme'|grep ^q3|awk '{print $2}'`")  # kill Xvfb
         self.bash('screen -S', screen_name, '-X stuff', ' " exit \n"')  # close screen
         clear_list.append(screen_name)
     for i in clear_list:
       self.bots_dict.pop(i)

  def ready(self, line):
    result = self.regex_ready.match(line)
    if result is not None:
      for screen_name, player in self.bots_dict.items():
        player_escaped = re.sub(r'\^\d', '', player)
        self.bash('screen -S', screen_name, '-X stuff', '"\\FOLLOW', player_escaped, ' \n"')  # go to spetators
        self.bash('screen -S', screen_name, '-X stuff', '"\\RECORD ',
                  ''.join([dt.now().strftime('%Y-%m-%d:%X'), '-', player_escaped]), ' \n"')  # start demo recording
    else:
      pass

  def warmup(self, line):
    result = self.regex_warmup.match(line)
    if result is not None:
      for screen_name, player in self.bots_dict.items():
        self.bash('screen -S', screen_name, '-X stuff', "'\\stoprecord \n'")  # stop demo recording
    else:
      pass

  def dropped(self, line):
    result = self.regex_dropped.match(line)
    if result is not None:
      clear_list = list()
      for screen_name, player in self.bots_dict.items():
        display_number = screen_name[7:]
        if player == result.groups()[1]:
          self.bash('screen -S', screen_name, '-X stuff', ' "\\Quit \n"')  # exit from game
          self.bash('screen -S', screen_name, '-X stuff', ' " exit \n"')  # exit to root
          self.bash("kill", "`ps aux|grep  'Xvfb", ''.join([':', str(display_number)]),
               "-shme'|grep ^q3|awk '{print $2}'`")  # kill Xvfb
          self.bash('screen -S', screen_name, '-X stuff', ' " exit \n"')  # close screen
          clear_list.append(screen_name)
        elif screen_name == result.groups()[1]:
          q3.log_it('camera bot dropped')
      for i in clear_list:
        self.bots_dict.pop(i)
    else:
      pass

  def timed(self, line):
    result = self.regex_timed.match(line)
    if result is not None:
      clear_list = list()
      for screen_name, player in self.bots_dict.items():
        display_number = screen_name[7:]
        if player == result.groups()[1]:
          self.bash('screen -S', screen_name, '-X stuff', ' "\\Quit \n"')  # exit from game
          self.bash('screen -S', screen_name, '-X stuff', ' " exit \n"')  # exit to root
          self.bash("kill", "`ps aux|grep  'Xvfb", ''.join([':', str(display_number)]),
               "-shme'|grep ^q3|awk '{print $2}'`")  # kill Xvfb
          self.bash('screen -S', screen_name, '-X stuff', ' " exit \n"')  # close screen
          clear_list.append(screen_name)
        elif screen_name == result.groups()[1]:
          print('something went wrong')  # FIXME
      for i in clear_list:
        self.bots_dict.pop(i)
    else:
      pass

  def tail(self, file):
    fd = open(file, mode='r')
    #fd.seek(0, 0)  # From the beggining of file
    fd.seek(0, 2)  # From the end of file
    old_inode = os.stat(file).st_ino
    print(old_inode)
    while True:
      line_buffer = fd.readlines()
      if len(line_buffer) == 0:
        try:
          new_inode = os.stat(file).st_ino
          if new_inode != old_inode:
            fd = open(file, mode='r')
            old_inode = os.stat(file)
          else:
            pass
        except Exception as e:
          print(e)
        time.sleep(0.5)
      else:
        for line in line_buffer:
          yield line


if __name__ == '__main__':
  q3 = q3_cam()
  lines_gen = q3.tail(q3.q3_log)
  for line in lines_gen:
    q3.connected(line)
    q3.entered(line)
    q3.disconnected(line)
    q3.ready(line)
    q3.warmup(line)
    q3.dropped(line)
    q3.timed(line)
