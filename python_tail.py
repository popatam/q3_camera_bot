import time
import os



def tail(file, from_where=2):
  fd = open(file, mode='r')
  #fd.seek(0, 0)  # From the beggining of file
  fd.seek(0, from_where)  # From the end of file
  old_inode = os.stat(file).st_ino
  try:
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
  except Exception as e:
    print(e)


### test
a = tail('./file')

for i in a:
  print(i, end='')