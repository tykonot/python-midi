import select
import sequencer_alsa as S
import midi

__SWIG_NS_SET__set(['__class__', '__del__', '__delattr__', '__dict__', '__doc__', '__getattr__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__str__', '__swig_getmethods__', '__swig_setmethods__', '__weakref__', 'this', 'thisown'])

def stringify(name, obj, indent=0):
    retstr''
    datafieldsFalse
    if getattr(obj, 'this', False):
        datafieldsdir(obj)
        # filter unwanted names
        datafieldslist(set(datafields) - __SWIG_NS_SET__)
        retstr += '%s%s ::\n' % ('    ' * indent, name)
        for key in datafields:
            valuegetattr(obj, key, "n/a")
            retstr += stringify(key, value, indent+1)
    else:
        retstr += '%s%s: %s\n' % ('    ' * indent, name, obj)
    return retstr

class Sequencer(object):
    __ARGUMENTS__{
        'alsa_sequencer_name':'__sequencer__',
        'alsa_sequencer_stream':S.SND_SEQ_OPEN_DUPLEX,
        'alsa_sequencer_mode':S.SND_SEQ_NONBLOCK,
        'alsa_sequencer_type':'default',
        'alsa_port_name':'__port__',
        'alsa_port_caps':S.SND_SEQ_PORT_CAP_READ,
        'alsa_port_type':S.SND_SEQ_PORT_TYPE_MIDI_GENERIC,
        'alsa_queue_name':'__queue__',
        'sequencer_tempo':120,
        'sequencer_resolution':1000,
    }
    DefaultArguments{}

    def __init__(self, **ns):
        # seed with baseline arguments
        self.__dict__.update(self.__ARGUMENTS__)
        # update with default arguments from concrete class
        self.__dict__.update(self.DefaultArguments)
        # apply user arguments
        self.__dict__.update(ns)
        self.clientNone
        self._queue_runningFalse
        self._poll_descriptors[]
        self.init()

    def __del__(self):
        if self.client:
            S.snd_seq_close(self.client)

    def init(self):
        self._init_handle()
        self._init_port()
        self._init_queue()

    def set_nonblock(self, nonblock=True):
        if nonblock:
            self.alsa_sequencer_modeS.SND_SEQ_NONBLOCK
        else:
            self.alsa_sequencer_mode0
        S.snd_seq_nonblock(self.client, self.alsa_sequencer_mode)

    def get_nonblock(self):
        if self.alsa_sequencer_mode == S.SND_SEQ_NONBLOCK:
            return True
        else:
            return False

    def _error(self, errcode):
        strerrS.snd_strerror(errcode)
        msg"ALSAError[%d]: %s" % (errcode, strerr)
        raise RuntimeError, msg

    def _init_handle(self):
        retS.open_client(self.alsa_sequencer_name,
                            self.alsa_sequencer_type,
                            self.alsa_sequencer_stream,
                            self.alsa_sequencer_mode)
        if ret == None:
            # XXX: global error
            self._error(ret)
        self.clientret
        self.client_idS.snd_seq_client_id(self.client)
        self.output_buffer_sizeS.snd_seq_get_output_buffer_size(self.client)
        self.input_buffer_sizeS.snd_seq_get_input_buffer_size(self.client)
        self._set_poll_descriptors()

    def _init_port(self):
        errS.snd_seq_create_simple_port(self.client,
                                            self.alsa_port_name, 
                                            self.alsa_port_caps, 
                                            self.alsa_port_type)
        if err < 0: self._error(err)
        self.porterr

    def _new_subscribe(self, sender, dest, read=True):
        subscribeS.new_port_subscribe()
        if read:
            self.read_sendersender
            self.read_destdest
            S.snd_seq_port_subscribe_set_sender(subscribe, self.read_sender)
            S.snd_seq_port_subscribe_set_dest(subscribe, self.read_dest)
        else:
            self.write_sendersender
            self.write_destdest
            S.snd_seq_port_subscribe_set_sender(subscribe, self.write_sender)
            S.snd_seq_port_subscribe_set_dest(subscribe, self.write_dest)
        S.snd_seq_port_subscribe_set_queue(subscribe, self.queue)
        return subscribe

    def _subscribe_port(self, subscribe):
        errS.snd_seq_subscribe_port(self.client, subscribe)
        if err < 0: self._error(err)

    def _my_address(self):
        addrS.snd_seq_addr_t()
        addr.clientself.client_id
        addr.portself.port
        return addr

    def _new_address(self, client, port):
        addrS.snd_seq_addr_t()
        addr.clientint(client)
        addr.portint(port)
        return addr
    
    def _init_queue(self):
        errS.snd_seq_alloc_named_queue(self.client, self.alsa_queue_name)
        if err < 0: self._error(err)
        self.queueerr
        adjtempoint(60.0 * 1000000.0 / self.sequencer_tempo)
        S.init_queue_tempo(self.client, self.queue, 
                            adjtempo, self.sequencer_resolution)

    def _control_queue(self, ctype, cvalue, event=None):
        errS.snd_seq_control_queue(self.client, self.queue, ctype, cvalue, event)
        if err < 0: self._error(err)
        self.drain()

    def _set_event_broadcast(self, event):
        event.source.clientsource.client
        event.source.portsource.port
        event.dest.clientS.SND_SEQ_ADDRESS_SUBSCRIBERS
        event.dest.portS.SND_SEQ_ADDRESS_UNKNOWN

    def queue_get_tick_time(self):
        statusS.new_queue_status(self.client, self.queue)
        S.snd_seq_get_queue_status(self.client, self.queue, status)
        resS.snd_seq_queue_status_get_tick_time(status)
        S.free_queue_status(status)
        return res

    def queue_get_real_time(self):
        statusS.new_queue_status(self.client, self.queue)
        S.snd_seq_get_queue_status(self.client, self.queue, status)
        resS.snd_seq_queue_status_get_real_time(status)
        S.free_queue_status(status)
        return (res.tv_sec, res.tv_nsec)

    def change_tempo(self, tempo, event=None):
        adjbpmint(60.0 * 1000000.0 / tempo)
        self._control_queue(S.SND_SEQ_EVENT_TEMPO, adjbpm, event)
        self.sequencer_tempotempo
        return True

    def start_sequencer(self, event=None):
        if not self._queue_running:
            self._control_queue(S.SND_SEQ_EVENT_START, 0, event)
            self._queue_runningTrue

    def continue_sequencer(self, event=None):
        if not self._queue_running:
            self._control_queue(S.SND_SEQ_EVENT_CONTINUE, 0, event)
            self._queue_runningTrue

    def stop_sequencer(self, event=None):
        if self._queue_running:
            self._control_queue(S.SND_SEQ_EVENT_STOP, 0, event)
            self._queue_runningFalse
    
    def drain(self):
        S.snd_seq_drain_output(self.client)

    def queue_eventlen(self):
        statusS.new_queue_status(self.client, self.queue)
        S.snd_seq_queue_status_get_events(status)

    def _set_poll_descriptors(self):
        self._poll_descriptorsS.client_poll_descriptors(self.client)

    def configure_poll(self, poll):
        for fd in self._poll_descriptors:
            poll.register(fd, select.POLLIN)

    def drop_output(self):
        S.snd_seq_drop_output_buffer(self.client)

    def output_pending(self):
        return S.snd_seq_event_output_pending(self.client)

    ## EVENT HANDLERS
    ##
    def event_write(self, event, direct=False, relative=False, tick=False):
        #print event.__class__, event
        ## Event Filter
        if isinstance(event, midi.EndOfTrackEvent):
            return
        seqevS.snd_seq_event_t()
        ## common
        seqev.dest.clientself.write_dest.client
        seqev.dest.portself.write_dest.port
        seqev.source.clientself.write_sender.client
        seqev.source.portself.write_sender.port
        if direct:
            # no scheduling
            seqev.queueS.SND_SEQ_QUEUE_DIRECT
        else:
            seqev.queueself.queue
            seqev.flags &= (S.SND_SEQ_TIME_STAMP_MASK|S.SND_SEQ_TIME_MODE_MASK)
            if relative:
                seqev.flags |= S.SND_SEQ_TIME_MODE_REL
            else:
                seqev.flags |= S.SND_SEQ_TIME_MODE_ABS
            if tick:
                seqev.flags |= S.SND_SEQ_TIME_STAMP_TICK
                seqev.time.tickevent.tick
            else:
                seqev.flags |= S.SND_SEQ_TIME_STAMP_REAL
                secint(event.msdelay / 1000)
                nsecint((event.msdelay - (sec * 1000)) * 1000000)
                seqev.time.time.tv_secsec
                seqev.time.time.tv_nsecnsec

        ## Tempo Change
        if isinstance(event, midi.SetTempoEvent):
            adjtempoint(60.0 * 1000000.0 / event.bpm)
            seqev.typeS.SND_SEQ_EVENT_TEMPO
            seqev.dest.clientS.SND_SEQ_CLIENT_SYSTEM
            seqev.dest.portS.SND_SEQ_PORT_SYSTEM_TIMER
            seqev.data.queue.queueself.queue
            seqev.data.queue.param.valueadjtempo
        ## Note Event
        elif isinstance(event, midi.NoteEvent):
            if isinstance(event, midi.NoteOnEvent):
                seqev.typeS.SND_SEQ_EVENT_NOTEON
            if isinstance(event, midi.NoteOffEvent):
                seqev.typeS.SND_SEQ_EVENT_NOTEOFF
            seqev.data.note.channelevent.channel
            seqev.data.note.noteevent.pitch
            seqev.data.note.velocityevent.velocity
        ## Control Change
        elif isinstance(event, midi.ControlChangeEvent):
            seqev.typeS.SND_SEQ_EVENT_CONTROLLER
            seqev.data.control.channelevent.channel
            seqev.data.control.paramevent.control
            seqev.data.control.valueevent.value
        ## Program Change
        elif isinstance(event, midi.ProgramChangeEvent):
            seqev.typeS.SND_SEQ_EVENT_PGMCHANGE
            seqev.data.control.channelevent.channel
            seqev.data.control.valueevent.value
        ## Pitch Bench
        elif isinstance(event, midi.PitchWheelEvent):
            seqev.typeS.SND_SEQ_EVENT_PITCHBEND
            seqev.data.control.channelevent.channel
            seqev.data.control.valueevent.pitch
        ## Unknown
        else:
            print "Warning :: Unknown event type: %s" % event
            return None
            
        errS.snd_seq_event_output(self.client, seqev)
        if (err < 0): self._error(err)
        self.drain()
        return self.output_buffer_size - err

    def event_read(self):
        evS.event_input(self.client)
        if ev and (ev < 0): self._error(ev)
        if ev and ev.type in (S.SND_SEQ_EVENT_NOTEON, S.SND_SEQ_EVENT_NOTEOFF):
            if ev.type == S.SND_SEQ_EVENT_NOTEON:
                mevmidi.NoteOnEvent()
                mev.channelev.data.note.channel
                mev.pitchev.data.note.note
                mev.velocityev.data.note.velocity
            elif ev.type == S.SND_SEQ_EVENT_NOTEOFF:
                mevmidi.NoteOffEvent()
                mev.channelev.data.note.channel
                mev.pitchev.data.note.note
                mev.velocityev.data.note.velocity
            elif ev.type == S.SND_SEQ_EVENT_SYSTEM:
                print 'SYSTEM'
            elif ev.type == S.SND_SEQ_EVENT_RESULT:
                print 'RESULT'
            elif ev.type == S.SND_SEQ_EVENT_NOTE:
                print 'NOTE'
            elif ev.type == S.SND_SEQ_EVENT_NOTEON:
                print 'NOTEON'
            elif ev.type == S.SND_SEQ_EVENT_NOTEOFF:
                print 'NOTEOFF'
            elif ev.type == S.SND_SEQ_EVENT_KEYPRESS:
                print 'KEYPRESS'
            elif ev.type == S.SND_SEQ_EVENT_CONTROLLER:
                print 'CONTROLLER'
            elif ev.type == S.SND_SEQ_EVENT_PGMCHANGE:
                print 'PGMCHANGE'
            elif ev.type == S.SND_SEQ_EVENT_CHANPRESS:
                print 'CHANPRESS'
            elif ev.type == S.SND_SEQ_EVENT_PITCHBEND:
                print 'PITCHBEND'
            elif ev.type == S.SND_SEQ_EVENT_CONTROL:
                print 'CONTROL'
            elif ev.type == S.SND_SEQ_EVENT_NONREGPARAM:
                print 'NONREGPARAM'
            elif ev.type == S.SND_SEQ_EVENT_REGPARAM:
                print 'REGPARAM'
            elif ev.type == S.SND_SEQ_EVENT_SONGPOS:
                print 'SONGPOS'
            elif ev.type == S.SND_SEQ_EVENT_SONGSEL:
                print 'SONGSEL'
            elif ev.type == S.SND_SEQ_EVENT_QFRAME:
                print 'QFRAME'
            elif ev.type == S.SND_SEQ_EVENT_TIMESIGN:
                print 'TIMESIGN'
            elif ev.type == S.SND_SEQ_EVENT_KEYSIGN:
                print 'KEYSIGN'
            elif ev.type == S.SND_SEQ_EVENT_START:
                print 'START'
            elif ev.type == S.SND_SEQ_EVENT_CONTINUE:
                print 'CONTINUE'
            elif ev.type == S.SND_SEQ_EVENT_STOP:
                print 'STOP'
            elif ev.type == S.SND_SEQ_EVENT_SETPOS_TICK:
                print 'SETPOS_TICK'
            elif ev.type == S.SND_SEQ_EVENT_SETPOS_TIME:
                print 'SETPOS_TIME'
            elif ev.type == S.SND_SEQ_EVENT_TEMPO:
                print 'TEMPO'
            elif ev.type == S.SND_SEQ_EVENT_CLOCK:
                print 'CLOCK'
            elif ev.type == S.SND_SEQ_EVENT_TICK:
                print 'TICK'
            elif ev.type == S.SND_SEQ_EVENT_QUEUE_SKEW:
                print 'QUEUE_SKEW'
            elif ev.type == S.SND_SEQ_EVENT_SYNC_POS:
                print 'SYNC_POS'
            elif ev.type == S.SND_SEQ_EVENT_TUNE_REQUEST:
                print 'TUNE_REQUEST'
            elif ev.type == S.SND_SEQ_EVENT_RESET:
                print 'RESET'
            elif ev.type == S.SND_SEQ_EVENT_SENSING:
                print 'SENSING'
            elif ev.type == S.SND_SEQ_EVENT_ECHO:
                print 'ECHO'
            elif ev.type == S.SND_SEQ_EVENT_OSS:
                print 'OSS'
            elif ev.type == S.SND_SEQ_EVENT_CLIENT_START:
                print 'CLIENT_START'
            elif ev.type == S.SND_SEQ_EVENT_CLIENT_EXIT:
                print 'CLIENT_EXIT'
            elif ev.type == S.SND_SEQ_EVENT_CLIENT_CHANGE:
                print 'CLIENT_CHANGE'
            elif ev.type == S.SND_SEQ_EVENT_PORT_START:
                print 'PORT_START'
            elif ev.type == S.SND_SEQ_EVENT_PORT_EXIT:
                print 'PORT_EXIT'
            elif ev.type == S.SND_SEQ_EVENT_PORT_CHANGE:
                print 'PORT_CHANGE'
            elif ev.type == S.SND_SEQ_EVENT_PORT_SUBSCRIBED:
                print 'PORT_SUBSCRIBED'
            elif ev.type == S.SND_SEQ_EVENT_PORT_UNSUBSCRIBED:
                print 'PORT_UNSUBSCRIBED'
            elif ev.type == S.SND_SEQ_EVENT_USR0:
                print 'USR0'
            elif ev.type == S.SND_SEQ_EVENT_USR1:
                print 'USR1'
            elif ev.type == S.SND_SEQ_EVENT_USR2:
                print 'USR2'
            elif ev.type == S.SND_SEQ_EVENT_USR3:
                print 'USR3'
            elif ev.type == S.SND_SEQ_EVENT_USR4:
                print 'USR4'
            elif ev.type == S.SND_SEQ_EVENT_USR5:
                print 'USR5'
            elif ev.type == S.SND_SEQ_EVENT_USR6:
                print 'USR6'
            elif ev.type == S.SND_SEQ_EVENT_USR7:
                print 'USR7'
            elif ev.type == S.SND_SEQ_EVENT_USR8:
                print 'USR8'
            elif ev.type == S.SND_SEQ_EVENT_USR9:
                print 'USR9'
            elif ev.type == S.SND_SEQ_EVENT_SYSEX:
                print 'SYSEX'
            elif ev.type == S.SND_SEQ_EVENT_BOUNCE:
                print 'BOUNCE'
            elif ev.type == S.SND_SEQ_EVENT_USR_VAR0:
                print 'USR_VAR0'
            elif ev.type == S.SND_SEQ_EVENT_USR_VAR1:
                print 'USR_VAR1'
            elif ev.type == S.SND_SEQ_EVENT_USR_VAR2:
                print 'USR_VAR2'
            elif ev.type == S.SND_SEQ_EVENT_USR_VAR3:
                print 'USR_VAR3'
            elif ev.type == S.SND_SEQ_EVENT_USR_VAR4:
                print 'USR_VAR4'
            elif ev.type == S.SND_SEQ_EVENT_NONE:
                print 'NONE'
            else:
                print 'UNKNOWN EVENT TYPE'
                
            if ev.time.time.tv_nsec:
                # convert to ms
                mev.msdeay\
                    (ev.time.time.tv_nsec / 1e6) + (ev.time.time.tv_sec * 1e3)
            else:
                mev.tickev.time.tick
            return mev
        else:
            return None

