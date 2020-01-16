import StringIO
import time
import datetime as dt
import pycurl

import stem.control

MIDDLE_NODE = 'E4F3849D1292D255C0BF6BB96FE7D3C507B098BB'#'198F12E2DEFBE6BEEBC38B2FEDD615AECB38DA7A'

#EXIT_FINGERPRINT = '3994E734DCD794479D1A60F4ABD3FC91CAA395EE'

SOCKS_PORT = 9050
CONNECTION_TIMEOUT = 30  # timeout before we give up on a circuit

def query(url):
  """
  Uses pycurl to fetch a site using the proxy on the SOCKS_PORT.
  """

  output = StringIO.StringIO()

  query = pycurl.Curl()
  query.setopt(pycurl.URL, url)
  query.setopt(pycurl.PROXY, 'localhost')
  query.setopt(pycurl.PROXYPORT, SOCKS_PORT)
  query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
  query.setopt(pycurl.CONNECTTIMEOUT, CONNECTION_TIMEOUT)
  query.setopt(pycurl.WRITEFUNCTION, output.write)



  try:
    query.perform()
    conn_time = query.getinfo(pycurl.CONNECT_TIME) #CONNECT_TIME
    total_time = query.getinfo(pycurl.TOTAL_TIME) #TOTAL_TIME
    downL_speed = query.getinfo(pycurl.SPEED_DOWNLOAD) #SPEED_DOWNLOAD
    print('time to first byte: %0.4f' % conn_time)
    print('time to last byte: %0.4f ' % total_time)
    print('Download speed: %0.2f' % downL_speed)

    return output.getvalue()
  except pycurl.error as exc:
    raise ValueError("Unable to reach %s (%s)" % (url, exc))

with stem.control.Controller.from_port() as controller:
  controller.authenticate()
  
  

  circuit_id = controller.extend_circuit('0',await_build = True) # We create a new circuit composed of nodes


  print(dt.datetime.now())
  circ = controller.get_circuit(circuit_id=circuit_id)

  entry_node = ""
  exit_node = ""

  for i, entry in enumerate(circ.path): #Here we store enter and exit node
      div = '+' if (i == len(circ.path) - 1) else '|'
      fingerprint, nickname = entry

      if (i == 0):
        entry_node = entry[0] 
      elif (i == len(circ.path) - 1):
        exit_node = entry[0] 


  controller.close_circuit(circuit_id) #We close generated circuits

  print ("entry node: %s" % entry_node)
  print("exit node : %s" % exit_node)

  tor_pid = controller.get_pid()

  

  start_time = time.time() #We get time
  circuit_id = controller.extend_circuit('0', path=[entry_node,MIDDLE_NODE,exit_node],await_build = True) #We create the circuit with our own node
  difference_time = (time.time() - start_time) # We calculate the difference time

  def attach_stream(stream):
    if stream.status == 'NEW':
      controller.attach_stream(stream.id, circuit_id)

  controller.add_event_listener(attach_stream, stem.control.EventType.STREAM)

  try:
    controller.set_conf('__LeaveStreamsUnattached', '1')  # leave stream management to us
    

    check_page = query('google.com') #The url that we want to reach

    print('%0.2f seconds' % difference_time) # Results for Step 2

  finally:
    controller.remove_event_listener(attach_stream)
    controller.reset_conf('__LeaveStreamsUnattached')