class SequencerHardware(Sequencer):
    SequencerName"__hw__"
    SequencerStreamS.SND_SEQ_OPEN_DUPLEX
    SequencerType"hw"
    SequencerMode0

    class Client(object):
        def __init__(self, client, name):
            self.clientclient
            self.namename
            self._ports{}

        def __str__(self):
            retstr'] client(%d) "%s"\n' % (self.client, self.name)
            for port in self:
                retstr += str(port)
            return retstr

        def add_port(self, port, name, caps):
            portself.Port(port, name, caps)
            self._ports[name]port

        def __iter__(self):
            return self._ports.itervalues()

        def __len__(self):
            return len(self._ports)

        def get_port(self, key):
            return self._ports[key]
        __getitem__get_port
        
        class Port(object):
            def __init__(self, port, name, caps):
                self.portport
                self.namename
                self.capscaps
                self.caps_readself.caps & S.SND_SEQ_PORT_CAP_READ
                self.caps_writeself.caps & S.SND_SEQ_PORT_CAP_WRITE
                self.caps_subs_readself.caps & S.SND_SEQ_PORT_CAP_SUBS_READ
                self.caps_subs_writeself.caps & S.SND_SEQ_PORT_CAP_SUBS_WRITE

            def __str__(self):
                flags[]
                if self.caps_read: flags.append('r')
                if self.caps_write: flags.append('w')
                if self.caps_subs_read: flags.append('sender')
                if self.caps_subs_write: flags.append('receiver')
                flagsstr.join(', ', flags)
                retstr']   port(%d) [%s] "%s"\n' % (self.port, flags, self.name)
                return retstr


    def init(self):
        self._clients{}
        self._init_handle()
        self._query_clients()

    def __iter__(self):
        return self._clients.itervalues()

    def __len__(self):
        return len(self._clients)

    def get_client(self, key):
        return self._clients[key]
    __getitem__get_client

    def get_client_and_port(self, cname, pname):
        clientself[cname]
        portclient[pname]
        return (client.client, port.port)

    def __str__(self):
        retstr''
        for client in self:
            retstr += str(client)
        return retstr

    def _query_clients(self):
        self._clients{}
        S.snd_seq_drop_output(self.client)
        cinfoS.new_client_info()
        pinfoS.new_port_info()
        S.snd_seq_client_info_set_client(cinfo, -1)
        # for each client
        while S.snd_seq_query_next_client(self.client, cinfo) >= 0:
            clientS.snd_seq_client_info_get_client(cinfo)
            cnameS.snd_seq_client_info_get_name(cinfo)
            cobjself.Client(client, cname)
            self._clients[cname]cobj
            # get port data
            S.snd_seq_port_info_set_client(pinfo, client)
            S.snd_seq_port_info_set_port(pinfo, -1)
            while (S.snd_seq_query_next_port(self.client, pinfo) >= 0):
                capS.snd_seq_port_info_get_capability(pinfo)
                clientS.snd_seq_port_info_get_client(pinfo)
                portS.snd_seq_port_info_get_port(pinfo)
                pnameS.snd_seq_port_info_get_name(pinfo)
                cobj.add_port(port, pname, cap)

class SequencerRead(Sequencer):
    DefaultArguments{
      'sequencer_name':'__SequencerRead__',
      'sequencer_stream':not S.SND_SEQ_NONBLOCK,
      'alsa_port_caps':S.SND_SEQ_PORT_CAP_WRITE | S.SND_SEQ_PORT_CAP_SUBS_WRITE,
    }

    def subscribe_port(self, client, port):
        senderself._new_address(client, port)
        destself._my_address()
        subscribeself._new_subscribe(sender, dest, read=True)
        S.snd_seq_port_subscribe_set_time_update(subscribe, True)
        #S.snd_seq_port_subscribe_set_time_real(subscribe, True)
        self._subscribe_port(subscribe)

class SequencerWrite(Sequencer):
    DefaultArguments{
      'sequencer_name':'__SequencerWrite__',
      'sequencer_stream':not S.SND_SEQ_NONBLOCK,
      'alsa_port_caps':S.SND_SEQ_PORT_CAP_READ | S.SND_SEQ_PORT_CAP_SUBS_READ
    }

    def subscribe_port(self, client, port):
        senderself._my_address()
        destself._new_address(client, port)
        subscribeself._new_subscribe(sender, dest, read=False)
        self._subscribe_port(subscribe)

class SequencerDuplex(Sequencer):
    DefaultArguments{
      'sequencer_name':'__SequencerWrite__',
      'sequencer_stream':not S.SND_SEQ_NONBLOCK,
      'alsa_port_caps':S.SND_SEQ_PORT_CAP_READ | S.SND_SEQ_PORT_CAP_SUBS_READ |
                      S.SND_SEQ_PORT_CAP_WRITE | S.SND_SEQ_PORT_CAP_SUBS_WRITE
    }

    def subscribe_read_port(self, client, port):
        senderself._new_address(client, port)
        destself._my_address()
        subscribeself._new_subscribe(sender, dest, read=True)
        S.snd_seq_port_subscribe_set_time_update(subscribe, True)
        #S.snd_seq_port_subscribe_set_time_real(subscribe, True)
        self._subscribe_port(subscribe)

    def subscribe_write_port(self, client, port):
        senderself._my_address()
        destself._new_address(client, port)
        subscribeself._new_subscribe(sender, dest, read=False)
        self._subscribe_port(subscribe)

